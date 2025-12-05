"""
Properties API endpoints
POST /cases/{case_id}/properties - Create property
GET /cases/{case_id}/properties - List properties
GET /cases/{case_id}/properties/{property_id} - Get property detail
PATCH /cases/{case_id}/properties/{property_id} - Update property
DELETE /cases/{case_id}/properties/{property_id} - Delete property
GET /cases/{case_id}/division-prediction - Get latest division prediction
POST /cases/{case_id}/division-prediction - Create/update division prediction
"""

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.db.schemas import (
    PropertyCreate,
    PropertyUpdate,
    PropertyOut,
    PropertyListResponse,
    DivisionPredictionCreate,
    DivisionPredictionOut,
)
from app.db.models import CaseProperty, DivisionPrediction, CaseMember
from app.core.dependencies import get_current_user_id


router = APIRouter()


def _check_case_access(db: Session, case_id: str, user_id: str) -> bool:
    """Check if user has access to the case"""
    member = db.query(CaseMember).filter(
        CaseMember.case_id == case_id,
        CaseMember.user_id == user_id
    ).first()
    return member is not None


@router.post("", response_model=PropertyOut, status_code=status.HTTP_201_CREATED)
def create_property(
    case_id: str,
    property_data: PropertyCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Create a new property for a case

    **Path Parameters:**
    - case_id: Case ID

    **Request Body:**
    - name: Property name (required)
    - property_type: Property type (real_estate, savings, stocks, vehicle, other)
    - estimated_value: Estimated value in KRW (optional)
    - owner_side: Owner side (plaintiff, defendant, joint) (optional)
    - description: Description (optional)
    - evidence_ids: Related evidence IDs (optional)

    **Response:**
    - 201: Property created successfully
    - 403: User does not have access to case
    """
    if not _check_case_access(db, case_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="사건에 대한 접근 권한이 없습니다."
        )

    new_property = CaseProperty(
        case_id=case_id,
        name=property_data.name,
        property_type=property_data.property_type,
        estimated_value=property_data.estimated_value,
        owner_side=property_data.owner_side,
        description=property_data.description,
        evidence_ids=property_data.evidence_ids
    )

    db.add(new_property)
    db.commit()
    db.refresh(new_property)

    return new_property


@router.get("", response_model=PropertyListResponse)
def list_properties(
    case_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    List all properties for a case

    **Path Parameters:**
    - case_id: Case ID

    **Response:**
    - 200: List of properties with total value
    - properties: List of property items
    - total: Total number of properties
    - total_value: Sum of estimated values
    """
    if not _check_case_access(db, case_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="사건에 대한 접근 권한이 없습니다."
        )

    properties = db.query(CaseProperty).filter(
        CaseProperty.case_id == case_id
    ).order_by(CaseProperty.created_at.desc()).all()

    total_value = sum(p.estimated_value or 0 for p in properties)

    return PropertyListResponse(
        properties=properties,
        total=len(properties),
        total_value=total_value
    )


@router.get("/{property_id}", response_model=PropertyOut)
def get_property(
    case_id: str,
    property_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get property detail by ID

    **Path Parameters:**
    - case_id: Case ID
    - property_id: Property ID

    **Response:**
    - 200: Property detail
    - 403: User does not have access
    - 404: Property not found
    """
    if not _check_case_access(db, case_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="사건에 대한 접근 권한이 없습니다."
        )

    property_item = db.query(CaseProperty).filter(
        CaseProperty.id == property_id,
        CaseProperty.case_id == case_id
    ).first()

    if not property_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="재산 항목을 찾을 수 없습니다."
        )

    return property_item


@router.patch("/{property_id}", response_model=PropertyOut)
def update_property(
    case_id: str,
    property_id: str,
    update_data: PropertyUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Update property information

    **Path Parameters:**
    - case_id: Case ID
    - property_id: Property ID

    **Request Body:**
    - name: Property name (optional)
    - property_type: Property type (optional)
    - estimated_value: Estimated value (optional)
    - owner_side: Owner side (optional)
    - description: Description (optional)
    - evidence_ids: Related evidence IDs (optional)

    **Response:**
    - 200: Updated property
    - 403: User does not have access
    - 404: Property not found
    """
    if not _check_case_access(db, case_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="사건에 대한 접근 권한이 없습니다."
        )

    property_item = db.query(CaseProperty).filter(
        CaseProperty.id == property_id,
        CaseProperty.case_id == case_id
    ).first()

    if not property_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="재산 항목을 찾을 수 없습니다."
        )

    # Update fields if provided
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(property_item, field, value)

    db.commit()
    db.refresh(property_item)

    return property_item


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_property(
    case_id: str,
    property_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Delete a property

    **Path Parameters:**
    - case_id: Case ID
    - property_id: Property ID

    **Response:**
    - 204: Property deleted successfully
    - 403: User does not have access
    - 404: Property not found
    """
    if not _check_case_access(db, case_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="사건에 대한 접근 권한이 없습니다."
        )

    property_item = db.query(CaseProperty).filter(
        CaseProperty.id == property_id,
        CaseProperty.case_id == case_id
    ).first()

    if not property_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="재산 항목을 찾을 수 없습니다."
        )

    db.delete(property_item)
    db.commit()

    return None


@router.get("/division-prediction/latest", response_model=DivisionPredictionOut)
def get_latest_division_prediction(
    case_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get the latest division prediction for a case

    **Path Parameters:**
    - case_id: Case ID

    **Response:**
    - 200: Latest division prediction
    - 403: User does not have access
    - 404: No prediction found
    """
    if not _check_case_access(db, case_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="사건에 대한 접근 권한이 없습니다."
        )

    prediction = db.query(DivisionPrediction).filter(
        DivisionPrediction.case_id == case_id
    ).order_by(DivisionPrediction.created_at.desc()).first()

    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="재산분할 예측 결과가 없습니다."
        )

    return prediction


@router.post("/division-prediction", response_model=DivisionPredictionOut, status_code=status.HTTP_201_CREATED)
def create_division_prediction(
    case_id: str,
    prediction_data: DivisionPredictionCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Create a new division prediction for a case

    **Path Parameters:**
    - case_id: Case ID

    **Request Body:**
    - plaintiff_ratio: Plaintiff's ratio (0-100)
    - defendant_ratio: Defendant's ratio (0-100)
    - plaintiff_amount: Plaintiff's amount in KRW (optional)
    - defendant_amount: Defendant's amount in KRW (optional)
    - confidence_level: Confidence level (high, medium, low)
    - evidence_impacts: List of evidence impacts (optional)
    - reasoning: AI reasoning explanation (optional)

    **Response:**
    - 201: Prediction created successfully
    - 400: Invalid ratio (must sum to 100)
    - 403: User does not have access
    """
    if not _check_case_access(db, case_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="사건에 대한 접근 권한이 없습니다."
        )

    # Validate ratios sum to 100
    if prediction_data.plaintiff_ratio + prediction_data.defendant_ratio != 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="원고와 피고 비율의 합은 100이어야 합니다."
        )

    # Convert evidence_impacts to JSON-serializable format
    evidence_impacts_json = None
    if prediction_data.evidence_impacts:
        evidence_impacts_json = [
            impact.model_dump() for impact in prediction_data.evidence_impacts
        ]

    new_prediction = DivisionPrediction(
        case_id=case_id,
        plaintiff_ratio=prediction_data.plaintiff_ratio,
        defendant_ratio=prediction_data.defendant_ratio,
        plaintiff_amount=prediction_data.plaintiff_amount,
        defendant_amount=prediction_data.defendant_amount,
        confidence_level=prediction_data.confidence_level,
        evidence_impacts=evidence_impacts_json,
        reasoning=prediction_data.reasoning,
        created_by=user_id
    )

    db.add(new_prediction)
    db.commit()
    db.refresh(new_prediction)

    return new_prediction
