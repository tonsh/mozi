import time
from typing import Callable
from fastapi import Request, Response
from fastapi.routing import APIRoute

from .api_logger import api_log
from .errors import APIError


class LogRequestRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            start_time = time.time()

            try:
                response = await original_route_handler(request)
                await api_log(request, status_code=response.status_code, start_time=start_time)
                return response
            except APIError as exc:
                await api_log(request, status_code=exc.status_code,
                              start_time=start_time, payload=exc.dict())
                raise
            except Exception as exc:
                await api_log(request, status_code=500, start_time=start_time,
                              payload={"detail": str(exc)})
                raise

        return custom_route_handler
