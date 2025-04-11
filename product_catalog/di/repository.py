from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from product_catalog.adapters.repository import CatalogRepository, ProductRepository, PropertyRepository
from product_catalog.di.database import get_db_session


def get_catalog_repository(db: Annotated[AsyncSession, Depends(get_db_session)]) -> CatalogRepository:
    return CatalogRepository(db=db)


def get_product_repository(db: Annotated[AsyncSession, Depends(get_db_session)]) -> ProductRepository:
    return ProductRepository(db=db)


def get_property_repository(db: Annotated[AsyncSession, Depends(get_db_session)]) -> PropertyRepository:
    return PropertyRepository(db=db)