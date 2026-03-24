try:
    from mistralai import Mistral
    print("from mistralai import Mistral: Success")
except ImportError as e:
    print(f"from mistralai import Mistral: Failed - {e}")

try:
    from mistralai.client import Mistral
    print("from mistralai.client import Mistral: Success")
except ImportError as e:
    print(f"from mistralai.client import Mistral: Failed - {e}")
