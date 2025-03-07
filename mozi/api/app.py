from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from mozi.api.errors import APIError
from mozi.utils import is_debug

app = FastAPI(debug=is_debug())


@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:  # pylint: disable=W0613
    return JSONResponse(content=exc.dict(), status_code=exc.status_code)


@app.exception_handler(Exception)
async def custom_error_handler(request: Request, exc: Exception) -> PlainTextResponse:  # pylint: disable=W0613
    return PlainTextResponse(f"Internal Server Error: {str(exc)}", status_code=500)
