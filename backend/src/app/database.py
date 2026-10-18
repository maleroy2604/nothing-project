import os
from collections.abc import AsyncIterator
from pathlib import Path

from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.app.model.base import Base
from src.app.model import quest as _quest_model  # noqa: F401


class Database:
    def __init__(self, url: str | URL) -> None:
        self.engine: AsyncEngine = create_async_engine(
            url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def start(self) -> None:
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def stop(self) -> None:
        await self.engine.dispose()

    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self.session_factory() as session:
            yield session


database_url: str | URL = os.getenv(
    "DATABASE_URL",
    "******localhost:5432/nothing",
)
database_password_file = os.getenv("DATABASE_PASSWORD_FILE")

if database_password_file:
    database_password = Path(database_password_file).read_text(
        encoding="utf-8"
    ).rstrip("\r\n")
    if not database_password:
        raise ValueError(f"Database password file is empty: {database_password_file}")
    database_url = make_url(database_url).set(password=database_password)

database = Database(database_url)
