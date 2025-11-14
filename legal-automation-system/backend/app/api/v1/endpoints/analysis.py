"""
분석 및 검토 API 엔드포인트
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_db
from app.models.document import Document
from app.services.risk.risk_analyzer import DocumentRiskAnalyzer, RiskMitigator
from app.services.risk.compliance_checker import ComplianceChecker
from app.services.risk.review_system import ReviewSystem, LegalReviewer
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/risk/{document_id}")
async def analyze_risk(
    document_id: int,
    deep_analysis: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    문서 리스크 분석

    문서의 잠재적 리스크를 분석합니다:
    - 법적 준수성 리스크
    - 재무적 리스크
    - 운영 리스크
    - 계약상 리스크
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
    analysis = await analyzer.analyze_document(document, deep_analysis=deep_analysis)

    # 완화 방안 제안
    mitigator = RiskMitigator()
    mitigations = await mitigator.suggest_mitigations(analysis)

    # 결과 저장
    document.risk_level = analysis['risk_level']
    document.risk_score = analysis['risk_score']
    document.risk_analysis = analysis
    await db.commit()

    return {
        "document_id": document_id,
        "risk_analysis": analysis,
        "mitigation_strategies": mitigations
    }


@router.post("/compliance/{document_id}")
async def check_compliance(
    document_id: int,
    check_categories: Optional[List[str]] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    법률 준수성 검사

    카테고리:
    - 개인정보보호: 개인정보보호법 준수 여부
    - 전자상거래: 전자상거래법 준수 여부
    - 근로계약: 근로기준법 준수 여부
    - 부동산거래: 부동산거래신고법 준수 여부
    - 금융거래: 금융실명법 준수 여부
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

    # 준수성 검사
    checker = ComplianceChecker()
    compliance_result = await checker.check_compliance(
        document,
        check_categories=check_categories
    )

    return compliance_result


@router.post("/review/{document_id}")
async def review_document(
    document_id: int,
    review_depth: str = Query("standard", regex="^(quick|standard|thorough)$"),
    focus_areas: Optional[List[str]] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    문서 종합 검토

    검토 깊이:
    - quick: 빠른 검토 (구조, 기본 내용)
    - standard: 표준 검토 (구조, 내용, 법률)
    - thorough: 심층 검토 (전체 + 비즈니스 측면)

    포커스 영역:
    - tax: 세무 관련
    - international: 국제 거래
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
    if focus_areas:
        # 전문가 검토
        reviewer = LegalReviewer()
        review_result = await reviewer.expert_review(
            document,
            focus_areas=focus_areas
        )
    else:
        # 일반 검토
        review_system = ReviewSystem()
        review_result = await review_system.review_document(
            document,
            review_depth=review_depth
        )

    # 결과 저장
    document.legal_review = review_result.get('detailed_report', '')
    await db.commit()

    return review_result


@router.get("/statistics")
async def get_analysis_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    사용자의 문서 분석 통계
    """
    from sqlalchemy import func

    # 문서별 리스크 레벨 통계
    risk_stats_query = select(
        Document.risk_level,
        func.count(Document.id).label('count')
    ).where(
        Document.user_id == current_user.id,
        Document.risk_level.isnot(None)
    ).group_by(Document.risk_level)

    risk_stats_result = await db.execute(risk_stats_query)
    risk_stats = {row.risk_level: row.count for row in risk_stats_result}

    # 평균 리스크 점수
    avg_risk_query = select(
        func.avg(Document.risk_score).label('avg_score')
    ).where(
        Document.user_id == current_user.id,
        Document.risk_score.isnot(None)
    )

    avg_risk_result = await db.execute(avg_risk_query)
    avg_risk = avg_risk_result.scalar()

    # 총 분석 문서 수
    total_analyzed_query = select(
        func.count(Document.id).label('total')
    ).where(
        Document.user_id == current_user.id,
        Document.risk_analysis.isnot(None)
    )

    total_analyzed_result = await db.execute(total_analyzed_query)
    total_analyzed = total_analyzed_result.scalar()

    return {
        "user_id": current_user.id,
        "total_documents_analyzed": total_analyzed or 0,
        "average_risk_score": float(avg_risk) if avg_risk else 0.0,
        "risk_level_distribution": risk_stats,
        "compliance_check_count": 0,  # TODO: 실제 준수성 검사 카운트
        "review_count": 0  # TODO: 실제 검토 카운트
    }


@router.post("/compare")
async def compare_documents(
    document_ids: List[int] = Query(..., min_items=2, max_items=5),
    comparison_type: str = Query("risk", regex="^(risk|compliance|similarity)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    문서 비교 분석

    비교 타입:
    - risk: 리스크 비교
    - compliance: 준수성 비교
    - similarity: 유사도 비교
    """
    # 문서들 조회
    query = select(Document).where(
        Document.id.in_(document_ids),
        Document.user_id == current_user.id
    )
    result = await db.execute(query)
    documents = result.scalars().all()

    if len(documents) != len(document_ids):
        raise HTTPException(status_code=404, detail="Some documents not found")

    comparison_results = []

    if comparison_type == "risk":
        analyzer = DocumentRiskAnalyzer()
        for doc in documents:
            analysis = await analyzer.analyze_document(doc, deep_analysis=False)
            comparison_results.append({
                "document_id": doc.id,
                "title": doc.title,
                "risk_score": analysis['risk_score'],
                "risk_level": analysis['risk_level'],
                "top_risks": analysis['risk_factors'][:3]
            })

    elif comparison_type == "compliance":
        checker = ComplianceChecker()
        for doc in documents:
            compliance = await checker.check_compliance(doc)
            comparison_results.append({
                "document_id": doc.id,
                "title": doc.title,
                "compliance_score": compliance['compliance_score'],
                "overall_compliance": compliance['overall_compliance'],
                "violations_count": len(compliance['violations'])
            })

    elif comparison_type == "similarity":
        # 문서 유사도 비교 (간단한 구현)
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        texts = [doc.content for doc in documents]
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(texts)
        similarity_matrix = cosine_similarity(tfidf_matrix)

        for i, doc in enumerate(documents):
            similarities = []
            for j, other_doc in enumerate(documents):
                if i != j:
                    similarities.append({
                        "document_id": other_doc.id,
                        "title": other_doc.title,
                        "similarity": float(similarity_matrix[i][j])
                    })

            comparison_results.append({
                "document_id": doc.id,
                "title": doc.title,
                "similarities": sorted(similarities, key=lambda x: x['similarity'], reverse=True)
            })

    return {
        "comparison_type": comparison_type,
        "documents_compared": len(documents),
        "results": comparison_results
    }