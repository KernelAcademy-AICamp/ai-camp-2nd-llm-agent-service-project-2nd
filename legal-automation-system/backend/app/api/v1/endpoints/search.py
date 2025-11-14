"""
검색 API 엔드포인트
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.services.rag.retriever import LegalRAGSystem, LegalSearchEngine
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.schemas.search import SearchRequest, SearchResponse, RecommendationResponse

router = APIRouter()


@router.post("/laws", response_model=SearchResponse)
async def search_laws(
    request: SearchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    법률 조항 검색

    Parameters:
    - query: 검색 쿼리
    - category: 법률 카테고리 필터 (민법, 형법, 상법 등)
    - top_k: 반환할 결과 수 (기본: 10)
    - min_score: 최소 유사도 점수 (0-1, 기본: 0.5)
    """
    rag_system = LegalRAGSystem()

    results = await rag_system.search_laws(
        query=request.query,
        top_k=request.top_k or 10,
        category=request.category,
        min_score=request.min_score or 0.5
    )

    return {
        "query": request.query,
        "total_results": len(results),
        "results": results
    }


@router.post("/hybrid", response_model=SearchResponse)
async def hybrid_search(
    request: SearchRequest,
    search_type: str = Query("all", regex="^(all|laws|cases|interpretations)$"),
    current_user: User = Depends(get_current_user)
):
    """
    하이브리드 검색 (법률 + 판례 + 해석례)

    Search types:
    - all: 모든 타입 검색
    - laws: 법률 조항만
    - cases: 판례만
    - interpretations: 해석례만
    """
    search_engine = LegalSearchEngine()

    results = await search_engine.hybrid_search(
        query=request.query,
        search_type=search_type,
        filters=request.filters
    )

    return {
        "query": request.query,
        "total_results": sum(len(v) for v in results.values()),
        "results": results
    }


@router.post("/similar-cases")
async def find_similar_cases(
    document_content: str,
    top_k: int = Query(5, le=20),
    current_user: User = Depends(get_current_user)
):
    """
    유사 판례 검색

    문서 내용을 기반으로 유사한 판례를 검색합니다.
    """
    rag_system = LegalRAGSystem()

    cases = await rag_system.find_similar_cases(
        document_content=document_content,
        top_k=top_k
    )

    return {
        "total_cases": len(cases),
        "cases": cases
    }


@router.post("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(
    context: str,
    document_type: str,
    top_k: int = Query(5, le=10),
    current_user: User = Depends(get_current_user)
):
    """
    문맥 기반 법률 조항 추천

    문서 내용과 타입을 기반으로 관련 법률 조항을 추천합니다.
    """
    rag_system = LegalRAGSystem()

    recommendations = await rag_system.get_recommendations(
        context=context,
        document_type=document_type,
        top_k=top_k
    )

    return {
        "document_type": document_type,
        "total_recommendations": len(recommendations),
        "recommendations": recommendations
    }


@router.get("/suggest")
async def search_suggestions(
    q: str = Query(..., min_length=2),
    limit: int = Query(10, le=20),
    db: AsyncSession = Depends(get_db)
):
    """
    검색어 자동완성/제안
    """
    from sqlalchemy import select, func
    from app.models.law import Law

    # 검색어를 포함하는 법률명/조항 제안
    query = select(Law.law_name).where(
        Law.law_name.ilike(f"%{q}%")
    ).distinct().limit(limit)

    result = await db.execute(query)
    suggestions = [row[0] for row in result.all()]

    # 키워드 기반 제안 추가
    keyword_suggestions = [
        "계약서 작성",
        "근로계약",
        "임대차계약",
        "손해배상",
        "개인정보보호",
        "저작권",
        "상표권",
        "특허",
        "부동산 거래",
        "이혼 소송"
    ]

    for keyword in keyword_suggestions:
        if q.lower() in keyword.lower() and keyword not in suggestions:
            suggestions.append(keyword)
            if len(suggestions) >= limit:
                break

    return {
        "query": q,
        "suggestions": suggestions[:limit]
    }


@router.get("/popular")
async def popular_searches(
    limit: int = Query(10, le=20),
    db: AsyncSession = Depends(get_db)
):
    """
    인기 검색어
    """
    # 실제로는 검색 로그를 기반으로 집계
    # 여기서는 예시 데이터 반환
    popular_terms = [
        {"term": "근로계약서", "count": 1523},
        {"term": "임대차계약", "count": 1342},
        {"term": "개인정보보호법", "count": 987},
        {"term": "손해배상청구", "count": 876},
        {"term": "이혼소송", "count": 765},
        {"term": "저작권침해", "count": 654},
        {"term": "부동산매매", "count": 543},
        {"term": "상표등록", "count": 432},
        {"term": "특허출원", "count": 321},
        {"term": "내용증명", "count": 210}
    ]

    return {
        "popular_searches": popular_terms[:limit]
    }


@router.get("/recent")
async def recent_searches(
    current_user: User = Depends(get_current_user),
    limit: int = Query(10, le=20)
):
    """
    최근 검색 기록
    """
    # 실제로는 사용자별 검색 기록을 데이터베이스에서 조회
    # 여기서는 예시 데이터 반환
    recent = [
        {
            "query": "근로계약서 작성",
            "timestamp": "2024-01-20T10:30:00",
            "results_count": 15
        },
        {
            "query": "임대차보호법",
            "timestamp": "2024-01-19T15:20:00",
            "results_count": 23
        }
    ]

    return {
        "user_id": current_user.id,
        "recent_searches": recent[:limit]
    }


@router.delete("/history")
async def clear_search_history(
    current_user: User = Depends(get_current_user)
):
    """
    검색 기록 삭제
    """
    # 실제로는 데이터베이스에서 사용자 검색 기록 삭제
    # 여기서는 성공 메시지만 반환
    return {
        "message": "Search history cleared successfully",
        "user_id": current_user.id
    }


@router.post("/advanced")
async def advanced_search(
    query: str,
    law_types: Optional[List[str]] = Query(None),
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    court_types: Optional[List[str]] = Query(None),
    include_interpretations: bool = Query(True),
    include_cases: bool = Query(True),
    current_user: User = Depends(get_current_user)
):
    """
    고급 검색

    상세한 필터 옵션을 사용한 검색
    """
    search_engine = LegalSearchEngine()

    filters = {}
    if law_types:
        filters['law_types'] = law_types
    if date_from:
        filters['date_from'] = date_from
    if date_to:
        filters['date_to'] = date_to
    if court_types:
        filters['court_types'] = court_types

    # 검색 타입 결정
    search_types = []
    if include_interpretations:
        search_types.append('interpretations')
    if include_cases:
        search_types.append('cases')
    search_types.append('laws')  # 항상 법률은 포함

    # 각 타입별로 검색
    all_results = {}
    for search_type in search_types:
        results = await search_engine.hybrid_search(
            query=query,
            search_type=search_type,
            filters=filters
        )
        all_results.update(results)

    return {
        "query": query,
        "filters": filters,
        "results": all_results,
        "total_results": sum(len(v) for v in all_results.values())
    }