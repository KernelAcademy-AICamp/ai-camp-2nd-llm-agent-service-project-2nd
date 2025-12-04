"""
Billing API Router
Tasks T143-T145, T148 - US8 Implementation

API endpoints for billing and invoice management.
Includes CRUD operations for lawyers and payment endpoint for clients.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.schemas import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceOut,
    InvoiceListResponse,
    InvoicePaymentRequest,
)
from app.core.dependencies import require_role
from app.services.billing_service import BillingService
from app.services.audit_service import AuditService


router = APIRouter(prefix="/billing", tags=["billing"])


# ============== Lawyer Billing Endpoints ==============


@router.get("/invoices", response_model=InvoiceListResponse)
async def get_invoices(
    status: Optional[str] = None,
    case_id: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_role(["lawyer", "admin"])),
):
    """
    Get list of invoices for the authenticated lawyer.

    Query parameters:
    - status: Filter by invoice status (pending, paid, overdue, cancelled)
    - case_id: Filter by case ID
    - page: Page number (default: 1)
    - limit: Items per page (default: 20)
    """
    service = BillingService(db)
    return service.get_invoices_for_lawyer(
        lawyer_id=user_id,
        status=status,
        case_id=case_id,
        page=page,
        limit=limit,
    )


@router.post("/invoices", response_model=InvoiceOut, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    data: InvoiceCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_role(["lawyer", "admin"])),
):
    """
    Create a new invoice for a case.

    Request body:
    - case_id: ID of the case
    - client_id: ID of the client to bill
    - amount: Amount in KRW (as string for precision)
    - description: Optional description
    - due_date: Optional due date
    """
    service = BillingService(db)
    invoice = service.create_invoice(lawyer_id=user_id, data=data)

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create invoice for this case",
        )

    # Audit logging (T148)
    audit_service = AuditService(db)
    audit_service.log(
        user_id=user_id,
        action="create_invoice",
        resource_type="invoice",
        resource_id=invoice.id,
        details={"amount": data.amount, "case_id": data.case_id},
    )

    return invoice


@router.get("/invoices/{invoice_id}", response_model=InvoiceOut)
async def get_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_role(["lawyer", "admin", "client"])),
):
    """
    Get invoice detail by ID.

    Returns invoice if user is the lawyer who created it or the client being billed.
    """
    service = BillingService(db)
    invoice = service.get_invoice_by_id(invoice_id=invoice_id, user_id=user_id)

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )

    return invoice


@router.put("/invoices/{invoice_id}", response_model=InvoiceOut)
async def update_invoice(
    invoice_id: str,
    data: InvoiceUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_role(["lawyer", "admin"])),
):
    """
    Update an invoice.

    Only the lawyer who created the invoice can update it.
    """
    service = BillingService(db)
    invoice = service.update_invoice(
        invoice_id=invoice_id, lawyer_id=user_id, data=data
    )

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found or access denied",
        )

    # Audit logging
    audit_service = AuditService(db)
    audit_service.log(
        user_id=user_id,
        action="update_invoice",
        resource_type="invoice",
        resource_id=invoice_id,
        details=data.model_dump(exclude_none=True),
    )

    return invoice


@router.delete("/invoices/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_role(["lawyer", "admin"])),
):
    """
    Delete an invoice.

    Only the lawyer who created the invoice can delete it.
    """
    service = BillingService(db)
    deleted = service.delete_invoice(invoice_id=invoice_id, lawyer_id=user_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found or access denied",
        )

    # Audit logging
    audit_service = AuditService(db)
    audit_service.log(
        user_id=user_id,
        action="delete_invoice",
        resource_type="invoice",
        resource_id=invoice_id,
        details={},
    )

    return None


# ============== Client Billing Endpoints ==============

client_router = APIRouter(prefix="/client/billing", tags=["client-billing"])


@client_router.get("", response_model=InvoiceListResponse)
async def get_client_invoices(
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_role(["client"])),
):
    """
    Get list of invoices for the authenticated client.

    Query parameters:
    - page: Page number (default: 1)
    - limit: Items per page (default: 20)
    """
    service = BillingService(db)
    return service.get_invoices_for_client(
        client_id=user_id, page=page, limit=limit
    )


@client_router.post("/{invoice_id}/pay", response_model=InvoiceOut)
async def pay_invoice(
    invoice_id: str,
    data: InvoicePaymentRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_role(["client"])),
):
    """
    Process payment for an invoice.

    Request body:
    - payment_method: Payment method (card, bank, etc.)
    - payment_reference: Optional payment reference number
    """
    service = BillingService(db)
    invoice = service.process_payment(
        invoice_id=invoice_id,
        client_id=user_id,
        payment_method=data.payment_method,
        payment_reference=data.payment_reference,
    )

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found or access denied",
        )

    # Audit logging (T148)
    audit_service = AuditService(db)
    audit_service.log(
        user_id=user_id,
        action="pay_invoice",
        resource_type="invoice",
        resource_id=invoice_id,
        details={"payment_method": data.payment_method},
    )

    return invoice
