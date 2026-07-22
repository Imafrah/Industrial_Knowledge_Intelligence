# 🏭 Industrial Knowledge Intelligence Platform

> **Unified Asset & Operations Brain** — An AI-powered knowledge engine for industrial asset management, automated safety compliance auditing, hybrid vector-lexical search, and predictive maintenance analysis.

[![Backend](https://img.shields.io/badge/Backend-FastAPI_0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LLM & Embeddings](https://img.shields.io/badge/AI-Google_Gemini_2.5_Flash-4285F4?style=for-the-badge&logo=googlegemini&logoColor=white)](https://ai.google.dev/)
[![Database](https://img.shields.io/badge/Database-PostgreSQL_%2B_pgvector-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Frontend](https://img.shields.io/badge/Frontend-React_%2B_Vite-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org/)
[![Container](https://img.shields.io/badge/Docker-Docker_Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Docker Setup (Recommended)](#docker-setup-recommended)
  - [Manual Local Setup](#manual-local-setup)
- [Environment Variables](#-environment-variables)
- [API Reference](#-api-reference)
- [Key Workflows](#-key-workflows)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

---

## 💡 Overview

Industrial plants generate thousands of complex documents — maintenance logs, piping & instrumentation diagrams (P&IDs), safety procedures, equipment manuals, inspection records, and regulatory standards. Information in these documents is often siloed, unstructured, or trapped in scanned physical PDFs.

**Industrial Knowledge Intelligence** unifies operational documentation into a single intelligent platform:
1. **Ingests & Vectorizes** heterogeneous plant documents (scanned/digital PDFs, DOCX, XLSX, TXT, Images) using Google Gemini 768-dim embeddings (`models/gemini-embedding-001`) with automatic Tesseract OCR fallbacks.
2. **Constructs Dynamic Knowledge Graphs** connecting equipment tags, personnel, inspection events, and regulatory constraints using `NetworkX`.
3. **Automates Safety Compliance Audits** against industrial codes (Factory Act, OISD, PESO standards) with automated risk severity scoring.
4. **Executes Hybrid RRF Search** combining PostgreSQL full-text keyword search and pgvector cosine similarity via Reciprocal Rank Fusion.
5. **Drives Predictive Maintenance & Field Operations** through failure probability models, spare parts tracking, historical incident RCA lookup, and a mobile-friendly Field Technician interface.

---

## ✨ Key Features

### 📄 1. Multi-Format Ingestion & Dual OCR Pipeline
- Support for **PDF**, **DOCX**, **XLSX**, **TXT**, **PNG**, **JPG**, and **JPEG** uploads.
- **Smart OCR Fallback:** Native document text parsing with automatic failover to `pytesseract` and `pdf2image` (Poppler) for scanned sheets or legacy blueprints.
- **Vector Embedding Engine:** Automatically extracts content chunks and generates 768-dimensional embeddings mapped into `pgvector` indexes.

### 🕸 2. Knowledge Graph & Relationship Discovery
- Automatic subject-predicate-object triple extraction upon document ingestion.
- Links equipment tags (e.g., `PUMP-101`, `VALVE-204`), maintenance teams, and regulatory compliance standards.
- Employs `NetworkX` algorithms to calculate degree centrality, node connections, and trace shortest connection paths between operational entities.

### 🛡 3. Automated Compliance & Risk Intelligence
- AI compliance engine auditing uploaded manuals and operational logs against **Factory Act**, **OISD** (Oil Industry Safety Directorate), and **PESO** (Petroleum and Explosives Safety Organization) codes.
- Generates overall plant safety scores, severity classifications (High, Medium, Low), and actionable corrective directives.

### 🔍 4. Hybrid Reciprocal Rank Fusion (RRF) Search
- Combines lexical Full-Text Search (FTS via PostgreSQL `tsvector`) with semantic vector similarity search (`pgvector`).
- Merges ranked lists using **Reciprocal Rank Fusion (RRF)** ($k=60$) to deliver high-precision results for technical queries.

### 🛠 5. Maintenance Intelligence & Predictive Timelines
- Interactive equipment timeline tracking historical breakdowns, repairs, safety checks, and specs.
- Advanced AI analysis generating failure probability scores, root-cause insights, spare parts inventory alerts, and recommended maintenance schedule windows.

### 📚 6. Lessons Learned & Incident Log Repository
- Semantic vector lookup across historical incident reports and near-miss logs.
- Enables field engineers to instantly surface past Root Cause Analyses (RCA) and mitigation strategies for active equipment issues.

### 📱 7. Mobile Field Technician Portal
- Responsive mobile interface tailored for plant operators and field technicians.
- Integrated barcode/QR scanner simulator, quick camera document uploader, and offline logging queue.

---

## 🏗 System Architecture

```
                                  ┌────────────────────────────────┐
                                  │      React + Vite Frontend     │
                                  │  (Dashboard, Chat, Search UI)  │
                                  └───────────────┬────────────────┘
                                                  │
                                                  │ HTTP / REST API
                                                  ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       FastAPI Backend App                                         │
│                                                                                                   │
│  ┌───────────────────────┐   ┌───────────────────────┐   ┌─────────────────────────────────────┐  │
│  │   Ingestion Engine    │   │  Knowledge Graph Engine│   │         Search & RAG Engine         │  │
│  │ (pypdf/pytesseract/   │   │     (NetworkX)        │   │ (Hybrid RRF FTS + Cosine Similarity)│  │
│  │     pdf2image)        │   │                       │   │                                     │  │
│  └───────────┬───────────┘   └───────────┬───────────┘   └──────────────────┬──────────────────┘  │
└──────────────┼───────────────────────────┼──────────────────────────────────┼─────────────────────┘
               │                           │                                  │
               ▼                           ▼                                  ▼
┌─────────────────────────────┐  ┌──────────────────┐               ┌──────────────────┐
│        PostgreSQL DB        │  │   NetworkX In-   │               │ Google Gemini    │
│  (pgvector + Full-Text FTS) │  │   Memory Graph   │               │ AI API           │
└─────────────────────────────┘  └──────────────────┘               └──────────────────┘
```

---

## 📁 Project Structure

```
.
├── docker-compose.yml              # Container orchestration for Postgres, Backend, and Frontend
├── .env.example                    # Sample environment variables configuration
├── README.md                       # Platform documentation
├── backend/
│   ├── Dockerfile                  # Python 3.11 image with Tesseract OCR & Poppler
│   ├── requirements.txt            # FastAPI, SQLAlchemy, pgvector, NetworkX, pytesseract
│   └── app/
│       ├── main.py                 # FastAPI app entry point & CORS configuration
│       ├── database.py             # SQLAlchemy async engine & database session management
│       ├── models.py               # DB Schema (Document, Chunk, Relation, Audit, Incident)
│       ├── gemini_client.py        # Gemini API client for embeddings & compliance auditing
│       ├── ingestion.py            # Text extraction, chunking, OCR fallback & graph parsing
│       ├── seed.py                 # Sample database seeder
│       └── routers/
│           ├── documents.py        # Document upload & ingestion status endpoints
│           ├── chat.py             # RAG conversational engine endpoints
│           ├── maintenance.py      # Timeline & predictive maintenance analysis endpoints
│           ├── dashboard.py        # High-level stats & metrics endpoints
│           ├── graph.py            # Knowledge graph visualization & pathfinding endpoints
│           ├── compliance.py       # Safety audit summary & findings endpoints
│           └── search.py           # Hybrid RRF search query endpoints
└── frontend/
    ├── Dockerfile                  # Vite React application Dockerfile
    ├── package.json                # Frontend dependencies
    ├── vite.config.js              # Vite server & proxy configuration
    └── src/
        ├── App.jsx                 # Main application router & layout wrapper
        ├── index.css               # Global CSS styling & design design system
        ├── main.jsx                # React DOM entry point
        └── pages/
            ├── Dashboard.jsx       # Overview dashboard with stats, recent docs, & quick links
            ├── Upload.jsx          # Drag-and-drop document upload interface
            ├── Chat.jsx            # RAG Copilot chat assistant with cited sources
            ├── Maintenance.jsx     # Equipment timeline & AI predictive breakdown analysis
            ├── Search.jsx          # Hybrid FTS + Vector RRF search interface
            ├── Compliance.jsx      # Safety compliance audit scores & directives dashboard
            ├── Lessons.jsx         # Historical incident & near-miss RCA lookup
            └── FieldTech.jsx       # Mobile Field Technician interface with barcode scanner
```

---

## 🚀 Getting Started

### Prerequisites

- [Docker](https://www.docker.com/get-started) and Docker Compose installed.
- A [Google Gemini API Key](https://aistudio.google.com/app/apikey) (Free tier available).

---

### Docker Setup (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Imafrah/Industrial_Knowledge_Intelligence.git
   cd Industrial_Knowledge_Intelligence
   ```

2. **Configure Environment Variables:**
   ```bash
   cp .env.example .env
   ```
   Open `.env` and set your Gemini API key:
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   ```

3. **Build and Launch Containers:**
   ```bash
   docker-compose up --build
   ```
   This will spin up:
   - **PostgreSQL Database** (`pgvector/pgvector:pg16`) on port `5432`
   - **FastAPI Backend** on port `8000` (including `tesseract-ocr` & `poppler-utils`)
   - **React + Vite Frontend** on port `5173`

4. **Access the Application:**
   - **Frontend UI:** [http://localhost:5173](http://localhost:5173)
   - **API Documentation (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Manual Local Setup

If you prefer running services outside Docker:

#### 1. Database Setup
Install PostgreSQL 16 with the `pgvector` extension enabled, and create a database named `indstry`:
```sql
CREATE DATABASE indstry;
\c indstry;
CREATE EXTENSION IF NOT EXISTS vector;
```

#### 2. System Dependencies (for OCR)
- **Ubuntu/Debian:** `sudo apt-get install -y tesseract-ocr poppler-utils`
- **macOS:** `brew install tesseract poppler`
- **Windows:** Install [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) and [Poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases/), adding them to system PATH.

#### 3. Backend Setup
```bash
cd backend
python -m venv venv

# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```
Set environment variables:
```bash
export GEMINI_API_KEY="your_api_key"
export DATABASE_URL="postgresql+asyncpg://indstry:indstry_pass@localhost:5432/indstry"
```
Run the FastAPI development server:
```bash
uvicorn app.main:app --reload --port 8000
```

#### 4. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## ⚙ Environment Variables

| Variable | Required | Default / Format | Description |
|----------|----------|------------------|-------------|
| `GEMINI_API_KEY` | **Yes** | `AIzaSy...` | API key from Google AI Studio for Gemini 2.5 Flash & embeddings |
| `DATABASE_URL` | **Yes** | `postgresql+asyncpg://indstry:indstry_pass@postgres:5432/indstry` | Async PostgreSQL connection string with `pgvector` support |

---

## 📡 API Reference

| Category | Method | Path | Description |
|----------|--------|------|-------------|
| **Dashboard** | `GET` | `/api/dashboard/stats` | High-level metrics, doc counts, & active knowledge node count |
| **Documents** | `POST` | `/api/documents/upload` | Upload & ingest document (OCR fallback, chunking, 768-dim embeddings, KG extraction) |
| | `GET` | `/api/documents/` | List all ingested documents and their metadata |
| **Chat (RAG)** | `POST` | `/api/chat` | Query RAG conversational engine with cited document sources |
| **Hybrid Search**| `POST` | `/api/search/hybrid` | Hybrid lexical FTS + pgvector cosine similarity via Reciprocal Rank Fusion (RRF) |
| **Knowledge Graph**| `GET` | `/api/graph/data` | Retrieve nodes, edges, degree centrality & connection metrics |
| | `GET` | `/api/graph/path` | Find shortest relationship path between two entity nodes |
| **Compliance** | `GET` | `/api/compliance/summary` | Get safety score averages, risk classifications & metrics |
| | `GET` | `/api/compliance/findings` | Detailed compliance gaps, violated standards (Factory Act, OISD, PESO) & actions |
| **Maintenance** | `GET` | `/api/maintenance/timeline/{equipment_id}` | Chronological repair history, audits, & specs for equipment tag |
| | `GET` | `/api/maintenance/advanced-analysis/{equipment_id}` | AI predictive breakdown probability, spares inventory alerts & schedule |

---

## 🔄 Sequence Workflow

```mermaid
sequenceDiagram
    autonumber
    actor User as "Plant Engineer / Operator"
    participant FE as "React + Vite Frontend"
    participant BE as "FastAPI Backend"
    participant OCR as "OCR / Text Extractor"
    participant GEM as "Google Gemini API"
    participant DB as "Postgres (pgvector)"
    participant KG as "NetworkX Graph"

    User->>FE: Upload Document / Manual
    FE->>BE: POST /api/documents/upload
    BE->>OCR: Extract Text (Tesseract fallback if image/scanned PDF)
    OCR-->>BE: Extracted Document Content
    BE->>GEM: Generate 768-dim Embeddings
    GEM-->>BE: Embeddings Vectors
    BE->>KG: Extract Entities & Relation Triples
    BE->>DB: Store Document, Chunks & Vectors
    BE-->>FE: Ingestion Complete Notification

    User->>FE: Submit Query in Chat or Search
    FE->>BE: POST /api/chat or POST /api/search/hybrid
    BE->>DB: Execute Lexical FTS + Vector Cosine Distance
    DB-->>BE: Top-K Context Chunks
    BE->>GEM: Generate Response with Citations
    GEM-->>BE: Final AI Response
    BE-->>FE: Display Response & References
```

---

## ❓ Troubleshooting

- **Poppler / Tesseract missing during manual local execution:**
  Ensure `tesseract` and `poppler-utils` are installed on your OS and added to system PATH. Running via `docker-compose up --build` includes all system dependencies automatically.
- **Database Connection Refused:**
  Ensure PostgreSQL is running (`docker-compose ps`). The backend container waits for Postgres healthcheck before starting.
- **Gemini API Error:**
  Verify `GEMINI_API_KEY` is specified correctly in `.env` without surrounding quotes or whitespace.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for details.