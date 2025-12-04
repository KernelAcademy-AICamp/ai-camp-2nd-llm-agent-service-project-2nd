"""
Prediction Service - Business logic for division prediction with AI Worker integration
"""

import sys
from pathlib import Path
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.db.schemas import (
    DivisionPredictionOut,
    DivisionPredictionRequest,
    EvidenceImpact,
    SimilarCase
)
from app.db.models import ConfidenceLevel, PropertyType
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.property_repository import PropertyRepository
from app.repositories.case_repository import CaseRepository
from app.repositories.case_member_repository import CaseMemberRepository
from app.core.errors import NotFoundError, PermissionError

logger = logging.getLogger(__name__)

# Add ai_worker to path for ImpactAnalyzer import
AI_WORKER_PATH = Path(__file__).parent.parent.parent.parent / "ai_worker"
if str(AI_WORKER_PATH) not in sys.path:
    sys.path.insert(0, str(AI_WORKER_PATH))


class PredictionService:
    """
    Service for division prediction business logic
    """

    def __init__(self, db: Session):
        self.db = db
        self.prediction_repo = PredictionRepository(db)
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

    def get_prediction(
        self,
        case_id: str,
        user_id: str
    ) -> Optional[DivisionPredictionOut]:
        """
        Get the latest prediction for a case

        Args:
            case_id: Case ID
            user_id: User ID requesting the prediction

        Returns:
            Latest prediction or None if not exists

        Raises:
            NotFoundError: Case not found
            PermissionError: User does not have access
        """
        self._check_case_access(case_id, user_id)

        prediction = self.prediction_repo.get_latest_for_case(case_id)
        if not prediction:
            return None

        return self._to_prediction_out(prediction)

    def calculate_prediction(
        self,
        case_id: str,
        user_id: str,
        request: DivisionPredictionRequest = None
    ) -> DivisionPredictionOut:
        """
        Calculate and save a new prediction

        Args:
            case_id: Case ID
            user_id: User ID requesting the calculation
            request: Optional request with force_recalculate flag

        Returns:
            New prediction

        Raises:
            NotFoundError: Case not found
            PermissionError: User does not have access
        """
        self._check_case_access(case_id, user_id)

        # Get property summary
        property_summary = self.property_repo.get_summary(case_id)
        total_assets = property_summary["total_assets"]
        total_debts = property_summary["total_debts"]
        net_value = property_summary["net_value"]

        # If no properties, return default 50:50 prediction
        if net_value == 0:
            return self._create_default_prediction(case_id, 0, 0, 0)

        # Try to use AI Worker's ImpactAnalyzer
        evidence_impacts, similar_cases, ai_ratio = self._analyze_with_ai_worker(case_id)

        # Calculate final ratio
        if ai_ratio is not None:
            plaintiff_ratio = ai_ratio
        else:
            # Default 50:50 if no AI analysis available
            plaintiff_ratio = 50

        defendant_ratio = 100 - plaintiff_ratio

        # Calculate amounts
        plaintiff_amount = int(net_value * plaintiff_ratio / 100)
        defendant_amount = net_value - plaintiff_amount

        # Determine confidence level
        confidence = self._determine_confidence(
            len(evidence_impacts),
            len(similar_cases),
            ai_ratio is not None
        )

        # Create prediction
        prediction = self.prediction_repo.create(
            case_id=case_id,
            total_property_value=total_assets,
            total_debt_value=total_debts,
            net_value=net_value,
            plaintiff_ratio=plaintiff_ratio,
            defendant_ratio=defendant_ratio,
            plaintiff_amount=plaintiff_amount,
            defendant_amount=defendant_amount,
            evidence_impacts=[ei.model_dump() for ei in evidence_impacts],
            similar_cases=[sc.model_dump() for sc in similar_cases],
            confidence_level=confidence
        )

        self.db.commit()
        self.db.refresh(prediction)

        return self._to_prediction_out(prediction)

    def _analyze_with_ai_worker(self, case_id: str) -> tuple:
        """
        Analyze case using AI Worker's ImpactAnalyzer

        Returns:
            Tuple of (evidence_impacts, similar_cases, ai_ratio)
        """
        evidence_impacts = []
        similar_cases = []
        ai_ratio = None

        try:
            from src.analysis.impact_analyzer import ImpactAnalyzer

            analyzer = ImpactAnalyzer(case_id=case_id)

            # Get mock evidence for now (in real implementation, query DynamoDB)
            # TODO: Integrate with actual evidence storage
            mock_evidences = self._get_mock_evidences(case_id)

            if mock_evidences:
                # Analyze each evidence
                for evidence in mock_evidences:
                    impact = analyzer.analyze_single_evidence(evidence)
                    if impact:
                        evidence_impacts.append(EvidenceImpact(
                            evidence_id=impact.evidence_id,
                            evidence_type=impact.evidence_type,
                            impact_type=impact.impact_type,
                            impact_percent=impact.impact_percent,
                            direction=impact.direction.value,
                            reason=impact.reason,
                            confidence=impact.confidence
                        ))

                # Calculate total prediction
                prediction = analyzer.calculate_prediction(mock_evidences)
                ai_ratio = prediction.plaintiff_ratio

                # Get similar cases
                for sc in prediction.similar_cases:
                    similar_cases.append(SimilarCase(
                        case_ref=sc.case_ref,
                        similarity_score=sc.similarity_score,
                        division_ratio=sc.division_ratio,
                        key_factors=sc.key_factors
                    ))

            logger.info(f"AI Worker analysis completed for case {case_id}")

        except ImportError as e:
            logger.warning(f"AI Worker not available: {e}")
        except Exception as e:
            logger.error(f"AI Worker analysis failed: {e}")

        return evidence_impacts, similar_cases, ai_ratio

    def _get_mock_evidences(self, case_id: str) -> list:
        """
        Get mock evidences for testing
        TODO: Replace with actual DynamoDB query
        """
        # Return empty list for now - will be populated when evidence is analyzed
        return []

    def _create_default_prediction(
        self,
        case_id: str,
        total_assets: int,
        total_debts: int,
        net_value: int
    ) -> DivisionPredictionOut:
        """
        Create default 50:50 prediction
        """
        prediction = self.prediction_repo.create(
            case_id=case_id,
            total_property_value=total_assets,
            total_debt_value=total_debts,
            net_value=net_value,
            plaintiff_ratio=50,
            defendant_ratio=50,
            plaintiff_amount=net_value // 2,
            defendant_amount=net_value - (net_value // 2),
            evidence_impacts=[],
            similar_cases=[],
            confidence_level=ConfidenceLevel.LOW
        )

        self.db.commit()
        self.db.refresh(prediction)

        return self._to_prediction_out(prediction)

    def _determine_confidence(
        self,
        evidence_count: int,
        similar_case_count: int,
        has_ai_analysis: bool
    ) -> ConfidenceLevel:
        """
        Determine confidence level based on available data
        """
        if not has_ai_analysis:
            return ConfidenceLevel.LOW

        if evidence_count >= 5 and similar_case_count >= 3:
            return ConfidenceLevel.HIGH
        elif evidence_count >= 2 or similar_case_count >= 1:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    def _to_prediction_out(self, prediction) -> DivisionPredictionOut:
        """
        Convert DivisionPrediction model to output schema
        """
        return DivisionPredictionOut(
            id=prediction.id,
            case_id=prediction.case_id,
            total_property_value=prediction.total_property_value,
            total_debt_value=prediction.total_debt_value,
            net_value=prediction.net_value,
            plaintiff_ratio=prediction.plaintiff_ratio,
            defendant_ratio=prediction.defendant_ratio,
            plaintiff_amount=prediction.plaintiff_amount,
            defendant_amount=prediction.defendant_amount,
            evidence_impacts=[
                EvidenceImpact(**ei) for ei in (prediction.evidence_impacts or [])
            ],
            similar_cases=[
                SimilarCase(**sc) for sc in (prediction.similar_cases or [])
            ],
            confidence_level=prediction.confidence_level,
            version=prediction.version,
            created_at=prediction.created_at,
            updated_at=prediction.updated_at
        )
