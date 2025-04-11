from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from product_catalog.domain.dto import ProductCreate, ProductResponse
from product_catalog.di.services import get_product_service
from product_catalog.service_layer.services import  ProductService


router = APIRouter(prefix="/product", tags=["product"])


@router.get(path="/{product_uid}", response_model=ProductResponse, status_code=200)
async def get_product(
    product_uid: str,
    product_service: Annotated[ProductService, Depends(get_product_service)]
):
    try:
        return await product_service.get_product(product_uid)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(path="/", response_model=ProductResponse, status_code=201)
async def create_product(
    product_data: ProductCreate,
    product_service: Annotated[ProductService, Depends(get_product_service)]
):
    try:
        return await product_service.create_product(product_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(path="/{product_uid}", status_code=204)
async def delete_product(
    product_uid: str,
    product_service: Annotated[ProductService, Depends(get_product_service)]
):
    try:
        await product_service.delete_product(product_uid)
        return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))