from fastapi import FastAPI

from product_catalog.api.routers import routers


def get_fastapi_app() -> FastAPI:
    return FastAPI()


def add_routers(app: FastAPI) -> None:
    for router in routers:
        app.include_router(router)


def get_app() -> FastAPI:
    fastapi_app = get_fastapi_app()
    add_routers(fastapi_app)
    return fastapi_app

