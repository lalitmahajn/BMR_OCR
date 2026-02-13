from typing import List, Dict, Any
from app.schemas.template import ROI
from loguru import logger


class TableExtractionEngine:
    def __init__(self):
        pass

    def extract_table(
        self, image_path: str, table_roi: ROI, column_positions: List[int]
    ) -> List[List[str]]:
        """
        Extracts table data based on fixed column positions.
        1. Crop table ROI.
        2. Detect rows (using line detection or fixed height).
        3. Split rows by column_positions.
        4. Run OCR on each cell (delegated to OCR engine).
        """
        # This is a placeholder for the logic.
        # Real implementation requires passing the OCR engine here or returning ROIs for cells.
        logger.info(f"Extracting table from {image_path} with cols {column_positions}")
        return []


class SignatureEngine:
    def __init__(self):
        pass

    def extract_signature(self, image_path: str, signature_roi: ROI) -> str:
        """
        Crops signature ROI and saves it for comparison.
        Returns path to cropped signature image.
        """
        logger.info(f"Processing signature ROI: {signature_roi}")
        # Logic to crop and save would go here.
        return ""
