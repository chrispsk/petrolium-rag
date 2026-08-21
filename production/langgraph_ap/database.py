from psycopg_pool import AsyncConnectionPool
from pgvector.psycopg import register_vector_async
from contextlib import asynccontextmanager


async def configure_connection(connection):
    await register_vector_async(connection)


pool = AsyncConnectionPool(
    conninfo="dbname=postgres user=postgres password=root host=localhost port=5432",
    min_size=2,
    max_size=10,
    configure=configure_connection,
    open=False
)