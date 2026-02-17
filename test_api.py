import requests
import sys

BASE_URL = "http://localhost:8000"


def test_api():
    print(f"Testing API at {BASE_URL}...")

    # 1. Get Documents
    print("\n1. GET /api/verification/documents")
    try:
        resp = requests.get(f"{BASE_URL}/api/verification/documents")
        resp.raise_for_status()
        docs = resp.json()
        print(f"✅ Success: Found {len(docs)} documents")
        if not docs:
            print("⚠️ No documents found. Run pipeline first.")
            return

        doc_id = docs[0]["id"]
        print(f"   Using Document ID: {doc_id}")
    except Exception as e:
        print(f"❌ Failed: {e}")
        return

    # 2. Get Pages
    print(f"\n2. GET /api/verification/documents/{doc_id}/pages")
    try:
        resp = requests.get(f"{BASE_URL}/api/verification/documents/{doc_id}/pages")
        resp.raise_for_status()
        pages = resp.json()
        print(f"✅ Success: Found {len(pages)} pages")

        page_id = pages[0]["id"]
        print(f"   Using Page ID: {page_id}")
    except Exception as e:
        print(f"❌ Failed: {e}")
        return

    # 3. Get Fields
    print(f"\n3. GET /api/verification/pages/{page_id}/fields")
    try:
        resp = requests.get(f"{BASE_URL}/api/verification/pages/{page_id}/fields")
        resp.raise_for_status()
        fields = resp.json()
        print(f"✅ Success: Found {len(fields)} fields")
        if fields:
            print(f"   Sample Field: {fields[0]['name']} = {fields[0]['value']}")
    except Exception as e:
        print(f"❌ Failed: {e}")


if __name__ == "__main__":
    test_api()
