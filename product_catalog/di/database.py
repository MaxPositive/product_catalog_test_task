from fastapi import Depends
from typing import Annotated, AsyncIterable

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    create_async_engine, AsyncEngine,
    AsyncSession, async_sessionmaker
)

from product_catalog.config import settings


async def get_engine() -> AsyncEngine:
    return create_async_engine(
        settings.database.url,
        echo=settings.database.echo,
    )


async def get_session_maker(
    async_engine: Annotated[AsyncEngine, Depends(get_engine)]
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        async_engine,
        class_=AsyncSession,
    )


async def get_db_session(
    session_maker: Annotated[async_sessionmaker[AsyncSession], Depends(get_session_maker)]
) -> AsyncIterable[AsyncSession]:
    session = session_maker()
    try:
        yield session
    except SQLAlchemyError as e:
        await session.rollback()
        raise e
    finally:
        await session.close()