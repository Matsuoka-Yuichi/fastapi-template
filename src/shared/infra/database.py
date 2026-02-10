"""Database connection management for both async (FastAPI) and sync (Celery) operations."""

from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager

from psycopg import AsyncConnection, Connection
from psycopg_pool import AsyncConnectionPool, ConnectionPool

from shared.infra.settings import settings


class DatabaseManager:
    """Manages both async and sync database connection pools."""

    def __init__(self) -> None:
        self._async_pool: AsyncConnectionPool | None = None
        self._sync_pool: ConnectionPool | None = None

    async def initialize_async_pool(self) -> None:
        """Initialize the async connection pool (call on FastAPI startup)."""
        if self._async_pool is not None:
            return

        self._async_pool = AsyncConnectionPool(
            conninfo=settings.database_url,
            min_size=1,
            max_size=10,
            open=False,
        )
        await self._async_pool.open()

    def initialize_sync_pool(self) -> None:
        """Initialize the sync connection pool (call on Celery worker startup)."""
        if self._sync_pool is not None:
            return

        if not settings.database_url:
            raise ValueError("DATABASE_URL must be set for sync connections")

        self._sync_pool = ConnectionPool(
            conninfo=settings.database_url,
            min_size=1,
            max_size=10,
            open=False,
            kwargs={"prepare_threshold": None},
        )
        self._sync_pool.open()

    async def close_async_pool(self) -> None:
        """Close the async connection pool (call on FastAPI shutdown)."""
        if self._async_pool is not None:
            await self._async_pool.close()
            self._async_pool = None

    def close_sync_pool(self) -> None:
        """Close the sync connection pool (call on Celery worker shutdown)."""
        if self._sync_pool is not None:
            self._sync_pool.close()
            self._sync_pool = None

    @asynccontextmanager
    async def async_connection(self) -> AsyncGenerator[AsyncConnection, None]:
        """Get an async database connection from the pool.

        Usage:
            async with db.async_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT * FROM table")
        """
        if self._async_pool is None:
            await self.initialize_async_pool()
            assert self._async_pool is not None  # Type narrowing: pool is set if no exception

        async with self._async_pool.connection() as conn:
            yield conn

    @contextmanager
    def sync_connection(self) -> Generator[Connection, None, None]:
        """Get a sync database connection from the pool.

        Usage:
            with db.sync_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM table")
                    conn.commit()
        """
        if self._sync_pool is None:
            self.initialize_sync_pool()
            assert self._sync_pool is not None  # Type narrowing: pool is set if no exception

        with self._sync_pool.connection() as conn:
            yield conn
# Global database manager instance
db = DatabaseManager()
