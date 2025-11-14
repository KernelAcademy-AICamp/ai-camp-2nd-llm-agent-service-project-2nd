"""
Learning Assistant Chatbot API
학습 도우미 챗봇 백엔드 서버
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import aiofiles
from datetime import datetime

from app.config import settings
from app.services.llm_service import LLMService
from app.services.summarizer import Summarizer
from app.services.qa_engine import QAEngine
from app.services.recommender import Recommender
from app.utils.pdf_parser import PDFParser
from app.utils.text_processor import TextProcessor

# FastAPI 앱 초기화
app = FastAPI(
    title="Learning Assistant API",
    description="AI 기반 학습 도우미 챗봇 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 서비스 초기화
llm_service = LLMService()
summarizer = Summarizer(llm_service)
qa_engine = QAEngine(llm_service)
recommender = Recommender()
pdf_parser = PDFParser()
text_processor = TextProcessor()

# 세션 저장소 (프로덕션에서는 Redis 사용 권장)
sessions: Dict[str, Dict] = {}


# Pydantic 모델
class QuestionRequest(BaseModel):
    question: str
    context: Optional[str] = None
    session_id: Optional[str] = None
    use_history: bool = True


class SummaryRequest(BaseModel):
    text: str
    max_lines: int = 5
    language: str = "korean"


class RecommendationRequest(BaseModel):
    topic: str
    level: str = "beginner"  # beginner, intermediate, advanced
    session_id: Optional[str] = None


class ChatMessage(BaseModel):
    role: str  # user, assistant
    content: str
    timestamp: Optional[datetime] = None


# 엔드포인트
@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "Learning Assistant API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/docs",
            "/upload",
            "/summarize",
            "/ask",
            "/recommend",
            "/chat",
            "/session/{session_id}"
        ]
    }


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    파일 업로드 및 텍스트 추출
    - PDF, TXT 파일 지원
    - 텍스트 추출 후 세션에 저장
    """
    try:
        # 파일 확장자 검증
        if not file.filename.endswith(('.pdf', '.txt', '.md')):
            raise HTTPException(
                status_code=400,
                detail="Supported file types: PDF, TXT, MD"
            )

        # 파일 저장 디렉토리 확인
        upload_dir = "data/uploads"
        os.makedirs(upload_dir, exist_ok=True)

        # 파일 저장
        file_path = os.path.join(upload_dir, file.filename)
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        # 텍스트 추출
        if file.filename.endswith('.pdf'):
            extracted_text = await pdf_parser.extract_text(file_path)
        else:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                extracted_text = await f.read()

        # 텍스트 처리
        processed_text = text_processor.preprocess(extracted_text)

        # 세션 ID 생성
        session_id = f"session_{datetime.now().timestamp()}"
        sessions[session_id] = {
            "filename": file.filename,
            "original_text": extracted_text,
            "processed_text": processed_text,
            "chat_history": [],
            "created_at": datetime.now()
        }

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "filename": file.filename,
                "text_length": len(extracted_text),
                "preview": extracted_text[:500],
                "session_id": session_id,
                "message": "File uploaded and processed successfully"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/summarize")
async def summarize_text(request: SummaryRequest):
    """
    텍스트 요약 생성
    - 다양한 길이의 요약 지원
    - 한국어/영어 지원
    """
    try:
        # 텍스트 전처리
        processed_text = text_processor.preprocess(request.text)

        # 요약 생성
        summary = await summarizer.generate_summary(
            text=processed_text,
            max_lines=request.max_lines,
            language=request.language
        )

        # 키워드 추출
        keywords = text_processor.extract_keywords(processed_text)

        return {
            "success": True,
            "summary": summary,
            "keywords": keywords,
            "original_length": len(request.text),
            "summary_length": len(summary)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask")
async def ask_question(request: QuestionRequest):
    """
    질문에 대한 답변 생성
    - 컨텍스트 기반 답변
    - 대화 히스토리 유지
    - 신뢰도 점수 제공
    """
    try:
        # 세션 확인
        session_data = None
        if request.session_id and request.session_id in sessions:
            session_data = sessions[request.session_id]
            context = session_data.get("processed_text", request.context)
            chat_history = session_data.get("chat_history", [])
        else:
            context = request.context or ""
            chat_history = []

        # 답변 생성
        result = await qa_engine.answer_question(
            question=request.question,
            context=context,
            chat_history=chat_history if request.use_history else []
        )

        # 대화 기록 업데이트
        if session_data:
            session_data["chat_history"].append({
                "role": "user",
                "content": request.question,
                "timestamp": datetime.now()
            })
            session_data["chat_history"].append({
                "role": "assistant",
                "content": result["answer"],
                "timestamp": datetime.now()
            })

        return {
            "success": True,
            "answer": result["answer"],
            "confidence": result["confidence"],
            "source": result["source"],
            "related_topics": result.get("related_topics", [])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/recommend")
async def get_recommendations(request: RecommendationRequest):
    """
    학습 자료 추천
    - 난이도별 자료 추천
    - 관련 주제 제안
    - 학습 경로 제공
    """
    try:
        # 세션 데이터 확인
        context = ""
        if request.session_id and request.session_id in sessions:
            session_data = sessions[request.session_id]
            context = session_data.get("processed_text", "")

        # 추천 생성
        recommendations = await recommender.get_recommendations(
            topic=request.topic,
            level=request.level,
            context=context
        )

        return {
            "success": True,
            "recommendations": recommendations,
            "learning_path": recommender.generate_learning_path(
                request.topic,
                request.level
            )
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
async def chat_conversation(
    message: str,
    session_id: Optional[str] = None
):
    """
    대화형 채팅 인터페이스
    - 컨텍스트 유지 대화
    - 스트리밍 응답 지원
    """
    try:
        # 세션 확인 또는 생성
        if not session_id:
            session_id = f"chat_{datetime.now().timestamp()}"
            sessions[session_id] = {
                "chat_history": [],
                "created_at": datetime.now()
            }

        session_data = sessions[session_id]

        # LLM으로 응답 생성
        response = await llm_service.chat(
            message=message,
            chat_history=session_data.get("chat_history", [])
        )

        # 대화 기록 업데이트
        session_data["chat_history"].append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now()
        })
        session_data["chat_history"].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now()
        })

        return {
            "success": True,
            "response": response,
            "session_id": session_id,
            "message_count": len(session_data["chat_history"])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """세션 정보 조회"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session_data = sessions[session_id]
    return {
        "session_id": session_id,
        "filename": session_data.get("filename"),
        "chat_history_length": len(session_data.get("chat_history", [])),
        "created_at": session_data.get("created_at")
    }


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """세션 삭제"""
    if session_id in sessions:
        del sessions[session_id]
        return {"success": True, "message": "Session deleted"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "service": "Learning Assistant API",
        "timestamp": datetime.now(),
        "active_sessions": len(sessions)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )