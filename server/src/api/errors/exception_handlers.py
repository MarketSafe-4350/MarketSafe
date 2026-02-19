from fastapi import Request
from fastapi.responses import JSONResponse

from src.api.errors import ApiError
from src.utils.errors import AppError


async def api_error_handler(request: Request, error: ApiError) -> JSONResponse:
    """Global exception handler for ApiError exceptions.

    Args:
        request (Request): The FastAPI request object.
        error (ApiError): The ApiError instance that was raised.

    Returns:
        JSONResponse: A JSON response containing the error message and status code.
    """
    return JSONResponse(
        status_code=error.status_code,
        content={"error_message": error.message},
    )


async def app_error_handler(request: Request, error: AppError) -> JSONResponse:
    """Global exception handler for AppError exceptions.

    Args:
        request (Request): The FastAPI request object.
        error (AppError): The AppError instance that was raised.

    Returns:
        JSONResponse: A JSON response containing the error message and status code.
    """
    payload = {
        "error_message": error.message,
        "error_code": error.code,
    }

    if error.details is not None:
        payload["details"] = error.details

    return JSONResponse(
        status_code=error.status_code,
        content=payload,
    )
