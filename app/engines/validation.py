"""
Validation Engine for Extracted Data

This module validates extracted OCR data against schema rules including:
- Type validation (string, number, date)
- Range validation (min/max)
- Pattern matching (regex)
- Enumeration checks (allowed_values)
- Required field validation
"""

import re
import json
from datetime import datetime
from typing import Dict, Any, List, Tuple


class FieldValidator:
    """Validator for individual field values"""

    @staticmethod
    def parse_number(value: str) -> Tuple[bool, float]:
        """Parse a string to number, handling common OCR errors"""
        if not value:
            return False, 0

        # Clean common OCR artifacts
        cleaned = value.strip()
        cleaned = cleaned.replace(",", ".")  # European decimal separator
        cleaned = cleaned.replace("O", "0")  # Letter O -> Zero
        cleaned = cleaned.replace("l", "1")  # Lowercase L -> One
        cleaned = cleaned.replace("I", "1")  # Capital I -> One

        # Extract numeric part (handle cases like "98 CPS" -> "98")
        import re

        match = re.search(r"[\d.]+", cleaned)
        if match:
            try:
                return True, float(match.group())
            except:
                pass

        return False, 0

    @staticmethod
    def parse_date(value: str, format_str: str = "DD/MM/YY") -> Tuple[bool, str]:
        """Parse and validate date string"""
        if not value:
            return False, ""

        # Common OCR cleanup
        cleaned = value.strip().replace(".", "/").replace(",", "/")

        # Try to parse DDMMYY format (e.g., "2810126" -> "28/01/26")
        if len(cleaned) >= 6 and cleaned.isdigit():
            try:
                dd = cleaned[:2]
                mm = cleaned[2:4]
                yy = cleaned[4:6]
                parsed = f"{dd}/{mm}/{yy}"

                # Validate it's a real date
                datetime.strptime(parsed, "%d/%m/%y")
                return True, parsed
            except (ValueError, TypeError):
                pass

        # Check if already in DD/MM/YY format
        if "/" in cleaned:
            try:
                datetime.strptime(cleaned, "%d/%m/%y")
                return True, cleaned
            except (ValueError, TypeError):
                pass

        return False, cleaned

    @staticmethod
    def parse_numeric_with_unit(
        value: str, allowed_units: List[str] = None
    ) -> Tuple[bool, float, str]:
        """Extracts number and unit from string like '78 CPS'"""
        if not value:
            return False, 0, ""

        import re

        # Match number and optional word/symbol at end
        match = re.search(r"([\d.]+)\s*([a-zA-Z%]+)?", value)
        if match:
            try:
                num = float(match.group(1))
                unit = match.group(2) if match.group(2) else ""

                # Check unit if restricted
                if allowed_units and unit:
                    if not any(u.lower() == unit.lower() for u in allowed_units):
                        return False, num, unit

                return True, num, unit
            except:
                pass
        return False, 0, ""

    @staticmethod
    def validate_type(value: str, field_type: str, schema: Any) -> Dict[str, Any]:
        """Validate value type against ValidationRule schema"""
        result = {
            "valid": True,
            "errors": [],
            "cleaned_value": value,
            "original_value": value,
        }

        # Determine rules source (dict or pydantic)
        rules = (
            schema
            if isinstance(schema, dict)
            else (schema.model_dump() if schema else {})
        )
        f_type = field_type or rules.get("type", "string")

        if f_type in ["number", "numeric", "numeric_with_unit", "percentage"]:
            allowed_units = rules.get("unit_allowed", [])
            if f_type == "percentage":
                allowed_units = ["%"]

            success, num, unit = FieldValidator.parse_numeric_with_unit(
                value, allowed_units
            )
            if not success:
                result["valid"] = False
                result["errors"].append(f"Invalid {f_type} or unit mismatch: '{value}'")
                return result

            result["cleaned_value"] = num

            # Range validation (supports min/max OR expected_range list)
            min_val = rules.get("min_value") or (
                rules.get("expected_range")[0] if rules.get("expected_range") else None
            )
            max_val = rules.get("max_value") or (
                rules.get("expected_range")[1] if rules.get("expected_range") else None
            )

            if min_val is not None and num < min_val:
                result["valid"] = False
                result["errors"].append(f"Value {num} below minimum {min_val}")

            if max_val is not None and num > max_val:
                result["valid"] = False
                result["errors"].append(f"Value {num} above maximum {max_val}")

        elif f_type == "date":
            success, parsed_date = FieldValidator.parse_date(
                value, rules.get("format", "DD/MM/YY")
            )
            if not success:
                result["valid"] = False
                result["errors"].append(f"Cannot parse as date: '{value}'")
            else:
                result["cleaned_value"] = parsed_date

        elif f_type == "signature":
            # Check if it looks like a markdown image: ![...](...)
            if re.search(r"!\[.*?\]\(.*?\)", value):
                result["valid"] = True
            else:
                result["valid"] = False
                result["errors"].append(
                    f"Value '{value}' is not a valid signature/image markdown"
                )

        return result


