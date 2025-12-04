"""
Property Service - Business logic for property division management
"""

from sqlalchemy.orm import Session
from typing import List

from app.db.schemas import (
    PropertyCreate,
    PropertyUpdate,
    PropertyOut,
    PropertyListResponse,
    PropertySummary
)
from app.db.models import PropertyType
from app.repositories.property_repository import PropertyRepository
from app.repositories.case_repository import CaseRepository
from app.repositories.case_member_repository import CaseMemberRepository
from app.core.errors import NotFoundError, PermissionError


class PropertyService:
    """
    Service for property management business logic
    """

    def __init__(self, db: Session):
        self.db = db
        self.property_repo = PropertyRepository(db)
        self.case_repo = CaseRepository(db)
        self.member_repo = CaseMemberRepository(db)

    def _check_case_access(self, case_id: str, user_id: str) -> None:
        """
        Check if case exists and user has access

        Raises:
            NotFoundError: Case not found
            PermissionError: User does not have access
        """
        case = self.case_repo.get_by_id(case_id)
        if not case:
            raise NotFoundError("Case")

        if not self.member_repo.has_access(case_id, user_id):
            raise PermissionError("You do not have access to this case")

    def create_property(
        self,
        case_id: str,
        property_data: PropertyCreate,
        user_id: str
    ) -> PropertyOut:
        """
        Create a new property for a case

        Args:
            case_id: Case ID
            property_data: Property creation data
            user_id: User ID creating the property

        Returns:
            Created property data

        Raises:
            NotFoundError: Case not found
            PermissionError: User does not have access
        """
        self._check_case_access(case_id, user_id)

        prop = self.property_repo.create(
            case_id=case_id,
            property_type=property_data.property_type,
            estimated_value=property_data.estimated_value,
            owner=property_data.owner,
            description=property_data.description,
            is_premarital=property_data.is_premarital,
            acquisition_date=property_data.acquisition_date,
            notes=property_data.notes
        )

        self.db.commit()
        self.db.refresh(prop)

        return PropertyOut.model_validate(prop)

    def get_properties(self, case_id: str, user_id: str) -> PropertyListResponse:
        """
        Get all properties for a case

        Args:
            case_id: Case ID
            user_id: User ID requesting the list

        Returns:
            List of properties with summary

        Raises:
            NotFoundError: Case not found
            PermissionError: User does not have access
        """
        self._check_case_access(case_id, user_id)

        properties = self.property_repo.get_all_for_case(case_id)
        summary = self.property_repo.get_summary(case_id)

        return PropertyListResponse(
            properties=[PropertyOut.model_validate(p) for p in properties],
            total=len(properties),
            total_assets=summary["total_assets"],
            total_debts=summary["total_debts"],
            net_value=summary["net_value"]
        )

    def get_property(
        self,
        case_id: str,
        property_id: str,
        user_id: str
    ) -> PropertyOut:
        """
        Get a specific property

        Args:
            case_id: Case ID
            property_id: Property ID
            user_id: User ID requesting the property

        Returns:
            Property data

        Raises:
            NotFoundError: Case or property not found
            PermissionError: User does not have access
        """
        self._check_case_access(case_id, user_id)

        prop = self.property_repo.get_by_id(property_id)
        if not prop or prop.case_id != case_id:
            raise NotFoundError("Property")

        return PropertyOut.model_validate(prop)

    def update_property(
        self,
        case_id: str,
        property_id: str,
        update_data: PropertyUpdate,
        user_id: str
    ) -> PropertyOut:
        """
        Update a property

        Args:
            case_id: Case ID
            property_id: Property ID
            update_data: Update data
            user_id: User ID requesting the update

        Returns:
            Updated property data

        Raises:
            NotFoundError: Case or property not found
            PermissionError: User does not have access
        """
        self._check_case_access(case_id, user_id)

        prop = self.property_repo.get_by_id(property_id)
        if not prop or prop.case_id != case_id:
            raise NotFoundError("Property")

        # Update fields
        if update_data.property_type is not None:
            prop.property_type = update_data.property_type
        if update_data.description is not None:
            prop.description = update_data.description
        if update_data.estimated_value is not None:
            prop.estimated_value = update_data.estimated_value
        if update_data.owner is not None:
            prop.owner = update_data.owner
        if update_data.is_premarital is not None:
            prop.is_premarital = update_data.is_premarital
        if update_data.acquisition_date is not None:
            prop.acquisition_date = update_data.acquisition_date
        if update_data.notes is not None:
            prop.notes = update_data.notes

        self.property_repo.update(prop)
        self.db.commit()
        self.db.refresh(prop)

        return PropertyOut.model_validate(prop)

    def delete_property(
        self,
        case_id: str,
        property_id: str,
        user_id: str
    ) -> None:
        """
        Delete a property

        Args:
            case_id: Case ID
            property_id: Property ID
            user_id: User ID requesting the deletion

        Raises:
            NotFoundError: Case or property not found
            PermissionError: User does not have access
        """
        self._check_case_access(case_id, user_id)

        prop = self.property_repo.get_by_id(property_id)
        if not prop or prop.case_id != case_id:
            raise NotFoundError("Property")

        self.property_repo.delete(property_id)
        self.db.commit()

    def get_summary(self, case_id: str, user_id: str) -> PropertySummary:
        """
        Get property summary for a case

        Args:
            case_id: Case ID
            user_id: User ID requesting the summary

        Returns:
            Property summary

        Raises:
            NotFoundError: Case not found
            PermissionError: User does not have access
        """
        self._check_case_access(case_id, user_id)

        summary = self.property_repo.get_summary(case_id)

        return PropertySummary(
            total_assets=summary["total_assets"],
            total_debts=summary["total_debts"],
            net_value=summary["net_value"],
            by_type=summary["by_type"],
            by_owner=summary["by_owner"]
        )
