"""
문서 생성 API 엔드포인트
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.document import Document, DocumentType
from app.models.template import Template
from app.services.llm.generator import DocumentGenerator
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.schemas.generation import (
    GenerationRequest,
    GenerationResponse,
    TemplateGenerationRequest
)

router = APIRouter()


@router.post("/contract", response_model=GenerationResponse)
async def generate_contract(
    request: GenerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    계약서 생성

    지원하는 계약서 타입:
    - employment: 근로계약서
    - lease: 임대차계약서
    - sales: 매매계약서
    - service: 용역계약서
    - nda: 비밀유지계약서
    """
    generator = DocumentGenerator()

    try:
        # 문서 생성
        generated_doc = await generator.generate_document(
            template_type=request.template_type,
            user_data=request.user_data,
            document_type="contract",
            language=request.language or "ko"
        )

        # 데이터베이스 저장
        document = Document(
            title=generated_doc['title'],
            document_type=DocumentType.CONTRACT,
            content=generated_doc['content'],
            metadata={
                'template_type': request.template_type,
                'generation_params': request.user_data
            },
            user_id=current_user.id,
            created_by=current_user.id
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)

        return {
            "document_id": document.id,
            "title": generated_doc['title'],
            "content": generated_doc['content'],
            "metadata": generated_doc.get('metadata', {}),
            "suggestions": generated_doc.get('suggestions', [])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lawsuit", response_model=GenerationResponse)
async def generate_lawsuit(
    request: GenerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    소장 생성

    지원하는 소장 타입:
    - civil: 민사소송
    - labor: 노동소송
    - damage: 손해배상청구
    - eviction: 명도소송
    """
    generator = DocumentGenerator()

    try:
        # 소장 생성
        generated_doc = await generator.generate_document(
            template_type=request.template_type,
            user_data=request.user_data,
            document_type="lawsuit",
            language=request.language or "ko"
        )

        # 데이터베이스 저장
        document = Document(
            title=generated_doc['title'],
            document_type=DocumentType.LAWSUIT,
            content=generated_doc['content'],
            metadata={
                'template_type': request.template_type,
                'generation_params': request.user_data
            },
            user_id=current_user.id,
            created_by=current_user.id
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)

        return {
            "document_id": document.id,
            "title": generated_doc['title'],
            "content": generated_doc['content'],
            "metadata": generated_doc.get('metadata', {}),
            "suggestions": generated_doc.get('suggestions', [])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notice", response_model=GenerationResponse)
async def generate_notice(
    request: GenerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    내용증명 생성

    지원하는 내용증명 타입:
    - payment: 대금지급 요구
    - contract_termination: 계약해지 통보
    - damage_claim: 손해배상 청구
    - eviction_notice: 명도 요구
    """
    generator = DocumentGenerator()

    try:
        # 내용증명 생성
        generated_doc = await generator.generate_document(
            template_type=request.template_type,
            user_data=request.user_data,
            document_type="notice",
            language=request.language or "ko"
        )

        # 데이터베이스 저장
        document = Document(
            title=generated_doc['title'],
            document_type=DocumentType.NOTICE,
            content=generated_doc['content'],
            metadata={
                'template_type': request.template_type,
                'generation_params': request.user_data
            },
            user_id=current_user.id,
            created_by=current_user.id
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)

        return {
            "document_id": document.id,
            "title": generated_doc['title'],
            "content": generated_doc['content'],
            "metadata": generated_doc.get('metadata', {}),
            "suggestions": generated_doc.get('suggestions', [])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/from-template/{template_id}", response_model=GenerationResponse)
async def generate_from_template(
    template_id: int,
    request: TemplateGenerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    템플릿 기반 문서 생성
    """
    # 템플릿 조회
    from sqlalchemy import select
    query = select(Template).where(Template.id == template_id, Template.is_active == True)
    result = await db.execute(query)
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    generator = DocumentGenerator()

    try:
        # 템플릿 기반 생성
        generated_doc = await generator.generate_from_template(
            template=template,
            user_data=request.field_values
        )

        # 데이터베이스 저장
        document = Document(
            title=generated_doc['title'],
            document_type=template.document_type,
            content=generated_doc['content'],
            template_id=template_id,
            metadata={
                'template_name': template.name,
                'field_values': request.field_values
            },
            user_id=current_user.id,
            created_by=current_user.id
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)

        return {
            "document_id": document.id,
            "title": generated_doc['title'],
            "content": generated_doc['content'],
            "metadata": generated_doc.get('metadata', {}),
            "suggestions": []
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/custom", response_model=GenerationResponse)
async def generate_custom_document(
    prompt: str = Query(..., description="문서 생성 요구사항"),
    document_type: DocumentType = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    사용자 정의 문서 생성 (프롬프트 기반)
    """
    generator = DocumentGenerator()

    try:
        # 프롬프트 기반 생성
        generated_doc = await generator.generate_from_prompt(
            prompt=prompt,
            document_type=document_type.value
        )

        # 데이터베이스 저장
        document = Document(
            title=generated_doc.get('title', 'Custom Document'),
            document_type=document_type,
            content=generated_doc['content'],
            metadata={
                'generation_prompt': prompt
            },
            user_id=current_user.id,
            created_by=current_user.id
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)

        return {
            "document_id": document.id,
            "title": document.title,
            "content": generated_doc['content'],
            "metadata": {},
            "suggestions": []
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates")
async def list_available_templates(
    document_type: Optional[DocumentType] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    사용 가능한 템플릿 목록 조회
    """
    from sqlalchemy import select

    query = select(Template).where(Template.is_active == True)

    if document_type:
        query = query.where(Template.document_type == document_type)

    result = await db.execute(query)
    templates = result.scalars().all()

    return {
        "templates": [
            {
                "id": t.id,
                "name": t.name,
                "display_name": t.display_name,
                "description": t.description,
                "category": t.category.value if t.category else None,
                "document_type": t.document_type.value if t.document_type else None,
                "required_fields": t.required_fields,
                "is_premium": t.is_premium
            }
            for t in templates
        ]
    }


@router.post("/enhance/{document_id}")
async def enhance_document(
    document_id: int,
    enhancement_type: str = Query("legal", regex="^(legal|clarity|professional)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    기존 문서 개선

    Enhancement types:
    - legal: 법률적 완성도 향상
    - clarity: 명확성 개선
    - professional: 전문성 강화
    """
    from sqlalchemy import select

    # 문서 조회
    query = select(Document).where(
        Document.id == document_id,
        Document.user_id == current_user.id
    )
    result = await db.execute(query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    generator = DocumentGenerator()

    try:
        # 문서 개선
        enhanced = await generator.enhance_document(
            content=document.content,
            enhancement_type=enhancement_type
        )

        # 새 버전으로 저장
        document.content = enhanced['content']
        document.version += 1
        document.updated_by = current_user.id

        await db.commit()

        return {
            "document_id": document.id,
            "enhanced_content": enhanced['content'],
            "improvements": enhanced.get('improvements', []),
            "version": document.version
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))