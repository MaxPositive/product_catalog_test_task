from typing import Optional, Annotated
from fastapi import APIRouter, Depends, Query, Request
from product_catalog.domain.dto import CatalogResponse, FilterStatsResponse
from product_catalog.di.services import get_catalog_service
from product_catalog.service_layer.services import CatalogService


router = APIRouter(prefix="/catalog", tags=["catalog"])


def parse_property_filters(query_params: dict) -> dict:
    """
    Парсит query параметры в виде property_uid1=uid1&property_uid1=uid2&property_uid2=uid1&property_uid2=uid2
    """
    property_filters = {}
    for key, value in query_params.items():
        if key.startswith("property_"):
            prop_uid = key[len("property_"):]
            if prop_uid.endswith("_from") or prop_uid.endswith("_to"):  # числовой формат
                prop_uid_base = prop_uid.rsplit("_", 1)[0]
                if prop_uid_base not in property_filters:
                    property_filters[prop_uid_base] = {}
                if prop_uid.endswith("_from"):
                    property_filters[prop_uid_base]["from"] = int(value)
                elif prop_uid.endswith("_to"):
                    property_filters[prop_uid_base]["to"] = int(value)
            else:  # формат в виде списка
                if isinstance(value, str):
                    if prop_uid not in property_filters:
                        property_filters[prop_uid] = [value]
                    else:
                        property_filters[prop_uid].append(value)
                elif isinstance(value, list):
                    property_filters[prop_uid] = value
    return property_filters


@router.get(path="/", response_model=CatalogResponse)
async def get_catalog(
    request: Request,
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    name: Optional[str] = None,
    sort: Optional[str] = Query(None, enum=["name", "uid"]),
):
    property_filters = parse_property_filters(dict(request.query_params))
    return await catalog_service.get_catalog(
        page=page,
        page_size=page_size,
        name=name,
        sort=sort,
        property_filters=property_filters
    )

@router.get(path="/filter/", response_model=FilterStatsResponse)
async def get_filter_stats(
    request: Request,
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    name: Optional[str] = None,
):
    property_filters = parse_property_filters(dict(request.query_params))
    return await catalog_service.get_filter_stats(
        name=name,
        property_filters=property_filters
    )