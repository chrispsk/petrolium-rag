import asyncio
import selectors
import sys
import time

from contextlib import asynccontextmanager

# IMPORTANT:
# Import graph before FastAPI because it loads the RAG runtime first.
from graph import app as rag_graph
from database import pool

import secrets
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, Response
from ingestion.graph import app as ingestion_graph
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field, field_validator
import os
from dotenv import load_dotenv

ingestion_running = False

# -------------------- Rate limiting --------------------

RATE_LIMIT = 10
RATE_WINDOW = 60

request_history = {}
total_queries = 0
cache_hits = 0

request_history_lock = asyncio.Lock()
statistics_lock = asyncio.Lock()


# -------------------- FastAPI --------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    await pool.open()

    try:
        yield
    finally:
        await pool.close()


app = FastAPI(title="RAG API", version="1.0", lifespan=lifespan)


# -------------------- CORS --------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "null",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://192.168.1.237:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------- Authentication --------------------

load_dotenv()

API_PASSWORD = os.getenv("API_PASSWORD")

if not API_PASSWORD:
    raise RuntimeError("API_PASSWORD is not configured.")

active_sessions = set()


class LoginRequest(BaseModel):
    password: str


async def verify_session(request: Request):
    session_token = request.cookies.get("rag_session")

    if not session_token or session_token not in active_sessions:
        raise HTTPException(status_code=401, detail="Authentication required.")

    return session_token


# -------------------- Request validation --------------------

class QueryRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1000)
    thread_id: str = Field(min_length=1, max_length=100)

    model_config = {"extra": "forbid"}

    @field_validator("query")
    @classmethod
    def validate_query(cls, value):
        value = value.strip()

        if not value:
            raise ValueError("Query cannot be empty.")

        return value


# -------------------- Rate limit --------------------

async def rate_limit(session_token: str = Depends(verify_session)):
    current_time = time.monotonic()

    async with request_history_lock:
        if session_token not in request_history:
            request_history[session_token] = []

        recent_requests = []

        for request_time in request_history[session_token]:
            if current_time - request_time < RATE_WINDOW:
                recent_requests.append(request_time)

        request_history[session_token] = recent_requests

        if len(recent_requests) >= RATE_LIMIT:
            raise HTTPException(status_code=429, detail="Rate limit exceeded.")

        request_history[session_token].append(current_time)

    return session_token

async def run_ingestion_background():
    global ingestion_running

    try:
        await ingestion_graph.ainvoke({})
    finally:
        ingestion_running = False

class LoginRequest(BaseModel):
    password: str

# -------------------- Routes --------------------

@app.post("/login")
async def login(login_request: LoginRequest, response: Response):
    if not secrets.compare_digest(login_request.password, API_PASSWORD):
        raise HTTPException(status_code=401, detail="Invalid password.")

    session_token = secrets.token_urlsafe(32)
    active_sessions.add(session_token)

    response.set_cookie(
        key="rag_session",
        value=session_token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=86400
    )

    return {"status": "authenticated"}

@app.get("/")
async def index():
    return {"status": "RAG API running"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/query")
async def query_rag(request: QueryRequest, session_token: str = Depends(rate_limit)):
    global total_queries
    global cache_hits

    config = {"configurable": {"thread_id": request.thread_id}}

    result = await rag_graph.ainvoke({"query": request.query}, config=config)

    async with statistics_lock:
        total_queries += 1

        if result.get("cache_hit", False):
            cache_hits += 1

    return {
        "query": request.query,
        "thread_id": request.thread_id,
        "subqueries": result.get("subqueries", []),
        "answer": result.get("answer", ""),
        "sources": result.get("sources", []),
        "complete": result.get("complete", False),
        "cache_hit": result.get("cache_hit", False)
    }


@app.post("/ingest", status_code=202)
async def ingest_documents(background_tasks: BackgroundTasks, session_token: str = Depends(verify_session)):
    global ingestion_running

    if ingestion_running:
        raise HTTPException(status_code=409, detail="Ingestion is already running.")

    ingestion_running = True
    background_tasks.add_task(run_ingestion_background)

    return {"status": "accepted", "message": "Ingestion started in background."}


@app.get("/stats")
async def stats(session_token: str = Depends(verify_session)):
    async with pool.connection() as connection:
        async with connection.cursor() as cursor:
            await cursor.execute("SELECT COUNT(*) FROM documents;")
            documents = (await cursor.fetchone())[0]

            await cursor.execute("SELECT COUNT(*) FROM chunks;")
            chunks = (await cursor.fetchone())[0]

            await cursor.execute("SELECT COUNT(*) FROM semantic_cache;")
            cached_queries = (await cursor.fetchone())[0]

    async with statistics_lock:
        current_total_queries = total_queries
        current_cache_hits = cache_hits

    if current_total_queries > 0:
        cache_hit_rate = (current_cache_hits / current_total_queries) * 100
    else:
        cache_hit_rate = 0

    return {
        "documents": documents,
        "chunks": chunks,
        "cached_queries": cached_queries,
        "total_queries": current_total_queries,
        "cache_hits": current_cache_hits,
        "cache_hit_rate": round(cache_hit_rate, 1)
    }


# -------------------- Run API --------------------

async def main():
    import uvicorn
    #config = uvicorn.Config(app=app, host="127.0.0.1", port=8000, loop="asyncio")
    config = uvicorn.Config(app=app, host="0.0.0.0", port=8000, loop="asyncio")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    if sys.platform == "win32":
        loop_factory = lambda: asyncio.SelectorEventLoop(selectors.SelectSelector())
        asyncio.run(main(), loop_factory=loop_factory)
    else:
        asyncio.run(main())