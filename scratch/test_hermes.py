import requests
import json

api_key = "sk-nous-J410ycLrYmOwXumMbehKFwDnxFuBeeZp"
base_url = "https://inference-api.nousresearch.com/v1"

def test_hermes():
    print("Testing Nous Hermes API Key...")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 1. Test get models
    try:
        response = requests.get(f"{base_url}/models", headers=headers, timeout=15)
        print("Models Status Code:", response.status_code)
        if response.status_code == 200:
            models = response.json().get("data", [])
            print("Available Models:")
            for m in models:
                print(f" - {m.get('id')}")
        else:
            print("Error response:", response.text)
            return
    except Exception as e:
        print("Exception querying models:", e)
        return

    # 2. Test simple completion
    payload = {
        "model": "NousResearch/Hermes-3-Llama-3.1-8B",  # standard model name or we'll pick one from the list
        "messages": [{"role": "user", "content": "Hola, responde brevemente."}],
        "temperature": 0.3
    }
    # Let's try to adjust the model if we see the list, or try a common one.
    try:
        print("\nSending a test completion request...")
        resp = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=20)
        print("Completion Status Code:", resp.status_code)
        if resp.status_code == 200:
            print("Response:")
            print(resp.json()["choices"][0]["message"]["content"])
        else:
            print("Completion Error:", resp.text)
    except Exception as e:
        print("Exception during completion:", e)

if __name__ == "__main__":
    test_hermes()
