"""
Properties API endpoints
POST /cases/{case_id}/properties - Create new property
GET /cases/{case_id}/properties - List properties for a case
GET /cases/{case_id}/properties/{property_id} - Get property detail
PATCH /cases/{case_id}/properties/{property_id} - Update property
DELETE /cases/{case_id}/properties/{property_id} - Delete property
GET /cases/{case_id}/properties/summary - Get property summary

Division Prediction API endpoints
GET /cases/{case_id}/division-prediction - Get latest prediction
POST /cases/{case_id}/division-prediction - Calculate new prediction
"""

from fastapi import APIRouter, Depends, status
from typing import Optional
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.schemas import (
    PropertyCreate,
    PropertyUpdate,
    PropertyOut,
    PropertyListResponse,
    PropertySummary,
    DivisionPredictionOut,
    DivisionPredictionRequest
)
from app.services.property_service import PropertyService
from app.services.prediction_service import PredictionService
from app.core.dependencies import get_current_user_id


router = APIRouter()


@router.post(
    "/cases/{case_id}/properties",
    response_model=PropertyOut,
    status_code=status.HTTP_201_CREATED
)
def create_property(
    case_id: str,
    property_data: PropertyCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Create a new property for a case

    **Request Body:**
    - property_type: Type of property (real_estate, savings, stocks, etc.)
    - estimated_value: Estimated value in KRW (required)
    - owner: Who owns the property (plaintiff, defendant, joint)
    - description: Property description (optional)
    - is_premarital: Whether acquired before marriage (optional)
    - acquisition_date: Date of acquisition (optional)
    - notes: Additional notes (optional)

    **Response:**
    - 201: Property created successfully
    - 404: Case not found
    - 403: User does not have access to case
    """
    service = PropertyService(db)
    return service.create_property(case_id, property_data, user_id)


@router.get(
    "/cases/{case_id}/properties",
    response_model=PropertyListResponse
)
def list_properties(
    case_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    List all properties for a case

    **Response:**
    - 200: List of properties with summary (total_assets, total_debts, net_value)
    - 404: Case not found
    - 403: User does not have access to case
    """
    service = PropertyService(db)
    return service.get_properties(case_id, user_id)


@router.get(
    "/cases/{case_id}/properties/summary",
    response_model=PropertySummary
)
def get_property_summary(
    case_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get property summary for a case

    **Response:**
    - 200: Property summary (total_assets, total_debts, net_value, by_type, by_owner)
    - 404: Case not found
    - 403: User does not have access to case
    """
    service = PropertyService(db)
    return service.get_summary(case_id, user_id)


@router.get(
    "/cases/{case_id}/properties/{property_id}",
    response_model=PropertyOut
)
def get_property(
    case_id: str,
    property_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get a specific property

    **Response:**
    - 200: Property details
    - 404: Case or property not found
    - 403: User does not have access to case
    """
    service = PropertyService(db)
    return service.get_property(case_id, property_id, user_id)


@router.patch(
    "/cases/{case_id}/properties/{property_id}",
    response_model=PropertyOut
)
def update_property(
    case_id: str,
    property_id: str,
    update_data: PropertyUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Update a property

    **Request Body (all optional):**
    - property_type: Type of property
    - estimated_value: Estimated value in KRW
    - owner: Who owns the property
    - description: Property description
    - is_premarital: Whether acquired before marriage
    - acquisition_date: Date of acquisition
    - notes: Additional notes

    **Response:**
    - 200: Updated property details
    - 404: Case or property not found
    - 403: User does not have access to case
    """
    service = PropertyService(db)
    return service.update_property(case_id, property_id, update_data, user_id)


@router.delete(
    "/cases/{case_id}/properties/{property_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_property(
    case_id: str,
    property_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Delete a property

    **Response:**
    - 204: Property deleted successfully
    - 404: Case or property not found
    - 403: User does not have access to case
    """
    service = PropertyService(db)
    service.delete_property(case_id, property_id, user_id)


# ============================================
# Division Prediction Endpoints
# ============================================

@router.get(
    "/cases/{case_id}/division-prediction",
    response_model=Optional[DivisionPredictionOut]
)
def get_division_prediction(
    case_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get the latest division prediction for a case

    Returns the most recent prediction if one exists.
    To calculate a new prediction, use POST.

    **Response:**
    - 200: Latest prediction (or null if none exists)
    - 404: Case not found
    - 403: User does not have access to case
    """
    service = PredictionService(db)
    return service.get_prediction(case_id, user_id)


@router.post(
    "/cases/{case_id}/division-prediction",
    response_model=DivisionPredictionOut,
    status_code=status.HTTP_201_CREATED
)
def calculate_division_prediction(
    case_id: str,
    request: DivisionPredictionRequest = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Calculate a new division prediction for a case

    This analyzes all properties and evidence for the case
    and generates a new prediction using AI Worker.

    **Request Body (optional):**
    - force_recalculate: Force recalculation even if recent prediction exists

    **Response:**
    - 201: New prediction created
    - 404: Case not found
    - 403: User does not have access to case

    **Note:**
    - Prediction includes plaintiff/defendant ratios, amounts
    - Evidence impacts show how each piece of evidence affects the ratio
    - Similar cases from precedent database are included
    - Confidence level indicates reliability of prediction
    """
    service = PredictionService(db)
    return service.calculate_prediction(
        case_id,
        user_id,
        request or DivisionPredictionRequest()
    )
