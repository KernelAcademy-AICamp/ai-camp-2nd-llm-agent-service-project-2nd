"""
API v1 라우터
"""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    documents,
    templates,
    laws,
    ocr,
    generation,
    analysis,
    search,
    auth
)

api_router = APIRouter()

# 인증
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# 문서 관리
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])

# 법률 데이터
api_router.include_router(laws.router, prefix="/laws", tags=["laws"])

# OCR 및 문서 처리
api_router.include_router(ocr.router, prefix="/ocr", tags=["ocr"])

# 문서 생성
api_router.include_router(generation.router, prefix="/generate", tags=["generation"])

# 분석 및 검토
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])

# 검색
api_router.include_router(search.router, prefix="/search", tags=["search"])