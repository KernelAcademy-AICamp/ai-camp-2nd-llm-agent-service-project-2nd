"""
LSSP v2.10 Keypoint Pipeline API

규칙 기반 쟁점 추출 및 후보 관리
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.db.session import get_db
from app.db.models.lssp import (
    KeypointRule, KeypointExtractionRun, KeypointCandidate,
    KeypointCandidateLink, Keypoint, KeypointGroundLink
)
from app.core.dependencies import get_current_user
from app.db.models import User

router = APIRouter(prefix="/pipeline", tags=["LSSP - Pipeline v2.10"])


# ============================================
# Schemas
# ============================================

class RuleResponse(BaseModel):
    rule_id: int
    version: str
    evidence_type: str
    kind: str
    name: str
    pattern: str
    flags: str
    ground_tags: List[str]
    base_confidence: float
    base_materiality: int
    is_enabled: bool

    class Config:
        from_attributes = True


class ExtractionRequest(BaseModel):
    """추출 요청"""
    mode: str = "rule_based"  # rule_based, ai_hybrid
    evidence_type: Optional[str] = None  # 필터: CHAT_EXPORT, MEDICAL_RECORD, etc.
    text_content: Optional[str] = None  # 직접 텍스트 제공 시


class ExtractionRunResponse(BaseModel):
    run_id: int
    case_id: str
    evidence_id: str
    extractor: str
    version: str
    status: str
    started_at: datetime
    finished_at: Optional[datetime]
    candidate_count: int
    error_message: Optional[str]

    class Config:
        from_attributes = True


class CandidateResponse(BaseModel):
    candidate_id: int
    case_id: str
    evidence_id: str
    extract_id: Optional[str]
    run_id: Optional[int]
    rule_id: Optional[int]
    kind: str
    content: str
    value: dict
    ground_tags: List[str]
    confidence: float
    materiality: int
    source_span: dict
    status: str
    reviewer_id: Optional[str]
    reviewed_at: Optional[datetime]
    rejection_reason: Optional[str]
    created_at: datetime
    # Additional
    rule_name: Optional[str] = None

    class Config:
        from_attributes = True


class CandidateUpdateRequest(BaseModel):
    """후보 수정/상태 변경"""
    status: Optional[str] = None  # CANDIDATE, ACCEPTED, REJECTED
    content: Optional[str] = None
    kind: Optional[str] = None
    ground_tags: Optional[List[str]] = None
    rejection_reason: Optional[str] = None


class PromoteRequest(BaseModel):
    """정식 쟁점 승격 요청"""
    candidate_ids: List[int]
    merge_similar: bool = False  # 유사 후보 자동 병합


class PromoteResponse(BaseModel):
    """승격 결과"""
    promoted_count: int
    keypoint_ids: List[str]
    merged_groups: List[int] = []


# ============================================
# Rules Endpoints
# ============================================

@router.get("/rules", response_model=List[RuleResponse])
async def list_rules(
    evidence_type: Optional[str] = None,
    kind: Optional[str] = None,
    enabled_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    추출 규칙 목록 조회
    """
    query = db.query(KeypointRule)
    
    if evidence_type:
        query = query.filter(KeypointRule.evidence_type == evidence_type.upper())
    if kind:
        query = query.filter(KeypointRule.kind == kind.upper())
    if enabled_only:
        query = query.filter(KeypointRule.is_enabled.is_(True))
    
    return query.order_by(KeypointRule.evidence_type, KeypointRule.kind).all()


# ============================================
# Extraction Endpoints
# ============================================

