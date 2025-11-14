"""
Learning Assistant Chatbot - Streamlit Frontend
학습 도우미 챗봇 프론트엔드
"""

import streamlit as st
import requests
import json
from datetime import datetime
import time
from typing import List, Dict, Optional
import base64
import os

# 페이지 설정
st.set_page_config(
    page_title="AI 학습 도우미 챗봇",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API 엔드포인트 설정
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

# 커스텀 CSS
st.markdown("""
    <style>
    .main {
        padding-top: 1rem;
    }
    .stButton > button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        animation: fadeIn 0.5s;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196F3;
    }
    .assistant-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    .metric-card {
        background-color: #f5f5f5;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)


def init_session_state():
    """세션 상태 초기화"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None
    if 'context' not in st.session_state:
        st.session_state.context = ""
    if 'uploaded_file_name' not in st.session_state:
        st.session_state.uploaded_file_name = None
    if 'quiz_mode' not in st.session_state:
        st.session_state.quiz_mode = False
    if 'current_quiz' not in st.session_state:
        st.session_state.current_quiz = None


def call_api(endpoint: str, method: str = "GET", data: Dict = None, files=None):
    """API 호출 헬퍼 함수"""
    url = f"{API_BASE}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            if files:
                response = requests.post(url, files=files)
            else:
                response = requests.post(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        else:
            raise ValueError(f"Unsupported method: {method}")

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API 에러: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"API 호출 실패: {str(e)}")
        return None


def upload_file(file):
    """파일 업로드 처리"""
    with st.spinner("파일 업로드 중..."):
        files = {'file': (file.name, file, file.type)}
        result = call_api("/upload", "POST", files=files)

        if result and result.get("success"):
            st.session_state.session_id = result["session_id"]
            st.session_state.context = result["preview"]
            st.session_state.uploaded_file_name = result["filename"]
            st.success(f"✅ {result['filename']} 업로드 완료!")
            st.info(f"텍스트 길이: {result['text_length']}자")
            return True
    return False


def generate_summary(text: str, max_lines: int):
    """텍스트 요약 생성"""
    with st.spinner("요약 생성 중..."):
        result = call_api("/summarize", "POST", {
            "text": text,
            "max_lines": max_lines,
            "language": "korean"
        })

        if result and result.get("success"):
            return result["summary"], result.get("keywords", [])
    return None, []


def ask_question(question: str, use_context: bool = True):
    """질문 답변 생성"""
    with st.spinner("답변 생성 중..."):
        data = {
            "question": question,
            "session_id": st.session_state.session_id if use_context else None,
            "context": st.session_state.context if use_context else None,
            "use_history": True
        }
        result = call_api("/ask", "POST", data)

        if result and result.get("success"):
            return result
    return None


def chat_interface():
    """채팅 인터페이스"""
    st.header("💬 AI 학습 도우미와 대화하기")

    # 대화 기록 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message.get("confidence"):
                st.caption(f"신뢰도: {message['confidence']:.1%}")

    # 입력창
    if prompt := st.chat_input("질문을 입력하세요..."):
        # 사용자 메시지 추가
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # 답변 생성
        result = ask_question(prompt)
        if result:
            answer = result["answer"]
            confidence = result.get("confidence", 0)

            # 어시스턴트 메시지 추가
            with st.chat_message("assistant"):
                st.write(answer)
                if confidence:
                    st.caption(f"신뢰도: {confidence:.1%} | 소스: {result.get('source', 'unknown')}")

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "confidence": confidence
            })


def summary_interface():
    """요약 인터페이스"""
    st.header("📝 텍스트 요약 생성")

    # 텍스트 입력
    text_input = st.text_area(
        "요약할 텍스트를 입력하세요",
        height=300,
        value=st.session_state.context[:2000] if st.session_state.context else "",
        placeholder="여기에 텍스트를 입력하거나 파일을 업로드하세요..."
    )

    # 옵션
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        max_lines = st.number_input("최대 줄 수", min_value=1, max_value=20, value=5)
    with col3:
        if st.button("요약 생성", type="primary", use_container_width=True):
            if text_input:
                summary, keywords = generate_summary(text_input, max_lines)
                if summary:
                    st.success("✅ 요약 생성 완료!")
                    st.info(summary)
                    if keywords:
                        st.write("**핵심 키워드:**", ", ".join(keywords))
            else:
                st.warning("요약할 텍스트를 입력해주세요.")


def qa_interface():
    """Q&A 인터페이스"""
    st.header("❓ 질문 & 답변")

    # 컨텍스트 표시
    if st.session_state.context:
        with st.expander("📄 현재 컨텍스트", expanded=False):
            st.text(st.session_state.context[:1000] + "..." if len(st.session_state.context) > 1000 else st.session_state.context)

    # 질문 입력
    col1, col2 = st.columns([4, 1])
    with col1:
        question = st.text_input("질문을 입력하세요", placeholder="무엇이 궁금하신가요?")
    with col2:
        use_context = st.checkbox("컨텍스트 사용", value=True)

    if st.button("답변 받기", type="primary", use_container_width=True):
        if question:
            result = ask_question(question, use_context)
            if result:
                st.success("✅ 답변:")
                st.write(result["answer"])

                # 메트릭 표시
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("신뢰도", f"{result.get('confidence', 0):.1%}")
                with col2:
                    st.metric("소스", result.get('source', 'unknown'))
                with col3:
                    st.metric("제공자", result.get('provider', 'openai'))
        else:
            st.warning("질문을 입력해주세요.")


