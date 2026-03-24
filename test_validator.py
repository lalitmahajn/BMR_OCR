from app.schemas.qc_report import TestRow, QCReportSchema
import json

def test():
    print("Testing TestRow validator...")
    row_data = {
        "sr_no": 2,
        "parameter": "Viscosity",
        "result_value": "78",
        "unit": "P3"
    }
    
    try:
        row = TestRow.model_validate(row_data)
        print(f"Validated Row Data: {row.model_dump()}")
        if row.unit == "CPS":
            print("SUCCESS: Viscosity unit forced to CPS")
        else:
            print(f"FAILURE: Viscosity unit is still {row.unit}")
    except Exception as e:
        print(f"ERROR during validation: {e}")

    print("\nTesting full schema validation...")
    full_data = {
        "product_name": "Test",
        "batch_no": "123",
        "test_results": [row_data]
    }
    try:
        schema = QCReportSchema.model_validate(full_data)
        print(f"Validated full data unit: {schema.test_results[0].unit}")
    except Exception as e:
        print(f"ERROR during full validation: {e}")

if __name__ == "__main__":
    test()
