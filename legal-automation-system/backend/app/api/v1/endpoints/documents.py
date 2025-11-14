"""
문서 관리 API 엔드포인트
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database.session import get_db
from app.models.document import Document, DocumentStatus, DocumentType
from app.schemas.document import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentListResponse
)
from app.services.ocr.document_parser import DocumentProcessor
from app.services.risk.risk_analyzer import DocumentRiskAnalyzer
from app.services.risk.review_system import ReviewSystem
from app.core.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=DocumentResponse)
async def create_document(
    document: DocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    새 문서 생성
    """
    # 문서 생성
    db_document = Document(
        **document.dict(),
        user_id=current_user.id,
        created_by=current_user.id
    )
    db.add(db_document)
    await db.commit()
    await db.refresh(db_document)

    return db_document


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100),
    document_type: Optional[DocumentType] = None,
    status: Optional[DocumentStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    문서 목록 조회
    """
    query = select(Document).where(Document.user_id == current_user.id)

    if document_type:
        query = query.where(Document.document_type == document_type)
    if status:
        query = query.where(Document.status == status)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    documents = result.scalars().all()

    # 총 개수
    count_query = select(func.count(Document.id)).where(Document.user_id == current_user.id)
    if document_type:
        count_query = count_query.where(Document.document_type == document_type)
    if status:
        count_query = count_query.where(Document.status == status)

    count_result = await db.execute(count_query)
    total = count_result.scalar()

    return {
        "documents": documents,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    특정 문서 조회
    """
    query = select(Document).where(
        Document.id == document_id,
        Document.user_id == current_user.id
    )
    result = await db.execute(query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return document


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    document_update: DocumentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    문서 수정
    """
    query = select(Document).where(
        Document.id == document_id,
        Document.user_id == current_user.id
    )
    result = await db.execute(query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # 업데이트
    update_data = document_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(document, field, value)

    document.updated_by = current_user.id
    await db.commit()
    await db.refresh(document)

    return document


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    문서 삭제
    """
    query = select(Document).where(
        Document.id == document_id,
        Document.user_id == current_user.id
    )
    result = await db.execute(query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    await db.delete(document)
    await db.commit()

    return {"message": "Document deleted successfully"}


@router.post("/{document_id}/analyze")
async def analyze_document_risk(
    document_id: int,
    deep_analysis: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    문서 리스크 분석
    """
    # 문서 조회
    query = select(Document).where(
        Document.id == document_id,
        Document.user_id == current_user.id
    )
    result = await db.execute(query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # 리스크 분석
    analyzer = DocumentRiskAnalyzer()
    analysis_result = await analyzer.analyze_document(document, deep_analysis=deep_analysis)

    # 결과 저장
    document.risk_level = analysis_result['risk_level']
    document.risk_score = analysis_result['risk_score']
    document.risk_analysis = analysis_result
    await db.commit()

    return analysis_result


@router.post("/{document_id}/review")
async def review_document(
    document_id: int,
    review_depth: str = Query("standard", regex="^(quick|standard|thorough)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    문서 검토
    """
    # 문서 조회
    query = select(Document).where(
        Document.id == document_id,
        Document.user_id == current_user.id
    )
    result = await db.execute(query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # 문서 검토
    review_system = ReviewSystem()
    review_result = await review_system.review_document(document, review_depth=review_depth)

    # 결과 저장
    document.legal_review = review_result.get('detailed_report', '')
    await db.commit()

    return review_result


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_type: DocumentType = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    문서 파일 업로드 및 처리
    """
    # 파일 저장
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name

    try:
        # 문서 처리
        processor = DocumentProcessor()
        processed = await processor.process_document(
            tmp_file_path,
            user_id=current_user.id,
            save_to_db=False
        )

        # 문서 생성
        document = Document(
            title=file.filename,
            document_type=document_type,
            content=processed['text'],
            metadata=processed.get('metadata', {}),
            file_path=tmp_file_path,
            file_format=processed.get('format', ''),
            user_id=current_user.id,
            created_by=current_user.id
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)

        return {
            "document_id": document.id,
            "title": document.title,
            "extracted_text": processed['text'][:500],
            "metadata": processed.get('metadata', {})
        }

    finally:
        # 임시 파일 삭제
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)


@router.get("/{document_id}/versions")
async def get_document_versions(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    문서 버전 이력 조회
    """
    # 문서 조회
    query = select(Document).where(
        Document.id == document_id,
        Document.user_id == current_user.id
    )
    result = await db.execute(query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # 버전 이력 조회
    from app.models.document import DocumentRevision
    revision_query = select(DocumentRevision).where(
        DocumentRevision.document_id == document_id
    ).order_by(DocumentRevision.version.desc())

    revision_result = await db.execute(revision_query)
    revisions = revision_result.scalars().all()

    return {
        "document_id": document_id,
        "current_version": document.version,
        "revisions": [
            {
                "version": rev.version,
                "changed_by": rev.changed_by,
                "change_reason": rev.change_reason,
                "created_at": rev.created_at
            }
            for rev in revisions
        ]
    }


@router.post("/{document_id}/sign")
async def sign_document(
    document_id: int,
    signature_data: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    문서 전자서명
    """
    from app.models.document import DocumentSignature
    from datetime import datetime

    # 문서 조회
    query = select(Document).where(
        Document.id == document_id,
        Document.user_id == current_user.id
    )
    result = await db.execute(query)
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # 서명 생성
    signature = DocumentSignature(
        document_id=document_id,
        signer_id=current_user.id,
        signature_type="electronic",
        signature_data=signature_data,
        signed_at=datetime.now(),
        is_verified=True
    )
    db.add(signature)

    # 문서 상태 업데이트
    document.is_signed = True
    await db.commit()

    return {"message": "Document signed successfully", "signature_id": signature.id}