"""
Billing Service
Task T146 - US8 Implementation

Business logic for billing and invoice management.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, Integer

from app.db.models import Invoice, InvoiceStatus, Case, CaseMember, User
from app.db.schemas import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceOut,
    InvoiceListResponse,
)


class BillingService:
    """Service for billing and invoice operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_invoices_for_lawyer(
        self,
        lawyer_id: str,
        status: Optional[str] = None,
        case_id: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> InvoiceListResponse:
        """
        Get invoices for a lawyer (created by them).

        Args:
            lawyer_id: ID of the lawyer
            status: Optional status filter
            case_id: Optional case ID filter
            page: Page number
            limit: Items per page

        Returns:
            InvoiceListResponse with invoices and totals
        """
        query = self.db.query(Invoice).filter(Invoice.lawyer_id == lawyer_id)

        if status:
            try:
                invoice_status = InvoiceStatus(status)
                query = query.filter(Invoice.status == invoice_status)
            except ValueError:
                pass

        if case_id:
            query = query.filter(Invoice.case_id == case_id)

        # Get total count
        total = query.count()

        # Calculate totals
        total_pending = self._calculate_total_by_status(
            lawyer_id, InvoiceStatus.PENDING
        )
        total_paid = self._calculate_total_by_status(lawyer_id, InvoiceStatus.PAID)

        # Get paginated results
        offset = (page - 1) * limit
        invoices = (
            query.order_by(Invoice.created_at.desc()).offset(offset).limit(limit).all()
        )

        # Convert to output schema with related data
        invoice_outs = [self._to_invoice_out(inv) for inv in invoices]

        return InvoiceListResponse(
            invoices=invoice_outs,
            total=total,
            total_pending=str(total_pending),
            total_paid=str(total_paid),
        )

    def get_invoices_for_client(
        self, client_id: str, page: int = 1, limit: int = 20
    ) -> InvoiceListResponse:
        """
        Get invoices for a client.

        Args:
            client_id: ID of the client
            page: Page number
            limit: Items per page

        Returns:
            InvoiceListResponse with invoices
        """
        query = self.db.query(Invoice).filter(Invoice.client_id == client_id)

        total = query.count()

        # Calculate totals for client
        total_pending = (
            self.db.query(func.sum(func.cast(Invoice.amount, type_=Integer)))
            .filter(Invoice.client_id == client_id, Invoice.status == InvoiceStatus.PENDING)
            .scalar()
            or 0
        )
        total_paid = (
            self.db.query(func.sum(func.cast(Invoice.amount, type_=Integer)))
            .filter(Invoice.client_id == client_id, Invoice.status == InvoiceStatus.PAID)
            .scalar()
            or 0
        )

        offset = (page - 1) * limit
        invoices = (
            query.order_by(Invoice.created_at.desc()).offset(offset).limit(limit).all()
        )

        invoice_outs = [self._to_invoice_out(inv) for inv in invoices]

        return InvoiceListResponse(
            invoices=invoice_outs,
            total=total,
            total_pending=str(total_pending),
            total_paid=str(total_paid),
        )

    def create_invoice(
        self, lawyer_id: str, data: InvoiceCreate
    ) -> Optional[InvoiceOut]:
        """
        Create a new invoice.

        Args:
            lawyer_id: ID of the lawyer creating the invoice
            data: Invoice creation data

        Returns:
            Created invoice or None if validation fails
        """
        # Verify lawyer has access to the case
        case_member = (
            self.db.query(CaseMember)
            .filter(
                CaseMember.case_id == data.case_id,
                CaseMember.user_id == lawyer_id,
            )
            .first()
        )

        if not case_member:
            return None

        # Create invoice
        invoice = Invoice(
            case_id=data.case_id,
            client_id=data.client_id,
            lawyer_id=lawyer_id,
            amount=data.amount,
            description=data.description,
            due_date=data.due_date,
            status=InvoiceStatus.PENDING,
        )

        self.db.add(invoice)
        self.db.commit()
        self.db.refresh(invoice)

        return self._to_invoice_out(invoice)

    def get_invoice_by_id(
        self, invoice_id: str, user_id: str
    ) -> Optional[InvoiceOut]:
        """
        Get invoice by ID with access check.

        Args:
            invoice_id: ID of the invoice
            user_id: ID of the requesting user

        Returns:
            Invoice or None if not found/not authorized
        """
        invoice = self.db.query(Invoice).filter(Invoice.id == invoice_id).first()

        if not invoice:
            return None

        # Check access - lawyer or client
        if invoice.lawyer_id != user_id and invoice.client_id != user_id:
            return None

        return self._to_invoice_out(invoice)

    def update_invoice(
        self, invoice_id: str, lawyer_id: str, data: InvoiceUpdate
    ) -> Optional[InvoiceOut]:
        """
        Update an invoice.

        Args:
            invoice_id: ID of the invoice
            lawyer_id: ID of the lawyer (must be owner)
            data: Update data

        Returns:
            Updated invoice or None if not found/not authorized
        """
        invoice = (
            self.db.query(Invoice)
            .filter(Invoice.id == invoice_id, Invoice.lawyer_id == lawyer_id)
            .first()
        )

        if not invoice:
            return None

        # Update fields
        if data.amount is not None:
            invoice.amount = data.amount
        if data.description is not None:
            invoice.description = data.description
        if data.status is not None:
            invoice.status = data.status
        if data.due_date is not None:
            invoice.due_date = data.due_date

        self.db.commit()
        self.db.refresh(invoice)

        return self._to_invoice_out(invoice)

    def delete_invoice(self, invoice_id: str, lawyer_id: str) -> bool:
        """
        Delete an invoice.

        Args:
            invoice_id: ID of the invoice
            lawyer_id: ID of the lawyer (must be owner)

        Returns:
            True if deleted, False if not found/not authorized
        """
        invoice = (
            self.db.query(Invoice)
            .filter(Invoice.id == invoice_id, Invoice.lawyer_id == lawyer_id)
            .first()
        )

        if not invoice:
            return False

        self.db.delete(invoice)
        self.db.commit()

        return True

    def process_payment(
        self,
        invoice_id: str,
        client_id: str,
        payment_method: str,
        payment_reference: Optional[str] = None,
    ) -> Optional[InvoiceOut]:
        """
        Process payment for an invoice.

        Args:
            invoice_id: ID of the invoice
            client_id: ID of the client paying
            payment_method: Payment method used
            payment_reference: Optional payment reference

        Returns:
            Updated invoice or None if not found/not authorized
        """
        invoice = (
            self.db.query(Invoice)
            .filter(Invoice.id == invoice_id, Invoice.client_id == client_id)
            .first()
        )

        if not invoice:
            return None

        # Check if already paid
        if invoice.status == InvoiceStatus.PAID:
            return self._to_invoice_out(invoice)

        # Update status to paid
        invoice.status = InvoiceStatus.PAID
        invoice.paid_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(invoice)

        return self._to_invoice_out(invoice)

    def _calculate_total_by_status(
        self, lawyer_id: str, status: InvoiceStatus
    ) -> int:
        """Calculate total amount for invoices with given status"""
        try:
            from sqlalchemy import Integer

            result = (
                self.db.query(func.sum(func.cast(Invoice.amount, type_=Integer)))
                .filter(Invoice.lawyer_id == lawyer_id, Invoice.status == status)
                .scalar()
            )
            return result or 0
        except Exception:
            # Fallback for SQLite
            invoices = (
                self.db.query(Invoice)
                .filter(Invoice.lawyer_id == lawyer_id, Invoice.status == status)
                .all()
            )
            return sum(int(inv.amount) for inv in invoices)

    def _to_invoice_out(self, invoice: Invoice) -> InvoiceOut:
        """Convert Invoice model to InvoiceOut schema with related data"""
        # Get related case
        case = self.db.query(Case).filter(Case.id == invoice.case_id).first()
        case_title = case.title if case else None

        # Get client name
        client = self.db.query(User).filter(User.id == invoice.client_id).first()
        client_name = client.name if client else None

        # Get lawyer name
        lawyer = self.db.query(User).filter(User.id == invoice.lawyer_id).first()
        lawyer_name = lawyer.name if lawyer else None

        return InvoiceOut(
            id=invoice.id,
            case_id=invoice.case_id,
            case_title=case_title,
            client_id=invoice.client_id,
            client_name=client_name,
            lawyer_id=invoice.lawyer_id,
            lawyer_name=lawyer_name,
            amount=invoice.amount,
            description=invoice.description,
            status=invoice.status,
            due_date=invoice.due_date,
            paid_at=invoice.paid_at,
            created_at=invoice.created_at,
        )


