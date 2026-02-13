import enum
import re
from typing import List, Optional, Dict
from loguru import logger
from thefuzz import fuzz
from pydantic import BaseModel


# ==========================================================
# Page Types (FINAL – aligned with your documents)
# ==========================================================


class PageType(str, enum.Enum):
    QC_TEST_REPORT = "QC_TEST_REPORT"
    PRODUCTION_REPORT = "PRODUCTION_REPORT"
    WORKSHEET_POLYMER = "WORKSHEET_POLYMER"
    DEVIATION_ACCEPTANCE = "DEVIATION_ACCEPTANCE"
    PRODUCT_SPEC = "PRODUCT_SPEC"
    EMAIL = "EMAIL"
    STORES_REQUISITION = "STORES_REQUISITION"
    RM_PACKING_ISSUANCE = "RM_PACKING_ISSUANCE"
    ISSUE_VOUCHER = "ISSUE_VOUCHER"
    SOP = "SOP"
    BMR = "BMR"
    PACKING_DETAILS = "PACKING_DETAILS"
    BMR_CHECKLIST = "BMR_CHECKLIST"
    UNKNOWN = "UNKNOWN"


# Mapping from PageType to the long header title found in documents
PAGE_HEADER_MAP = {
    PageType.QC_TEST_REPORT: "Finished Good Q.C. Test Report for Speciality Chemicals",
    PageType.PRODUCTION_REPORT: "Production Report",
    PageType.WORKSHEET_POLYMER: "Worksheet for Polymer Product",
    PageType.DEVIATION_ACCEPTANCE: "Acceptance Under Deviation for Raw Material/ Finished Products/ Packing Material",
    PageType.PRODUCT_SPEC: "View Product Specification",
    PageType.EMAIL: "Rishabh Metals & Chemicals Pvt Ltd Mail",
    PageType.STORES_REQUISITION: "Stores Requisition Slip Polymer Plant",
    PageType.RM_PACKING_ISSUANCE: "Raw Material & Packing Material Issuance Record",
    PageType.ISSUE_VOUCHER: "Issue - Mtrl Voucher",
    PageType.SOP: "Standard Operating Procedure",
    PageType.BMR: "Batch Manufacturing Record (BMR)",
    PageType.PACKING_DETAILS: "Packing Details",
    PageType.BMR_CHECKLIST: "BMR Review Checklist",
}


class ClassificationResult(BaseModel):
    page_type: PageType
    page_num: Optional[int] = None
    total_pages: Optional[int] = None
    score: float
    line: Optional[str] = None


# ==========================================================
# Classification Engine
# ==========================================================


