from fastapi import Request
from fastapi.responses import JSONResponse

from src.api.errors import ApiError


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
