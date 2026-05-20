# 🧠 PalmMind AI — Privacy-First Agentic RAG Backend

A production-ready, **fully local** Retrieval-Augmented Generation (RAG) backend powered by a GPU-accelerated LLM, vector search, and an autonomous LangGraph agent — with **zero data sent to external APIs**.

---

## 📋 Table of Contents

- [Architecture Overview](#-architecture-overview)
- [Tech Stack](#-tech-stack)
- [Prerequisites](#-prerequisites)
- [Quick Start Guide](#-quick-start-guide)
  - [Step 1: Clone & Setup Virtual Environment](#step-1-clone--setup-virtual-environment)
  - [Step 2: Start the LLM Server (GPU)](#step-2-start-the-llm-server-gpu)
  - [Step 3: Start Database Services](#step-3-start-database-services)
  - [Step 4: Run the FastAPI Application](#step-4-run-the-fastapi-application)
- [API Endpoints & Usage](#-api-endpoints--usage)
  - [Health Check](#1-health-check)
  - [Upload Documents](#2-upload-documents-post-upload)
  - [Chat with Agent](#3-chat-with-agent-post-chat)
- [Testing Guide](#-testing-guide)
  - [Verification Scripts](#1-verification-scripts)
  - [Unit Tests (pytest)](#2-unit-tests-pytest)
  - [Integration Tests](#3-full-integration-tests)
- [Docker Deployment](#-docker-deployment-full-stack)
- [Project Structure](#-project-structure)
- [Configuration Reference](#-configuration-reference)
- [CI/CD Pipeline](#-cicd-pipeline)
- [Troubleshooting](#-troubleshooting)

---

## 🏗 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT / CURL / UI                       │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTP
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI (port 8000)                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │ POST /upload │    │ POST /chat   │    │ GET /health      │  │
│  └──────┬───────┘    └──────┬───────┘    └──────────────────┘  │
│         │                   │                                   │
│  ┌──────▼───────┐    ┌──────▼───────────────────────────────┐  │
│  │  Ingestion   │    │  LangGraph Agent State Machine       │  │
│  │  Service     │    │  ┌─────────┐  ┌──────────────────┐   │  │
│  │              │    │  │ Agent   │→ │ Tool Node        │   │  │
│  │  - Extract   │    │  │ Node    │← │ - retrieve_knowledge│ │  │
│  │  - Chunk     │    │  └─────────┘  │ - book_interview │   │  │
│  │  - Embed     │    │               └──────────────────┘   │  │
│  │  - Store     │    └──────────────────────────────────────┘  │
│  └──────────────┘                                               │
└────────┬─────────────────────┬─────────────────┬───────────────┘
         │                     │                 │
         ▼                     ▼                 ▼
┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐
│ Qdrant (6333)   │  │ PostgreSQL      │  │ Redis (6379)     │
│ Vector Store    │  │ (5432)          │  │ Session Memory   │
│ 768-dim Cosine  │  │ Metadata + CRUD │  │ Checkpoints      │
└─────────────────┘  └─────────────────┘  └──────────────────┘
                               │
                     ┌─────────▼──────────┐
                     │ llama.cpp (8080)   │
                     │ GPU CUDA Server    │
                     │ Qwen3.5-4B-Q4_K_S │
                     └────────────────────┘
```

---

## 🛠 Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **LLM Engine** | llama.cpp + CUDA | Local GPU-accelerated inference (Qwen3.5-4B) |
| **Embeddings** | FastEmbed + Snowflake Arctic-M | 768-dim text embeddings for semantic search |
| **Vector DB** | Qdrant v1.7 | Cosine similarity search on embedded chunks |
| **SQL DB** | PostgreSQL 15 | Document metadata, bookings, chunk text storage |
| **Memory** | Redis 7 | LangGraph checkpoint persistence for multi-turn chat |
| **Agent Framework** | LangGraph | Stateful agent loop with tool calling |
| **API** | FastAPI | Async REST API with Pydantic V2 validation |
| **Containerization** | Docker + Docker Compose | Reproducible deployment |
| **CI/CD** | GitHub Actions | Automated linting, testing, and build verification |

---

## 📌 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10+** — [Download](https://www.python.org/downloads/)
- **Docker Desktop** — [Download](https://www.docker.com/products/docker-desktop/) (with WSL2 backend on Windows)
- **NVIDIA GPU + CUDA drivers** — Required for GPU-accelerated LLM inference
- **NVIDIA Container Toolkit** — [Install Guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
- **Git** — For version control

### Verify GPU is available to Docker:
```bash
docker run --rm --gpus all nvidia/cuda:13.0.0-base-ubuntu22.04 nvidia-smi
```
If this shows your GPU info, you're good to go!

---

## 🚀 Quick Start Guide

### Step 1: Clone & Setup Virtual Environment

```bash
# Clone the repository
git clone https://github.com/Raj-Shriwastav/PalmMindAI.git
cd PalmMindAI

# Create a Python virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# On Windows (CMD):
.venv\Scripts\activate.bat

# On macOS/Linux:
source .venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install testing dependencies
pip install pytest pytest-asyncio httpx
```

### Step 2: Start the LLM Server (GPU)

This starts the Qwen3.5-4B model on your GPU via llama.cpp. The model files must be pre-downloaded.

```bash
docker run -d \
  --name palmmind_llm \
  -p 8080:8080 \
  --gpus all \
  -v "C:<Model Location>\Qwen3.5-4B:/models" \
  ghcr.io/ggml-org/llama.cpp:server-cuda \
  -m /models/Qwen3.5-4B-Q4_K_S.gguf \
  --mmproj /models/mmproj-F32.gguf \
  -ngl 99
```

> **💡 Tip: Pin the image to avoid re-downloads.** The `:server-cuda` tag is a floating tag that may trigger re-pulls. To use the exact tested version, first pull once with `docker pull ghcr.io/ggml-org/llama.cpp:server-cuda`, then use the pinned digest for future runs:
> ```bash
> # Use pinned digest (never re-downloads)
> ghcr.io/ggml-org/llama.cpp@sha256:8c79e4acf00e403e601278989e1d5144c6882ffc0ddf60bef01f90c213c225dd
> ```

> **⏳ Wait ~30-60 seconds** for the model to load into GPU memory.

**Verify LLM is running:**
```bash
curl http://localhost:8080/v1/models
# Expected: {"object":"list","data":[{"id":"Qwen3.5-4B-Q4_K_S.gguf",...}]}
```

Or use the built-in verification script:
```bash
python tests/verify_llm.py
```

### Step 3: Start Database Services

```bash
# Start PostgreSQL, Redis, and Qdrant
docker-compose up -d postgres redis qdrant

# Verify all databases are online
python tests/verify_dbs.py
```

Expected output:
```
==========================================
Verification Summary
==========================================
Postgres Port/Connection: ONLINE
Redis Port/Connection:    ONLINE
Qdrant Port/Connection:   ONLINE
==========================================
```

### Step 4: Run the FastAPI Application

**Option A — Run locally (recommended for development):**
```bash
# Make sure your .venv is activated!
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Option B — Run via Docker Compose (production-like):**
```bash
docker-compose up -d
```

**Verify the API is running:**
```bash
curl http://localhost:8000/health
```
Expected response:
```json
{
  "status": "healthy",
  "service": "PalmMind RAG Agent Backend",
  "llm_engine": "llama.cpp (GPU-accelerated host execution)"
}
```

---

## 📡 API Endpoints & Usage

### 1. Health Check

```bash
GET http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "service": "PalmMind RAG Agent Backend",
  "llm_engine": "llama.cpp (GPU-accelerated host execution)"
}
```

---

### 2. Upload Documents (`POST /upload`)

Ingests `.pdf` or `.txt` files into the RAG pipeline. The file is:
1. Parsed for text content
2. Chunked (recursively or semantically)
3. Embedded using Snowflake Arctic-M (768 dimensions)
4. Stored in Qdrant (vectors) and PostgreSQL (metadata + raw text)

**Using cURL:**
```bash
# Upload with recursive chunking (default)
curl -X POST http://localhost:8000/upload \
  -F "file=@company_policy.txt" \
  -F "chunk_strategy=recursive" \
  -F "chunk_size=500" \
  -F "chunk_overlap=50"

# Upload with semantic chunking
curl -X POST http://localhost:8000/upload \
  -F "file=@product_specs.txt" \
  -F "chunk_strategy=semantic" \
  -F "similarity_percentile=90"
```

**Using Python:**
```python
import requests

# Upload a text file with recursive chunking
with open("company_policy.txt", "rb") as f:
    response = requests.post(
        "http://localhost:8000/upload",
        files={"file": ("company_policy.txt", f, "text/plain")},
        data={
            "chunk_strategy": "recursive",
            "chunk_size": 500,
            "chunk_overlap": 50
        }
    )
print(response.json())
```

**Response Schema:**
```json
{
  "status": "success",
  "message": "File 'company_policy.txt' ingested successfully.",
  "document_id": "e24f095d-52e9-4d69-9dee-07ffbe68db45",
  "strategy_used": "recursive",
  "embedding_model": "Snowflake/snowflake-arctic-embed-m",
  "chunks_count": 3,
  "metadata": {
    "filename": "company_policy.txt",
    "file_size_bytes": 352,
    "timestamp": "2026-05-20T07:15:45.123456"
  }
}
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file` | File | *required* | `.pdf` or `.txt` file to ingest |
| `chunk_strategy` | string | `"recursive"` | `"recursive"` or `"semantic"` |
| `chunk_size` | int | `500` | Character limit per chunk (recursive only) |
| `chunk_overlap` | int | `50` | Overlap between chunks (recursive only) |
| `similarity_percentile` | float | `90.0` | Transition threshold (semantic only) |

---

### 3. Chat with Agent (`POST /chat`)

Send messages to the stateful LangGraph agent. The agent can:
- **Answer questions directly** from its training
- **Retrieve knowledge** from uploaded documents via vector search
- **Book interviews** by saving to PostgreSQL and sending confirmation emails

**Using cURL (PowerShell):**
```powershell
# Simple greeting
$body = '{"session_id": "my-session-001", "message": "Hello! Who are you and what can you do?"}'
Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method POST -ContentType "application/json" -Body $body

# Ask about uploaded documents (RAG retrieval)
$body = '{"session_id": "my-session-001", "message": "What are the working hours at PalmMind?"}'
Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method POST -ContentType "application/json" -Body $body

# Book an interview
$body = '{"session_id": "my-session-001", "message": "Please book an interview for Raj Shriwastava, email raj@example.com, on June 10 2026 at 11:00 AM"}'
Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method POST -ContentType "application/json" -Body $body
```

**Using Python:**
```python
import requests

# Start a conversation
response = requests.post("http://localhost:8000/chat", json={
    "session_id": "my-session-001",
    "message": "Hello! What tools do you have?"
})
print(response.json()["response"])

# Ask about uploaded documents
response = requests.post("http://localhost:8000/chat", json={
    "session_id": "my-session-001",
    "message": "What are the working hours at PalmMind based on uploaded docs?"
})
print(response.json()["response"])

# Book an interview
response = requests.post("http://localhost:8000/chat", json={
    "session_id": "my-session-001",
    "message": "Book an interview for John Doe, john@example.com, on July 15 2026 at 2:00 PM"
})
print(response.json()["response"])
```

**Response Schema:**
```json
{
  "session_id": "my-session-001",
  "response": "Hello! I am PalmMind AI's Agentic Assistant...",
  "history": [
    {"role": "user", "content": "Hello! What tools do you have?"},
    {"role": "assistant", "content": "Hello! I am PalmMind AI's Agentic Assistant..."}
  ]
}
```

**Key behaviors:**
- The `session_id` maintains conversational memory across multiple requests (stored in Redis)
- Using the **same session_id** continues the conversation with full context
- Using a **new session_id** starts a fresh conversation
- The agent automatically decides when to use `retrieve_knowledge` or `book_interview` tools

---

## 🧪 Testing Guide

### 1. Verification Scripts

These standalone scripts verify that each infrastructure component is working:

```bash
# Verify llama.cpp LLM server connection (port 8080)
python tests/verify_llm.py

# Verify FastEmbed model loads and generates 768-dim embeddings
python tests/verify_fastembed.py

# Verify PostgreSQL, Redis, and Qdrant connections
python tests/verify_dbs.py
```

### 2. Unit Tests (pytest)

Run the fast, isolated unit tests (no LLM or Docker required):

```bash
# Run all unit tests with verbose output
python -m pytest tests/test_pdf.py tests/test_chunking.py tests/test_api.py -v
```

**What they test:**
| Test File | Tests |
|-----------|-------|
| `test_pdf.py` | UTF-8 text extraction, unsupported format rejection |
| `test_chunking.py` | Recursive chunker splitting, empty input handling |
| `test_api.py` | Health endpoint returns 200 with correct payload |

### 3. Full Integration Tests

These test the **live system end-to-end** (requires all services running):

```bash
# Make sure all services are running first:
# 1. LLM container on port 8080
# 2. docker-compose services (postgres, redis, qdrant)
# 3. FastAPI on port 8000

python tests/test_api_endpoints.py
```

**What it tests:**
1. ✅ `POST /upload` with recursive chunking strategy
2. ✅ `POST /upload` with semantic chunking strategy
3. ✅ `POST /chat` with a greeting message
4. ✅ `POST /chat` with a RAG retrieval query
5. ✅ `POST /chat` with a booking tool trigger

**Test data files:**
- `tests/test_inputs.json` — Sample requests for all endpoints
- `tests/test_expected_outputs.json` — Expected response structures

---

## 🐳 Docker Deployment (Full Stack)

Deploy the entire stack with one command:

```bash
# 1. First, start the LLM container separately (needs GPU access)
docker run -d --name palmmind_llm -p 8080:8080 --gpus all \
  -v "C:\<Model Address>\Qwen3.5-4B:/models" \
  ghcr.io/ggml-org/llama.cpp:server-cuda \
  -m /models/Qwen3.5-4B-Q4_K_S.gguf \
  --mmproj /models/mmproj-F32.gguf -ngl 99

# 2. Then start all application services
docker-compose up -d

# 3. Check all containers are healthy
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

Expected output:
```
NAMES               STATUS                    PORTS
palmmind_llm        Up 2 minutes              0.0.0.0:8080->8080/tcp
palmmind_api        Up 30 seconds (healthy)   0.0.0.0:8000->8000/tcp
palmmind_postgres   Up 1 minute (healthy)     0.0.0.0:5432->5432/tcp
palmmind_redis      Up 1 minute (healthy)     0.0.0.0:6379->6379/tcp
palmmind_qdrant     Up 1 minute               0.0.0.0:6333->6333/tcp
```

**To stop everything:**
```bash
docker-compose down
docker stop palmmind_llm && docker rm palmmind_llm
```

---

## 📁 Project Structure

```
PalmMindAI/
├── .env                          # Local environment configuration
├── .github/
│   └── workflows/
│       └── ci.yml                # GitHub Actions CI/CD pipeline
├── .venv/                        # Python virtual environment (not committed)
├── Dockerfile                    # Multi-stage production Docker image
├── docker-compose.yml            # Service orchestration (Postgres, Redis, Qdrant, API)
├── requirements.txt              # Python dependencies
├── README.md                     # This file
│
├── app/                          # Application source code
│   ├── __init__.py
│   ├── main.py                   # FastAPI entry point + lifespan hooks
│   │
│   ├── api/                      # REST API routers (Controllers)
│   │   ├── chat.py               # POST /chat — Agent conversation endpoint
│   │   └── upload.py             # POST /upload — Document ingestion endpoint
│   │
│   ├── core/                     # Infrastructure & configuration
│   │   ├── config.py             # Pydantic V2 settings (loads from .env)
│   │   ├── database.py           # SQLAlchemy engine, session factory
│   │   ├── qdrant.py             # Qdrant client + collection auto-creation
│   │   └── redis.py              # Custom Redis checkpoint saver for LangGraph
│   │
│   ├── models/                   # SQLAlchemy ORM models
│   │   ├── booking.py            # Interview booking table
│   │   └── document.py           # Document + DocumentChunk tables
│   │
│   ├── repositories/             # Database access layer (CRUD)
│   │   ├── base.py               # Base repository with session injection
│   │   ├── booking.py            # Booking queries
│   │   └── document.py           # Document/chunk queries
│   │
│   ├── schemas/                  # Pydantic V2 request/response schemas
│   │   ├── booking.py            # Booking validation schema
│   │   ├── chat.py               # Chat request/response schema
│   │   └── upload.py             # Upload response schema
│   │
│   ├── services/                 # Business logic orchestrators
│   │   ├── agent.py              # LangGraph state machine + ChatOpenAI
│   │   └── ingestion.py          # Document processing pipeline
│   │
│   ├── tools/                    # LangGraph agent tools
│   │   ├── booking.py            # book_interview tool + SMTP dispatcher
│   │   └── retriever.py          # retrieve_knowledge tool (Qdrant search)
│   │
│   └── utils/                    # Utility helpers
│       ├── chunking.py           # Recursive + Semantic text chunkers
│       └── pdf.py                # PDF/TXT text extractor
│
└── tests/                        # Test suite
    ├── test_api.py               # Health endpoint unit test
    ├── test_api_endpoints.py     # Full integration test runner
    ├── test_chunking.py          # Chunker unit tests
    ├── test_pdf.py               # Text extraction unit tests
    ├── test_inputs.json          # Sample test input data
    ├── test_expected_outputs.json # Expected response structures
    ├── verify_dbs.py             # Database connectivity checker
    ├── verify_fastembed.py       # Embedding model verifier
    └── verify_llm.py             # LLM server connectivity checker
```

---

## ⚙ Configuration Reference

All configuration is managed via the `.env` file:

```env
# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=palmmind_db
POSTGRES_HOST=localhost          # Use 'postgres' when running inside Docker
POSTGRES_PORT=5432

# Redis
REDIS_HOST=localhost             # Use 'redis' when running inside Docker
REDIS_PORT=6379

# Qdrant Vector DB
QDRANT_HOST=localhost            # Use 'qdrant' when running inside Docker
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=palmmind_rag

# LLM Server (llama.cpp)
LLM_BASE_URL=http://localhost:8080/v1   # Use 'host.docker.internal' inside Docker
LLM_API_KEY=not-needed
LLM_MODEL_NAME=Qwen3.5-4B-Q4_K_S.gguf

# Embeddings
EMBEDDING_MODEL_NAME=Snowflake/snowflake-arctic-embed-m

# SMTP (Optional — leave empty for mock email logging)
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_SENDER=
```

> **Note:** When running via `docker-compose`, the `docker-compose.yml` overrides these with container-internal hostnames (e.g., `postgres`, `redis`, `qdrant`, `host.docker.internal`).

---

## 🔄 CI/CD Pipeline

The project includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that runs on every push/PR to `main` or `master`:

| Stage | What it does |
|-------|-------------|
| **Lint & Format** | Checks code with `black` (formatting) and `flake8` (quality) |
| **Integration Tests** | Spins up real PostgreSQL, Redis, and Qdrant services; runs `pytest` with coverage |
| **Docker Build** | Verifies the multi-stage Dockerfile compiles without errors |

---

## 🔧 Troubleshooting

### LLM container won't start
```bash
# Check if port 8080 is already in use
netstat -ano | findstr :8080

# Check GPU access
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi

# Check container logs
docker logs palmmind_llm
```

### Chat endpoint returns 500
```bash
# Check API container logs for the actual Python traceback
docker logs palmmind_api --tail 50

# Common causes:
# 1. LLM server not running → start palmmind_llm container
# 2. Redis not accessible → check docker-compose services
# 3. Model not loaded → wait for LLM to fully initialize
```

### Database connection refused
```bash
# Ensure containers are running
docker ps

# If containers exited, restart them
docker-compose up -d

# Verify connectivity
python tests/verify_dbs.py
```

### FastEmbed model download fails
```bash
# Clear the cache and retry
python -c "import shutil; shutil.rmtree(r'C:\Users\<User Name>\AppData\Local\Temp\fastembed_cache', ignore_errors=True)"

# Re-run
python tests/verify_fastembed.py
```

### Qdrant version mismatch warning
The `qdrant-client` Python package (v1.18) may warn about version mismatch with Qdrant server (v1.7). This is non-fatal and can be suppressed. To fix properly, pin the Docker image to a compatible version or upgrade:
```yaml
# In docker-compose.yml, change:
qdrant:
  image: qdrant/qdrant:v1.12.0   # Matches client better
```

---
