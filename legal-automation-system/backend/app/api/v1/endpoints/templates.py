"""
템플릿 관리 API 엔드포인트
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_db
from app.models.template import Template, TemplateCategory
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/")
async def list_templates(
    category: Optional[TemplateCategory] = None,
    is_premium: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    템플릿 목록 조회
    """
    query = select(Template).where(Template.is_active == True)

    if category:
        query = query.where(Template.category == category)
    if is_premium is not None:
        query = query.where(Template.is_premium == is_premium)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    templates = result.scalars().all()

    return {
        "templates": templates,
        "total": len(templates),
        "skip": skip,
        "limit": limit
    }


@router.get("/{template_id}")
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    특정 템플릿 조회
    """
    query = select(Template).where(
        Template.id == template_id,
        Template.is_active == True
    )
    result = await db.execute(query)
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return template


@router.get("/{template_id}/preview")
async def preview_template(
    template_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    템플릿 미리보기
    """
    query = select(Template).where(
        Template.id == template_id,
        Template.is_active == True
    )
    result = await db.execute(query)
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return {
        "template_id": template.id,
        "name": template.display_name,
        "preview_content": template.sample_content or template.template_content[:500],
        "required_fields": template.required_fields,
        "instructions": template.instructions
    }