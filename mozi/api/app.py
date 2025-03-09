# pylint: disable=W0613
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse

from mozi.api.errors import APIError
from mozi.utils import is_debug

app = FastAPI(debug=is_debug())


@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    return JSONResponse(content=exc.dict(), status_code=exc.status_code)


@app.exception_handler(Exception)
async def custom_error_handler(request: Request, exc: Exception) -> PlainTextResponse:
    return PlainTextResponse(f"Internal Server Error: {str(exc)}", status_code=500)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    msg = "Invalid "
    for error in exc.errors():
        msg += f" {'.'.join(error['loc'])}: {error['msg']};"

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={'error_code': 102, 'detail': msg},
    )
