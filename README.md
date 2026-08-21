# Petroleum RAG Assistant

A production-style conversational Retrieval-Augmented Generation (RAG) system built with LangGraph, FastAPI, PostgreSQL/pgvector and local LLM inference through Ollama.

The project includes:

- conversational memory
- query understanding and follow-up resolution
- semantic caching
- pgvector retrieval
- CrossEncoder reranking
- Markdown-aware document ingestion
- source attribution
- LangSmith Studio tracing and evaluation
- FastAPI backend
- lightweight ChatGPT-style frontend

By default, the repository is configured for **LangGraph Studio development mode**.

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

Move to the LangGraph application:

```bash
cd production/langgraph_ap
```

Install the required packages:

```bash
pip install -r requirements.txt
```

The `requirements.txt` file was tested in a clean Python 3.11 environment.

---

## 4. Install Ollama

Install Ollama for your operating system.

Download the model used by the project:

```bash
ollama pull qwen2.5:7b
```

Verify:

```bash
ollama list
```

Ensure Ollama is running before starting the RAG application.

---

## 5. Install PostgreSQL and pgvector

Install PostgreSQL and enable the `pgvector` extension.

The project was developed using PostgreSQL 17.

After installing pgvector, enable it inside PostgreSQL:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

The application uses PostgreSQL for:

- documents
- chunks
- vector embeddings
- semantic cache

The embedding model produces 768-dimensional vectors.

---

## 6. Create the Database Schema

From:

```text
production/
```

run:

```bash
python setup_database.py
```

This creates the database structures required by the application.

---

## 7. Configure Environment Variables

Create:

```text
production/langgraph_ap/.env
```

Example:

```env
API_PASSWORD=your_password
```

If LangSmith tracing is used, the required LangSmith environment variables can also be added here.

Never commit `.env` files or real credentials.

---

# Development Mode — LangGraph Studio

The repository is configured for **Studio mode by default**.

Activate the environment:

```bash
conda activate cyberag
```

Move to:

```bash
cd production/langgraph_ap
```

Start LangGraph Studio:

```bash
langgraph dev
```

The project exposes two graphs through `langgraph.json`:

```text
rag
ingestion
```

Studio can be used to inspect:

- graph routing
- node execution
- conversation state
- query decomposition
- cache hits
- retrieval
- reranking
- generation
- sources
- ingestion stages

---

# Production Mode — FastAPI

To run the application through FastAPI, switch the database imports from Studio mode to production mode.

## 1. `ingestion/graph.py`

By default:

```python
# for production (FastAPI)
#from database import pool

# for development (Studio)
from studio_database import studio_pool as pool
```

For production, change it to:

```python
# for production (FastAPI)
from database import pool

# for development (Studio)
#from studio_database import studio_pool as pool
```

---

## 2. `langgraph_ap/graph.py`

By default:

```python
#from database import pool  # production

from studio_database import studio_pool as pool  # Studio
```

For production, change it to:

```python
from database import pool  # production

#from studio_database import studio_pool as pool  # Studio
```

---

## 3. Enable the Production Checkpointer

By default, Studio uses:

```python
# For production
#checkpointer = InMemorySaver()
#app = graph.compile(checkpointer=checkpointer)

# For Studio
app = graph.compile()
```

For production, change it to:

```python
# For production
checkpointer = InMemorySaver()
app = graph.compile(checkpointer=checkpointer)

# For Studio
#app = graph.compile()
```

This enables conversational thread memory for the FastAPI runtime.

---

## 4. Start the FastAPI Backend

Activate the environment:

```bash
conda activate cyberag
```

Move to:

```bash
cd production/langgraph_ap
```

Start the API:

```bash
python api.py
```

The backend listens on:

```text
http://127.0.0.1:8000
```

FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

OpenAPI schema:

```text
http://127.0.0.1:8000/openapi.json
```

---

## 5. Start the Frontend

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

For LAN access:

```text
http://<LOCAL-IP>:5500/index.html
```

---

## Switching Back to Studio

To return to Studio mode:

### `ingestion/graph.py`

```python
# for production (FastAPI)
#from database import pool

# for development (Studio)
from studio_database import studio_pool as pool
```

### `langgraph_ap/graph.py`

```python
#from database import pool  # production

from studio_database import studio_pool as pool  # Studio
```

### Graph compilation

```python
# For production
#checkpointer = InMemorySaver()
#app = graph.compile(checkpointer=checkpointer)

# For Studio
app = graph.compile()
```

Then run:

```bash
langgraph dev
```
