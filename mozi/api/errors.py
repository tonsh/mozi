from typing import Optional
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError


class GenericError(Exception):
    error_code = 20


class APIValidateError(RequestValidationError):
    error_code = 90
    status_code = 422


class APIError(HTTPException):
    error_code = 100
    status_code = 400

    def __init__(self, detail: Optional[str] = None, status_code: Optional[int] = None, **kwargs):
        if status_code:
            self.status_code = status_code

        super().__init__(self.status_code, detail=detail, **kwargs)

    def dict(self) -> dict:
        return {"error_code": self.error_code, "detail": self.detail}


class NotFoundError(APIError):
    error_code = 101
    status_code = 404
