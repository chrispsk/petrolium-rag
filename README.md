# Petroleum RAG Assistant

A production-style conversational Retrieval-Augmented Generation (RAG) system built with **LangGraph**, **FastAPI**, **PostgreSQL/pgvector**, **BGE embeddings and reranking**, and local LLM inference through **Ollama / Qwen 2.5**.

The project goes beyond a basic retrieval notebook and implements a complete conversational RAG application with:

- conversational memory
- query understanding and intent routing
- follow-up resolution
- multi-query decomposition
- vector retrieval
- CrossEncoder reranking
- semantic caching
- Markdown-aware ingestion
- source attribution
- LangSmith tracing and evaluation
- FastAPI API
- session authentication
- rate limiting
- a lightweight ChatGPT-style web interface

---

# Architecture

![Petroleum RAG System Architecture](assets/architecture.png)

The application contains two separate LangGraph workflows:

1. **Conversational RAG Graph**
2. **Document Ingestion Graph**

The ingestion pipeline creates the searchable knowledge base, while the conversational graph handles runtime questions, retrieval and generation.

---

# Main Technology Stack

| Component | Technology |
|---|---|
| Backend | FastAPI |
| RAG Orchestration | LangGraph |
| LLM | Qwen 2.5 7B |
| Local Inference | Ollama |
| Embeddings | BAAI/bge-base-en-v1.5 |
| Reranker | BAAI/bge-reranker-base |
| Database | PostgreSQL |
| Vector Search | pgvector |
| Database Driver | Psycopg 3 |
| Tracing | LangSmith |
| Evaluation | LangSmith |
| Frontend | HTML / CSS / JavaScript |
| Authentication | HttpOnly session cookie |
| API Validation | Pydantic |

---

# Conversational RAG Workflow

The main runtime graph processes both knowledge-base queries and ordinary conversation.

```text
START
  |
  v
add_user_message
  |
  v
understand_query
  |
  +---------------- conversation ----------------+
  |                                              |
  |                                              v
  |                                        chat_response
  |                                              |
  |                                              v
  |                                             END
  |
  +---------------- retry ----------------------+
  |                                              |
  |                                              v
  |                                           retrieve
  |
  +------------- query / follow_up -------------+
                                                 |
                                                 v
                                            check_cache
                                             /       \
                                           HIT       MISS
                                            |          |
                                            v          v
                                           END      retrieve
                                                       |
                                                       v
                                                     rerank
                                                       |
                                                       v
                                                    generate
                                                       |
                                                       v
                                                   save_cache
                                                       |
                                                       v
                                                      END
```

The query-understanding stage distinguishes between:

- standalone knowledge queries
- conversational follow-ups
- retry requests
- comparisons
- greetings
- polite/social messages
- ordinary conversation

Conversation history is used only when necessary to resolve references and follow-ups.

---

# Query Decomposition

Independent information requirements are decomposed into standalone subqueries.

Example:

```text
Compare the minimum transaction size for DEF
with the minimum volume for Argo ethanol in Chicago.
```

becomes:

```text
What is the minimum transaction size for DEF?

What is the minimum volume for Argo ethanol in Chicago?
```

Each subquery is retrieved and reranked independently before the final answer is generated.

---

# Retrieval Pipeline

```text
User Query
    |
    v
Query Understanding
    |
    v
Query Embedding
    |
    v
PostgreSQL + pgvector
    |
    v
Candidate Chunks
    |
    v
BGE CrossEncoder
    |
    v
Reranked Context
    |
    v
Qwen 2.5 through Ollama
    |
    v
Grounded Answer + Sources
```

Vector retrieval is used for candidate generation, while CrossEncoder reranking provides a second relevance stage.

---

# Semantic Cache

Standalone knowledge queries may be stored in a semantic cache backed by pgvector.

The cache stores:

- query
- query embedding
- answer
- returned sources
- decomposed subqueries

A response is cached only when:

- the answer is complete
- sources are present
- reranking confidence passes the configured threshold
- the request is a standalone query

Current cache threshold:

```text
0.95
```

Follow-ups are deliberately **not cached**, because their meaning may depend on conversation history.

Examples that may be cached:

```text
What is DEF?

What is the minimum transaction size for DEF?
```

Examples that are not cached:

```text
Are you sure?

And maximum?

Try again.

Thanks.
```

---

# Document Ingestion Pipeline

Document ingestion is implemented as a second LangGraph workflow.

```text
START
  |
  v
scan_files
  |
  v
detect_changes
  |
  v
load_documents
  |
  v
chunk_documents
  |
  v
contextualize_chunks
  |
  v
embed_chunks
  |
  v
save_to_database
  |
  v
END
```

Only new or modified documents are re-indexed.

