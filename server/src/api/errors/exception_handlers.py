from fastapi import Request
from api_error import ApiError
from fastapi.responses import JSONResponse


async def api_error_handler(request: Request, error: ApiError):
    return JSONResponse(
        status_code=error.status_code,
        content={"error_message": error.message},
    )
