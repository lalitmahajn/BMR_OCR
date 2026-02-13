from pydantic import BaseModel
from typing import List, Optional, Union, Dict, Any
from enum import Enum


class FieldType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    DATE = "date"
    ENUM = "enum"
    SIGNATURE = "signature"


class ROI(BaseModel):
    x: int
    y: int
    w: int
    h: int


class ValidationRule(BaseModel):
    model_config = {"extra": "allow"}
    type: Optional[str] = "string"
    regex: Optional[str] = None
    min_value: Optional[float] = None


class ConfigField(BaseModel):
    model_config = {"extra": "allow"}
    label: Optional[str] = None
    value: Optional[str] = None
    validation_rules: Optional[ValidationRule] = None


class TableRowTemplate(BaseModel):
    model_config = {"extra": "allow"}
    sr_no: Optional[int] = None
    parameter: str
    result: Optional[str] = None
    validation_rules: Optional[ValidationRule] = None


class TableConfig(BaseModel):
    model_config = {"extra": "allow"}
    parameter_column_keywords: Optional[List[str]] = ["parameter", "test", "field"]
    result_column_keywords: Optional[List[str]] = ["result", "value"]
    index_column_keywords: Optional[List[str]] = ["sr. no", "index", "sl. no"]
    header_identifier_keywords: Optional[List[str]] = [
        "parameter",
        "test",
        "field",
        "observation",
    ]
    extract_all_columns: Optional[bool] = False
    dynamic_rows: Optional[bool] = False
    column_mapping: Optional[Dict[str, List[str]]] = None
    noise_markers: Optional[List[str]] = None


class ExtractionTemplate(BaseModel):
    model_config = {"extra": "allow"}
    header_fields: Optional[Dict[str, ConfigField]] = None
    test_parameters_table: Optional[List[TableRowTemplate]] = None
    table_config: Optional[TableConfig] = None
    footer_fields: Optional[Dict[str, Any]] = None
    noise_markers: Optional[List[str]] = None


class FieldDefinition(BaseModel):
    name: str
    type: FieldType
    expected_label: Optional[List[str]] = None
    roi: Optional[ROI] = None
    regex: Optional[str] = None
    validation: Optional[ValidationRule] = None
    required: bool = True


class PageTemplate(BaseModel):
    page_type: str
    base_width: Optional[int] = 1000
    base_height: Optional[int] = 1414
    fields: Optional[List[FieldDefinition]] = None
    extraction_template: Optional[ExtractionTemplate] = None
    document_metadata: Optional[Dict[str, Any]] = None
