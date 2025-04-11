from product_catalog.api.catalog import router as catalog_router
from product_catalog.api.product import router as product_router
from product_catalog.api.property import router as property_router

routers = (catalog_router, product_router, property_router)