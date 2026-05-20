#!/usr/bin/env python3
import os
import sys

def install_reportlab_if_missing():
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    except ImportError:
        print("[INFO] 'reportlab' is missing. Installing reportlab to generate PDF files...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
        print("[SUCCESS] 'reportlab' installed successfully!")

def create_txt_files():
    print("Generating TXT files...")
    
    # 1. PalmMind Culture & Perks Info
    culture_content = (
        "========================================================================\n"
        "PALMMIND AI - COMPANY CULTURE & WORK PERKS INFORMATION SHEET\n"
        "========================================================================\n\n"
        "Welcome to PalmMind AI! We are a privacy-first, edge-computing oriented AI Research\n"
        "and Engineering company specializing in fully local agentic setups, CUDA-accelerated\n"
        "microservices, and highly optimized RAG pipelines.\n\n"
        "CORE CULTURE PILLARS:\n"
        "1. Async-First Communication: We coordinate across global time zones primarily\n"
        "   through written specs, git commits, and Slack threads. Meetings are kept to a minimum.\n"
        "2. Privacy-Centric Philosophy: We believe private data belongs to the user. We never\n"
        "   forward customer database schemas, proprietary documents, or server credentials\n"
        "   to third-party public LLM cloud endpoints.\n"
        "3. Local Execution: Our engineers run local test environments using Docker Compose,\n"
        "   llama.cpp, Qdrant, and Redis to mirror the production topology.\n\n"
        "EMPLOYEE BENEFITS & PERKS:\n"
        "- Flexible Work Hours: Pick your own working hours. Core overlap time is strictly between\n"
        "  13:00 and 16:00 UTC.\n"
        "- Hardware Stipend: Every engineer receives a $3,000 yearly stipend to upgrade their GPUs,\n"
        "  host machines, memory devices, or local test rigs.\n"
        "- Learning Budget: $1,500 annual allowance for textbooks, LLM API keys, research paper\n"
        "  subscriptions, and attending global deep learning conferences (e.g. NeurIPS, ICML).\n"
        "- Unlimited Paid Time Off (PTO): A minimum of 20 days off per year is mandatory to prevent burnout."
    )
    
    with open("tests/palmmind_culture.txt", "w", encoding="utf-8") as f:
        f.write(culture_content)
    print("  [CREATED] tests/palmmind_culture.txt")

    # 2. Local Setup Guide Info
    setup_content = (
        "========================================================================\n"
        "PALMMIND AI - LOCAL ENGINEERING ENVIRONMENT SETUP GUIDE\n"
        "========================================================================\n\n"
        "This guide outlines the standard operating instructions to configure and execute\n"
        "the PalmMind Agentic microservices stack on your local developer workspace.\n\n"
        "SYSTEM PREREQUISITES:\n"
        "- Operating System: Windows 11 (WSL2 with Ubuntu) or Ubuntu 22.04 LTS native.\n"
        "- Python Runtime: Python 3.10.x environment required.\n"
        "- Docker Desktop: Installed with active CUDA driver passthrough capabilities.\n"
        "- Hardware: Dedicated NVIDIA GPU with at least 8GB VRAM is highly recommended.\n\n"
        "STEP-BY-STEP INITIALIZATION:\n"
        "Step 1: Set up the virtual environment and install packages:\n"
        "   $ python -m venv .venv\n"
        "   $ source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate\n"
        "   $ pip install -r requirements.txt\n\n"
        "Step 2: Initialize backing databases in Docker:\n"
        "   $ docker-compose up -d postgres redis qdrant\n\n"
        "Step 3: Download and run the llama.cpp server GGUF engine:\n"
        "   Make sure to map your local GGUF models folder to /models inside the container:\n"
        "   $ docker run -p 8080:8080 --gpus all -v \"/path/to/models:/models\" \\\n"
        "     ghcr.io/ggml-org/llama.cpp:server-cuda -m /models/Qwen3.5-4B-Q4_K_S.gguf\n\n"
        "Step 4: Launch the FastAPI Application:\n"
        "   $ uvicorn app.main:app --host 0.0.0.0 --port 8000\n\n"
        "Step 5: Verify the setup via tests:\n"
        "   $ pytest tests/"
    )
    
    with open("tests/palmmind_setup_guide.txt", "w", encoding="utf-8") as f:
        f.write(setup_content)
    print("  [CREATED] tests/palmmind_setup_guide.txt")

def create_pdf_files():
    print("Generating PDF files via reportlab...")
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    
    styles = getSampleStyleSheet()
    
    # Define clean, custom typography styling
    title_style = ParagraphStyle(
        name="TitleStyle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor="#1E293B",
        spaceAfter=15
    )
    h2_style = ParagraphStyle(
        name="H2Style",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor="#2563EB",
        spaceBefore=12,
        spaceAfter=8
    )
    body_style = ParagraphStyle(
        name="BodyStyle",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor="#334155",
        spaceAfter=8
    )

    # 1. PDF File: palmmind_company_policies.pdf
    doc1 = SimpleDocTemplate("tests/palmmind_company_policies.pdf", pagesize=letter)
    story1 = []
    
    story1.append(Paragraph("PalmMind AI — Official Company Policies", title_style))
    story1.append(Spacer(1, 10))
    
    story1.append(Paragraph("1. Code Quality & Peer Reviews", h2_style))
    story1.append(Paragraph(
        "All code submissions must be integrated through Pull Requests targeting the 'main' branch. "
        "Each PR requires a minimum of one passing peer review from a senior engineer and 100% "
        "successful passing coverage on GitHub Actions CI/CD pipelines before merge approvals. "
        "Standard formatting rules are strictly enforced using the 'Black' format checker.",
        body_style
    ))
    
    story1.append(Paragraph("2. Operational Security Guidelines", h2_style))
    story1.append(Paragraph(
        "Security is our highest operational priority. Never check passwords, API tokens, email passwords, "
        "or database connection strings directly into Git version control. Always utilize dynamic `.env` "
        "loading layers, and verify that all configuration keys are covered under active `.gitignore` rules. "
        "Redis servers storing LangGraph session checkpointers must be isolated from the public network "
        "and run under strict local bindings.",
        body_style
    ))
    
    story1.append(Paragraph("3. Annual Vacation & Administrative Leave", h2_style))
    story1.append(Paragraph(
        "We mandate a minimum of 20 days of paid administrative leave per year. Work-life harmony "
        "is critical to achieving high engineering output. Leave requests should be logged through "
        "our HR intranet portal at least one week in advance to ensure continuous coverage across active sprint cards.",
        body_style
    ))
    
    doc1.build(story1)
    print("  [CREATED] tests/palmmind_company_policies.pdf")

    # 2. PDF File: palmmind_interview_syllabus.pdf
    doc2 = SimpleDocTemplate("tests/palmmind_interview_syllabus.pdf", pagesize=letter)
    story2 = []
    
    story2.append(Paragraph("PalmMind AI — Junior AI Engineer Hiring Track", title_style))
    story2.append(Spacer(1, 10))
    
    story2.append(Paragraph("Course Outline & Assessment Syllabus", h2_style))
    story2.append(Paragraph(
        "To ensure all candidates possess robust systems-level and AI-engineering competencies, "
        "our technical screening tracks evaluate candidates across multiple specific domains.",
        body_style
    ))
    
    story2.append(Paragraph("Phase 1: Local RAG Pipeline Engineering", h2_style))
    story2.append(Paragraph(
        "Candidates must construct a fully functional RAG system in memory or using local database containers. "
        "Key skills evaluated include document text extraction, recursive character splitting, "
        "semantic sentence boundaries parsing, dense vector generation using local embeddings models (e.g. FastEmbed), "
        "and high-efficiency upsert and search query execution in a vector database like Qdrant.",
        body_style
    ))
    
    story2.append(Paragraph("Phase 2: Stateful LLM Agentic Loops", h2_style))
    story2.append(Paragraph(
        "Developing AI agent logic using LangGraph to invoke tool calling, handle database transactions, "
        "and persist conversation checkpoints using Redis. The system must operate fully locally using "
        "unsloth Qwen or LLaMA GGUF structures via llama.cpp server CUDA containers.",
        body_style
    ))
    
    story2.append(Paragraph("Phase 3: Security, Hardening & Input Sanitization", h2_style))
    story2.append(Paragraph(
        "Mitigating Remote Code Execution hazards from deserializers, enforcing file upload boundaries (e.g. 10MB limits), "
        "preventing directory traversal filename exploits, securing CORS configs, and writing robust pytest "
        "regression validation structures to secure the endpoints against Prompt DoS and SQL/Key injections.",
        body_style
    ))
    
    doc2.build(story2)
    print("  [CREATED] tests/palmmind_interview_syllabus.pdf")

if __name__ == "__main__":
    print("==================================================")
    print("PalmMind AI Test Files Generator Utility")
    print("==================================================")
    
    # 1. Create text files
    create_txt_files()
    
    # 2. Setup reportlab and build PDF files
    install_reportlab_if_missing()
    create_pdf_files()
    
    print("\n[COMPLETE] All 4 distinct test files successfully created in the 'tests/' directory!")
    print("  - Text File 1: tests/palmmind_culture.txt")
    print("  - Text File 2: tests/palmmind_setup_guide.txt")
    print("  - PDF File 1:  tests/palmmind_company_policies.pdf")
    print("  - PDF File 2:  tests/palmmind_interview_syllabus.pdf")
    print("==================================================")
