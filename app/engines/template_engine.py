import json
import os
import cv2
import re
from pathlib import Path
from loguru import logger
from typing import Dict, Any, Optional, List, Tuple
from app.engines.classification import PageType
from app.engines.ocr import PaddleOCRAdapter
from app.schemas.template import ROI
import numpy as np


class TemplateEngine:
    def __init__(
        self,
        templates_dir: str = "d:/Official/BMR_OCR2/templates",
        ocr_adapter: Optional[PaddleOCRAdapter] = None,
    ):
        self.templates_dir = templates_dir
        self.ocr = ocr_adapter or PaddleOCRAdapter()
        self.templates: Dict[str, Dict] = {}
        self._load_templates()

    def _load_templates(self):
        """Loads all JSON templates from the templates directory."""
        if not os.path.exists(self.templates_dir):
            logger.warning(f"Templates directory not found: {self.templates_dir}")
            return

        for fname in os.listdir(self.templates_dir):
            if fname.endswith(".json"):
                try:
                    path = os.path.join(self.templates_dir, fname)
                    with open(path, "r") as f:
                        data = json.load(f)
                        if "page_type" in data:
                            self.templates[data["page_type"]] = data
                            logger.info(f"Loaded template for {data['page_type']}")
                except Exception as e:
                    logger.error(f"Failed to load template {fname}: {e}")

    def extract(self, image_path: str, page_type: Any) -> Dict[str, Any]:
        """
        Extracts data from the image using the template for the given page_type.
        Supports dynamic anchor-based ROI adjustment.
        """
        # Handle both PageType enum or string name
        template_key = page_type.name if hasattr(page_type, "name") else str(page_type)
        template = self.templates.get(template_key)

        if not template:
            logger.warning(f"No template found for {template_key}")
            return {}

        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"Could not read image: {image_path}")
            return {}

        base_w = template.get("base_dimensions", {}).get("width", 1000)
        base_h = template.get("base_dimensions", {}).get("height", 1000)
        curr_h, curr_w = img.shape[:2]

        scale_x = curr_w / base_w
        scale_y = curr_h / base_h

        # Calculate Anchor Offset
        offset_x, offset_y = 0, 0
        anchor_config = template.get("anchor")
        if anchor_config:
            keyword = anchor_config.get("keyword")
            expected_res = anchor_config.get("expected_rect")  # [x, y, w, h]

            if keyword and expected_res:
                logger.info(f"Searching for anchor '{keyword}'...")
                # We can pass the image path directly to utilize cached OCR if possible or just fresh run
                found_cen = self.ocr.find_anchor(image_path, keyword)

                if found_cen:
                    fx, fy = found_cen
                    # Calculate Expected Centroid
                    ex_cx = int(expected_res[0] + expected_res[2] / 2)
                    ex_cy = int(expected_res[1] + expected_res[3] / 2)

                    # Scale expected centroid to current image size
                    # because find_anchor returns coordinates in current image
                    ex_cx_scaled = int(ex_cx * scale_x)
                    ex_cy_scaled = int(ex_cy * scale_y)

                    offset_x = fx - ex_cx_scaled
                    offset_y = fy - ex_cy_scaled

                    logger.info(f"Anchor found. Offset: dx={offset_x}, dy={offset_y}")
                else:
                    logger.warning(f"Anchor '{keyword}' not found. Using default ROIs.")

        # Perform Full Layout Analysis (Dynamic Search)
        logger.info(f"Performing Dynamic Layout Analysis for {template_key}...")
        layout_data = self.ocr.analyze_page(img)

        extracted_data = {}

        # Extract Fields
        for field in template.get("fields", []):
            name = field["name"]
            roi_static = field["roi"]  # [x, y, w, h] (Fallback)

            # --- PHASE 1: Dynamic Keyword Spotting ---
            found_dynamically = False
            for region in layout_data:
                # Search in all possible content fields
                content_to_search = [region.get("text", "")]
                if region.get("html"):
                    content_to_search.append(region["html"])
                if region.get("markdown"):
                    content_to_search.append(region["markdown"])

                # Check for field name in any of the content
                full_content = " ".join(content_to_search)

                if name.lower() in full_content.lower():
                    # Attempt to extract value using split
                    # Note: re.escape(name) handles spaces, but we also want to handle '.' or ':'
                    clean_name = re.escape(name)
                    # Pattern: name followed by optional dots/spaces and a colon/separator, then the value
                    pattern = f"{clean_name}[\\.\\s]*[:\\-]*\\s*(.*)"
                    match = re.search(pattern, full_content, re.IGNORECASE)

                    if match:
                        raw_val = match.group(1).split("<")[0].strip()
                        # Further refine: stop if we see another capitalized label or common separator
                        # Most labels are "Word Word :" or similar
                        refined_val = re.split(
                            r"  +| [A-Z][a-z]+ [A-Z][a-z]+ :| [A-Z][a-z]+ :", raw_val
                        )[0].strip()

                        if refined_val and len(refined_val) < 100:
                            logger.info(
                                f"Dynamic match found for '{name}': '{refined_val}'"
                            )
                            extracted_data[name] = {
                                "value": refined_val,
                                "confidence": region["confidence"] or 0.8,
                                "roi": region["bbox"],
                                "method": "dynamic",
                            }
                            found_dynamically = True
                            break

            if found_dynamically:
                continue

            # --- PHASE 2: Static ROI Fallback ---
            logger.debug(f"Falling back to Static ROI for '{name}'")
            # Scale ROI and Apply Offset
            x = int(roi_static[0] * scale_x) + offset_x
            y = int(roi_static[1] * scale_y) + offset_y
            w = int(roi_static[2] * scale_x)
            h = int(roi_static[3] * scale_y)

            # Boundary Checks
            x = max(0, x)
            y = max(0, y)
            w = min(w, curr_w - x)
            h = min(h, curr_h - y)

            if w <= 0 or h <= 0:
                logger.warning(f"Skipping Invalid ROI for {name}: {x},{y},{w},{h}")
                continue

            # Crop
            cropped = img[y : y + h, x : x + w]
            ocr_result = self.ocr.recognize_field(cropped)
            extracted_value = ocr_result.text

            extracted_data[name] = {
                "value": extracted_value,
                "confidence": ocr_result.confidence,
                "roi": [x, y, w, h],
                "method": "static",
            }

            # Validation (Basic)
            validation = field.get("validation")
            if validation and validation.get("regex"):
                pattern = validation["regex"]
                if not re.match(pattern, extracted_value):
                    extracted_data[name]["warning"] = "Regex Validation Failed"

        # Extract Tables
        tables_results = {}
        for table_def in template.get("tables", []):
            tname = table_def["name"]
            roi_raw = table_def["roi_area"]

            # Scale & Offset
            tx = int(roi_raw[0] * scale_x) + offset_x
            ty = int(roi_raw[1] * scale_y) + offset_y
            tw = int(roi_raw[2] * scale_x)
            th = int(roi_raw[3] * scale_y)

            # ROI object
            table_roi = ROI(x=tx, y=ty, w=tw, h=th)

            logger.info(f"Extracting Table: {tname}...")
            table_res = self.ocr.extract_table(img, roi=table_roi)
            tables_results[tname] = table_res

        return {
            "fields": extracted_data,
            "tables": tables_results,
            "metadata": {"offset": {"dx": offset_x, "dy": offset_y}},
        }
