import fitz  # PyMuPDF
from pathlib import Path
from typing import List
from loguru import logger
import hashlib
import shutil

from app.core.config import settings


class IngestionEngine:
    def __init__(self, upload_dir: Path = settings.DATA_DIR / "uploads"):
        self.upload_dir = upload_dir
        self.images_dir = settings.DATA_DIR / "images"

        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)

    def process_file(self, file_path: Path) -> List[str]:
        """
        Ingests a PDF or image file.
        Returns a list of paths to the generated page images.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Ingesting file: {file_path}")

        # Calculate file hash for audit
        file_hash = self._calculate_file_hash(file_path)
        logger.debug(f"File hash: {file_hash}")

        # Copy original to uploads (if not already there)
        dest_path = self.upload_dir / f"{file_hash}{file_path.suffix}"
        if not dest_path.exists():
            shutil.copy2(file_path, dest_path)

        generated_images = []

        if file_path.suffix.lower() == ".pdf":
            generated_images = self._convert_pdf_to_images(dest_path)
        elif file_path.suffix.lower() in [".jpg", ".jpeg", ".png", ".tiff"]:
            # For direct images, just copy/organize them
            image_dest = self.images_dir / f"p1_{file_path.stem}_{file_hash}.jpg"
            shutil.copy2(file_path, image_dest)
            generated_images.append(str(image_dest))
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")

        return generated_images

    def _convert_pdf_to_images(self, pdf_path: Path) -> List[str]:
        doc = fitz.open(pdf_path)
        image_paths = []

        logger.info(f"Converting {len(doc)} pages from {pdf_path.name}")

        for page_num, page in enumerate(doc):
            # Render page to image (high resolution)
            zoom = 2.0  # 2.0 = 200% resolution (approx 144 dpi), good for OCR
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)

            output_filename = f"p{page_num + 1}_{pdf_path.stem}.jpg"
            output_path = self.images_dir / output_filename

            pix.save(output_path)
            image_paths.append(str(output_path))

        return image_paths

    def _calculate_file_hash(self, file_path: Path) -> str:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
