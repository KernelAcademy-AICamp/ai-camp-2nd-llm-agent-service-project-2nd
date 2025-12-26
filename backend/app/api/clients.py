"""
Client Contact API Routes
Issue #297 - FR-009~010, FR-015

API endpoints for client contact management.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user_id
from app.core.error_messages import ErrorMessages
from app.services.client_contact_service import ClientContactService
from app.services.client_list_service import ClientListService
from app.db.schemas import (
    ClientContactCreate,
    ClientContactUpdate,
    ClientContactResponse,
    ClientContactListResponse,
)
from app.schemas.client_list import (
    ClientListResponse,
    ClientDetail,
    ClientFilter,
    ClientSortField,
    SortOrder,
    ClientStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/clients", tags=["clients"])


# ============================================
# Client User Management (Lawyer Portal)
# ============================================

@router.get(
    "/lawyer-portal",
    response_model=ClientListResponse,
    summary="Get lawyer's clients (Users)",
)
async def get_lawyer_clients(
    search: Optional[str] = Query(None, description="Search by name or email"),
    status: Optional[ClientStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: ClientSortField = Query(
        ClientSortField.NAME, description="Field to sort by"
    ),
    sort_order: SortOrder = Query(SortOrder.ASC, description="Sort order"),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Get list of lawyer's clients (users with role='client') with filters.
    """
    service = ClientListService(db)
    filters = ClientFilter(search=search, status=status)
    return service.get_clients(
        lawyer_id=user_id,
        filters=filters,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get(
    "/lawyer-portal/{client_id}",
    response_model=ClientDetail,
    summary="Get client data detail",
)
async def get_client_detail(
    client_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get detailed information for a specific client user."""
    service = ClientListService(db)
    client = service.get_client_detail(lawyer_id=user_id, client_id=client_id)
    if not client:
        raise HTTPException(
            status_code=404,
            detail="Client not found or access denied",
        )
    return client


# ============================================
# Client Contact CRUD (Address Book)
# ============================================


@router.get(
    "",
    response_model=ClientContactListResponse,
    summary="Get client contacts",
    description="Get current lawyer's client contacts with optional search",
)
async def get_clients(
    search: str = Query(None, description="Search by name, phone, or email"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Get client contacts for the current lawyer.

    - **Lawyer role required**
    - Supports search by name, phone, or email
    - Paginated results

    Returns:
        - items: List of client contacts
        - total: Total number of matching contacts
        - page: Current page number
        - limit: Items per page
    """
    service = ClientContactService(db)
    try:
        return service.get_clients(
            lawyer_id=user_id,
            search=search,
            page=page,
            limit=limit,
        )
    except PermissionError as e:
        logger.warning(f"Permission denied for user {user_id}: {e}")
        raise HTTPException(status_code=403, detail=ErrorMessages.PERMISSION_DENIED)


@router.post(
    "",
    response_model=ClientContactResponse,
    status_code=201,
    summary="Create client contact",
    description="Create a new client contact",
)
async def create_client(
    data: ClientContactCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Create a new client contact.

    - **Lawyer role required**
    - Name is required
    - Either phone or email must be provided

    Returns:
        - Created client contact object
    """
    service = ClientContactService(db)
    try:
        return service.create_client(lawyer_id=user_id, data=data)
    except PermissionError as e:
        logger.warning(f"Permission denied for user {user_id} creating client: {e}")
        raise HTTPException(status_code=403, detail=ErrorMessages.PERMISSION_DENIED)
    except ValueError as e:
        logger.warning(f"Validation error creating client: {e}")
        raise HTTPException(status_code=400, detail="의뢰인 생성에 실패했습니다. 입력값을 확인해주세요")


@router.get(
    "/{client_id}",
    response_model=ClientContactResponse,
    summary="Get client contact",
    description="Get a specific client contact by ID",
)
async def get_client(
    client_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Get a specific client contact.

    - **Lawyer role required**
    - Only returns contacts owned by the current lawyer
    """
    service = ClientContactService(db)
    try:
        return service.get_client(client_id=client_id, lawyer_id=user_id)
    except PermissionError as e:
        logger.warning(f"Permission denied for user {user_id} accessing client {client_id}: {e}")
        raise HTTPException(status_code=403, detail=ErrorMessages.PERMISSION_DENIED)
    except KeyError:
        raise HTTPException(status_code=404, detail=ErrorMessages.CLIENT_NOT_FOUND)


@router.put(
    "/{client_id}",
    response_model=ClientContactResponse,
    summary="Update client contact",
    description="Update a client contact's information",
)
async def update_client(
    client_id: str,
    data: ClientContactUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Update a client contact.

    - **Lawyer role required**
    - Only updates contacts owned by the current lawyer
    - Must maintain at least one contact method (phone or email)
    """
    service = ClientContactService(db)
    try:
        return service.update_client(
            client_id=client_id,
            lawyer_id=user_id,
            data=data,
        )
    except PermissionError as e:
        logger.warning(f"Permission denied for user {user_id} updating client {client_id}: {e}")
        raise HTTPException(status_code=403, detail=ErrorMessages.PERMISSION_DENIED)
    except KeyError:
        raise HTTPException(status_code=404, detail=ErrorMessages.CLIENT_NOT_FOUND)
    except ValueError as e:
        logger.warning(f"Validation error updating client {client_id}: {e}")
        raise HTTPException(status_code=400, detail="의뢰인 수정에 실패했습니다. 입력값을 확인해주세요")


@router.delete(
    "/{client_id}",
    status_code=204,
    summary="Delete client contact",
    description="Delete a client contact (hard delete)",
)
async def delete_client(
    client_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Delete a client contact.

    - **Lawyer role required**
    - Only deletes contacts owned by the current lawyer
    - This is a permanent deletion
    """
    service = ClientContactService(db)
    try:
        result = service.delete_client(client_id=client_id, lawyer_id=user_id)
        if not result:
            raise HTTPException(status_code=404, detail=ErrorMessages.CLIENT_NOT_FOUND)
    except PermissionError as e:
        logger.warning(f"Permission denied for user {user_id} deleting client {client_id}: {e}")
        raise HTTPException(status_code=403, detail=ErrorMessages.PERMISSION_DENIED)
