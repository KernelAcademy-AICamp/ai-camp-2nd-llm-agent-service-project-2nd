"""
Legal Evidence Hub (LEH) - API Package
API endpoint routers (REST API endpoints)

Per BACKEND_SERVICE_REPOSITORY_GUIDE.md:
- API layer handles HTTP routing, request validation, and response wrapping
- Business logic delegated to services
- No direct DB or AWS SDK calls
"""

from . import auth
from . import admin
from . import cases
from . import clients
from . import evidence
from . import lawyer_portal
from . import lawyer_investigators
from . import properties
from . import settings
from . import party
from . import relationships
from . import evidence_links
from . import search
from . import dashboard
from . import calendar

__all__ = [
    "auth", "admin", "cases", "clients", "evidence", "lawyer_portal",
    "lawyer_investigators", "properties",
    "settings", "party", "relationships", "evidence_links", "search",
    "dashboard", "calendar"
]
