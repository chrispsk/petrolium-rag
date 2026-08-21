import asyncio
from contextlib import asynccontextmanager

from psycopg_pool import AsyncConnectionPool
from pgvector.psycopg import register_vector_async


async def configure_connection(connection):
    await register_vector_async(connection)


class StudioPool:
    def __init__(self):
        self.pool = AsyncConnectionPool(
            conninfo="dbname=postgres user=postgres password=root host=localhost port=5432",
            min_size=2,
            max_size=10,
            configure=configure_connection,
            open=False
        )

        self.opened = False
        self.lock = asyncio.Lock()

    async def ensure_open(self):
        if self.opened:
            return

        async with self.lock:
            if not self.opened:
                await self.pool.open()
                self.opened = True

    @asynccontextmanager
    async def connection(self):
        await self.ensure_open()

        async with self.pool.connection() as connection:
            yield connection


studio_pool = StudioPool()