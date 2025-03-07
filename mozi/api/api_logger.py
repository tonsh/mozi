import json
import time
from typing import Optional

from fastapi import Request
from mozi.logger import get_logger
from mozi.utils import APP_NAME

logger = get_logger(f"{APP_NAME}_api")


def is_http_success(status_code: int):
    if status_code >= 400:
        return False
    return True


class APILogger:

    def __init__(self, request: Request, payload: Optional[dict] = None):
        self.request = request
        self.payload = payload

    async def get_body(self) -> bytes:
        try:
            return await self.request.json()
        except json.decoder.JSONDecodeError:
            return b"{}"

    async def dict(self) -> dict:
        log_info = {
            "h": self.request.client.host,  # type: ignore
            "p": self.request.client.port,  # type: ignore
            "u": self.request.url.path,
            "m": self.request.method,
            "q": self.request.url.query,
        }

        body = await self.get_body()
        if isinstance(body, dict):
            body = json.dumps(body)
        else:
            body = body.decode()  # type: ignore
        log_info["b"] = body

        if self.payload:
            log_info.update(self.payload)

        return log_info


async def api_log(
    request: Request,
    status_code: int = 200,
    start_time: Optional[float] = None,
    payload: Optional[dict] = None
) -> None:
    if payload is None:
        payload = {}
    payload["c"] = status_code
    if start_time:
        payload["t"] = round((time.time() - start_time) * 1000, 2)  # ms

    log = APILogger(request=request, payload=payload)
    log_info = await log.dict()
    if is_http_success(status_code):
        logger.info(json.dumps(log_info))
    else:
        logger.error(json.dumps(log_info))
