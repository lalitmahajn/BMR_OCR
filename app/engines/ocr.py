import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple, List, Optional, Union, Dict, Any
import numpy as np
import cv2
from loguru import logger
from app.schemas.template import ROI


class OCRResult:
    def __init__(self, text: str, confidence: float):
        self.text = text
        self.confidence = confidence


class OCRAdapter(ABC):
    @abstractmethod
    def extract_text(self, image_path: str, roi: Optional[ROI] = None) -> OCRResult:
        pass


class PaddleOCRAdapter(OCRAdapter):
    def __init__(self, use_angle_cls: bool = True, lang: str = "en"):
        try:
            from paddleocr import PaddleOCR, TextRecognition, PPStructureV3

            # 1. Main OCR Engine (Path 1)
            self.ocr = PaddleOCR(
                lang=lang,
                ocr_version="PP-OCRv5",
                use_doc_orientation_classify=True,
                use_textline_orientation=True,
                text_det_box_thresh=0.3,
                text_det_unclip_ratio=1.8,
                text_rec_score_thresh=0.5,
                device="cpu",
            )

            # 2. Recognition-Only Engine (Path 3)
            self.rec_model = TextRecognition()

            # 3. Table Structure Engine (Path 5)
            self.table_engine = PPStructureV3(
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_chart_recognition=False,
            )

            logger.info("PaddleOCR Engines (OCR, Rec, Table) initialized successfully.")
        except ImportError as e:
            logger.error(f"Initialization failed: {e}")
            self.ocr = None
            self.rec_model = None
            self.table_engine = None

    def extract_text(self, image_path: str, roi: Optional[ROI] = None) -> OCRResult:
        if not self.ocr:
            return OCRResult("", 0.0)

        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"Could not read image: {image_path}")
            return OCRResult("", 0.0)

        # Crop if ROI is provided
        if roi:
            x, y, w, h = roi.x, roi.y, roi.w, roi.h
            # Boundary checks
            h_img, w_img = img.shape[:2]
            x = max(0, x)
            y = max(0, y)
            w = min(w, w_img - x)
            h = min(h, h_img - y)

            if w <= 0 or h <= 0:
                logger.error(f"Invalid ROI: {roi}")
                return OCRResult("", 0.0)

            img = img[y : y + h, x : x + w]

        # Run OCR
        # cls=True needed if orientation might be wrong, but usually false for ROIs to save time?
        # Spec says "CPU-only", text usually horizontal in forms.
        result = self.ocr.ocr(img)

        # PaddleOCR result structure: [[[[box], [text, conf]], ...]]
        # We need to join all text in the ROI

        extracted_text = []
        confidences = []

        if result:
            # Check if result is in the new dictionary format (list of dicts)
            if (
                isinstance(result, list)
                and len(result) > 0
                and isinstance(result[0], dict)
            ):
                # New format: [{'rec_texts': [...], 'rec_scores': [...], ...}]
                page_result = result[0]
                rec_texts = page_result.get("rec_texts", [])
                rec_scores = page_result.get("rec_scores", [])

                for text, conf in zip(rec_texts, rec_scores):
                    extracted_text.append(text)
                    confidences.append(conf)

            # Check for old format: [[[box, (text, conf)], ...]] or [[box, (text, conf)], ...]
            else:
                lines = (
                    result[0]
                    if (
                        result
                        and isinstance(result, list)
                        and len(result) > 0
                        and isinstance(result[0], list)
                    )
                    else result
                )

                if lines:
                    for line in lines:
                        if not line:
                            continue
                        # Structure: [box, (text, conf)]
                        text = line[1][0]
                        conf = line[1][1]
                        extracted_text.append(text)
                        confidences.append(conf)

            full_text = " ".join(extracted_text).strip()
            avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
            return OCRResult(full_text, avg_conf)

        return OCRResult("", 0.0)

    def find_anchor(self, image_input, keyword: str) -> Optional[Tuple[int, int]]:
        """
        Finds the centroid (x, y) of the first text block containing the keyword.
        Accepts image_input as path (str) or numpy array.
        """
        if not self.ocr:
            return None

        # self.ocr.ocr() accepts path or array
        result = self.ocr.ocr(image_input)

        found_box = None

        if not result:
            return None

        # Check for new Dict format (PaddleX style)
        if isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict):
            res_dict = result[0]
            boxes = res_dict.get("dt_polys", [])
            texts = res_dict.get("rec_texts", [])
            # Iterate
            for box, text in zip(boxes, texts):
                if keyword in text:
                    logger.info(f"Found anchor match: '{text}' at {box}")
                    found_box = box
                    break
        else:
            # Old list format
            lines = (
                result[0]
                if (result and isinstance(result, list) and isinstance(result[0], list))
                else result
            )
            if lines:
                for line in lines:
                    box = line[0]
                    text_obj = line[1]
                    # Robust unpacking
                    text = (
                        text_obj[0]
                        if isinstance(text_obj, (list, tuple))
                        else str(text_obj)
                    )

                    if keyword in text:
                        logger.info(f"Found anchor match: '{text}' at {box}")
                        found_box = box
                        break

        if found_box is not None:
            # Calculate centroid
            if isinstance(found_box, np.ndarray):
                found_box = found_box.tolist()

            xs = [p[0] for p in found_box]
            ys = [p[1] for p in found_box]
            c_x = int(sum(xs) / len(xs))
            c_y = int(sum(ys) / len(ys))
            return (c_x, c_y)

        return None

    def recognize_field(self, image_input: Union[str, np.ndarray]) -> OCRResult:
        """
        Uses specialized TextRecognition model (Path 3) for speed.
        Assumes the input image is already a crop of a single text line/field.
        Accepts image path (str) or numpy array (ndarray).
        """
        if not self.rec_model:
            return OCRResult("", 0.0)

        # predict() takes image path or ndarray
        # Returns list of results (usually just one for a crop)
        # Result structure usually: [{'rec_text': '...', 'rec_score': 0.9}]

        try:
            results = self.rec_model.predict(image_input)

            if results and isinstance(results, list):
                # Inspect first result
                res = results[0]
                # Check for PaddleX dict format
                if isinstance(res, dict):
                    text = res.get("rec_text", "")
                    score = res.get("rec_score", 0.0)
                    return OCRResult(text, score)
                # Fallback if structure differs (e.g. tuple)
                elif isinstance(res, (list, tuple)) and len(res) >= 2:
                    return OCRResult(res[0], res[1])

        except Exception as e:
            logger.error(f"Recognition failed: {e}")

        return OCRResult("", 0.0)

    def extract_table(
        self, image_input, roi: Optional[ROI] = None
    ) -> List[Dict[str, Any]]:
        """
        Extracts tables from the image. If ROI is provided, crops first.
        Returns a list of tables with HTML, Markdown, and JSON data.
        """
        if not self.table_engine:
            return []

        img = image_input
        if isinstance(image_input, (str, Path)):
            img = cv2.imread(str(image_input))

        if img is None:
            return []

        if roi:
            h_img, w_img = img.shape[:2]
            x, y, w, h = roi.x, roi.y, roi.w, roi.h
            # Boundary checks
            x = max(0, x)
            y = max(0, y)
            w = min(w, w_img - x)
            h = min(h, h_img - y)
            img = img[y : y + h, x : x + w]

        try:
            # PPStructureV3 uses .predict()
            results = self.table_engine.predict(input=img)

            tables_data = []
            for res in results:
                # In PPStructureV3 results, we check if it has table data
                html = getattr(res, "html", "")
                markdown = getattr(res, "markdown", "")
                raw_json = getattr(res, "json", {})

                # If these are lists, join them
                if isinstance(html, list):
                    html = "\n".join(html)
                if isinstance(markdown, list):
                    markdown = "\n".join(markdown)

                if html or markdown:
                    tables_data.append(
                        {
                            "html": html,
                            "markdown": markdown,
                            "json": self._sanitize(raw_json),
                        }
                    )
            return tables_data
        except Exception as e:
            logger.error(f"Table extraction failed: {e}")
            return []

    def analyze_page(self, image_input) -> List[Dict[str, Any]]:
        """
        Performs full layout analysis of the page using PPStructureV3.
        Identifies all regions (text, title, table, etc.) with their content and bboxes.
        """
        if not self.table_engine:
            return []

        img = image_input
        if isinstance(image_input, (str, Path)):
            img = cv2.imread(str(image_input))

        if img is None:
            return []

        try:
            # Full page prediction
            results = self.table_engine.predict(input=img)

            layout_data = []
            for res in results:
                # Based on PPStructureV3 / PaddleX structure
                bbox_raw = getattr(res, "bbox", [0, 0, 0, 0])
                # Convert [x1, y1, x2, y2] -> [x, y, w, h]
                x1, y1, x2, y2 = bbox_raw
                bbox_xywh = [int(x1), int(y1), int(x2 - x1), int(y2 - y1)]

                html_val = getattr(res, "html", "")
                if isinstance(html_val, dict):
                    html_val = "\n".join([str(v) for v in html_val.values()])
                elif isinstance(html_val, list):
                    html_val = "\n".join([str(v) for v in html_val])

                md_val = getattr(res, "markdown", "")
                if isinstance(md_val, dict):
                    md_val = "\n".join([str(v) for v in md_val.values()])
                elif isinstance(md_val, list):
                    md_val = "\n".join([str(v) for v in md_val])

                region = {
                    "type": getattr(res, "type", "text"),
                    "bbox": bbox_xywh,
                    "text": "",
                    "html": str(html_val),
                    "markdown": str(md_val),
                    "confidence": 0.0,
                    "sub_regions": [],
                }

                # Extract text for text/title blocks
                if hasattr(res, "res") and isinstance(res.res, list):
                    texts = []
                    scores = []
                    for line in res.res:
                        # line = [box, (text, conf)]
                        if isinstance(line, list) and len(line) == 2:
                            texts.append(line[1][0])
                            scores.append(line[1][1])
                        elif isinstance(line, dict):
                            # Handle dict format if present
                            texts.append(line.get("text", ""))
                            scores.append(line.get("confidence", 0.0))

                    region["text"] = " ".join(texts)
                    region["confidence"] = sum(scores) / len(scores) if scores else 0.0
                    region["sub_regions"] = self._sanitize(res.res)

                layout_data.append(region)

            return layout_data
        except Exception as e:
            logger.error(f"Layout analysis failed: {e}")
            return []

    def _sanitize(self, obj):
        """Internal helper to ensure JSON serializability."""
        if isinstance(obj, (dict,)):
            return {str(k): self._sanitize(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple, set)):
            return [self._sanitize(v) for v in obj]
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.float16, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, (np.int8, np.int16, np.int32, np.int64)):
            return int(obj)
        elif "Image" in str(type(obj)):
            return "<Image Object>"
        elif hasattr(obj, "__dict__"):
            return {
                k: self._sanitize(v)
                for k, v in obj.__dict__.items()
                if not k.startswith("_")
            }
        return obj
