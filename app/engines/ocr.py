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
    """
    Placeholder/Disabled adapter. 
    Code removed to prevent unnecessary dependencies.
    """
    def __init__(self, use_angle_cls: bool = True, lang: str = "en"):
        self.ocr = None
        self.rec_model = None
        self.table_engine = None

    def extract_text(self, image_path: str, roi: Optional[ROI] = None) -> OCRResult:
        return OCRResult("", 0.0)

    def find_anchor(self, image_input, keyword: str) -> Optional[Tuple[int, int]]:
        return None

    def recognize_field(self, image_input: Union[str, np.ndarray]) -> OCRResult:
        return OCRResult("", 0.0)

    def extract_table(
        self, image_input, roi: Optional[ROI] = None
    ) -> List[Dict[str, Any]]:
        return []

    def analyze_page(self, image_input) -> List[Dict[str, Any]]:
        return []

    def _sanitize(self, obj):
        return obj