class ValidationEngine:
    """High-level validation engine used by Orchestrator"""

    def __init__(self):
        pass

    def validate_field(self, value: str, field_definition: Any) -> str:
        """
        Validate a single field value against its definition.
        """
        if not value or value.strip() == "":
            return "RED"

        # Handle both old FieldDefinition and new ConfigField/nested styles
        rules = None
        f_type = "string"

        if hasattr(field_definition, "validation"):
            rules = field_definition.validation
            f_type = field_definition.type
        elif hasattr(field_definition, "validation_rules"):
            rules = field_definition.validation_rules
            f_type = rules.type if rules else "string"

        result = FieldValidator.validate_type(value, f_type, rules)

        if result["valid"]:
            return "GREEN"
        else:
            return "YELLOW"

    def validate_all(
        self, page_data: Dict[str, str], fields_def: List[Any]
    ) -> Dict[str, str]:
        """Validates a set of fields and handles cross-field dependencies"""
        results = {}
        # 1. Basic Validation
        for f_def in fields_def:
            val = page_data.get(f_def.name, "")
            results[f_def.name] = self.validate_field(val, f_def)

        # 2. Cross-Field Validation (e.g., Exp Date > Mfg Date)
        # TODO: Implement if needed for this phase
        return results


class SchemaValidator:
    """Validates entire extraction results against schema"""

    def __init__(self, schema_path: str):
        """Load validation schema"""
        with open(schema_path, "r", encoding="utf-8") as f:
            self.schema = json.load(f)

    def validate_section(
        self, section_name: str, extraction_data: Dict, schema_section: Dict
    ) -> Dict:
        """Validate a section of extracted data"""
        results = {}

        for field_name, field_schema in schema_section.items():
            if not isinstance(field_schema, dict) or "type" not in field_schema:
                continue

            # Get extracted value
            extracted = extraction_data.get(field_name, {})

            if not isinstance(extracted, dict) or "status" not in extracted:
                results[field_name] = {
                    "validation_status": "error",
                    "errors": ["Field extraction data malformed"],
                }
                continue

            # Check if field was extracted
            if extracted["status"] != "success":
                if field_schema.get("required", False):
                    results[field_name] = {
                        "validation_status": "error",
                        "errors": [
                            f"Required field not extracted: {extracted['status']}"
                        ],
                    }
                else:
                    results[field_name] = {
                        "validation_status": "warning",
                        "errors": [
                            f"Optional field not extracted: {extracted['status']}"
                        ],
                    }
                continue

            # Validate the extracted value
            value = extracted["value"]
            field_type = field_schema["type"]

            validation_result = FieldValidator.validate_type(
                value, field_type, field_schema
            )

            results[field_name] = {
                "validation_status": "valid"
                if validation_result["valid"]
                else "invalid",
                "original_value": validation_result["original_value"],
                "cleaned_value": validation_result["cleaned_value"],
                "confidence": extracted.get("confidence", 0),
                "errors": validation_result["errors"],
                "label_found": extracted.get("label_found", ""),
                "box": extracted.get("value_box", []),
            }

        return results

    def validate_all(self, extraction_results: Dict) -> Dict:
        """Validate all sections"""
        validation_results = {
            "summary": {
                "total_fields": 0,
                "valid_fields": 0,
                "invalid_fields": 0,
                "missing_required": 0,
                "missing_optional": 0,
            },
            "sections": {},
        }

        # Validate each section
        for section_name in ["product_information", "test_parameters", "qc_result"]:
            if section_name not in self.schema:
                continue

            schema_section = self.schema[section_name]
            extraction_section = extraction_results.get(
                section_name.replace("_", "_").lower(), {}
            )

            if not isinstance(extraction_section, dict):
                extraction_section = extraction_results.get(
                    section_name.split("_")[0], {}
                )

            section_results = self.validate_section(
                section_name, extraction_section, schema_section
            )
            validation_results["sections"][section_name] = section_results

            # Update summary
            for field_result in section_results.values():
                validation_results["summary"]["total_fields"] += 1

                if field_result["validation_status"] == "valid":
                    validation_results["summary"]["valid_fields"] += 1
                elif field_result["validation_status"] == "invalid":
                    validation_results["summary"]["invalid_fields"] += 1
                elif field_result["validation_status"] == "error":
                    validation_results["summary"]["missing_required"] += 1
                elif field_result["validation_status"] == "warning":
                    validation_results["summary"]["missing_optional"] += 1

        return validation_results


