from pydantic import BaseModel
from typing import Any, Optional, List


class ProductPropertyResponse(BaseModel):
    uid: str
    name: str
    value_uid: Optional[str] = None
    value: Any
    class Config:
        from_attributes = True


class ProductResponse(BaseModel):
    uid: str
    name: str
    properties: List[ProductPropertyResponse]
    class Config:
        from_attributes = True


class IntPropertyStats(BaseModel):
    min_value: int
    max_value: int


class CatalogResponse(BaseModel):
    products: List[ProductResponse]
    count: int


class FilterStatsResponse(BaseModel):
    count: int
    class Config:
        extra = "allow"


class ProductPropertyCreate(BaseModel):
    uid: str
    value_uid: Optional[str] = None
    value: Optional[int] = None


class ProductCreate(BaseModel):
    uid: str
    name: str
    properties: List[ProductPropertyCreate]


class PropertyValueCreate(BaseModel):
    value_uid: str
    value: str


class PropertyCreate(BaseModel):
    uid: str
    name: str
    type: str
    values: Optional[List[PropertyValueCreate]] = None