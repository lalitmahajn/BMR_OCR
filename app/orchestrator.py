import re
from pathlib import Path
from loguru import logger
import sys
from sqlalchemy import select

from app.engines.ingestion import IngestionEngine
from app.engines.classification import PageClassificationEngine, PageType, ClassificationResult
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
    """Standardize date formats to DD/MM/YYYY."""
    if not val:
        return val
    
    # 1. Try DD/MM/YYYY or DD-MM-YYYY (or 2-digit years)
    match_dmv = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})", val)
    if match_dmv:
        d, m, y = match_dmv.groups()
        if len(y) == 2:
            y = "20" + y
        return f"{int(d):02}/{int(m):02}/{y}"
    
    # 2. Try YYYY-MM-DD (ISO)
    match_iso = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", val)
    if match_iso:
        y, m, d = match_iso.groups()
        return f"{int(d):02}/{int(m):02}/{y}"
        
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

                # Extraction & Validation
                processed_via_pattern_b = False
                
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
                    logger.info(f"Successfully extracted {len(extracted_data)} top-level keys for Group {group_idx + 1}")
                    self._process_structured_generic(extracted_data, db_pages, session, page_type)
                    processed_via_pattern_b = True
                else:
                    logger.error(f"Pattern B extraction RETURNED NULL for Group {group_idx + 1} (Type={page_type})")

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

    def _process_structured_qc_report(self, data: dict, db_pages: list[Page], session):
        """Deprecated: Now handled by _process_structured_generic."""
        return self._process_structured_generic(data, db_pages, session)

    def _process_structured_polymer_worksheet(self, data: dict, db_pages: list[Page], session):
        """Deprecated: Now handled by _process_structured_generic."""
        return self._process_structured_generic(data, db_pages, session, page_type=PageType.WORKSHEET_POLYMER)

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

    def _get_template_label(self, key, fallback):
        """Deprecated: Now replaced by auto-labeling logic in _flatten_and_add_generic."""
        return fallback

    def _process_structured_qc_report(self, data: dict, db_pages: list[Page], session):
        """Deprecated: Now handled by _process_structured_generic."""
        return self._process_structured_generic(data, db_pages, session, page_type=PageType.QC_TEST_REPORT)

    # ================================================================
    # Generic Mapper (for all remaining document types)
    # ================================================================

    def _get_target_page(self, key: str, value, db_pages: list[Page], page_type=None) -> Page:
        """Determines which physical page in a document unit should receive a field."""
        if not db_pages:
            return None
        if len(db_pages) == 1:
            return db_pages[0]

        # 1. Check for footer/signature names (usually last page)
        is_footer = False
        kl = key.lower()
        if any(w in kl for w in ("signature", "remark", "footer", "reviewed_by", "approved_by", "checked_by")):
            is_footer = True
            
        if is_footer:
            return db_pages[-1]

        # 2. Document-specific distribution (Pattern-based)
        if page_type == PageType.BMR_CHECKLIST:
            # Section A (Review Points) -> Page 1
            if key == "review_points":
                return db_pages[0]
            # Section B (Attachments) -> Page 2
            if key == "attachments":
                return db_pages[1] if len(db_pages) > 1 else db_pages[0]
        
        if page_type == PageType.SOP:
            if "REVISION" in key.upper():
                return db_pages[-1]

        if page_type == PageType.WORKSHEET_POLYMER:
            # Page distribution (Assuming db_pages index 0=P3, 1=P4, 2=P5)
            ukey = key.upper()
            if "PAGE_4" in ukey or "STABILITY" in ukey or "SOLID_CONTENT" in ukey or "CHARGE" in ukey:
                return db_pages[1] if len(db_pages) > 1 else db_pages[0]
            if "PAGE_5" in ukey or "GRAINS" in ukey or "WET_STRENGTH" in ukey:
                return db_pages[2] if len(db_pages) > 2 else db_pages[-1]
            return db_pages[0]

        # Default to first page for headers/scalars
        return db_pages[0]

    def _flatten_and_add_generic(self, session, data: dict, target_page, db_pages, page_type, prefix=""):
        """Recursively flattens nested dicts into database fields with smart labeling."""
        for key, value in data.items():
            if value is None:
                continue

            field_name = f"{prefix}_{key}".upper() if prefix else key.upper()
            
            if isinstance(value, dict):
                # Recurse
                self._flatten_and_add_generic(session, value, target_page, db_pages, page_type, prefix=field_name)
            elif isinstance(value, (str, int, float, bool)):
                # Cleanup Label & Fix "Results" labeling
                clean_name = field_name
                
                # SMART FIX: If we are at a leaf named "RESULTS" or "COMPLIES", 
                # we want the parent key to be the basis of our label.
                # E.g. PAGE_3_TESTS_PHYSICAL_APPEARANCE_RESULTS -> PHYSICAL_APPEARANCE
                if clean_name.endswith("_RESULTS"):
                    clean_name = clean_name.replace("_RESULTS", "")
                elif clean_name.endswith("_COMPLIES"):
                    # We might want to keep "Compliance" if it's the checkmark
                    if "APPEARANCE" in clean_name or "VISCOSITY" in clean_name or "PH" in clean_name:
                         clean_name = clean_name.replace("_COMPLIES", "_COMPLIANCE")

                prefixes_to_strip = ["GENERIC_TESTS_", "PAGE_1_TESTS_", "PAGE_3_TESTS_", "PAGE_4_TESTS_", "PAGE_5_TESTS_", "TEST_RESULTS_"]
                for p in prefixes_to_strip:
                    if clean_name.startswith(p):
                        clean_name = clean_name.replace(p, "")
                
                label = clean_name.replace("_", " ").title().strip()
                
                # Specific overrides for acronyms
                if label.startswith("Ph "):
                    label = "pH " + label[3:]
                elif label == "Ph":
                    label = "pH"
                elif "Ar No" in label:
                    label = label.replace("Ar No", "AR No")
                elif "Sc Percentage" in label:
                    label = label.replace("Sc Percentage", "SC %")

                # Type detection
                if isinstance(value, bool) or str(value).lower() in ("true", "false"):
                    f_type = "boolean"
                elif "date" in field_name.lower() or "date" in key.lower():
                    f_type = "date"
                else:
                    f_type = "string"

                self._add_field(session, target_page, field_name, value, label=label, field_type=f_type)

    def _process_structured_generic(self, data: dict, db_pages: list[Page], session, page_type=None):
        """Maps any Pydantic-extracted JSON to Field records by walking the dict.
        
        Distributes fields across multi-page units if multiple db_pages are provided.
        """
        logger.info(f"Mapping Pattern B (generic) JSON to {len(db_pages)} database Pages")
        
        for key, value in data.items():
            if value is None:
                continue

            # Determine target page for this specific key
            target_page = self._get_target_page(key, value, db_pages, page_type)
            db_key = key.upper()

            # Recursive flattening for scalars and dicts
            if isinstance(value, (str, int, float, bool, dict)):
                self._flatten_and_add_generic(session, {key: value}, target_page, db_pages, page_type)

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
                                session, target_page,
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
                    self._add_field(session, target_page, db_key, joined, label=db_key.replace("_", " ").title())