@router.post(
    "/cases/{case_id}/evidences/{evidence_id}/extract",
    response_model=ExtractionRunResponse,
    status_code=status.HTTP_201_CREATED
)
async def extract_keypoint_candidates(
    case_id: str,
    evidence_id: str,
    request: ExtractionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    증거에서 쟁점 후보 추출 (규칙 기반)
    """
    import re
    
    # 1. 추출 실행 로그 생성
    run = KeypointExtractionRun(
        case_id=case_id,
        evidence_id=evidence_id,
        extractor=request.mode,
        status="RUNNING",
    )
    db.add(run)
    db.flush()
    
    try:
        # 2. Get text content
        text_content = request.text_content or ""
        
        # 3. 규칙 조회
        rule_query = db.query(KeypointRule).filter(KeypointRule.is_enabled.is_(True))
        if request.evidence_type:
            rule_query = rule_query.filter(
                KeypointRule.evidence_type == request.evidence_type.upper()
            )
        rules = rule_query.all()
        
        # 4. 규칙 적용 & 후보 생성
        candidates_created = 0
        
        for rule in rules:
            try:
                flags = 0
                if "i" in (rule.flags or ""):
                    flags |= re.IGNORECASE
                
                pattern = re.compile(rule.pattern, flags)
                
                for match in pattern.finditer(text_content):
                    candidate = KeypointCandidate(
                        case_id=case_id,
                        evidence_id=evidence_id,
                        run_id=run.run_id,
                        rule_id=rule.rule_id,
                        kind=rule.kind,
                        content=match.group(0),
                        value={"match": match.group(0)},
                        ground_tags=rule.ground_tags or [],
                        confidence=rule.base_confidence,
                        materiality=rule.base_materiality,
                        source_span={
                            "start": match.start(),
                            "end": match.end(),
                        },
                        status="CANDIDATE",
                    )
                    db.add(candidate)
                    candidates_created += 1
                    
            except re.error:
                # 잘못된 정규식 건너뛰기
                continue
        
        # 5. 완료 처리
        run.status = "DONE"
        run.finished_at = datetime.utcnow()
        run.candidate_count = candidates_created
        
        db.commit()
        db.refresh(run)
        
        return run
        
    except Exception as e:
        run.status = "ERROR"
        run.finished_at = datetime.utcnow()
        run.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cases/{case_id}/extraction-runs", response_model=List[ExtractionRunResponse])
async def list_extraction_runs(
    case_id: str,
    evidence_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    추출 실행 이력 조회
    """
    query = db.query(KeypointExtractionRun).filter(
        KeypointExtractionRun.case_id == case_id
    )
    
    if evidence_id:
        query = query.filter(KeypointExtractionRun.evidence_id == evidence_id)
    if status:
        query = query.filter(KeypointExtractionRun.status == status.upper())
    
    return query.order_by(KeypointExtractionRun.started_at.desc()).limit(limit).all()


# ============================================
# Candidate Endpoints
# ============================================

@router.get("/cases/{case_id}/candidates", response_model=List[CandidateResponse])
async def list_candidates(
    case_id: str,
    evidence_id: Optional[str] = None,
    status: Optional[str] = Query(None, description="CANDIDATE, ACCEPTED, REJECTED, MERGED"),
    kind: Optional[str] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    쟁점 후보 목록 조회
    """
    query = db.query(KeypointCandidate).filter(KeypointCandidate.case_id == case_id)
    
    if evidence_id:
        query = query.filter(KeypointCandidate.evidence_id == evidence_id)
    if status:
        query = query.filter(KeypointCandidate.status == status.upper())
    if kind:
        query = query.filter(KeypointCandidate.kind == kind.upper())
    
    candidates = query.order_by(
        KeypointCandidate.materiality.desc(),
        KeypointCandidate.confidence.desc()
    ).offset(offset).limit(limit).all()
    
    # Rule name 추가
    result = []
    for c in candidates:
        resp = CandidateResponse(
            candidate_id=c.candidate_id,
            case_id=c.case_id,
            evidence_id=c.evidence_id,
            extract_id=c.extract_id,
            run_id=c.run_id,
            rule_id=c.rule_id,
            kind=c.kind,
            content=c.content,
            value=c.value,
            ground_tags=c.ground_tags or [],
            confidence=float(c.confidence),
            materiality=c.materiality,
            source_span=c.source_span,
            status=c.status,
            reviewer_id=c.reviewer_id,
            reviewed_at=c.reviewed_at,
            rejection_reason=c.rejection_reason,
            created_at=c.created_at,
            rule_name=c.rule.name if c.rule else None,
        )
        result.append(resp)
    
    return result


@router.patch("/cases/{case_id}/candidates/{candidate_id}", response_model=CandidateResponse)
async def update_candidate(
    case_id: str,
    candidate_id: int,
    request: CandidateUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    후보 수정/상태 변경 (수락/거절)
    """
    candidate = db.query(KeypointCandidate).filter(
        KeypointCandidate.candidate_id == candidate_id,
        KeypointCandidate.case_id == case_id,
    ).first()
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # 업데이트
    update_data = request.model_dump(exclude_unset=True)
    
    if "status" in update_data:
        candidate.reviewer_id = current_user.id
        candidate.reviewed_at = datetime.utcnow()
    
    for field, value in update_data.items():
        setattr(candidate, field, value)
    
    db.commit()
    db.refresh(candidate)
    
    return CandidateResponse(
        candidate_id=candidate.candidate_id,
        case_id=candidate.case_id,
        evidence_id=candidate.evidence_id,
        extract_id=candidate.extract_id,
        run_id=candidate.run_id,
        rule_id=candidate.rule_id,
        kind=candidate.kind,
        content=candidate.content,
        value=candidate.value,
        ground_tags=candidate.ground_tags or [],
        confidence=float(candidate.confidence),
        materiality=candidate.materiality,
        source_span=candidate.source_span,
        status=candidate.status,
        reviewer_id=candidate.reviewer_id,
        reviewed_at=candidate.reviewed_at,
        rejection_reason=candidate.rejection_reason,
        created_at=candidate.created_at,
        rule_name=candidate.rule.name if candidate.rule else None,
    )


# ============================================
# Promote Endpoints
# ============================================

@router.post("/cases/{case_id}/promote", response_model=PromoteResponse)
async def promote_candidates(
    case_id: str,
    request: PromoteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    수락된 후보를 정식 쟁점으로 승격
    """
    import uuid
    
    keypoint_ids = []
    merged_groups = []
    
    # 후보 조회
    candidates = db.query(KeypointCandidate).filter(
        KeypointCandidate.candidate_id.in_(request.candidate_ids),
        KeypointCandidate.case_id == case_id,
        KeypointCandidate.status == "ACCEPTED",
    ).all()
    
    if not candidates:
        raise HTTPException(status_code=400, detail="No accepted candidates found")
    
    # TODO: merge_similar 로직 (유사도 기반 병합)
    # 현재는 개별 승격만 지원
    
    for candidate in candidates:
        # 정식 쟁점 생성
        keypoint = Keypoint(
            id=str(uuid.uuid4()),
            case_id=case_id,
            title=candidate.content[:200],
            statement=candidate.content,
            type_code=candidate.kind,
            status="READY",
            risk_flags=[],
            actors=[],
            created_by=current_user.id,
        )
        db.add(keypoint)
        db.flush()
        
        # Ground 연결
        for tag in (candidate.ground_tags or []):
            db.add(KeypointGroundLink(
                keypoint_id=keypoint.id,
                ground_code=tag.upper()
            ))
        
        # 후보 연결
        db.add(KeypointCandidateLink(
            candidate_id=candidate.candidate_id,
            keypoint_id=keypoint.id,
        ))
        
        # 후보 상태 변경
        candidate.status = "MERGED"
        
        keypoint_ids.append(keypoint.id)
    
    db.commit()
    
    return PromoteResponse(
        promoted_count=len(keypoint_ids),
        keypoint_ids=keypoint_ids,
        merged_groups=merged_groups,
    )


# ============================================
# Statistics Endpoint
# ============================================

class PipelineStats(BaseModel):
    total_runs: int
    total_candidates: int
    pending_candidates: int
    accepted_candidates: int
    rejected_candidates: int
    promoted_keypoints: int


@router.get("/cases/{case_id}/stats", response_model=PipelineStats)
async def get_pipeline_stats(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    파이프라인 통계
    """
    from sqlalchemy import func
    
    total_runs = db.query(func.count(KeypointExtractionRun.run_id)).filter(
        KeypointExtractionRun.case_id == case_id
    ).scalar() or 0
    
    total_candidates = db.query(func.count(KeypointCandidate.candidate_id)).filter(
        KeypointCandidate.case_id == case_id
    ).scalar() or 0
    
    pending = db.query(func.count(KeypointCandidate.candidate_id)).filter(
        KeypointCandidate.case_id == case_id,
        KeypointCandidate.status == "CANDIDATE"
    ).scalar() or 0
    
    accepted = db.query(func.count(KeypointCandidate.candidate_id)).filter(
        KeypointCandidate.case_id == case_id,
        KeypointCandidate.status == "ACCEPTED"
    ).scalar() or 0
    
    rejected = db.query(func.count(KeypointCandidate.candidate_id)).filter(
        KeypointCandidate.case_id == case_id,
        KeypointCandidate.status == "REJECTED"
    ).scalar() or 0
    
    promoted = db.query(func.count(KeypointCandidateLink.candidate_id)).join(
        KeypointCandidate
    ).filter(
        KeypointCandidate.case_id == case_id
    ).scalar() or 0
    
    return PipelineStats(
        total_runs=total_runs,
        total_candidates=total_candidates,
        pending_candidates=pending,
        accepted_candidates=accepted,
        rejected_candidates=rejected,
        promoted_keypoints=promoted,
    )
