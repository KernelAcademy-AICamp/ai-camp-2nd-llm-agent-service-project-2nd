"""
L-work Demo API

테스트용 API 엔드포인트 - 실제 AI Worker 연동
- 인물 추출 (PersonExtractor)
- 관계 추론 (RelationshipInferrer)
- 재산분할 예측 (ImpactAnalyzer)

이 파일은 L-work 테스트 전용입니다.
P-work/H-work와 독립적으로 작동합니다.
"""

import sys
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel

from fastapi import APIRouter, HTTPException

# ai_worker 경로 추가
AI_WORKER_PATH = Path(__file__).parent.parent.parent.parent.parent / "ai_worker"
if str(AI_WORKER_PATH) not in sys.path:
    sys.path.insert(0, str(AI_WORKER_PATH))

print("DEBUG: Loading l_demo module...")
router = APIRouter(prefix="/l-demo", tags=["L-Demo"])


# =============================================================================
# Request/Response 모델
# =============================================================================

class TextInput(BaseModel):
    text: str

class EvidenceInput(BaseModel):
    evidences: List[dict]
    case_id: Optional[str] = "demo-case"


# =============================================================================
# Health Check
# =============================================================================

@router.get("/health")
async def health_check():
    """L-Demo API 상태 확인"""
    # AI Worker 모듈 로드 테스트
    modules_status = {}

    try:
        from src.analysis.person_extractor import PersonExtractor
        modules_status["person_extractor"] = "ok"
    except Exception as e:
        modules_status["person_extractor"] = str(e)

    try:
        from src.analysis.relationship_inferrer import RelationshipInferrer
        modules_status["relationship_inferrer"] = "ok"
    except Exception as e:
        modules_status["relationship_inferrer"] = str(e)

    try:
        from src.analysis.impact_analyzer import ImpactAnalyzer
        modules_status["impact_analyzer"] = "ok"
    except Exception as e:
        modules_status["impact_analyzer"] = str(e)

    all_ok = all(v == "ok" for v in modules_status.values())

    return {
        "status": "ok" if all_ok else "partial",
        "module": "L-work Demo",
        "ai_worker_path": str(AI_WORKER_PATH),
        "modules": modules_status
    }


# =============================================================================
# 인물 추출 API
# =============================================================================

@router.post("/analyze/persons")
async def analyze_persons(input_data: TextInput):
    """
    텍스트에서 인물 추출

    실제 PersonExtractor 사용
    """
    try:
        from src.analysis.person_extractor import PersonExtractor

        extractor = PersonExtractor()
        result = extractor.extract(input_data.text)

        return {
            "status": "success",
            "input_length": len(input_data.text),
            "result": {
                "persons": [p.to_dict() for p in result.persons],
                "total_mentions": result.total_mentions,
                "unique_names": result.unique_names,
                "role_counts": result.role_counts
            }
        }
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"AI Worker import error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {e}")


# =============================================================================
# 관계 추론 API
# =============================================================================

@router.post("/analyze/relationships")
async def analyze_relationships(input_data: TextInput):
    """
    인물 간 관계 추론 및 그래프 생성

    실제 RelationshipInferrer 사용
    """
    try:
        from src.analysis.relationship_inferrer import RelationshipInferrer

        inferrer = RelationshipInferrer()
        graph = inferrer.build_graph(input_data.text, case_id="demo")

        return {
            "status": "success",
            "input_length": len(input_data.text),
            "result": graph.to_dict()
        }
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"AI Worker import error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {e}")


# =============================================================================
# 재산분할 영향도 분석 API
# =============================================================================

@router.post("/analyze/impact")
async def analyze_impact(input_data: EvidenceInput):
    """
    재산분할 영향도 분석

    실제 ImpactAnalyzer 사용

    예시 입력:
    {
        "evidences": [
            {"evidence_id": "ev1", "evidence_type": "chat_log", "fault_types": ["adultery"]},
            {"evidence_id": "ev2", "evidence_type": "photo", "fault_types": ["violence"]}
        ],
        "case_id": "test-001"
    }
    """
    try:
        from src.analysis.impact_analyzer import ImpactAnalyzer

        analyzer = ImpactAnalyzer(case_id=input_data.case_id)
        prediction = analyzer.analyze(input_data.evidences)

        return {
            "status": "success",
            "case_id": input_data.case_id,
            "result": {
                "plaintiff_ratio": prediction.plaintiff_ratio,
                "defendant_ratio": prediction.defendant_ratio,
                "confidence_level": prediction.confidence_level,
                "evidence_impacts": [
                    {
                        "evidence_id": ei.evidence_id,
                        "evidence_type": ei.evidence_type,
                        "impact_type": ei.impact_type,
                        "impact_percent": ei.impact_percent,
                        "direction": ei.direction.value,
                        "reason": ei.reason
                    }
                    for ei in prediction.evidence_impacts
                ],
                "similar_cases": [
                    {
                        "case_ref": sc.case_ref,
                        "similarity_score": sc.similarity_score,
                        "division_ratio": sc.division_ratio
                    }
                    for sc in prediction.similar_cases
                ]
            }
        }
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"AI Worker import error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {e}")


# =============================================================================
# 날짜 추출 API
# =============================================================================

@router.post("/analyze/dates")
async def analyze_dates(input_data: TextInput):
    """
    텍스트에서 날짜 추출

    실제 DateExtractor 사용
    """
    try:
        from src.utils.date_extractor import extract_dates_from_text

        dates = extract_dates_from_text(input_data.text)

        return {
            "status": "success",
            "input_length": len(input_data.text),
            "result": {
                "dates": [
                    {
                        "original": d.original,
                        "datetime": d.datetime.isoformat() if d.datetime else None,
                        "confidence": d.confidence
                    }
                    for d in dates
                ]
            }
        }
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"AI Worker import error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {e}")


# =============================================================================
# 이벤트 요약 API
# =============================================================================

@router.post("/analyze/summarize")
async def analyze_summarize(input_data: TextInput, fault_types: Optional[List[str]] = None):
    """
    이벤트 한 줄 요약 생성

    실제 EventSummarizer 사용
    """
    try:
        from src.analysis.event_summarizer import EventSummarizer

        summarizer = EventSummarizer()
        summary = summarizer.summarize(
            content=input_data.text,
            fault_types=fault_types
        )

        return {
            "status": "success",
            "result": summary.to_dict()
        }
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"AI Worker import error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {e}")
