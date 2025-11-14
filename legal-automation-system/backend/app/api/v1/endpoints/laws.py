"""
법률 데이터 API 엔드포인트
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database.session import get_db
from app.models.law import Law, LawCase, LawInterpretation, LawCategory
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/")
async def list_laws(
    category: Optional[str] = None,
    law_name: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    법률 조항 목록 조회
    """
    query = select(Law).where(Law.is_active == True)

    if category:
        query = query.where(Law.category == category)
    if law_name:
        query = query.where(Law.law_name.ilike(f"%{law_name}%"))

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    laws = result.scalars().all()

    # 총 개수
    count_query = select(func.count(Law.id)).where(Law.is_active == True)
    if category:
        count_query = count_query.where(Law.category == category)
    if law_name:
        count_query = count_query.where(Law.law_name.ilike(f"%{law_name}%"))

    count_result = await db.execute(count_query)
    total = count_result.scalar()

    return {
        "laws": laws,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{law_id}")
async def get_law(
    law_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    특정 법률 조항 조회
    """
    query = select(Law).where(Law.id == law_id)
    result = await db.execute(query)
    law = result.scalar_one_or_none()

    if not law:
        raise HTTPException(status_code=404, detail="Law not found")

    # 조회수 증가
    law.view_count = (law.view_count or 0) + 1
    await db.commit()

    return law


@router.get("/cases")
async def list_cases(
    court_name: Optional[str] = None,
    case_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    판례 목록 조회
    """
    query = select(LawCase)

    if court_name:
        query = query.where(LawCase.court_name.ilike(f"%{court_name}%"))
    if case_type:
        query = query.where(LawCase.case_type == case_type)

    query = query.order_by(LawCase.judgment_date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    cases = result.scalars().all()

    return {
        "cases": cases,
        "skip": skip,
        "limit": limit
    }


@router.get("/cases/{case_id}")
async def get_case(
    case_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    특정 판례 조회
    """
    query = select(LawCase).where(LawCase.id == case_id)
    result = await db.execute(query)
    case = result.scalar_one_or_none()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # 조회수 증가
    case.view_count = (case.view_count or 0) + 1
    await db.commit()

    return case


@router.get("/interpretations")
async def list_interpretations(
    requesting_agency: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    법령해석례 목록 조회
    """
    query = select(LawInterpretation)

    if requesting_agency:
        query = query.where(LawInterpretation.requesting_agency.ilike(f"%{requesting_agency}%"))

    query = query.order_by(LawInterpretation.response_date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    interpretations = result.scalars().all()

    return {
        "interpretations": interpretations,
        "skip": skip,
        "limit": limit
    }


@router.get("/categories")
async def list_law_categories(
    db: AsyncSession = Depends(get_db)
):
    """
    법률 카테고리 목록 조회
    """
    query = select(LawCategory).where(LawCategory.is_active == True).order_by(LawCategory.display_order)
    result = await db.execute(query)
    categories = result.scalars().all()

    return {
        "categories": [
            {
                "id": cat.id,
                "name": cat.name,
                "description": cat.description,
                "icon": cat.icon,
                "parent_id": cat.parent_id
            }
            for cat in categories
        ]
    }