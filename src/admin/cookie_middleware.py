"""
Middleware to handle JWT cookies for SQLAdmin in Lambda environment
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.requests import Request
from typing import Callable

from src.admin.sqladmin_lambda import (
    COOKIE_NAME,
    COOKIE_SECURE,
    COOKIE_HTTPONLY,
    COOKIE_SAMESITE,
    COOKIE_PATH,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)


class AdminCookieMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle setting/clearing JWT cookies for admin panel.
    Works around SQLAdmin's session-based approach for Lambda compatibility.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Process the request
        response = await call_next(request)

        # Check if we need to set the admin token cookie
        if hasattr(request.state, "_admin_token"):
            response.set_cookie(
                key=COOKIE_NAME,
                value=request.state._admin_token,
                max_age=60 * ACCESS_TOKEN_EXPIRE_MINUTES,
                path=COOKIE_PATH,
                secure=COOKIE_SECURE,
                httponly=COOKIE_HTTPONLY,
                samesite=COOKIE_SAMESITE,
            )

        # Check if we need to clear the admin token cookie
        elif hasattr(request.state, "_clear_admin_token"):
            response.delete_cookie(
                key=COOKIE_NAME,
                path=COOKIE_PATH,
                secure=COOKIE_SECURE,
                httponly=COOKIE_HTTPONLY,
                samesite=COOKIE_SAMESITE,
            )

        return response
