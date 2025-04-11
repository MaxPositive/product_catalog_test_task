from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from product_catalog.domain.dto import PropertyCreate
from product_catalog.di.services import get_property_service
from product_catalog.service_layer.services import PropertyService


router = APIRouter(prefix="/properties", tags=["property"])


@router.post(path="/", status_code=201)
async def create_property(
    property_data: PropertyCreate,
    property_service: Annotated[PropertyService, Depends(get_property_service)]
):
    try:
        return await property_service.create_property(property_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(path="/{property_uid}", status_code=204)
async def delete_property(
    property_uid: str,
    property_service: Annotated[PropertyService, Depends(get_property_service)]
):
    try:
        await property_service.delete_property(property_uid)
        return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))