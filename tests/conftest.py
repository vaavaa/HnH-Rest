import asyncio
import uuid
from typing import Any, AsyncGenerator
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from fakeredis import FakeServer
from fakeredis.aioredis import FakeConnection
from redis.asyncio import ConnectionPool
from hnh_rest.services.redis.dependency import get_redis_pool

from hnh_rest.settings import settings
from hnh_rest.web.application import get_app
from sqlalchemy.ext.asyncio import (AsyncConnection, AsyncEngine, AsyncSession,
                                    async_sessionmaker, create_async_engine)
from hnh_rest.db.dependencies import get_db_session
from hnh_rest.db.utils import create_database, drop_database


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """
    Backend for anyio pytest plugin.

    :return: backend name.
    """
    return 'asyncio'
@pytest.fixture(scope="session")
async def _engine(anyio_backend: Any) -> AsyncGenerator[AsyncEngine, None]:
    """
    Create engine and databases.

    :yield: new engine.
    """
    from hnh_rest.db.meta import meta
    from hnh_rest.db.models import load_all_models

    load_all_models()

    await create_database()

    engine = create_async_engine(str(settings.db_url))
    async with engine.begin() as conn:
        await conn.run_sync(meta.create_all)

    try:
        yield engine
    finally:
        await engine.dispose()
        await drop_database()

@pytest.fixture
async def dbsession(
    _engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Get session to database.

    Fixture that returns a SQLAlchemy session with a SAVEPOINT, and the rollback to it
    after the test completes.

    :param _engine: current engine.
    :yields: async session.
    """
    connection = await _engine.connect()
    trans = await connection.begin()

    session_maker = async_sessionmaker(
        connection,
        expire_on_commit=False,
    )
    session = session_maker()

    try:
        yield session
    finally:
        await session.close()
        await trans.rollback()
        await connection.close()

@pytest.fixture
async def fake_redis_pool() -> AsyncGenerator[ConnectionPool, None]:
    """
    Get instance of a fake redis.

    :yield: FakeRedis instance.
    """
    server = FakeServer()
    server.connected = True
    pool = ConnectionPool(connection_class=FakeConnection, server=server)

    yield pool

    await pool.disconnect()

@pytest.fixture
def fastapi_app(
    dbsession: AsyncSession,
    fake_redis_pool: ConnectionPool,
) -> FastAPI:
    """
    Fixture for creating FastAPI app.

    :return: fastapi app with mocked dependencies.
    """
    application = get_app()
    application.dependency_overrides[get_db_session] = lambda: dbsession
    application.dependency_overrides[get_redis_pool] = lambda: fake_redis_pool
    return application  # noqa: RET504


@pytest.fixture
def fastapi_app_per_request_session(
    _engine: AsyncEngine,
    fake_redis_pool: ConnectionPool,
) -> FastAPI:
    """
    App with a new DB session per request (for concurrency tests).
    Each request commits and closes its own session.
    """
    session_factory = async_sessionmaker(
        _engine,
        expire_on_commit=False,
        autoflush=False,
    )

    async def get_db_session_per_request() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            try:
                yield session
            finally:
                await session.commit()
                await session.close()

    application = get_app()
    application.dependency_overrides[get_db_session] = get_db_session_per_request
    application.dependency_overrides[get_redis_pool] = lambda: fake_redis_pool
    return application


@pytest.fixture
async def client(
    fastapi_app: FastAPI,
    anyio_backend: Any
) -> AsyncGenerator[AsyncClient, None]:
    """
    Fixture that creates client for requesting server.

    :param fastapi_app: the application.
    :yield: client for the app.
    """
    async with AsyncClient(transport=ASGITransport(fastapi_app), base_url="http://test", timeout=2.0) as ac:
            yield ac


@pytest.fixture
async def client_per_request_session(
    fastapi_app_per_request_session: FastAPI,
    anyio_backend: Any,
) -> AsyncGenerator[AsyncClient, None]:
    """Client for app that uses a new DB session per request (for race/concurrency tests)."""
    async with AsyncClient(
        transport=ASGITransport(fastapi_app_per_request_session),
        base_url="http://test",
        timeout=5.0,
    ) as ac:
        yield ac
