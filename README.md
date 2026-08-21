# Petroleum RAG Assistant

A production-style conversational Retrieval-Augmented Generation (RAG) system built with LangGraph, FastAPI, PostgreSQL/pgvector and local LLM inference through Ollama.

The project includes conversational memory, query understanding, semantic caching, hybrid retrieval and reranking, document ingestion, source attribution, evaluation with LangSmith, authentication, rate limiting and a lightweight ChatGPT-style web interface.

## Overview

The system was designed as an end-to-end RAG application rather than a simple retrieval notebook.

It consists of two LangGraph workflows:

- **Conversational RAG graph** for query understanding, retrieval, reranking, generation, caching and conversational follow-ups.
- **Document ingestion graph** for file discovery, change detection, Markdown-aware chunking, contextualisation, embedding generation and PostgreSQL/pgvector indexing.

The application is exposed through a FastAPI backend and a lightweight single-page web client.

## Architecture

![Petroleum RAG Architecture](assets/architecture.png)

### Main components

- **Frontend:** HTML, CSS and JavaScript single-page interface
- **API:** FastAPI
- **Orchestration:** LangGraph
- **LLM:** Qwen 2.5 7B through Ollama
- **Embeddings:** `BAAI/bge-base-en-v1.5`
- **Reranker:** `BAAI/bge-reranker-base`
- **Vector database:** PostgreSQL + pgvector
- **Tracing and evaluation:** LangSmith
- **Document ingestion:** LangGraph ingestion pipeline
- **Authentication:** HttpOnly session cookies
- **Semantic cache:** pgvector similarity search
- **Concurrency:** asynchronous FastAPI and PostgreSQL connection pooling

## Conversational RAG Workflow

The conversational graph handles both knowledge-base queries and normal conversation.

Main stages:

1. Add the current user message to conversation history.
2. Analyse the message and classify its intent.
3. Resolve follow-ups and retry requests using conversation history.
4. Check the semantic cache for sufficiently similar previous queries.
5. Retrieve candidate chunks from PostgreSQL/pgvector.
6. Rerank retrieved results with a CrossEncoder.
7. Generate the final grounded answer with Qwen.
8. Return document and heading-path sources.
9. Cache only complete, high-confidence standalone queries.

The graph can distinguish between:

- standalone knowledge queries
- multi-part comparisons
- conversational follow-ups
- retry/correction requests
- greetings
- polite/social messages
- ordinary conversation

Follow-up queries are deliberately excluded from the semantic cache because their meaning can depend on previous conversation history.

## LangGraph Studio

LangSmith Studio is used to inspect graph execution, individual node state and routing decisions.

![LangGraph Studio](assets/langsmith-studio.png)

This makes it possible to inspect behaviours such as:

- semantic cache hits
- query decomposition
- retrieval
- reranking
- answer generation
- retry routing
- conversational branches

## Web Interface

The application includes a lightweight ChatGPT-style interface.

![RAG Assistant](assets/chat-interface.png)

The frontend supports:

- multi-turn conversations
- source attribution
- automatic session handling
- document ingestion
- statistics
- isolated conversation thread IDs

Example comparison query:

> Compare the minimum transaction size for DEF with the minimum volume for Argo ethanol in Chicago.

The system decomposes comparison requests into independent retrieval requirements and combines the grounded results into one response.

## Statistics

The application exposes operational RAG statistics through the frontend.

![RAG Statistics](assets/statistics.png)

Currently displayed metrics include:

- indexed documents
- indexed chunks
- semantic cache entries
- total queries
- cache hit rate

## Document Ingestion

The ingestion workflow is implemented as a separate LangGraph graph.

Pipeline:

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
