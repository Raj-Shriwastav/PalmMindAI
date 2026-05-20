#!/usr/bin/env python3
import json
import sys
import urllib.request
import urllib.error

API_BASE_URL = "http://localhost:8000"


def load_json_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] Required test definition file not found: {file_path}")
        sys.exit(1)


def build_multipart_formdata(
    filename, content, fields, boundary="----PalmMindTestBoundary"
):
    body_parts = []

    # Add file content
    body_parts.append(f"--{boundary}")
    body_parts.append(
        f'Content-Disposition: form-data; name="file"; filename="{filename}"'
    )
    body_parts.append("Content-Type: text/plain")
    body_parts.append("")
    body_parts.append(content)

    # Add extra metadata fields
    for key, val in fields.items():
        body_parts.append(f"--{boundary}")
        body_parts.append(f'Content-Disposition: form-data; name="{key}"')
        body_parts.append("")
        body_parts.append(str(val))

    body_parts.append(f"--{boundary}--")
    body_parts.append("")

    body = "\r\n".join(body_parts)
    content_type = f"multipart/form-data; boundary={boundary}"
    return body.encode("utf-8"), content_type


def run_endpoint_upload(filename, content, fields, strategy):
    url = f"{API_BASE_URL}/upload"
    print(f"\n---> Testing POST /upload with strategy '{strategy}'...")

    body_bytes, content_type = build_multipart_formdata(filename, content, fields)
    headers = {"Content-Type": content_type, "Content-Length": str(len(body_bytes))}

    req = urllib.request.Request(url, data=body_bytes, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            res_body = res.read().decode("utf-8")
            res_json = json.loads(res_body)

            # Assert core structural keys exist
            assert "status" in res_json, "Missing 'status' key in response"
            assert "document_id" in res_json, "Missing 'document_id' key in response"
            assert (
                "strategy_used" in res_json
            ), "Missing 'strategy_used' key in response"
            assert "chunks_count" in res_json, "Missing 'chunks_count' key in response"
            assert (
                res_json["strategy_used"] == strategy
            ), f"Expected strategy {strategy}, got {res_json['strategy_used']}"

            print(
                f"[PASSED] Ingestion successful! Document ID: {res_json['document_id']}, Chunks: {res_json['chunks_count']}"
            )
            return True
    except urllib.error.URLError as e:
        print(f"[FAILED] Could not connect to API server: {e}")
        return False
    except AssertionError as e:
        print(f"[FAILED] Response assertion failed: {str(e)}")
        print(f"Response returned: {res_body}")
        return False
    except Exception as e:
        print(f"[FAILED] Unexpected error: {str(e)}")
        return False


def run_endpoint_chat(payload, test_name):
    url = f"{API_BASE_URL}/chat"
    print(f"\n---> Testing POST /chat [{test_name}]...")

    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            res_body = res.read().decode("utf-8")
            res_json = json.loads(res_body)

            # Assert chat schema fields
            assert "session_id" in res_json, "Missing 'session_id' in response"
            assert "response" in res_json, "Missing 'response' in response"
            assert "history" in res_json, "Missing 'history' in response"
            assert isinstance(
                res_json["history"], list
            ), "'history' must be a list of turns"

            print(
                f"[PASSED] Chat turns validated. Session ID: {res_json['session_id']}"
            )
            print(f"Agent Response Snippet: {res_json['response'][:120]}...")
            return True
    except urllib.error.URLError as e:
        print(f"[FAILED] Connection to API failed: {e}")
        return False
    except AssertionError as e:
        print(f"[FAILED] Response assertion failed: {str(e)}")
        print(f"Response returned: {res_body}")
        return False
    except Exception as e:
        print(f"[FAILED] Unexpected error: {str(e)}")
        return False


if __name__ == "__main__":
    print("==================================================")
    print("PalmMind AI Endpoint Integration Testing Runner")
    print("==================================================")
    print(f"Target URL: {API_BASE_URL}")
    print(
        "Please make sure your FastAPI app is running (e.g. uvicorn app.main:app) before calling this runner."
    )

    # Load input/output validation data
    inputs = load_json_file("tests/test_inputs.json")

    # 1. Test Ingestion - Recursive Character Strategy
    rec_inputs = inputs["ingestion"]["recursive_chunking"]
    fields_rec = {
        "chunk_strategy": rec_inputs["chunk_strategy"],
        "chunk_size": rec_inputs["chunk_size"],
        "chunk_overlap": rec_inputs["chunk_overlap"],
    }
    t1 = run_endpoint_upload(
        rec_inputs["file_name"], rec_inputs["file_content"], fields_rec, "recursive"
    )

    # 2. Test Ingestion - Semantic Strategy
    sem_inputs = inputs["ingestion"]["semantic_chunking"]
    fields_sem = {
        "chunk_strategy": sem_inputs["chunk_strategy"],
        "similarity_percentile": sem_inputs["similarity_percentile"],
    }
    t2 = run_endpoint_upload(
        sem_inputs["file_name"], sem_inputs["file_content"], fields_sem, "semantic"
    )

    # 3. Test Chat - Standard Greeting
    t3 = run_endpoint_chat(inputs["chat"]["greeting"], "Greeting")

    # 4. Test Chat - RAG Query
    t4 = run_endpoint_chat(inputs["chat"]["rag_retrieval"], "RAG Retrieval")

    # 5. Test Chat - Booking Tool Automation
    t5 = run_endpoint_chat(inputs["chat"]["booking_trigger"], "Booking Activation")

    print("\n==================================================")
    print("Integration Test Run Results")
    print("==================================================")
    print(f"Upload (Recursive Chunk): {'SUCCESS' if t1 else 'FAILED'}")
    print(f"Upload (Semantic Chunk):  {'SUCCESS' if t2 else 'FAILED'}")
    print(f"Chat (Greeting Turn):     {'SUCCESS' if t3 else 'FAILED'}")
    print(f"Chat (RAG Retrieval):     {'SUCCESS' if t4 else 'FAILED'}")
    print(f"Chat (Booking Tool):      {'SUCCESS' if t5 else 'FAILED'}")
    print("==================================================")

    all_success = t1 and t2 and t3 and t4 and t5
    sys.exit(0 if all_success else 1)
