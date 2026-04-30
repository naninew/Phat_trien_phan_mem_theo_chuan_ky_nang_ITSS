"""
Standardized response formatting for API endpoints.
"""
from typing import Optional, Any, Dict
from fastapi.responses import JSONResponse


def success_response(data: Any = None, message: str = "Success", code: int = 200) -> Dict:
    """
    Create a standardized success response.
    
    Args:
        data: Response data (can be any type)
        message: Success message
        code: HTTP status code
    
    Returns:
        Dictionary with standardized response format
    """
    return {
        "code": code,
        "message": message,
        "data": data
    }


def error_response(message: str = "Error", code: int = 400, errors: Optional[Dict] = None) -> Dict:
    """
    Create a standardized error response.
    
    Args:
        message: Error message
        code: HTTP status code
        errors: Additional error details (optional)
    
    Returns:
        Dictionary with standardized error format
    """
    response = {
        "code": code,
        "message": message,
        "data": None
    }
    if errors:
        response["errors"] = errors
    return response


def create_json_response(data: Any = None, message: str = "Success", code: int = 200) -> JSONResponse:
    """
    Create a FastAPI JSONResponse with standardized format.
    
    Args:
        data: Response data
        message: Success message
        code: HTTP status code
    
    Returns:
        FastAPI JSONResponse object
    """
    return JSONResponse(
        status_code=code,
        content=success_response(data=data, message=message, code=code)
    )


def create_error_json_response(message: str = "Error", code: int = 400) -> JSONResponse:
    """
    Create a FastAPI JSONResponse with standardized error format.
    
    Args:
        message: Error message
        code: HTTP status code
    
    Returns:
        FastAPI JSONResponse object
    """
    return JSONResponse(
        status_code=code,
        content=error_response(message=message, code=code)
    )
