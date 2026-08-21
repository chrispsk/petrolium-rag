# Petroleum RAG Assistant

A production-style conversational Retrieval-Augmented Generation (RAG) system built with LangGraph, FastAPI, PostgreSQL/pgvector and local LLM inference through Ollama.

The project includes conversational memory, query understanding, semantic caching, retrieval and reranking, document ingestion, source attribution, LangSmith tracing/evaluation, authentication, rate limiting and a lightweight ChatGPT-style web interface.

---

## Overview

This project was designed as an end-to-end RAG application rather than a simple retrieval notebook.

It consists of two main LangGraph workflows:

- **Conversational RAG graph** for query understanding, conversational follow-ups, semantic cache lookup, retrieval, reranking, generation and response handling.
- **Document ingestion graph** for file discovery, change detection, Markdown-aware chunking, contextualisation, embedding generation and PostgreSQL/pgvector indexing.

The application is exposed through a FastAPI backend and a lightweight single-page web client.

---

## System Architecture

![Petroleum RAG System Architecture](assets/architecture.png)

The system separates document ingestion from runtime question answering.

At runtime, a user query is first analysed and classified. Standalone knowledge queries can be checked against the semantic cache before retrieval. If no suitable cache entry exists, relevant chunks are retrieved from PostgreSQL/pgvector, reranked using a CrossEncoder and passed to a local Ollama model for grounded answer generation.

---

## Main Components

- **Frontend:** HTML, CSS and JavaScript single-page interface
- **API:** FastAPI
- **Orchestration:** LangGraph
- **LLM:** Qwen 2.5 7B through Ollama
- **Embeddings:** `BAAI/bge-base-en-v1.5`
- **Reranker:** `BAAI/bge-reranker-base`
- **Vector database:** PostgreSQL + pgvector
- **Tracing and evaluation:** LangSmith
- **Document ingestion:** LangGraph ingestion workflow
- **Authentication:** HttpOnly session cookies
- **Semantic cache:** pgvector similarity search
- **Database access:** asynchronous Psycopg connection pool

---

## Conversational RAG Workflow

The conversational graph handles both knowledge-base queries and ordinary conversation.

Main stages:

1. Add the current user message to conversation history.
2. Analyse the current message and classify its intent.
3. Resolve follow-ups and retry requests using conversation history.
4. Check the semantic cache when appropriate.
5. Retrieve candidate chunks from PostgreSQL/pgvector.
6. Rerank retrieved chunks with a CrossEncoder.
7. Generate a grounded answer with Qwen through Ollama.
8. Return document sources and heading paths.
9. Save only suitable standalone queries to the semantic cache.

The system can distinguish between:

- standalone knowledge queries
- multi-part comparisons
- conversational follow-ups
- retry/correction requests
- greetings
- polite/social messages
- ordinary conversation

Follow-up queries are deliberately excluded from the semantic cache because their meaning may depend on previous conversation history.

---

## LangGraph Studio

LangSmith Studio is used to inspect graph execution, state transitions and routing decisions.

![LangGraph Studio](assets/langsmith-studio.png)

This makes it possible to inspect behaviours such as:

- query understanding
- semantic cache hits
- retrieval
- reranking
- generation
- retry routing
- conversational branches
- final state values
- returned sources

---

## Web Interface

The project includes a lightweight ChatGPT-style frontend.

![RAG Assistant Web Interface](assets/chat-interface.png)

The frontend supports:

- multi-turn conversations
- source attribution
- session-based authentication
- document ingestion
- statistics
- isolated conversation thread IDs

Example comparison query:

> Compare the minimum transaction size for DEF with the minimum volume for Argo ethanol in Chicago.

The system decomposes comparison requests into independent information requirements and combines the grounded results into a single final response.

---

## Statistics

The application exposes operational RAG statistics through the frontend.

![RAG Statistics](assets/statistics.png)

Currently displayed metrics include:

- indexed documents
- indexed chunks
- cached queries
- total queries
- cache hit rate

---

## Document Ingestion

The ingestion pipeline is implemented as a separate LangGraph workflow.

```text
scan_files
    ↓
detect_changes
    ↓
load_documents
    ↓
chunk_documents
    ↓
contextualize_chunks
    ↓
embed_chunks
    ↓
save_to_database
```

Only new or modified Markdown documents are re-indexed.

---

## Markdown-Aware Chunking

Documents are first split using Markdown hierarchy:

```text
#     Document title
##    Section
###   Subsection
####  Sub-subsection
##### Detail
```

Long sections are then recursively split using:

```text
chunk_size = 1500
chunk_overlap = 150
```

Each embedded chunk is contextualised with its source and heading path:

```text
Source: document.md
Context: Section > Subsection > Detail

Original chunk content...
```

This gives the embedding model additional structural context while preserving the original hierarchy for source attribution.

---

## Semantic Cache

Standalone knowledge queries can be stored in a pgvector-based semantic cache.

A response is cached only when:

- the generated answer is complete
- sources are present
- retrieval/reranking confidence passes the configured threshold
- the request is a standalone query
- the request is not a follow-up
- the request is not a retry

Current reranker threshold:

```text
0.95
```

The cache stores:

- original query
- query embedding
- generated answer
- sources
- decomposed subqueries

---

## Retrieval and Reranking

The runtime retrieval pipeline follows this structure:

```text
Query
  ↓
BGE embedding
  ↓
pgvector similarity search
  ↓
Candidate chunks
  ↓
BGE CrossEncoder reranker
  ↓
Best grounded context
  ↓
Qwen generation
```

