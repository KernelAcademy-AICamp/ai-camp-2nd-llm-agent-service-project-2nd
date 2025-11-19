"""
Legal Evidence Hub (LEH) - Security Middleware
Security headers and HTTPS enforcement
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses

    Based on OWASP recommendations and SECURITY_COMPLIANCE.md
    """

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking attacks
        response.headers["X-Frame-Options"] = "DENY"

        # Enable XSS protection (for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Strict Transport Security (HSTS)
        # Only add in production with HTTPS enabled
        from app.core.config import settings
        if settings.APP_ENV == "prod":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Content Security Policy (CSP)
        # Adjust as needed for your frontend
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (formerly Feature-Policy)
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    Redirect HTTP requests to HTTPS in production

    Only active when APP_ENV=prod
    """

    async def dispatch(self, request: Request, call_next):
        from app.core.config import settings

        # Only enforce HTTPS in production
        if settings.APP_ENV == "prod":
            # Check if request is using HTTP (not HTTPS)
            if request.url.scheme == "http":
                # Build HTTPS URL
                https_url = request.url.replace(scheme="https")

                logger.warning(
                    f"Redirecting HTTP to HTTPS: {request.url} -> {https_url}"
                )

                from starlette.responses import RedirectResponse
                return RedirectResponse(url=str(https_url), status_code=301)

        response = await call_next(request)
        return response