File changes are detected using SHA-256 hashes.

---

# Markdown-Aware Chunking

Documents are split according to Markdown structure.

```text
#     document_title
##    section
###   subsection
####  subsubsection
##### detail
```

The complete hierarchy is preserved as a heading path.

Example:

```text
METHODOLOGY AND SPECIFICATIONS GUIDE
>
Argus AdBlue®-DEF and TGU
>
Product specification
>
Diesel exhaust fluid (DEF)
```

Long sections are additionally split using:

```text
chunk_size = 1500
chunk_overlap = 150
```

---

# Contextualised Embeddings

Before embedding, each chunk is enriched with structural context.

Example:

```text
Source: adblue-and-def.md
Context: METHODOLOGY AND SPECIFICATIONS GUIDE > Product specification > Diesel exhaust fluid (DEF)

Original document content...
```

The contextualised text is embedded while the original source metadata is preserved for attribution.

Embedding model:

```text
BAAI/bge-base-en-v1.5
```

Embedding dimension:

```text
768
```

Embeddings are normalised before storage.

---

# LangGraph Studio

LangSmith Studio is used during development to inspect graph execution.

![LangGraph Studio](assets/langsmith-studio.png)

Studio allows inspection of:

- node execution
- graph routing
- state transitions
- conversation history
- cache hits
- retrieval results
- reranking
- generated answers
- sources
- ingestion stages

---

# Web Interface

The project includes a lightweight ChatGPT-style single-page frontend.

![RAG Assistant Web Interface](assets/chat-interface.png)

Features include:

- multi-turn conversations
- source attribution
- isolated thread IDs
- authentication
- document ingestion
- statistics
- automatic scrolling
- responsive dark interface

Sources are displayed using the original document and heading hierarchy.

Example:

```text
adblue-and-def.md
>
METHODOLOGY AND SPECIFICATIONS GUIDE
>
Argus AdBlue®-DEF and TGU
>
Product specification
>
Diesel exhaust fluid (DEF)
```

---

# Statistics

![RAG Statistics](assets/statistics.png)

The frontend exposes operational metrics including:

- Documents
- Chunks
- Cached Queries
- Total Queries
- Cache Hit Rate

---

# API

FastAPI exposes the application through the following primary endpoints:

```text
POST /login
POST /query
POST /ingest
GET  /stats
GET  /health
```

FastAPI also generates:

```text
/docs
/redoc
/openapi.json
```

Example:

```text
http://127.0.0.1:8000/docs
```

OpenAPI schema:

```text
http://127.0.0.1:8000/openapi.json
```

The OpenAPI schema can also be imported into tools such as Burp Suite Professional for API security testing.

---

# Authentication

The frontend does not contain a hardcoded API key.

Authentication flow:

```text
User Password
      |
      v
POST /login
      |
      v
FastAPI
      |
      v
Validate API_PASSWORD from .env
      |
      v
Generate random session token
      |
      v
HttpOnly cookie
      |
      v
Authenticated API requests
```

Session tokens are generated using:

```python
secrets.token_urlsafe(32)
```

The cookie is configured as:

```text
HttpOnly
SameSite=Lax
```

For the current local HTTP development environment:

```text
Secure=False
```

HTTPS deployment should use:

```text
Secure=True
```

---

# Rate Limiting

Knowledge queries are currently limited to:

```text
10 requests / 60 seconds / authenticated session
```

Rate limiting occurs before the RAG graph is executed.

---

# PostgreSQL Database

The project uses PostgreSQL with the pgvector extension.

The database stores:

- document metadata
- document chunks
- chunk embeddings
- semantic cache queries
- semantic cache embeddings
- cached answers
- decomposed subqueries

---

# Database Schema

The logical database structure used by the application is:

```text
documents
|
+-- id
+-- filename
+-- file_hash
+-- indexed_at
|
|  1
|  |
|  | N
v
chunks
|
+-- document_id
+-- chunk_id
+-- heading_path
+-- content
+-- embedding VECTOR(768)


semantic_cache
|
+-- id
+-- query
+-- query_embedding VECTOR(768)
+-- answer
+-- subqueries
```

Relationship:

```text
documents
    |
    | 1 : N
    |
    v
chunks
```

Deleting/re-indexing a document removes its previous chunks before the new version is inserted.

The source of truth for database creation is:

```text
production/setup_database.py
```

---

# Requirements

The dependency file is located at:

```text
production/langgraph_ap/requirements.txt
```

The requirements were tested by installing them into a clean Python 3.11 Conda environment.

Current direct dependencies:

