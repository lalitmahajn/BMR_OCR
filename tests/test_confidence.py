import sys
import os


# Add app to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.engines.extraction import MarkdownExtractionEngine
from app.engines.validation import ValidationEngine
from app.models.domain import FieldType
from app.schemas.template import FieldDefinition


def test_confidence_scoring():
    extractor = MarkdownExtractionEngine()
    validator = ValidationEngine()

    print("\n--- Testing Confidence Scoring ---")

    # Case 1: High Confidence (Label + Regex)
    print("\nTest 1: High Confidence (Label + Regex)")
    md_high = "Batch No: B12345"
    field_high = FieldDefinition(
        name="batch_no",
        type=FieldType.STRING,
        expected_label=["Batch No"],
        regex="B\\d+",
    )
    val, pos, conf = extractor.extract_field(md_high, field_high)
    print(f"Extraction: Val='{val}', Conf={conf}")

    level = validator.validate_field(val, field_high, extraction_confidence=conf)
    print(f"Validation Level: {level}")

    assert val == "B12345"
    assert conf == 0.95
    assert level == "GREEN"

    # Case 2: Medium Confidence (Label Only)
    print("\nTest 2: Medium Confidence (Label Only)")
    md_med = "Batch No: B12345"
    field_med = FieldDefinition(
        name="batch_no",
        type=FieldType.STRING,
        expected_label=["Batch No"],
        # No regex
    )
    val, pos, conf = extractor.extract_field(md_med, field_med)
    print(f"Extraction: Val='{val}', Conf={conf}")

    level = validator.validate_field(val, field_med, extraction_confidence=conf)
    print(f"Validation Level: {level}")

    assert val == "B12345"
    assert conf == 0.80
    assert level == "YELLOW"

    # Case 3: Low Confidence (Regex Fallback)
    print("\nTest 3: Low Confidence (Regex Fallback)")
    md_low = "Some random text B12345 end."
    field_low = FieldDefinition(
        name="batch_no",
        type=FieldType.STRING,
        expected_label=["Missing Label"],
        regex="B\\d+",
    )
    val, pos, conf = extractor.extract_field(
        md_low, field_low, fallback_name="batch_no"
    )
    print(f"Extraction: Val='{val}', Conf={conf}")

    level = validator.validate_field(val, field_low, extraction_confidence=conf)
    print(f"Validation Level: {level}")

    assert val == "B12345"
    assert conf == 0.70
    assert level == "RED"  # <= 0.7 is RED

    # Case 4: Format Failure
    print("\nTest 4: Format Failure")
    md_fail = "Batch No: WRONG_FORMAT"
    field_fail = FieldDefinition(
        name="batch_no",
        type=FieldType.INTEGER,  # Expecting Integer
        expected_label=["Batch No"],
    )
    val, pos, conf = extractor.extract_field(md_fail, field_fail)
    print(f"Extraction: Val='{val}', Conf={conf}")

    level = validator.validate_field(val, field_fail, extraction_confidence=conf)
    print(f"Validation Level: {level}")

    assert val == "WRONG_FORMAT"
    assert conf == 0.80  # Extraction found it by label
    assert level == "RED"  # But format validation failed

    print("\n--- All Tests Passed ---")


if __name__ == "__main__":
    test_confidence_scoring()
