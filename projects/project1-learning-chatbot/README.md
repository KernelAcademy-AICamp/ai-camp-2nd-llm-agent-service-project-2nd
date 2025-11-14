# Project 1: 학습 도우미 챗봇 (Learning Assistant Chatbot)

## 🎯 프로젝트 개요
LLM API를 활용하여 학습자 맞춤형 지원을 제공하는 AI 챗봇 개발

## 📋 요구사항

### 필수 기능 (70%)
1. **문서 요약 자동화**
   - PDF/텍스트 파일 업로드
   - 5줄 이내 핵심 요약 생성
   - 챕터별 요약 지원

2. **Q&A 자동화**
   - 업로드된 자료 기반 질문 답변
   - 컨텍스트 유지 대화
   - 답변 신뢰도 표시

3. **학습 자료 추천**
   - 학습 진도 기반 추천
   - 난이도별 자료 분류
   - 관련 자료 링크 제공

### 선택 기능 (30%)
1. **퀴즈 자동 생성**
   - 학습 내용 기반 문제 생성
   - 객관식/주관식 지원
   - 정답 해설 제공

2. **학습 진도 관리**
   - 일일/주간 학습 목표 설정
   - 진도율 시각화
   - 학습 리마인더

3. **멀티모달 지원**
   - 이미지 설명 생성
   - 다이어그램 해석
   - 음성 입출력

## 🛠️ 기술 스택

### Backend
```python
# requirements.txt
fastapi==0.104.1
uvicorn==0.24.0
python-dotenv==1.0.0
openai==1.3.0
anthropic==0.7.0
langchain==0.0.350
pydantic==2.5.0
python-multipart==0.0.6
PyPDF2==3.0.0
```

### Frontend
```python
# Streamlit UI
streamlit==1.28.0
streamlit-chat==0.1.1
plotly==5.18.0
```

## 📁 프로젝트 구조
```
project1-learning-chatbot/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI 앱
│   │   ├── config.py         # 설정 관리
│   │   ├── models/           # 데이터 모델
│   │   ├── services/         # 비즈니스 로직
│   │   │   ├── llm_service.py
│   │   │   ├── summarizer.py
│   │   │   ├── qa_engine.py
│   │   │   └── recommender.py
│   │   └── utils/            # 유틸리티
│   │       ├── pdf_parser.py
│   │       └── text_processor.py
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── app.py                # Streamlit 메인
│   ├── pages/
│   │   ├── chat.py
│   │   ├── upload.py
│   │   └── dashboard.py
│   └── components/
│       ├── chat_interface.py
│       └── file_uploader.py
├── data/
│   ├── uploads/              # 업로드 파일
│   └── processed/            # 처리된 데이터
├── docker-compose.yml
└── README.md
```

## 💻 구현 예제

### 1. LLM 서비스 (backend/app/services/llm_service.py)
```python
from openai import OpenAI
from typing import List, Dict
import os

class LLMService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def generate_summary(self, text: str, max_lines: int = 5) -> str:
        """텍스트 요약 생성"""
        prompt = f"다음 텍스트를 {max_lines}줄 이내로 요약해주세요:\n\n{text}"

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "당신은 학습 도우미 AI입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )

        return response.choices[0].message.content

    async def answer_question(self, context: str, question: str) -> Dict:
        """컨텍스트 기반 질문 답변"""
        prompt = f"""
        Context: {context}

        Question: {question}

        Please provide a detailed answer based on the context.
        If the answer is not in the context, say so.
        """

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful learning assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )

        answer = response.choices[0].message.content

        # 신뢰도 계산 (간단한 예시)
        confidence = self._calculate_confidence(context, answer)

        return {
            "answer": answer,
            "confidence": confidence,
            "source": "context" if confidence > 0.7 else "general knowledge"
        }

    def _calculate_confidence(self, context: str, answer: str) -> float:
        """답변 신뢰도 계산"""
        # 실제로는 더 복잡한 로직 필요
        context_words = set(context.lower().split())
        answer_words = set(answer.lower().split())
        overlap = len(context_words & answer_words)
        return min(overlap / 10, 1.0)  # 간단한 예시
```

### 2. FastAPI 엔드포인트 (backend/app/main.py)
```python
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import aiofiles
import os

from app.services.llm_service import LLMService
from app.utils.pdf_parser import PDFParser

app = FastAPI(title="Learning Assistant API")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 서비스 초기화
llm_service = LLMService()
pdf_parser = PDFParser()

class QuestionRequest(BaseModel):
    question: str
    context: Optional[str] = None
    session_id: Optional[str] = None

class SummaryRequest(BaseModel):
    text: str
    max_lines: int = 5

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """파일 업로드 및 처리"""
    if not file.filename.endswith(('.pdf', '.txt')):
        raise HTTPException(400, "Only PDF and TXT files are supported")

    # 파일 저장
    file_path = f"data/uploads/{file.filename}"
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)

    # 텍스트 추출
    if file.filename.endswith('.pdf'):
        text = pdf_parser.extract_text(file_path)
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

    return {
        "filename": file.filename,
        "text_length": len(text),
        "preview": text[:500],
        "file_id": os.path.basename(file_path)
    }

@app.post("/summarize")
async def summarize(request: SummaryRequest):
    """텍스트 요약 생성"""
    summary = await llm_service.generate_summary(
        request.text,
        request.max_lines
    )
    return {"summary": summary}

@app.post("/ask")
async def ask_question(request: QuestionRequest):
    """질문 답변"""
    result = await llm_service.answer_question(
        request.context or "",
        request.question
    )
    return result

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {"status": "healthy", "service": "Learning Assistant API"}
```

