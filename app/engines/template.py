import json
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger

from app.core.config import settings
from app.schemas.template import PageTemplate, FieldDefinition, ROI


class TemplateEngine:
    def __init__(self, template_dir: Path = settings.TEMPLATE_DIR):
        self.template_dir = template_dir
        self.templates: Dict[str, PageTemplate] = {}
        self._load_templates()

    def _load_templates(self):
        """Loads all .json templates from the template directory."""
        if not self.template_dir.exists():
            logger.warning(f"Template directory not found: {self.template_dir}")
            return

        for file_path in self.template_dir.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    template = PageTemplate(**data)
                    self.templates[template.page_type] = template
                    logger.info(
                        f"Loaded template: {template.page_type} from {file_path.name}"
                    )
            except Exception as e:
                logger.error(f"Failed to load template {file_path}: {e}")

    def get_template(self, page_type: str) -> Optional[PageTemplate]:
        return self.templates.get(page_type)

    def get_fields(
        self, page_type: str, image_width: int, image_height: int
    ) -> List[FieldDefinition]:
        """
        Returns fields for a page type, with ROIs scaled to the actual image size.
        """
        template = self.get_template(page_type)
        if not template:
            return []

        # Scale ROIs
        scale_x = image_width / template.base_width
        scale_y = image_height / template.base_height

        scaled_fields = []
        if not template.fields:
            return []

        for field in template.fields:
            # Create a copy with scaled ROI if it exists
            original_roi = field.roi
            if original_roi:
                scaled_roi = ROI(
                    x=int(original_roi.x * scale_x),
                    y=int(original_roi.y * scale_y),
                    w=int(original_roi.w * scale_x),
                    h=int(original_roi.h * scale_y),
                )
            else:
                scaled_roi = None

            # Construct new field def
            new_field = field.model_copy()
            new_field.roi = scaled_roi
            scaled_fields.append(new_field)

        return scaled_fields
