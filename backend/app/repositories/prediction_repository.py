"""
Prediction Repository - Database operations for division predictions
"""

from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone
import uuid

from app.db.models import DivisionPrediction, ConfidenceLevel


class PredictionRepository:
    """
    Repository for DivisionPrediction database operations
    """

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        case_id: str,
        total_property_value: int,
        total_debt_value: int,
        net_value: int,
        plaintiff_ratio: int,
        defendant_ratio: int,
        plaintiff_amount: int,
        defendant_amount: int,
        evidence_impacts: list = None,
        similar_cases: list = None,
        confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    ) -> DivisionPrediction:
        """
        Create a new prediction for a case

        Args:
            case_id: Case ID
            total_property_value: Total asset value
            total_debt_value: Total debt value
            net_value: Net value (assets - debts)
            plaintiff_ratio: Plaintiff ratio (0-100)
            defendant_ratio: Defendant ratio (0-100)
            plaintiff_amount: Plaintiff expected amount
            defendant_amount: Defendant expected amount
            evidence_impacts: List of evidence impacts
            similar_cases: List of similar cases
            confidence_level: Prediction confidence level

        Returns:
            Created DivisionPrediction instance
        """
        # Check if prediction already exists for this case
        existing = self.get_latest_for_case(case_id)
        version = 1 if not existing else existing.version + 1

        prediction = DivisionPrediction(
            id=f"pred_{uuid.uuid4().hex[:12]}",
            case_id=case_id,
            total_property_value=total_property_value,
            total_debt_value=total_debt_value,
            net_value=net_value,
            plaintiff_ratio=plaintiff_ratio,
            defendant_ratio=defendant_ratio,
            plaintiff_amount=plaintiff_amount,
            defendant_amount=defendant_amount,
            evidence_impacts=evidence_impacts or [],
            similar_cases=similar_cases or [],
            confidence_level=confidence_level,
            version=version,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        self.session.add(prediction)
        self.session.flush()

        return prediction

    def get_by_id(self, prediction_id: str) -> Optional[DivisionPrediction]:
        """
        Get prediction by ID

        Args:
            prediction_id: Prediction ID

        Returns:
            DivisionPrediction instance if found, None otherwise
        """
        return self.session.query(DivisionPrediction).filter(
            DivisionPrediction.id == prediction_id
        ).first()

    def get_latest_for_case(self, case_id: str) -> Optional[DivisionPrediction]:
        """
        Get the latest prediction for a case

        Args:
            case_id: Case ID

        Returns:
            Latest DivisionPrediction instance if found, None otherwise
        """
        return self.session.query(DivisionPrediction).filter(
            DivisionPrediction.case_id == case_id
        ).order_by(DivisionPrediction.version.desc()).first()

    def get_all_for_case(self, case_id: str) -> list:
        """
        Get all predictions for a case (history)

        Args:
            case_id: Case ID

        Returns:
            List of DivisionPrediction instances
        """
        return self.session.query(DivisionPrediction).filter(
            DivisionPrediction.case_id == case_id
        ).order_by(DivisionPrediction.version.desc()).all()

    def update(self, prediction: DivisionPrediction) -> DivisionPrediction:
        """
        Update prediction in database

        Args:
            prediction: DivisionPrediction instance with updated fields

        Returns:
            Updated DivisionPrediction instance
        """
        prediction.updated_at = datetime.now(timezone.utc)
        self.session.add(prediction)
        self.session.flush()
        return prediction

    def delete(self, prediction_id: str) -> bool:
        """
        Delete prediction from database

        Args:
            prediction_id: Prediction ID

        Returns:
            True if deleted, False if not found
        """
        prediction = self.get_by_id(prediction_id)
        if not prediction:
            return False

        self.session.delete(prediction)
        self.session.flush()
        return True