def recommendations_interface():
    """학습 자료 추천"""
    st.header("📚 학습 자료 추천")

    col1, col2 = st.columns([2, 1])
    with col1:
        topic = st.text_input("학습하고 싶은 주제", placeholder="예: Python 프로그래밍, 머신러닝 기초")
    with col2:
        level = st.selectbox("난이도", ["beginner", "intermediate", "advanced"])

    if st.button("추천 받기", type="primary"):
        if topic:
            with st.spinner("추천 자료 검색 중..."):
                result = call_api("/recommend", "POST", {
                    "topic": topic,
                    "level": level,
                    "session_id": st.session_state.session_id
                })

                if result and result.get("success"):
                    st.success("✅ 추천 자료")
                    for idx, rec in enumerate(result["recommendations"], 1):
                        st.write(f"{idx}. {rec}")

                    if result.get("learning_path"):
                        st.subheader("🛤️ 학습 경로")
                        for step in result["learning_path"]:
                            st.write(f"- {step}")
        else:
            st.warning("학습 주제를 입력해주세요.")


def dashboard_interface():
    """대시보드"""
    st.header("📊 학습 대시보드")

    # 메트릭 카드
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="총 질문 수",
            value=len([m for m in st.session_state.messages if m["role"] == "user"])
        )

    with col2:
        st.metric(
            label="업로드 파일",
            value=st.session_state.uploaded_file_name or "없음"
        )

    with col3:
        avg_confidence = 0
        confidences = [m.get("confidence", 0) for m in st.session_state.messages if m.get("confidence")]
        if confidences:
            avg_confidence = sum(confidences) / len(confidences)
        st.metric(
            label="평균 신뢰도",
            value=f"{avg_confidence:.1%}"
        )

    with col4:
        st.metric(
            label="세션 ID",
            value=st.session_state.session_id[:8] + "..." if st.session_state.session_id else "없음"
        )

    # 대화 기록
    st.subheader("💬 대화 기록")
    if st.session_state.messages:
        for idx, msg in enumerate(st.session_state.messages):
            with st.container():
                col1, col2 = st.columns([1, 5])
                with col1:
                    st.write(f"**{msg['role'].title()}**")
                with col2:
                    st.write(msg['content'][:200] + "..." if len(msg['content']) > 200 else msg['content'])
                    if msg.get("confidence"):
                        st.caption(f"신뢰도: {msg['confidence']:.1%}")
    else:
        st.info("아직 대화 기록이 없습니다.")

    # 세션 관리
    st.subheader("🔧 세션 관리")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("대화 기록 초기화", type="secondary"):
            st.session_state.messages = []
            st.success("대화 기록이 초기화되었습니다.")
            st.rerun()

    with col2:
        if st.button("세션 종료", type="secondary"):
            if st.session_state.session_id:
                call_api(f"/session/{st.session_state.session_id}", "DELETE")
                st.session_state.session_id = None
                st.session_state.context = ""
                st.session_state.messages = []
                st.success("세션이 종료되었습니다.")
                st.rerun()


def main():
    """메인 함수"""
    init_session_state()

    # 사이드바
    with st.sidebar:
        st.title("🤖 AI 학습 도우미")
        st.markdown("---")

        # 파일 업로드
        st.subheader("📁 파일 업로드")
        uploaded_file = st.file_uploader(
            "학습 자료를 업로드하세요",
            type=['pdf', 'txt', 'md'],
            help="PDF, TXT, Markdown 파일을 지원합니다"
        )

        if uploaded_file:
            if upload_file(uploaded_file):
                st.rerun()

        # 현재 파일 정보
        if st.session_state.uploaded_file_name:
            st.info(f"📄 현재 파일: {st.session_state.uploaded_file_name}")

        st.markdown("---")

        # 모드 선택
        st.subheader("🎯 기능 선택")
        mode = st.selectbox(
            "사용할 기능을 선택하세요",
            [
                "💬 채팅",
                "📝 요약",
                "❓ Q&A",
                "📚 추천",
                "📊 대시보드"
            ],
            index=0
        )

        st.markdown("---")

        # API 상태 체크
        st.subheader("🔌 API 상태")
        if st.button("상태 확인"):
            health = call_api("/health")
            if health:
                st.success("✅ API 정상 작동 중")
                st.json(health)
            else:
                st.error("❌ API 연결 실패")

        # 정보
        st.markdown("---")
        st.caption("💡 **도움말**")
        st.caption("• 파일을 업로드하면 자동으로 텍스트가 추출됩니다")
        st.caption("• 채팅에서는 대화 기록이 유지됩니다")
        st.caption("• Q&A에서는 업로드한 파일 기반으로 답변합니다")

    # 메인 영역
    if mode == "💬 채팅":
        chat_interface()
    elif mode == "📝 요약":
        summary_interface()
    elif mode == "❓ Q&A":
        qa_interface()
    elif mode == "📚 추천":
        recommendations_interface()
    elif mode == "📊 대시보드":
        dashboard_interface()


if __name__ == "__main__":
    main()