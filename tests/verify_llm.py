#!/usr/bin/env python3
import json
import sys
import urllib.request
import urllib.error

from app.core.config import settings


def verify_llama_cpp():
    # Dynamically build standard chat completions URL from settings config
    base_url = settings.LLM_BASE_URL.rstrip("/")
    url = f"{base_url}/chat/completions"

    payload = {
        "model": settings.LLM_MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are a helpful and concise assistant."},
            {
                "role": "user",
                "content": "Hello! Please reply with exactly: 'LLaMA.cpp server is successfully connected and responding with GPU acceleration!'",
            },
        ],
        "temperature": 0.2,
        "max_tokens": 100,
    }

    headers = {"Content-Type": "application/json"}

    print("--------------------------------------------------")
    print(f"Connecting to llama.cpp server at: {url}...")
    print("--------------------------------------------------")

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            status = response.status
            response_body = response.read().decode("utf-8")

            if status == 200:
                res_json = json.loads(response_body)
                content = res_json["choices"][0]["message"]["content"]
                print("\n[SUCCESS] Successfully connected to llama.cpp!")
                print(f"Server Response:\n{content.strip()}\n")
                print("Usage Stats:")
                print(
                    f"  Prompt tokens: {res_json.get('usage', {}).get('prompt_tokens', 'N/A')}"
                )
                print(
                    f"  Completion tokens: {res_json.get('usage', {}).get('completion_tokens', 'N/A')}"
                )
                print(
                    f"  Total tokens: {res_json.get('usage', {}).get('total_tokens', 'N/A')}"
                )
                return True
            else:
                print(f"\n[FAILED] Server returned status code: {status}")
                print(f"Response: {response_body}")
                return False

    except urllib.error.URLError as e:
        print("\n[ERROR] Could not connect to llama.cpp server.")
        print(f"Reason: {e.reason}")
        print("\nPlease verify that:")
        print("  1. Your Docker container is running.")
        print("  2. It is mapped to the correct host port.")
        print("  3. The model file path inside the container is correct.")
        print(
            "\nEnsure you started the model with the correct local docker execution syntax."
        )
        return False
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {str(e)}")
        return False


if __name__ == "__main__":
    success = verify_llama_cpp()
    sys.exit(0 if success else 1)