```text
# Web API
fastapi==0.141.1
uvicorn==0.46.0
pydantic==2.13.3
python-dotenv==1.2.2

# LangChain / LangGraph
langchain-core==1.5.4
langchain-huggingface==1.2.2
langchain-ollama==1.1.0
langchain-text-splitters==1.1.2
langgraph==1.2.11
langgraph-cli[inmem]==0.4.31
langsmith==0.7.37

# Embeddings / reranking
sentence-transformers==5.4.1
transformers==5.6.2
torch==2.8.0
scikit-learn==1.8.0
numpy==2.4.4

# PostgreSQL / pgvector
psycopg==3.3.4
psycopg-binary==3.3.4
psycopg-pool==3.3.1
pgvector==0.5.0
```

The requirements were verified with:

```bash
python -c "import fastapi, langgraph, psycopg, pgvector, sentence_transformers, torch; print('Imports OK')"
```

Both:

```text
langgraph dev
```

and:

```text
python api.py
```

were successfully tested from a clean environment.

---

# Installation

## 1. Clone the Repository

```bash
git clone https://github.com/chrispsk/petrolium-rag.git
cd petrolium-rag
```

---

## 2. Create a Python Environment

Python 3.11 is recommended.

Using Conda:

```bash
conda create -n cyberag python=3.11
conda activate cyberag
```

---

## 3. Install Python Dependencies

Move to the backend directory:

```bash
cd production/langgraph_ap
```

Install:

```bash
pip install -r requirements.txt
```

For NVIDIA GPU acceleration, install the appropriate CUDA-enabled PyTorch build for the local system if required.

GPU acceleration is recommended for:

- embedding generation
- CrossEncoder reranking
- model-related workloads

CPU execution is also possible.

---

# PostgreSQL Installation

## Windows

Install PostgreSQL from the official PostgreSQL installer.

The project was developed using PostgreSQL 17.

During installation configure:

```text
Host: localhost
Port: 5432
User: postgres
```

Choose a local password for the PostgreSQL user.

The application database configuration must match the PostgreSQL installation.

---

## Linux / Debian / Ubuntu

Example:

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

Start PostgreSQL:

```bash
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

Verify:

```bash
sudo systemctl status postgresql
```

---

# pgvector Installation

The application requires the PostgreSQL `vector` extension.

After pgvector is installed, connect to PostgreSQL and enable:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Verify:

```sql
SELECT extname
FROM pg_extension
WHERE extname = 'vector';
```

Expected:

```text
vector
```

---

# Create the Database Schema

The repository contains:

```text
production/setup_database.py
```

From the `production` directory run:

```bash
python setup_database.py
```

This initialises the database structures required by the RAG system.

The schema includes:

```text
documents
chunks
semantic_cache
```

The vector columns use:

```text
VECTOR(768)
```

to match:

```text
BAAI/bge-base-en-v1.5
```

---

# Ollama Installation

Install Ollama for the target operating system.

After installation, download the model:

```bash
ollama pull qwen2.5:7b
```

Verify:

```bash
ollama list
```

Expected to include:

```text
qwen2.5:7b
```

Ensure Ollama is running before starting the RAG application.

---

# Environment Configuration

Create:

```text
production/langgraph_ap/.env
```

Example:

```env
API_PASSWORD=change_this_password
```

LangSmith configuration can also be added when tracing is required.

Example:

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=petroleum-rag
```

Never commit:

```text
.env
API keys
passwords
access tokens
private credentials
```

The repository `.gitignore` excludes environment files.

---

# Development Mode — LangGraph Studio

Development mode is used to visually inspect and debug the LangGraph workflows.

Activate the environment:

```bash
conda activate cyberag
```

Move to:

```bash
cd production/langgraph_ap
```

The project contains:

```text
langgraph.json
```

which exposes both graphs:

```text
rag
ingestion
```

For Studio development, the graph can use the Studio-compatible database pool:

```python
from studio_database import studio_pool as pool
```

Start LangGraph development mode:

```bash
langgraph dev
```

LangGraph starts the local development runtime and connects the application to Studio.

The following graphs can then be inspected:

```text
rag
ingestion
```

Studio is useful for inspecting:

```text
Input
State
Messages
Subqueries
Cache decisions
Retrieved chunks
Reranked chunks
Generated answers
Sources
Conditional routes
Conversation memory
Ingestion state
```

Stop the development server with:

```text
Ctrl + C
```

---

# Production Mode — FastAPI

For normal application execution, use the production database pool.

Both runtime graphs should import:

```python
from database import pool
```

instead of:

```python
from studio_database import studio_pool as pool
```

Ensure the following are running first:

```text
PostgreSQL
Ollama
```

Activate the Python environment:

```bash
conda activate cyberag
```

Move to:

```bash
cd production/langgraph_ap
```

Start:

```bash
python api.py
```

The API listens on:

