import re
from pathlib import Path
from loguru import logger
import sys
from sqlalchemy import select

from app.engines.ingestion import IngestionEngine
from app.engines.classification import PageClassificationEngine, PageType, ClassificationResult
from app.engines.template import TemplateEngine
from app.engines.mistral_ocr import MistralOCRAdapter
from app.engines.validation import ValidationEngine
from app.engines.storage import StorageEngine
from app.models.domain import Document, Page, Field, ConfidenceLevel
from app.schemas.qc_report import QCReportSchema
from app.schemas.worksheet_polymer import PolymerWorksheetSchema
from app.schemas.production_report import ProductionReportSchema
from app.schemas.stores_requisition import StoresRequisitionSchema
from app.schemas.issue_voucher import IssueVoucherSchema
from app.schemas.deviation_acceptance import DeviationAcceptanceSchema
from app.schemas.product_spec import ProductSpecSchema
from app.schemas.email_schema import EmailSchema
from app.schemas.rm_packing_issuance import RMPackingIssuanceSchema
from app.schemas.packing_details import PackingDetailsSchema
from app.schemas.bmr_checklist import BMRChecklistSchema
from app.schemas.sop import SOPSchema
from app.schemas.bmr import BMRSchema
import cv2

# Ensure debug logs are visible
logger.remove()
logger.add(sys.stderr, level="DEBUG")


def parse_extracted_date(val: str) -> str:
    """Parse dates like DD/MM/YY or DD/MM/YYYY into ISO YYYY-MM-DD."""
    if not val:
        return val
    match = re.search(r"(\d{2})/(\d{2})/(\d{2,4})", val)
    if match:
        d, m, y = match.groups()
        if len(y) == 2:
            y = "20" + y
        return f"{y}-{m}-{d}"
    return val


def get_field_type(config) -> str:
    if not config:
        return "string"
    t = getattr(config, "type", None) or (
        config.get("type") if isinstance(config, dict) else None
    )
    if t and hasattr(t, "value"):  # Handle enum
        return str(t.value)
    return str(t) if t else "string"


