import re
from pathlib import Path
from loguru import logger


from app.engines.ingestion import IngestionEngine
from app.engines.classification import PageClassificationEngine, PageType
from app.engines.template import TemplateEngine
from app.engines.mistral_ocr import MistralOCRAdapter
from app.engines.validation import ValidationEngine
from app.engines.storage import StorageEngine
from app.engines.extraction import MarkdownExtractionEngine
from app.models.domain import Document, Page, Field


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
        self.extraction_engine = MarkdownExtractionEngine()

    def process_document(self, file_path: str):
        logger.info(f"Starting processing for {file_path}")

        # 1. Ingestion
        image_paths = self.ingestion.process_file(file_path)

        # Create DB Document (Pending)
        session = self.storage.get_session()
        doc = Document(filename=Path(file_path).name)
        self.storage.save_pending_document(session, doc)

        # Persistence cache for header fields (keyed by page_type)
        header_cache = {}

        try:
            for i, img_path in enumerate(image_paths):
                logger.info(f"Processing Page {i + 1}: {img_path}")

                # Read image dimensions
                import cv2

                img = cv2.imread(img_path)
                h, w = img.shape[:2]

                # 2. OCR (with check if output is already present/cached)
                cache_file = Path(img_path).with_suffix(".md")
                if cache_file.exists():
                    logger.info(
                        f"Page {i + 1}: Skipping Mistral API (Local OCR Cache Found)"
                    )

                page_ocr_cache = self.ocr_adapter.extract_text(img_path)

                # Export to output folder for audit
                if page_ocr_cache.text:
                    try:
                        doc_output_dir = Path("output") / Path(file_path).stem
                        doc_output_dir.mkdir(parents=True, exist_ok=True)
                        output_file = doc_output_dir / f"page_{i + 1}.md"
                        with open(output_file, "w", encoding="utf-8") as f:
                            f.write(page_ocr_cache.text)
                        logger.info(f"Saved raw OCR to {output_file}")
                    except Exception as e:
                        logger.error(f"Failed to save raw OCR output: {e}")

                # 2. Classification using cached OCR result
                classification_res = self.classification.classify(
                    page_ocr_cache.text, context=f"{doc.filename} - Page {i + 1}"
                )
                page_type_name = classification_res.page_type.name

                # Create Page
                db_page = Page(
                    document=doc,
                    page_number=i + 1,
                    image_path=str(img_path),
                    page_type=page_type_name,
                    sub_page_num=classification_res.page_num,
                    total_pages=classification_res.total_pages,
                )
                session.add(db_page)

                if classification_res.page_type == PageType.UNKNOWN:
                    logger.warning(
                        f"Page {i + 1} Unknown Type - Skipping specific extraction"
                    )
                    continue

                # 3. Template Loading
                template = self.template_engine.get_template(
                    classification_res.page_type.value
                )
                fields_def = self.template_engine.get_fields(
                    classification_res.page_type.value, w, h
                )

                # 4. Extraction & Validation
                # --- NEW: Nested Extraction Logic ---
                if template and template.extraction_template:
                    logger.info(
                        f"Using Nested Extraction for {classification_res.page_type}"
                    )
                    nested_res = self.extraction_engine.process_nested_template(
                        page_ocr_cache.text, template.extraction_template
                    )

                    # Initialize cache for this page type if missing
                    if page_type_name not in header_cache:
                        header_cache[page_type_name] = {}

                    # 4a. Process Headers (with Persistence)
                    for key, data in nested_res["headers"].items():
                        val = data["value"]
                        config = data["config"]

                        # PERSISTENCE LOGIC:
                        # If val is empty but we have a cached value for this doc type, use it
                        if not val and key in header_cache[page_type_name]:
                            val = header_cache[page_type_name][key]
                            logger.debug(f"Inherited header '{key}': {val}")
                        elif val:
                            # Update cache with fresh value
                            header_cache[page_type_name][key] = val

                        conf_level = self.validator.validate_field(val, config)
                        f = Field(
                            page=db_page,
                            name=key,
                            ocr_value=val,
                            roi_coordinates="0,0,0,0",
                            confidence_level=conf_level,
                        )
                        session.add(f)

                    # 4b. Process Table Rows
                    for row_data in nested_res["rows"]:
                        extracted = row_data["extracted"]
                        config = row_data["config"]
                        ext_tpl = template.extraction_template

                        # PRIORITY 1: Check row-specific result labels
                        dynamic_keys = [
                            "observation_label",
                            "result_label",
                            "extracted_label",
                            "value_label",
                        ]
                        target_label = None
                        for dk in dynamic_keys:
                            if hasattr(config, dk) and getattr(config, dk):
                                target_label = getattr(config, dk)
                                break

                        res_key = None
                        from thefuzz import fuzz

                        if target_label:
                            highest_match = 0
                            for k in extracted.keys():
                                score = fuzz.partial_ratio(
                                    target_label.lower(), k.lower()
                                )
                                if score > 85 and score > highest_match:
                                    highest_match = score
                                    res_key = k

                        # PRIORITY 2: Check template-level table_config result keywords
                        if not res_key and ext_tpl and ext_tpl.table_config:
                            kw_res = ext_tpl.table_config.result_column_keywords
                            highest_match = 0
                            for k in extracted.keys():
                                for kw in kw_res:
                                    score = fuzz.partial_ratio(kw.lower(), k.lower())
                                    if score > 85 and score > highest_match:
                                        highest_match = score
                                        res_key = k

                        # Fallback to generic column identification
                        if not res_key:
                            res_key = next(
                                (
                                    k
                                    for k in extracted.keys()
                                    if any(
                                        kw in k.lower()
                                        for kw in [
                                            "result",
                                            "value",
                                            "observation",
                                            "finding",
                                        ]
                                    )
                                ),
                                list(extracted.keys())[-1] if extracted else "Result",
                            )

                        val = extracted.get(res_key, "")

                        # CLEANUP: Handle extraction using target_label
                        if target_label:
                            target_label = target_label.replace("\\n", "\n")
                            logger.debug(
                                f"[{config.parameter}] Label Clean for '{repr(target_label)}'"
                            )

                            # NEW: LINE-HOPPING LOGIC (Bulletproof generic extraction)
                            # If label ends with one or more newlines, skip that many lines down
                            if target_label.endswith("\n"):
                                shift = target_label.count("\n")
                                anchor = target_label.strip()
                                lines = [l.strip() for l in val.split("\n")]

                                logger.debug(
                                    f"[{config.parameter}] Line-Hoping (Shift: {shift}) for anchor '{anchor}'"
                                )
                                found = False
                                for idx, line in enumerate(lines):
                                    if anchor.lower() in line.lower():
                                        target_idx = idx + shift
                                        if target_idx < len(lines):
                                            val = lines[target_idx]
                                            # Strip trailing pipes/delimiters from OCR cells
                                            val = re.sub(r"[ |:\-=]+$", "", val).strip()
                                            logger.debug(
                                                f"[{config.parameter}] Hop Success! Result: {repr(val)}"
                                            )
                                            found = True
                                            break
                                if found:
                                    # Skip regex fallbacks if hop worked
                                    val = re.sub(r"^[ :\-=]+", "", val).strip()
                                else:
                                    logger.debug(
                                        f"[{config.parameter}] Hop failed (Anchor not found or out of bounds). Falling back to Regex."
                                    )

                            # REGEX FALLBACK (for wildcards like Solid Content)
                            if not target_label.endswith("\n") or val == extracted.get(
                                res_key, ""
                            ):
                                # Space-Flexible Regex Normalization
                                norm_label = (
                                    re.escape(target_label.strip())
                                    .replace(r"\.\*", r".*?")
                                    .replace(r"\\\.", r".")
                                )
                                # Allow multiple spaces
                                norm_label = re.sub(r"\\\s+", r"\\s*", norm_label)

                                pattern = rf"{norm_label}(?P<tail>.*?)(?:\s*\n|$)"
                                match = re.search(
                                    pattern, val, flags=re.IGNORECASE | re.DOTALL
                                )

                                if match and match.group("tail").strip():
                                    val = match.group("tail").strip()
                                    # Clean pipes
                                    val = re.sub(r"[ |:\-=]+$", "", val).strip()
                                else:
                                    # Final fallback: simple start-strip
                                    val = re.sub(
                                        rf"^{re.escape(target_label)}",
                                        "",
                                        val,
                                        flags=re.IGNORECASE,
                                    ).strip()

                            # Extra cleanup for common delimiters like ':' or '='
                            val = re.sub(r"^[ :\-=]+", "", val).strip()

                        conf_level = self.validator.validate_field(val, config)

                        # Check if full column extraction is enabled
                        ext_tpl = template.extraction_template
                        extract_all = (
                            ext_tpl
                            and ext_tpl.table_config
                            and getattr(
                                ext_tpl.table_config, "extract_all_columns", False
                            )
                        )

                        if extract_all:
                            # Save ALL columns as separate fields
                            for col_name, col_val in extracted.items():
                                if col_val and col_val.strip():
                                    f = Field(
                                        page=db_page,
                                        name=f"TABLE_{config.parameter}_{col_name}",
                                        ocr_value=col_val.strip(),
                                        roi_coordinates="0,0,0,0",
                                        confidence_level=conf_level,
                                    )
                                    session.add(f)
                        else:
                            # Save only the result column (original behavior)
                            f = Field(
                                page=db_page,
                                name=f"TABLE_{config.parameter}",
                                ocr_value=val,
                                roi_coordinates="0,0,0,0",
                                confidence_level=conf_level,
                            )
                            session.add(f)

                    # 4c. Process Footers
                    for key, data in nested_res["footers"].items():
                        val = data["value"]
                        config = data["config"]

                        # FALLBACK: If footer is empty, search for it in the table rows
                        if not val and "rows" in nested_res:
                            # Use template-defined label if available, else derive from key
                            target_label = None
                            if hasattr(config, "label"):
                                target_label = config.label
                            elif isinstance(config, dict):
                                target_label = config.get("label")

                            target_label = target_label or key
                            search_key_raw = target_label.lower()

                            for tr in nested_res["rows"]:
                                # Look for key in all cell values
                                row_content = " ".join(str(v) for v in tr.values())
                                if search_key_raw in row_content.lower():
                                    val = row_content
                                    # Strip the key from the content (take everything after it)
                                    split_idx = val.lower().find(search_key_raw)
                                    if split_idx != -1:
                                        val = val[
                                            split_idx + len(search_key_raw) :
                                        ].strip()

                                    val = re.sub(r"^[ :\-=]+", "", val).strip()

                                    # If image found in the remaining string, we're good
                                    if "![" in val:
                                        break
                                    # Otherwise keep searching other cells if this one was empty
                                    if not val:
                                        continue
                                    break

                        conf_level = self.validator.validate_field(val, config)
                        f = Field(
                            page=db_page,
                            name=key,
                            ocr_value=val,
                            roi_coordinates="0,0,0,0",
                            confidence_level=conf_level,
                        )
                        session.add(f)

                # --- OLD: Flat Extraction Fallback ---
                elif fields_def:
                    for f_def in fields_def:
                        logger.debug(
                            f"Extracting field {f_def.name} from Mistral source"
                        )
                        extracted_value = self.extraction_engine.extract_field(
                            page_ocr_cache.text, f_def
                        )
                        conf_level = self.validator.validate_field(
                            extracted_value, f_def
                        )
                        db_field = Field(
                            page=db_page,
                            name=f_def.name,
                            roi_coordinates="0,0,0,0",
                            ocr_value=extracted_value,
                            ocr_confidence=0.95,
                            confidence_level=conf_level,
                        )
                        session.add(db_field)

            session.commit()
            logger.info("Document processing complete. Data saved to DB.")

        except Exception:
            logger.exception("Processing failed")
            session.rollback()
        finally:
            session.close()