### 3. Streamlit UI (frontend/app.py)
```python
import streamlit as st
import requests
import json
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="학습 도우미 챗봇",
    page_icon="🤖",
    layout="wide"
)

# API 엔드포인트
API_BASE = "http://localhost:8000"

# 세션 상태 초기화
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'context' not in st.session_state:
    st.session_state.context = ""

# 사이드바
with st.sidebar:
    st.title("📚 학습 도우미 챗봇")

    # 파일 업로드
    uploaded_file = st.file_uploader(
        "학습 자료 업로드",
        type=['pdf', 'txt']
    )

    if uploaded_file:
        with st.spinner("파일 처리 중..."):
            files = {'file': uploaded_file}
            response = requests.post(f"{API_BASE}/upload", files=files)
            if response.status_code == 200:
                data = response.json()
                st.success(f"✅ {data['filename']} 업로드 완료!")
                st.session_state.context = data['preview']

    # 기능 선택
    mode = st.selectbox(
        "모드 선택",
        ["💬 채팅", "📝 요약", "❓ Q&A", "📊 대시보드"]
    )

# 메인 영역
st.title("🤖 AI 학습 도우미")

if mode == "💬 채팅":
    # 채팅 인터페이스
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # 입력창
    if prompt := st.chat_input("질문을 입력하세요..."):
        # 사용자 메시지 추가
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # API 호출
        with st.chat_message("assistant"):
            with st.spinner("생각 중..."):
                response = requests.post(
                    f"{API_BASE}/ask",
                    json={
                        "question": prompt,
                        "context": st.session_state.context
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    answer = data['answer']
                    confidence = data['confidence']

                    st.write(answer)
                    st.caption(f"신뢰도: {confidence:.1%}")

                    # 응답 저장
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer
                    })

elif mode == "📝 요약":
    st.subheader("텍스트 요약 생성")

    text_input = st.text_area(
        "요약할 텍스트를 입력하세요",
        height=300,
        value=st.session_state.context
    )

    col1, col2 = st.columns([3, 1])
    with col2:
        max_lines = st.number_input("최대 줄 수", 1, 10, 5)

    if st.button("요약 생성", type="primary"):
        with st.spinner("요약 생성 중..."):
            response = requests.post(
                f"{API_BASE}/summarize",
                json={
                    "text": text_input,
                    "max_lines": max_lines
                }
            )
            if response.status_code == 200:
                summary = response.json()['summary']
                st.success("✅ 요약 완료!")
                st.info(summary)

elif mode == "❓ Q&A":
    st.subheader("질문 & 답변")

    # 컨텍스트 표시
    with st.expander("현재 컨텍스트", expanded=False):
        st.text(st.session_state.context[:1000])

    # 질문 입력
    question = st.text_input("질문을 입력하세요")

    if st.button("답변 받기", type="primary"):
        with st.spinner("답변 생성 중..."):
            response = requests.post(
                f"{API_BASE}/ask",
                json={
                    "question": question,
                    "context": st.session_state.context
                }
            )
            if response.status_code == 200:
                data = response.json()
                st.success("답변:")
                st.write(data['answer'])

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("신뢰도", f"{data['confidence']:.1%}")
                with col2:
                    st.metric("소스", data['source'])

elif mode == "📊 대시보드":
    st.subheader("학습 대시보드")

    # 통계 표시
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("총 질문 수", len(st.session_state.messages) // 2)
    with col2:
        st.metric("업로드 파일", "1" if st.session_state.context else "0")
    with col3:
        st.metric("세션 시간", "15분")

    # 대화 기록
    st.subheader("대화 기록")
    for msg in st.session_state.messages:
        st.text(f"[{msg['role']}]: {msg['content'][:100]}...")
```

## 🚀 실행 방법

### 1. 환경 설정
```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt

# 환경변수 설정
cp .env.example .env
# OPENAI_API_KEY 설정
```

### 2. 백엔드 실행
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 3. 프론트엔드 실행
```bash
cd frontend
streamlit run app.py --server.port 8501
```

### 4. Docker 실행 (선택)
```bash
docker-compose up -d
```

## 📊 평가 기준

### 기능 구현 (40%)
- [ ] 파일 업로드 및 처리
- [ ] 텍스트 요약 생성
- [ ] Q&A 기능
- [ ] 학습 자료 추천

### 코드 품질 (30%)
- [ ] 클린 코드
- [ ] 에러 처리
- [ ] 테스트 코드
- [ ] 문서화

### UI/UX (20%)
- [ ] 직관적 인터페이스
- [ ] 반응형 디자인
- [ ] 로딩 상태 표시
- [ ] 에러 메시지

### 창의성 (10%)
- [ ] 추가 기능
- [ ] 성능 최적화
- [ ] 독창적 아이디어

## 📚 참고 자료
- [OpenAI API 문서](https://platform.openai.com/docs)
- [LangChain 문서](https://python.langchain.com/)
- [Streamlit 문서](https://docs.streamlit.io/)
- [FastAPI 문서](https://fastapi.tiangolo.com/)