```text
0.0.0.0:8000
```

Local access:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

OpenAPI:

```text
http://127.0.0.1:8000/openapi.json
```

---

# Start the Frontend

Open another terminal.

Move to:

```bash
cd production/client
```

Start the static frontend server:

```bash
python -m http.server 5500 --bind 0.0.0.0
```

Open:

```text
http://127.0.0.1:5500/index.html
```

For another machine on the same LAN:

```text
http://<SERVER-IP>:5500/index.html
```

Example:

```text
http://192.168.1.100:5500/index.html
```

---

# Complete Local Runtime

A complete production-style local run requires three components:

```text
Terminal 1
---------
Ollama

        +

Terminal 2
---------
python api.py
FastAPI :8000

        +

Terminal 3
---------
python -m http.server 5500 --bind 0.0.0.0
Frontend :5500
```

Flow:

```text
Browser
   |
   v
Frontend :5500
   |
   v
FastAPI :8000
   |
   v
LangGraph
   |
   +----------------------+
   |                      |
   v                      v
PostgreSQL             Ollama
pgvector               Qwen 2.5
```

---

# Project Structure

```text
petrolium/
|
+-- data/
|   |
|   +-- adblue-and-def.md
|   +-- americas-biofuels.md
|
+-- Notebooks/
|   |
|   +-- 01_chunking_ingestion.ipynb
|   +-- 02_retrieval_reranking.ipynb
|
+-- production/
|   |
|   +-- client/
|   |   |
|   |   +-- index.html
|   |   +-- app.js
|   |   +-- style.css
|   |
|   +-- langgraph_ap/
|   |   |
|   |   +-- api.py
|   |   +-- database.py
|   |   +-- evaluation.py
|   |   +-- graph.py
|   |   +-- nodes.py
|   |   +-- state.py
|   |   +-- studio_database.py
|   |   +-- langgraph.json
|   |   +-- requirements.txt
|   |   |
|   |   +-- ingestion/
|   |       |
|   |       +-- __init__.py
|   |       +-- graph.py
|   |       +-- nodes.py
|   |       +-- state.py
|   |
|   +-- setup_database.py
|
+-- assets/
|   |
|   +-- architecture.png
|   +-- langsmith-studio.png
|   +-- chat-interface.png
|   +-- statistics.png
|
+-- .gitignore
+-- README.md
```

---

# Evaluation

LangSmith is used for tracing and evaluation.

The evaluation pipeline includes retrieval-oriented metrics such as:

```text
Precision@K
Recall@K
Mean Reciprocal Rank
Source/path correctness
Rejection behaviour
```

This allows retrieval quality to be analysed separately from final answer generation.

---

# Security

The application includes several security controls:

- HttpOnly session cookies
- server-side password configuration
- authenticated API endpoints
- Pydantic input validation
- rate limiting
- CORS configuration
- ingestion concurrency protection
- isolated conversation thread IDs
- secrets excluded through `.gitignore`

The application is also being used for controlled RAG/API penetration testing.

Security areas of interest include:

```text
Authentication
Session management
CSRF
CORS
Rate-limit behaviour
Malformed API requests
Thread isolation
Semantic cache poisoning
Prompt injection
Indirect prompt injection
Retrieval manipulation
Source spoofing
Information leakage
```

Burp Suite Professional can import:

```text
/openapi.json
```

for API-driven testing.

---

# Current Security Limitations

The current implementation is primarily intended for local development and controlled testing.

Examples of areas that should be hardened before Internet-facing deployment:

- sessions are currently held in application memory
- no persistent session store
- no logout endpoint
- local HTTP uses `Secure=False` cookies
- CSRF protection should be added for Internet-facing deployment
- HTTPS should be enabled
- rate limiting should use persistent/shared storage for multi-worker deployments
- production database credentials should be managed through secrets/environment configuration

---

# Git Ignore

The repository excludes local and sensitive files such as:

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

# Screenshots

## LangGraph Studio

![LangGraph Studio](assets/langsmith-studio.png)

---

## Conversational Interface

![RAG Chat Interface](assets/chat-interface.png)

---

## Statistics

![RAG Statistics](assets/statistics.png)

---

# Future Improvements

Possible future work includes:

- persistent session storage
- logout endpoint
- HTTPS deployment
- Secure cookies
- CSRF protection
- per-user authentication
- persistent distributed rate limiting
- hybrid lexical + semantic retrieval
- larger document collections
- automated security regression tests
- more RAG evaluation metrics
- improved semantic cache invalidation
- containerised deployment
- production secrets management

---

# Disclaimer

This project is intended for:

- research
- education
- RAG experimentation
- AI engineering
- controlled security testing

Security testing should only be performed against systems that you own or have explicit permission to test.