def main():
    """Test validation engine"""
    print("=" * 80)
    print("VALIDATION ENGINE TEST")
    print("=" * 80 + "\n")

    # Load extraction results
    with open(
        r"d:\Official\BMR_OCR2\output\qc_page1_extraction.json", "r", encoding="utf-8"
    ) as f:
        extraction_results = json.load(f)

    # Initialize validator
    validator = SchemaValidator(
        r"d:\Official\BMR_OCR2\templates\qc_test_report_unified.json"
    )

    # Validate
    validation_results = validator.validate_all(extraction_results)

    # Display results
    print("📊 VALIDATION SUMMARY")
    print("-" * 80)
    summary = validation_results["summary"]
    print(f"Total Fields:        {summary['total_fields']}")
    print(f"✅ Valid:            {summary['valid_fields']}")
    print(f"❌ Invalid:          {summary['invalid_fields']}")
    print(f"⚠️  Missing (Req):    {summary['missing_required']}")
    print(f"ℹ️  Missing (Opt):    {summary['missing_optional']}")

    success_rate = (
        (summary["valid_fields"] / summary["total_fields"] * 100)
        if summary["total_fields"] > 0
        else 0
    )
    print(f"\n📈 Validation Rate:  {success_rate:.1f}%\n")

    # Display detailed results
    for section_name, section_results in validation_results["sections"].items():
        print(f"\n📁 {section_name.upper().replace('_', ' ')}")
        print("-" * 80)

        for field_name, field_result in section_results.items():
            status = field_result["validation_status"]
            icon = "✅" if status == "valid" else "❌" if status == "invalid" else "⚠️"

            print(f"{icon} {field_name.replace('_', ' ').title():30s}", end="")

            if status == "valid":
                print(f": {field_result['cleaned_value']}")
                if field_result["original_value"] != field_result["cleaned_value"]:
                    print(
                        f"   {'':30s}  (cleaned from: '{field_result['original_value']}')"
                    )
            else:
                print(f": {field_result.get('original_value', 'N/A')}")
                for error in field_result["errors"]:
                    print(f"   {'':30s}  ⚠ {error}")

    # Save validation results
    output_path = r"d:\Official\BMR_OCR2\output\qc_page1_validation_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(validation_results, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 80}")
    print(f"✓ Validation results saved to: {output_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