This separates fast vector retrieval from more precise neural reranking.

---

## API

FastAPI exposes the main application functionality.

```text
POST /login
POST /query
POST /ingest
GET  /stats
GET  /health
```

FastAPI also automatically exposes:

```text
/docs
/redoc
/openapi.json
```

The generated OpenAPI schema can be imported into API testing tools such as Burp Suite Professional.

---

## Authentication

The browser does not contain a hardcoded API secret.

Authentication flow:

```text
User password
    ↓
POST /login
    ↓
Server validates API_PASSWORD from .env
    ↓
Random session token
    ↓
HttpOnly session cookie
    ↓
Protected API requests
```

The password remains server-side in `.env` and is excluded from Git.

Session tokens are generated server-side and stored in memory.

---

## Rate Limiting

Knowledge queries are currently limited to:

```text
10 requests / 60 seconds / authenticated session
```

The limiter is implemented asynchronously and runs before the RAG graph is invoked.

---

## Database

PostgreSQL stores:

- documents
- document chunks
- vector embeddings
- semantic cache entries

pgvector is used for vector similarity search.

The backend uses an asynchronous Psycopg connection pool.

---

## Evaluation

LangSmith is used for tracing and evaluation.

Evaluation includes retrieval-focused metrics such as:

- Precision@K
- Recall@K
- Mean Reciprocal Rank
- source/path correctness
- rejection behaviour

This allows retrieval quality to be evaluated independently from answer generation.

---

## Project Structure

```text
petrolium/
│
├── data/
│   ├── adblue-and-def.md
│   └── americas-biofuels.md
│
├── Notebooks/
│   ├── 01_chunking_ingestion.ipynb
│   └── 02_retrieval_reranking.ipynb
│
├── production/
│   │
│   ├── client/
│   │   ├── index.html
│   │   ├── app.js
│   │   └── style.css
│   │
│   ├── langgraph_ap/
│   │   ├── api.py
│   │   ├── database.py
│   │   ├── evaluation.py
│   │   ├── graph.py
│   │   ├── nodes.py
│   │   ├── state.py
│   │   ├── studio_database.py
│   │   ├── langgraph.json
│   │   │
│   │   └── ingestion/
│   │       ├── __init__.py
│   │       ├── graph.py
│   │       ├── nodes.py
│   │       └── state.py
│   │
│   └── setup_database.py
│
├── assets/
│   ├── architecture.png
│   ├── langsmith-studio.png
│   ├── chat-interface.png
│   └── statistics.png
│
├── .gitignore
└── README.md
```

---

## Security

The application currently includes:

- HttpOnly session cookies
- server-side password configuration
- request validation with Pydantic
- authenticated API endpoints
- rate limiting
- CORS restrictions
- ingestion concurrency protection
- isolated conversation thread IDs

The project is also intended to be security-tested as an API/RAG application using Burp Suite Professional.

Areas of interest include:

- authentication and session management
- CORS and CSRF
- rate-limit behaviour
- API input validation
- thread isolation
- semantic cache poisoning
- prompt injection
- indirect prompt injection
- retrieval manipulation
- source spoofing

---

## Running the Frontend

From the client directory:

```bash
python -m http.server 5500 --bind 0.0.0.0
```

Then open:

```text
http://127.0.0.1:5500/index.html
```

For LAN testing:

```text
http://<LOCAL-IP>:5500/index.html
```

---

## Running the API

Run the FastAPI application from the backend environment.

The API listens on:

```text
0.0.0.0:8000
```

Example local URL:

```text
http://127.0.0.1:8000
```

---

## Configuration

Sensitive configuration is stored in `.env` and intentionally excluded from Git.

Example:

```env
API_PASSWORD=your_password
```

Do not commit:

```text
.env
API keys
passwords
private tokens
database credentials
```

---

## Git Ignore

Recommended ignored files and folders include:

```text
.env
*.env
__pycache__/
*.pyc
.langgraph_api/
.ipynb_checkpoints/
files_to_be_added_to_data/
*.db
*.sqlite
*.sqlite3
.vscode/
.idea/
```

---

## Technologies

```text
Python
FastAPI
LangGraph
LangSmith
PostgreSQL
pgvector
Ollama
Qwen 2.5
HuggingFace Embeddings
BGE
CrossEncoder
Psycopg
HTML
CSS
JavaScript
Burp Suite Professional
```

---

## Current Status

The project is under active development.

Current areas of work include:

- production-style conversational RAG orchestration
- semantic caching
- retrieval evaluation
- document ingestion
- API security
- RAG-specific penetration testing
- prompt injection testing
- session isolation
- deployment hardening

---

## Screenshots

### LangGraph Studio

![LangGraph Studio](assets/langsmith-studio.png)

### Chat Interface

![Chat Interface](assets/chat-interface.png)

### Statistics

![Statistics](assets/statistics.png)

---

## Future Improvements

Potential future improvements include:

- persistent session storage
- logout support
- HTTPS deployment
- secure cookie enforcement
- CSRF protection
- per-user authentication
- persistent rate-limit storage
- containerised deployment
- automated security testing
- additional RAG evaluation metrics
- larger document collections
- hybrid lexical + vector retrieval
- more advanced cache invalidation

---

## Disclaimer

This project is intended for research, learning, experimentation and controlled security testing.

Security testing should only be performed against systems you own or have explicit permission to test.