class Orchestrator:
    def __init__(self):
        logger.info("Initializing Orchestrator...")
        self.ingestion = IngestionEngine()
        self.classification = PageClassificationEngine()
        self.template_engine = TemplateEngine()

        # Initialize OCR adapters
        self.mistral_ocr = MistralOCRAdapter()
        self.ocr_adapter = self.mistral_ocr
        logger.info("Mistral OCR engine initialized (PaddleOCR disabled)")

        self.validator = ValidationEngine()
        self.storage = StorageEngine()

    def process_document(self, file_path: str):
        logger.info(f"Starting processing for {file_path}")

        # 0. Deduplication Check
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            logger.error(f"File not found: {file_path}")
            return

        # Calculate hash (using ingestion engine's utility)
        file_hash = self.ingestion._calculate_file_hash(file_path_obj)
        logger.info(f"File Hash: {file_hash}")

        session = self.storage.get_session()
        try:
            # Check if hash exists
            existing_doc = session.scalar(
                select(Document).where(Document.file_hash == file_hash)
            )

            if existing_doc:
                logger.info(
                    f"Existing document found (ID: {existing_doc.id}). "
                    f"Re-using classification but re-running extraction."
                )
                doc = existing_doc
                
                # Check for existing classified pages
                db_pages = session.scalars(
                    select(Page).where(Page.document_id == doc.id).order_by(Page.page_number)
                ).all()

                if db_pages and all(p.page_type for p in db_pages):
                    logger.info(f"Reusing {len(db_pages)} classified pages from database.")
                    image_paths = [p.image_path for p in db_pages]
                    
                    # Pre-populate page_data_list to skip Phase 1
                    page_data_list = []
                    for i, p in enumerate(db_pages):
                        # Clear old fields for re-extraction
                        p.fields.clear()
                        
                        # Add to list with existing classification
                        page_data_list.append({
                            "index": i,
                            "img_path": p.image_path,
                            "ocr_text": None, # Will be fetched in Phase 1 if needed
                            "classification": ClassificationResult(
                                page_type=PageType(p.page_type),
                                page_num=p.sub_page_num,
                                total_pages=p.total_pages,
                                score=1.0, # Default high confidence for previously stored results
                                line="" # Not stored in DB
                            ),
                            "db_page": p # Pass through to avoid re-creation
                        })
                else:
                    logger.info("No classified pages found in DB. Clearing and re-running ingestion.")
                    doc.pages.clear()
                    session.commit()
                    image_paths = self.ingestion.process_file(file_path)
                    page_data_list = []
            else:
                # 1. Ingestion (new document)
                image_paths = self.ingestion.process_file(file_path)
                doc = Document(filename=file_path_obj.name, file_hash=file_hash)
                self.storage.save_pending_document(session, doc)
                page_data_list = []
            
            # --- PHASE 1: Classification & Pre-Processing ---
            # Populate or complete page_data_list
            if not page_data_list:
                logger.info(f"Phase 1: Classifying all {len(image_paths)} pages")
                for i, img_path in enumerate(image_paths):
                    # 1a. Read image dimensions
                    img = cv2.imread(img_path)
                    if img is None:
                        logger.error(f"Failed to read image: {img_path}")
                        continue
                    h, w = img.shape[:2]

                    # 1b. OCR (check cache)
                    page_ocr_cache = self.ocr_adapter.extract_text(img_path)
                    
                    # 1c. Classify
                    classification_res = self.classification.classify(
                        page_ocr_cache.text, context=f"{doc.filename} - Page {i + 1}"
                    )
                    
                    page_data_list.append({
                        "index": i,
                        "img_path": img_path,
                        "ocr_text": page_ocr_cache.text,
                        "classification": classification_res,
                        "height": h,
                        "width": w
                    })
                    logger.info(f"Page {i+1} classified as {classification_res.page_type}")
            else:
                # Already have classification, still need OCR text and dimensions for extraction
                for p_data in page_data_list:
                    img_path = p_data["img_path"]
                    
                    # OCR (cached)
                    page_ocr_cache = self.ocr_adapter.extract_text(img_path)
                    p_data["ocr_text"] = page_ocr_cache.text
                    
                    # Dimensions
                    img = cv2.imread(img_path)
                    if img is not None:
                        p_data["height"], p_data["width"] = img.shape[:2]
                    
                    logger.info(f"Page {p_data['index']+1} reusing classification: {p_data['classification'].page_type}")

            # --- PHASE 2: Grouping consecutive pages of same type ---
            logger.info("Phase 2: Grouping consecutive pages")
            groups = []
            if page_data_list:
                current_group = [page_data_list[0]]
                for i in range(1, len(page_data_list)):
                    prev = page_data_list[i-1]
                    curr = page_data_list[i]
                    
                    # Grouping rule: Same page type, and neither is unknown
                    if (curr["classification"].page_type == prev["classification"].page_type and 
                        curr["classification"].page_type != PageType.UNKNOWN):
                        current_group.append(curr)
                    else:
                        groups.append(current_group)
                        current_group = [curr]
                groups.append(current_group)

            # --- PHASE 3: Processing Groups ---
            logger.info(f"Phase 3: Processing {len(groups)} Document Units")
            
            for group_idx, group in enumerate(groups):
                first_page_data = group[0]
                classification_res = first_page_data["classification"]
                page_type = classification_res.page_type
                
                logger.info(f"Processing Group {group_idx + 1}: Type={page_type}, Pages={[p['index']+1 for p in group]}")

                # Create or reuse DB Page records
                db_pages = []
                for p_data in group:
                    if "db_page" in p_data:
                        db_pages.append(p_data["db_page"])
                    else:
                        db_page = Page(
                            document=doc,
                            page_number=p_data["index"] + 1,
                            image_path=str(p_data["img_path"]),
                            page_type=p_data["classification"].page_type.name,
                            sub_page_num=p_data["classification"].page_num,
                            total_pages=p_data["classification"].total_pages,
                        )
                        session.add(db_page)
                        db_pages.append(db_page)
                
                session.flush() # Get IDs

                if page_type == PageType.UNKNOWN:
                    logger.warning(f"Group {group_idx + 1} Unknown Type - Skipping")
                    continue

                # Template Loading
                template = self.template_engine.get_template(page_type.value)
                
                # Extraction & Validation
                processed_via_pattern_b = False
                if template and template.extraction_template:
                    img_paths = [p["img_path"] for p in group]
                    
                    extracted_data = None
                    schema_map = {
                        PageType.QC_TEST_REPORT: QCReportSchema,
                        PageType.WORKSHEET_POLYMER: PolymerWorksheetSchema,
                        PageType.PRODUCTION_REPORT: ProductionReportSchema,
                        PageType.STORES_REQUISITION: StoresRequisitionSchema,
                        PageType.ISSUE_VOUCHER: IssueVoucherSchema,
                        PageType.DEVIATION_ACCEPTANCE: DeviationAcceptanceSchema,
                        PageType.PRODUCT_SPEC: ProductSpecSchema,
                        PageType.EMAIL: EmailSchema,
                        PageType.RM_PACKING_ISSUANCE: RMPackingIssuanceSchema,
                        PageType.PACKING_DETAILS: PackingDetailsSchema,
                        PageType.BMR_CHECKLIST: BMRChecklistSchema,
                        PageType.SOP: SOPSchema,
                        PageType.BMR: BMRSchema,
                    }
                    schema_cls = schema_map.get(page_type)
                    if schema_cls:
                        extracted_data = self.ocr_adapter.extract_structured_data(img_paths, schema_cls)

                    # Map to Database
                    if extracted_data:
                        if page_type == PageType.WORKSHEET_POLYMER:
                            self._process_structured_polymer_worksheet(extracted_data, db_pages, session, template)
                        else:
                            self._process_structured_generic(extracted_data, db_pages, session, template)
                        processed_via_pattern_b = True

                if processed_via_pattern_b:
                    session.commit()
                else:
                    logger.warning(
                        f"Skipping extraction for Group {group_idx + 1} (Type={page_type}): "
                        "No Pattern B Schema registered for this document type. Legacy regex path has been disabled."
                    )

            doc.status = "COMPLETED"
            session.commit()
            logger.info("Document processing complete. Data saved to DB.")

        except Exception:
            logger.exception("Processing failed")
            session.rollback()
        finally:
            session.close()

    def _process_structured_qc_report(self, data: dict, db_pages: list[Page], session, template=None):
        """Deprecated: Now handled by _process_structured_generic."""
        return self._process_structured_generic(data, db_pages, session, template)

    def _process_structured_polymer_worksheet(self, data: dict, db_pages: list[Page], session, template=None):
        """Maps the PolymerWorksheetSchema JSON directly to Field records."""
        logger.info("Mapping Pattern B Polymer Worksheet JSON to database Fields")
        
        # Helper to get page by index (safe)
        def get_pg(idx: int) -> Page:
            if idx < len(db_pages):
                return db_pages[idx]
            return db_pages[-1]

        # 1. Document Header (Metadata) -> PAGE 3 (Index 0)
        p1 = get_pg(0)
        header = data.get("header")
        if header:
            header_fields = {
                "title": "DOC_HEADER_TITLE",
                "document_no": "DOC_HEADER_NO",
                "revision_no": "DOC_HEADER_REV",
                "effective_date": "DOC_HEADER_EFF_DATE",
                "next_revision_due": "DOC_HEADER_NEXT_REV_DATE",
            }
            for key, db_name in header_fields.items():
                val = header.get(key)
                if val:
                    # Get label from template
                    label = key.replace("_", " ").title()
                    if template and hasattr(template, "extraction_template"):
                        h_fields = getattr(template.extraction_template, "header_fields", {}) or {}
                        field_cfg = h_fields.get(key.upper()) or h_fields.get(key)
                        if field_cfg:
                            label = getattr(field_cfg, "label", label) or label

                    f = Field(
                        page=p1,
                        name=db_name,
                        label=label.strip(": "),
                        field_type="string",
                        ocr_value=str(val).strip(),
                        roi_coordinates="0,0,0,0",
                        ocr_confidence=0.95,
                        confidence_level=ConfidenceLevel.GREEN,
                    )
                    session.add(f)

        # 2. Batch Details Header -> PAGE 4 (Index 1)
        p2 = get_pg(1)
        batch_mapping = {
            "product_code": "PRODUCT_CODE",
            "ar_no": "AR_NO",
            "batch_no": "BATCH_NO",
            "containers_packs": "CONTAINERS_PACKING",
            "batch_quantity": "BATCH_QUANTITY",
            "sampled_quantity": "SAMPLED_QUANTITY",
            "sampling_date": "SAMPLING_DATE",
            "analysis_date": "ANALYSIS_DATE",
            "release_date": "RELEASE_DATE",
        }

        for key, db_name in batch_mapping.items():
            val = data.get(key)
            if val is not None and str(val).strip():
                f_type = "date" if "date" in key else "string"
                if f_type == "date" and isinstance(val, str):
                    val = parse_extracted_date(val)
                
                # Get label from template
                label = key.replace("_", " ").title()
                if template and hasattr(template, "extraction_template"):
                    h_fields = getattr(template.extraction_template, "header_fields", {}) or {}
                    field_cfg = h_fields.get(key.upper()) or h_fields.get(key)
                    if field_cfg:
                        label = getattr(field_cfg, "label", label) or label

                f = Field(
                    page=p2,
                    name=db_name,
                    label=label.strip(": "),
                    field_type=f_type,
                    ocr_value=str(val).strip(),
                    roi_coordinates="0,0,0,0",
                    ocr_confidence=0.95,
                    confidence_level=ConfidenceLevel.GREEN,
                )
                session.add(f)

        # 3. Main Generic Tests -> Distributed (P3/P4)
        generic_tests = data.get("generic_tests", [])
        for row in generic_tests:
            param = row.get("parameter")
            obs = row.get("observation")
            complies = row.get("complies")
            sr_no = row.get("sr_no")

            if param and obs is not None:
                # Distribution Logic: Test 08 (Charge) and above belong on P4+
                # Based on user feedback, "Charge" (Sr No 8) is on Page 4.
                target_page = p1 # Page 3
                if sr_no and sr_no >= 8:
                    target_page = p2 # Page 4
                elif param and "CHARGE" in param.upper():
                    target_page = p2 # Page 4

                clean_param = re.sub(r"[^A-Z0-9]", "_", param.upper()).strip("_")
                f = Field(
                    page=target_page,
                    name=f"TABLE_TEST_{clean_param}",
                    label=param, # USE FIELD NAMES PROVIDED BY OCR
                    field_type="string",
                    ocr_value=str(obs).strip(),
                    sr_no=sr_no,
                    roi_coordinates="0,0,0,0",
                    ocr_confidence=0.95,
                    confidence_level=ConfidenceLevel.GREEN,
                )
                session.add(f)
                
                if complies is not None:
                    f_comp = Field(
                        page=target_page,
                        name=f"TABLE_TEST_{clean_param}_COMPLIANCE",
                        label=f"{param} (Compliance)",
                        field_type="boolean",
                        ocr_value=str(complies),
                        sr_no=sr_no,
                        roi_coordinates="0,0,0,0",
                        ocr_confidence=0.95,
                        confidence_level=ConfidenceLevel.GREEN,
                    )
                    session.add(f_comp)

        # 4. Solid Content (Test 09) -> PAGE 4 (Index 1)
        sc = data.get("solid_content")
        if sc:
            for dish_key in ["dish_1", "dish_2"]:
                dish = sc.get(dish_key)
                if dish:
                    prefix = f"TABLE_SC_{dish_key.upper()}"
                    dish_fields = {
                        "dish_id": f"{prefix}_ID",
                        "weight_empty_dish": f"{prefix}_EMPTY_WEIGHT",
                        "weight_dish_plus_sample": f"{prefix}_DISH_PLUS_SAMPLE",
                        "weight_sample": f"{prefix}_SAMPLE_WEIGHT",
                        "weight_dried_sample_with_dish": f"{prefix}_DRIED_WITH_DISH",
                        "net_weight_dried_sample": f"{prefix}_NET_DRIED",
                        "sc_percentage": f"{prefix}_SC_PERCENT",
                    }
                    for k, db_name in dish_fields.items():
                        v = dish.get(k)
                        if v:
                            # Prettier labels for SC
                            label_map = {
                                "dish_id": "Dish ID",
                                "weight_empty_dish": "Empty Dish Weight",
                                "weight_dish_plus_sample": "Dish + Sample Weight",
                                "weight_sample": "Sample Weight",
                                "weight_dried_sample_with_dish": "Dried Sample w/ Dish",
                                "net_weight_dried_sample": "Net Dried Weight",
                                "sc_percentage": "SC %",
                            }
                            friendly_label = label_map.get(k, k.replace("_", " ").title())
                            full_label = f"Dish {dish_key[-1]} - {friendly_label}"

                            f = Field(
                                page=p2,
                                name=db_name,
                                label=full_label,
                                field_type="string",
                                ocr_value=str(v).strip(),
                                roi_coordinates="0,0,0,0",
                                ocr_confidence=0.95,
                                confidence_level=ConfidenceLevel.GREEN,
                            )
                            session.add(f)
            
            if sc.get("average_sc_percentage"):
                f_avg = Field(
                    page=p2,
                    name="TABLE_SC_AVERAGE_PERCENT",
                    label="Solid Content - Average %",
                    field_type="string",
                    ocr_value=str(sc["average_sc_percentage"]).strip(),
                    roi_coordinates="0,0,0,0",
                    ocr_confidence=0.95,
                    confidence_level=ConfidenceLevel.GREEN,
                )
                session.add(f_avg)
            
            if sc.get("complies") is not None:
                f_comp = Field(
                    page=p2,
                    name="TABLE_SC_COMPLIANCE",
                    label="Solid Content - Compliance",
                    field_type="boolean",
                    ocr_value=str(sc["complies"]),
                    roi_coordinates="0,0,0,0",
                    ocr_confidence=0.95,
                    confidence_level=ConfidenceLevel.GREEN,
                )
                session.add(f_comp)

        # 5. Stability Tests (Test 10) -> PAGE 4 (Index 1)
        stability = data.get("stability")
        if stability:
            results = stability.get("results", [])
            for i, row in enumerate(results):
                interval = row.get("interval", f"INT_{i}").upper().replace(" ", "_").replace(".", "_")
                for sub_field in ["ph", "viscosity"]:
                    val = row.get(sub_field)
                    if val is not None:
                        f = Field(
                            page=p2,
                            name=f"TABLE_STABILITY_80C_{interval}_{sub_field.upper()}",
                            label=f"Stability 80C ({interval}) - {sub_field.upper()}",
                            field_type="float",
                            ocr_value=str(val),
                            roi_coordinates="0,0,0,0",
                            ocr_confidence=0.95,
                            confidence_level=ConfidenceLevel.GREEN,
                        )
                        session.add(f)

        # 6. Other Tests (Test 11) -> PAGE 5 (Index 2)
        p3 = get_pg(2)
        others = data.get("other_tests")
        if others:
            if others.get("grains_gel"):
                f = Field(
                    page=p3,
                    name="TABLE_TEST_GRAINS_GEL",
                    label="Grains / Gel",
                    field_type="string",
                    ocr_value=str(others["grains_gel"]).strip(),
                    roi_coordinates="0,0,0,0",
                    ocr_confidence=0.95,
                    confidence_level=ConfidenceLevel.GREEN,
                )
                session.add(f)
            if others.get("wet_strength_n"):
                f = Field(
                    page=p3,
                    name="TABLE_TEST_WET_STRENGTH",
                    label="Wet Strength (N)",
                    field_type="string",
                    ocr_value=str(others["wet_strength_n"]).strip(),
                    roi_coordinates="0,0,0,0",
                    ocr_confidence=0.95,
                    confidence_level=ConfidenceLevel.GREEN,
                )
                session.add(f)

        # 7. Footer / Signatures -> PAGE 5 (Index 2)
        footer_fields = {
            "compliance_statement": "COMPLIANCE_STATEMENT",
            "final_remark": "FINAL_REMARK",
            "analyzed_by": "ANALYZED_BY",
            "analyzed_by_date": "ANALYZED_BY_DATE",
            "checked_by": "CHECKED_BY",
            "checked_by_date": "CHECKED_BY_DATE",
            "prepared_by": "PREPARED_BY",
            "prepared_by_date": "PREPARED_BY_DATE",
            "reviewed_by": "REVIEWED_BY",
            "reviewed_by_date": "REVIEWED_BY_DATE",
            "approved_by": "APPROVED_BY",
            "approved_by_date": "APPROVED_BY_DATE",
        }

        for key, db_name in footer_fields.items():
            val = data.get(key)
            if val is not None and str(val).strip():
                label = key.replace("_", " ").title()
                if template and hasattr(template, "extraction_template"):
                    f_fields = getattr(template.extraction_template, "footer_fields", {}) or {}
                    field_cfg = f_fields.get(key.upper()) or f_fields.get(key)
                    if field_cfg:
                        if isinstance(field_cfg, dict):
                            label = field_cfg.get("label", label)
                        else:
                            label = getattr(field_cfg, "label", label) or label

                f = Field(
                    page=p3,
                    name=db_name,
                    label=label.strip(": "),
                    field_type="string",
                    ocr_value=str(val).strip(),
                    roi_coordinates="0,0,0,0",
                    ocr_confidence=0.95,
                    confidence_level=ConfidenceLevel.GREEN,
                )
                session.add(f)

    # ================================================================
    # Helper: Shared field creator (reduces duplication)
    # ================================================================

    def _add_field(self, session, page, name, value, label=None,
                   field_type="string", sr_no=None, confidence=0.95):
        """Creates and adds a Field record to the session."""
        if value is None or not str(value).strip():
            return
        if field_type == "date" and isinstance(value, str):
            value = parse_extracted_date(value)
        f = Field(
            page=page,
            name=name,
            label=(label or name.replace("_", " ").title()).strip(": "),
            field_type=field_type,
            ocr_value=str(value).strip(),
            sr_no=sr_no,
            roi_coordinates="0,0,0,0",
            ocr_confidence=confidence,
            confidence_level=ConfidenceLevel.GREEN,
        )
        session.add(f)

    def _get_template_label(self, template, section, key, fallback):
        """Looks up a human-readable label from a template section."""
        if not template or not hasattr(template, "extraction_template"):
            return fallback
        fields = getattr(template.extraction_template, section, {}) or {}
        cfg = fields.get(key.upper()) or fields.get(key)
        if cfg:
            lbl = getattr(cfg, "label", None) if not isinstance(cfg, dict) else cfg.get("label")
            if lbl:
                return lbl
        return fallback

    def _process_structured_qc_report(self, data: dict, db_pages: list[Page], session, template=None):
        """Deprecated: Now handled by _process_structured_generic."""
        return self._process_structured_generic(data, db_pages, session, template)

    def _process_structured_polymer_worksheet(self, data: dict, db_pages: list[Page], session, template=None):
        """Maps the PolymerWorksheetSchema JSON directly to Field records."""
        logger.info("Mapping Pattern B Polymer Worksheet JSON to database Fields")
        
        # Helper to get page by index (safe)
        def get_pg(idx: int) -> Page:
            if idx < len(db_pages):
                return db_pages[idx]
            return db_pages[-1]

        # 1. Document Header (Metadata) -> PAGE 3 (Index 0)
        p1 = get_pg(0)
        header = data.get("header")
        if header:
            header_fields = {
                "title": "DOC_HEADER_TITLE",
                "document_no": "DOC_HEADER_NO",
                "revision_no": "DOC_HEADER_REV",
                "effective_date": "DOC_HEADER_EFF_DATE",
                "next_revision_due": "DOC_HEADER_NEXT_REV_DATE",
            }
            for key, db_name in header_fields.items():
                val = header.get(key)
                if val:
                    # Get label from template
                    label = key.replace("_", " ").title()
                    if template and hasattr(template, "extraction_template"):
                        h_fields = getattr(template.extraction_template, "header_fields", {}) or {}
                        field_cfg = h_fields.get(key.upper()) or h_fields.get(key)
                        if field_cfg:
                            label = getattr(field_cfg, "label", label) or label

                    f = Field(
                        page=p1,
                        name=db_name,
                        label=label.strip(": "),
                        field_type="string",
                        ocr_value=str(val).strip(),
                        roi_coordinates="0,0,0,0",
                        ocr_confidence=0.95,
                        confidence_level=ConfidenceLevel.GREEN,
                    )
                    session.add(f)

        # 2. Batch Details Header -> PAGE 4 (Index 1)
        p2 = get_pg(1)
        batch_mapping = {
            "product_code": "PRODUCT_CODE",
            "ar_no": "AR_NO",
            "batch_no": "BATCH_NO",
            "containers_packs": "CONTAINERS_PACKING",
            "batch_quantity": "BATCH_QUANTITY",
            "sampled_quantity": "SAMPLED_QUANTITY",
            "sampling_date": "SAMPLING_DATE",
            "analysis_date": "ANALYSIS_DATE",
            "release_date": "RELEASE_DATE",
        }

        for key, db_name in batch_mapping.items():
            val = data.get(key)
            if val is not None and str(val).strip():
                f_type = "date" if "date" in key else "string"
                if f_type == "date" and isinstance(val, str):
                    val = parse_extracted_date(val)
                
                # Get label from template
                label = key.replace("_", " ").title()
                if template and hasattr(template, "extraction_template"):
                    h_fields = getattr(template.extraction_template, "header_fields", {}) or {}
                    field_cfg = h_fields.get(key.upper()) or h_fields.get(key)
                    if field_cfg:
                        label = getattr(field_cfg, "label", label) or label

                f = Field(
                    page=p2,
                    name=db_name,
                    label=label.strip(": "),
                    field_type=f_type,
                    ocr_value=str(val).strip(),
                    roi_coordinates="0,0,0,0",
                    ocr_confidence=0.95,
                    confidence_level=ConfidenceLevel.GREEN,
                )
                session.add(f)

        # 3. Main Generic Tests -> Distributed (P3/P4)
        generic_tests = data.get("generic_tests", [])
        for row in generic_tests:
            param = row.get("parameter")
            obs = row.get("observation")
            complies = row.get("complies")
            sr_no = row.get("sr_no")

            if param and obs is not None:
                # Distribution Logic: Test 08 (Charge) and above belong on P4+
                target_page = p1 # Page 3
                if sr_no and sr_no >= 8:
                    target_page = p2 # Page 4
                elif param and "CHARGE" in param.upper():
                    target_page = p2 # Page 4

                clean_param = re.sub(r"[^A-Z0-9]", "_", param.upper()).strip("_")
                f = Field(
                    page=target_page,
                    name=f"TABLE_TEST_{clean_param}",
                    label=param, # USE FIELD NAMES PROVIDED BY OCR
                    field_type="string",
                    ocr_value=str(obs).strip(),
                    sr_no=sr_no,
                    roi_coordinates="0,0,0,0",
                    ocr_confidence=0.95,
                    confidence_level=ConfidenceLevel.GREEN,
                )
                session.add(f)
                
                if complies is not None:
                    f_comp = Field(
                        page=target_page,
                        name=f"TABLE_TEST_{clean_param}_COMPLIANCE",
                        label=f"{param} (Compliance)",
                        field_type="boolean",
                        ocr_value=str(complies),
                        sr_no=sr_no,
                        roi_coordinates="0,0,0,0",
                        ocr_confidence=0.95,
                        confidence_level=ConfidenceLevel.GREEN,
                    )
                    session.add(f_comp)

        # 4. Solid Content (Test 09) -> PAGE 4 (Index 1)
        p2 = get_pg(1)
        sc = data.get("solid_content")
        if sc:
            for dish_key in ["dish_1", "dish_2"]:
                dish = sc.get(dish_key)
                if dish:
                    prefix = f"TABLE_SC_{dish_key.upper()}"
                    dish_fields = {
                        "dish_id": f"{prefix}_ID",
                        "weight_empty_dish": f"{prefix}_EMPTY_WEIGHT",
                        "weight_dish_plus_sample": f"{prefix}_DISH_PLUS_SAMPLE",
                        "weight_sample": f"{prefix}_SAMPLE_WEIGHT",
                        "weight_dried_sample_with_dish": f"{prefix}_DRIED_WITH_DISH",
                        "net_weight_dried_sample": f"{prefix}_NET_DRIED",
                        "sc_percentage": f"{prefix}_SC_PERCENT",
                    }
                    for k, db_name in dish_fields.items():
                        v = dish.get(k)
                        if v:
                            # Prettier labels for SC
                            label_map = {
                                "dish_id": "Dish ID",
                                "weight_empty_dish": "Empty Dish Weight",
                                "weight_dish_plus_sample": "Dish + Sample Weight",
                                "weight_sample": "Sample Weight",
                                "weight_dried_sample_with_dish": "Dried Sample w/ Dish",
                                "net_weight_dried_sample": "Net Dried Weight",
                                "sc_percentage": "SC %",
                            }
                            friendly_label = label_map.get(k, k.replace("_", " ").title())
                            full_label = f"Dish {dish_key[-1]} - {friendly_label}"

                            f = Field(
                                page=p2,
                                name=db_name,
                                label=full_label,
                                field_type="string",
                                ocr_value=str(v).strip(),
                                roi_coordinates="0,0,0,0",
                                ocr_confidence=0.95,
                                confidence_level=ConfidenceLevel.GREEN,
                            )
                            session.add(f)
            
            if sc.get("average_sc_percentage"):
                f_avg = Field(
                    page=p2,
                    name="TABLE_SC_AVERAGE_PERCENT",
                    label="Solid Content - Average %",
                    field_type="string",
                    ocr_value=str(sc["average_sc_percentage"]).strip(),
                    roi_coordinates="0,0,0,0",
                    ocr_confidence=0.95,
                    confidence_level=ConfidenceLevel.GREEN,
                )
                session.add(f_avg)
            
            if sc.get("complies") is not None:
                f_comp = Field(
                    page=p2,
                    name="TABLE_SC_COMPLIANCE",
                    label="Solid Content - Compliance",
                    field_type="boolean",
                    ocr_value=str(sc["complies"]),
                    roi_coordinates="0,0,0,0",
                    ocr_confidence=0.95,
                    confidence_level=ConfidenceLevel.GREEN,
                )
                session.add(f_comp)

        # 5. Stability Tests (Test 10) -> PAGE 4 (Index 1)
        stability = data.get("stability")
        if stability:
            results = stability.get("results", [])
            for i, row in enumerate(results):
                interval = row.get("interval", f"INT_{i}").upper().replace(" ", "_").replace(".", "_")
                for sub_field in ["ph", "viscosity"]:
                    val = row.get(sub_field)
                    if val is not None:
                        f = Field(
                            page=p2,
                            name=f"TABLE_STABILITY_80C_{interval}_{sub_field.upper()}",
                            label=f"Stability 80C ({interval}) - {sub_field.upper()}",
                            field_type="float",
                            ocr_value=str(val),
                            roi_coordinates="0,0,0,0",
                            ocr_confidence=0.95,
                            confidence_level=ConfidenceLevel.GREEN,
                        )
                        session.add(f)

        # 6. Other Tests (Test 11) -> PAGE 5 (Index 2)
        p3 = get_pg(2)
        others = data.get("other_tests")
        if others:
            if others.get("grains_gel"):
                f = Field(
                    page=p3,
                    name="TABLE_TEST_GRAINS_GEL",
                    label="Grains / Gel",
                    field_type="string",
                    ocr_value=str(others["grains_gel"]).strip(),
                    roi_coordinates="0,0,0,0",
                    ocr_confidence=0.95,
                    confidence_level=ConfidenceLevel.GREEN,
                )
                session.add(f)
            if others.get("wet_strength_n"):
                f = Field(
                    page=p3,
                    name="TABLE_TEST_WET_STRENGTH",
                    label="Wet Strength (N)",
                    field_type="string",
                    ocr_value=str(others["wet_strength_n"]).strip(),
                    roi_coordinates="0,0,0,0",
                    ocr_confidence=0.95,
                    confidence_level=ConfidenceLevel.GREEN,
                )
                session.add(f)

        # 7. Footer / Signatures -> PAGE 5 (Index 2)
        footer_fields = {
            "compliance_statement": "COMPLIANCE_STATEMENT",
            "final_remark": "FINAL_REMARK",
            "analyzed_by": "ANALYZED_BY",
            "analyzed_by_date": "ANALYZED_BY_DATE",
            "checked_by": "CHECKED_BY",
            "checked_by_date": "CHECKED_BY_DATE",
            "prepared_by": "PREPARED_BY",
            "prepared_by_date": "PREPARED_BY_DATE",
            "reviewed_by": "REVIEWED_BY",
            "reviewed_by_date": "REVIEWED_BY_DATE",
            "approved_by": "APPROVED_BY",
            "approved_by_date": "APPROVED_BY_DATE",
        }

        for key, db_name in footer_fields.items():
            val = data.get(key)
            if val is not None and str(val).strip():
                label = key.replace("_", " ").title()
                if template and hasattr(template, "extraction_template"):
                    f_fields = getattr(template.extraction_template, "footer_fields", {}) or {}
                    field_cfg = f_fields.get(key.upper()) or f_fields.get(key)
                    if field_cfg:
                        if isinstance(field_cfg, dict):
                            label = field_cfg.get("label", label)
                        else:
                            label = getattr(field_cfg, "label", label) or label

                f = Field(
                    page=p3,
                    name=db_name,
                    label=label.strip(": "),
                    field_type="string",
                    ocr_value=str(val).strip(),
                    roi_coordinates="0,0,0,0",
                    ocr_confidence=0.95,
                    confidence_level=ConfidenceLevel.GREEN,
                )
                session.add(f)

    # ================================================================
    # Generic Mapper (for all remaining document types)
    # ================================================================

    def _process_structured_generic(self, data: dict, db_pages: list[Page], session, template=None):
        """Maps any Pydantic-extracted JSON to Field records by walking the dict.
        
        Handles:
        - Flat scalar fields (string, date, boolean, etc.)
        - Nested dicts (flattened as PARENT_CHILD)
        - Lists of dicts (table rows with automatic sr_no detection)
        """
        logger.info("Mapping Pattern B (generic) JSON to database Fields")
        page = db_pages[0]

        for key, value in data.items():
            if value is None:
                continue

            db_key = key.upper()
            label = self._get_template_label(template, "header_fields", key, key.replace("_", " ").title())
            
            # Smart type detection
            if isinstance(value, bool) or str(value).lower() in ("true", "false"):
                f_type = "boolean"
            elif "date" in key.lower() or "dated" in key.lower():
                f_type = "date"
            else:
                f_type = "string"

            # Case 1: Scalar (string, int, float, bool)
            if isinstance(value, (str, int, float, bool)):
                # Also check footer_fields for label if not in header
                if not self._get_template_label(template, "header_fields", key, None):
                    footer_label = self._get_template_label(template, "footer_fields", key, None)
                    if footer_label:
                        label = footer_label
                
                self._add_field(session, page, db_key, value, label=label, field_type=f_type)

            # Case 2: Nested dict (e.g., batch_reconciliation)
            elif isinstance(value, dict):
                for sub_key, sub_val in value.items():
                    if sub_val is not None and str(sub_val).strip():
                        flat_name = f"{db_key}_{sub_key.upper()}"
                        sub_label = sub_key.replace("_", " ").title()
                        
                        # Sub-key type detection
                        if isinstance(sub_val, bool) or str(sub_val).lower() in ("true", "false"):
                            sub_type = "boolean"
                        elif "date" in sub_key.lower() or "dated" in sub_key.lower():
                            sub_type = "date"
                        else:
                            sub_type = "string"
                            
                        self._add_field(session, page, flat_name, sub_val, label=sub_label, field_type=sub_type)

            # Case 3: List of dicts (table rows)
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                table_prefix = f"TABLE_{db_key}"
                for i, row in enumerate(value):
                    # Auto-detect serial number column
                    sr = row.get("sr_no") or row.get("sn") or row.get("no") or row.get("sr") or (i + 1)
                    for col, col_val in row.items():
                        if col in ("sr_no", "sn", "no", "sr"):
                            continue
                        if col_val is not None and str(col_val).strip():
                            col_name = f"{table_prefix}_{col.upper()}"
                            col_label = col.replace("_", " ").title()
                            
                            # Column type detection
                            col_type = "date" if "date" in col.lower() else "string"
                            
                            self._add_field(
                                session, page,
                                name=col_name,
                                value=col_val,
                                label=col_label,
                                field_type=col_type,
                                sr_no=sr,
                            )

            # Case 4: List of scalars (e.g., tags, simple lists)
            elif isinstance(value, list):
                joined = ", ".join(str(v) for v in value if v is not None)
                if joined.strip():
                    self._add_field(session, page, db_key, joined, label=label)
