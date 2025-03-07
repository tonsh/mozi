from fastapi import APIRouter

from mozi.api import APIError, LogRequestRoute
from mozi.api.app import app

router = APIRouter(
    prefix="/demo",
    tags=["demo"],
    route_class=LogRequestRoute,
)


@router.get("/hello")
async def hello():
    return {"message": "Hello Demo."}


@router.get("/error")
async def error():
    raise APIError('this is a test error.')

app.include_router(router)
