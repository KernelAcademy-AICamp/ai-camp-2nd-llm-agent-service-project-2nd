"""
Property Repository - Database operations for case properties
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from app.db.models import CaseProperty, PropertyType, PropertyOwner


class PropertyRepository:
    """
    Repository for CaseProperty database operations
    """

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        case_id: str,
        property_type: PropertyType,
        estimated_value: int,
        owner: PropertyOwner = PropertyOwner.JOINT,
        description: Optional[str] = None,
        is_premarital: bool = False,
        acquisition_date: Optional[datetime] = None,
        notes: Optional[str] = None
    ) -> CaseProperty:
        """
        Create a new property for a case

        Args:
            case_id: Case ID
            property_type: Type of property
            estimated_value: Estimated value in KRW
            owner: Property owner
            description: Property description
            is_premarital: Whether acquired before marriage
            acquisition_date: Date of acquisition
            notes: Additional notes

        Returns:
            Created CaseProperty instance
        """
        prop = CaseProperty(
            id=f"prop_{uuid.uuid4().hex[:12]}",
            case_id=case_id,
            property_type=property_type,
            description=description,
            estimated_value=estimated_value,
            owner=owner,
            is_premarital=is_premarital,
            acquisition_date=acquisition_date,
            notes=notes,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        self.session.add(prop)
        self.session.flush()

        return prop

    def get_by_id(self, property_id: str) -> Optional[CaseProperty]:
        """
        Get property by ID

        Args:
            property_id: Property ID

        Returns:
            CaseProperty instance if found, None otherwise
        """
        return self.session.query(CaseProperty).filter(
            CaseProperty.id == property_id
        ).first()

    def get_all_for_case(self, case_id: str) -> List[CaseProperty]:
        """
        Get all properties for a case

        Args:
            case_id: Case ID

        Returns:
            List of CaseProperty instances
        """
        return self.session.query(CaseProperty).filter(
            CaseProperty.case_id == case_id
        ).order_by(CaseProperty.created_at.desc()).all()

    def update(self, prop: CaseProperty) -> CaseProperty:
        """
        Update property in database

        Args:
            prop: CaseProperty instance with updated fields

        Returns:
            Updated CaseProperty instance
        """
        prop.updated_at = datetime.now(timezone.utc)
        self.session.add(prop)
        self.session.flush()
        return prop

    def delete(self, property_id: str) -> bool:
        """
        Delete property from database

        Args:
            property_id: Property ID

        Returns:
            True if deleted, False if not found
        """
        prop = self.get_by_id(property_id)
        if not prop:
            return False

        self.session.delete(prop)
        self.session.flush()
        return True

    def get_total_assets(self, case_id: str) -> int:
        """
        Calculate total assets (non-debt properties) for a case

        Args:
            case_id: Case ID

        Returns:
            Total asset value in KRW
        """
        properties = self.get_all_for_case(case_id)
        return sum(
            p.estimated_value for p in properties
            if p.property_type != PropertyType.DEBT
        )

    def get_total_debts(self, case_id: str) -> int:
        """
        Calculate total debts for a case

        Args:
            case_id: Case ID

        Returns:
            Total debt value in KRW
        """
        properties = self.get_all_for_case(case_id)
        return sum(
            p.estimated_value for p in properties
            if p.property_type == PropertyType.DEBT
        )

    def get_summary(self, case_id: str) -> dict:
        """
        Get property summary for a case

        Args:
            case_id: Case ID

        Returns:
            Dictionary with summary statistics
        """
        properties = self.get_all_for_case(case_id)

        by_type = {}
        by_owner = {}
        total_assets = 0
        total_debts = 0

        for p in properties:
            # By type
            type_key = p.property_type.value
            by_type[type_key] = by_type.get(type_key, 0) + p.estimated_value

            # By owner
            owner_key = p.owner.value
            by_owner[owner_key] = by_owner.get(owner_key, 0) + p.estimated_value

            # Totals
            if p.property_type == PropertyType.DEBT:
                total_debts += p.estimated_value
            else:
                total_assets += p.estimated_value

        return {
            "total_assets": total_assets,
            "total_debts": total_debts,
            "net_value": total_assets - total_debts,
            "by_type": by_type,
            "by_owner": by_owner
        }