class PageClassificationEngine:
    """
    Header-based page classification engine.
    - Matches OCR text headers against known PageType titles.
    - Uses fuzzy substring matching.
    """

    def __init__(self):
        self.history: List[ClassificationResult] = []

    def _extract_page_info(self, ocr_text: str) -> Dict[str, Optional[int]]:
        """
        Extracts Page X of Y patterns from OCR text.
        Searches top 20 and bottom 10 lines.
        """
        lines = ocr_text.splitlines()
        search_lines = lines[:20] + lines[-10:]

        # Patterns:
        # "Page 01 of 06"
        # "Page No.: 02 of 08"
        # "Page 1 of 3"
        patterns = [
            r"PAGE\s*(?:NO\.:)?\s*(\d+)\s*OF\s*(\d+)",
            r"PAGE\s*(\d+)\s*/\s*(\d+)",
            r"SHEET\s*NO\.:\s*(\d+)",
        ]

        for line in search_lines:
            line_upper = line.upper()
            for pattern in patterns:
                match = re.search(pattern, line_upper)
                if match:
                    groups = match.groups()
                    try:
                        res = {"page_num": int(groups[0])}
                        if len(groups) > 1:
                            res["total_pages"] = int(groups[1])
                        return res
                    except (ValueError, IndexError):
                        continue
        return {"page_num": None, "total_pages": None}

    def get_match_score(self, line: str, title: str) -> float:
        """
        Checks how well 'title' matches 'line'.
        Returns 0.0 to 1.0.
        Optimized for clean OCR (like Mistral).
        """
        if not line or not title:
            return 0.0

        # Normalization
        # Strip markdown symbols (#, *, _, >) and common noise
        line_norm = re.sub(r"[#*_>]+", " ", line).strip().lower()
        title_norm = title.lower().strip()

        # Handle variants like "Q. C." vs "QC"
        line_norm = line_norm.replace(". ", ".").replace(".", "")
        title_norm = title_norm.replace(". ", ".").replace(".", "")

        # 1. Exact Substring Match (Fast & Preferred for Mistral)
        if title_norm in line_norm or line_norm in title_norm:
            return 1.0

        # 2. Fuzzy Matching fallback
        # Partial Ratio handles cases where title is part of a longer header line
        score = fuzz.partial_ratio(line_norm, title_norm) / 100.0

        return score

    def classify(self, ocr_text: str, context: str = "N/A") -> ClassificationResult:
        """
        Classifies page with support for positional weighting, context inheritance,
        and sub-classification (page numbers).
        """
        if not ocr_text:
            logger.warning(f"[{context}] Empty OCR text, returning UNKNOWN")
            return ClassificationResult(page_type=PageType.UNKNOWN, score=0.0)

        # 1. Search top 30 lines (increased depth for Mistral markdown)
        lines = ocr_text.upper().splitlines()[:30]

        # Collect all valid candidates
        candidates = []
        THRESHOLD = 0.82  # Slightly stricter

        for i, line in enumerate(lines):
            line = line.strip()
            if len(line) < 4:
                continue

            for p_type in PageType:
                if p_type in [PageType.UNKNOWN, PageType.EMAIL]:
                    continue

                title = PAGE_HEADER_MAP.get(p_type)
                if not title:
                    continue

                raw_score = self.get_match_score(line, title)

                if raw_score >= THRESHOLD:
                    # Positional Weighting: Small boost for early lines
                    position_boost = max(0, (20 - i) / 400.0)
                    final_score = min(1.0, raw_score + position_boost)

                    candidates.append(
                        {
                            "type": p_type,
                            "title": title,
                            "score": final_score,
                            "line": line,
                            "index": i,
                        }
                    )

        # 2. Refined Email detection (Secondary check)
        if (
            "mail.google.com" in ocr_text.lower()
            or "rishabh metals" in ocr_text.lower()
        ):
            # Check if it's in the extreme top or bottom (headers/footers)
            header_footer = lines[:5] + ocr_text.upper().splitlines()[-5:]
            if any("MAIL.GOOGLE.COM" in line_content for line_content in header_footer):
                # Only add if no stronger header match was found
                email_score = 0.85
                candidates.append(
                    {
                        "type": PageType.EMAIL,
                        "title": "Email Signature",
                        "score": email_score,
                        "line": "GMAIL_FOOTER",
                        "index": 99,
                    }
                )

        # 3. Sort candidates (Score DESC, Title Length DESC, Index ASC)
        candidates.sort(
            key=lambda x: (x["score"], len(x["title"]), -x["index"]),
            reverse=True,
        )

        best_type = candidates[0]["type"] if candidates else None
        best_score = candidates[0]["score"] if candidates else 0.0
        best_line = candidates[0]["line"] if candidates else None

        # 4. Extract Sub-Classification (Page X of Y)
        page_info = self._extract_page_info(ocr_text)

        # 5. History Inheritance (The "Continuation" Rule)
        if not best_type:
            # Inheritance Rule: Only inherit if the current page has sufficient text content (> 100 chars)
            if self.history and len(ocr_text) > 100:
                prev_res = self.history[-1]
                # Inherit from previous page only if it's a "Sticky" type (not email/unknown)
                if prev_res.page_type not in [PageType.EMAIL, PageType.UNKNOWN]:
                    logger.info(
                        f"[{context}] No header. Inheriting {prev_res.page_type} from history."
                    )
                    best_type = PageType(prev_res.page_type)
                    best_score = prev_res.score

        if not best_type:
            best_type = PageType.UNKNOWN

        # 6. Page number interpolation (Inference for obscured/stamped indices)
        final_page_num = page_info["page_num"]
        final_total_pages = page_info["total_pages"]

        if not final_page_num and self.history:
            prev_res = self.history[-1]
            if (
                prev_res.page_type == best_type
                and prev_res.page_num is not None
                and prev_res.total_pages is not None
            ):
                if prev_res.page_num < prev_res.total_pages:
                    final_page_num = prev_res.page_num + 1
                    final_total_pages = prev_res.total_pages
                    logger.info(
                        f"[{context}] Inferred index {final_page_num}/{final_total_pages} (Previous was {prev_res.page_num})"
                    )

        result = ClassificationResult(
            page_type=best_type,
            page_num=final_page_num,
            total_pages=final_total_pages,
            score=best_score,
            line=best_line,
        )

        # Track history
        self.history.append(result)

        # Logging
        sub_info = (
            f" (Page {result.page_num}/{result.total_pages})" if result.page_num else ""
        )
        logger.info(f"[{context}] Classified as {result.page_type.name}{sub_info}")

        return result


# ==========================================================
# Helper: Header-only OCR text extractor (recommended usage)
# ==========================================================


def extract_header_text(full_ocr_text: str, max_lines: int = 20) -> str:
    """
    Use only top lines of OCR text for classification.
    This avoids noise from tables.
    """
    lines = full_ocr_text.splitlines()
    header_lines = lines[:max_lines]
    return "\n".join(header_lines)


# ==========================================================
# Example Usage
# ==========================================================

if __name__ == "__main__":
    sample_ocr = """
    BATCH MANUFACTURING RECORD
    Product Name: XYZ Shampoo
    Batch No: BMR-001
    Batch Size: 500 KG
    """

    engine = PageClassificationEngine()
    page_type = engine.classify(sample_ocr)

    print("Detected Page Type:", page_type)
