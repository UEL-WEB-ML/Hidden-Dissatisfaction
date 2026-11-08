from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def build_session_factory(url: str) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(create_async_engine(url, pool_pre_ping=True), expire_on_commit=False)


async def unit_of_work(factory: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
    async with factory() as session:
        yield session
