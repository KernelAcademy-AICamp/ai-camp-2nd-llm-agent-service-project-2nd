"""
Streamlit 기반 법률 자동화 시스템 UI
"""

import streamlit as st
import requests
import json
from pathlib import Path
import pandas as pd
from datetime import datetime
import time
from typing import Optional, Dict, Any, List
import base64
import io

# 페이지 설정
st.set_page_config(
    page_title="Legal AI Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if 'auth_token' not in st.session_state:
    st.session_state.auth_token = None
if 'user' not in st.session_state:
    st.session_state.user = None
if 'current_document' not in st.session_state:
    st.session_state.current_document = None

# API 설정
API_BASE_URL = "http://localhost:8000/api/v1"

# 스타일 설정
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #333;
        margin-top: 1rem;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border: 1px solid #c3e6cb;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border: 1px solid #ffeeba;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border: 1px solid #f5c6cb;
    }
</style>
""", unsafe_allow_html=True)


def make_api_request(endpoint: str, method: str = "GET", data: Dict = None, files: Dict = None) -> Dict:
    """API 요청 헬퍼 함수"""
    headers = {}
    if st.session_state.auth_token:
        headers["Authorization"] = f"Bearer {st.session_state.auth_token}"

    try:
        if method == "GET":
            response = requests.get(f"{API_BASE_URL}{endpoint}", headers=headers, params=data)
        elif method == "POST":
            if files:
                response = requests.post(f"{API_BASE_URL}{endpoint}", headers=headers, data=data, files=files)
            else:
                response = requests.post(f"{API_BASE_URL}{endpoint}", headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(f"{API_BASE_URL}{endpoint}", headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(f"{API_BASE_URL}{endpoint}", headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API 오류: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"연결 오류: {str(e)}")
        return None


def login_page():
    """로그인 페이지"""
    st.markdown('<h1 class="main-header">⚖️ Legal AI Assistant</h1>', unsafe_allow_html=True)
    st.markdown("### 로그인")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        with st.form("login_form"):
            email = st.text_input("이메일", placeholder="your@email.com")
            password = st.text_input("비밀번호", type="password")
            submitted = st.form_submit_button("로그인", use_container_width=True)

            if submitted:
                if email and password:
                    response = make_api_request("/auth/login", "POST", {
                        "username": email,
                        "password": password
                    })
                    if response:
                        st.session_state.auth_token = response.get("access_token")
                        st.session_state.user = response.get("user", {"email": email})
                        st.rerun()
                else:
                    st.error("이메일과 비밀번호를 입력해주세요.")

        st.markdown("---")

        # 회원가입 섹션
        with st.expander("신규 회원가입"):
            with st.form("register_form"):
                reg_name = st.text_input("이름")
                reg_email = st.text_input("이메일")
                reg_password = st.text_input("비밀번호", type="password")
                reg_password_confirm = st.text_input("비밀번호 확인", type="password")

                register_submitted = st.form_submit_button("회원가입", use_container_width=True)

                if register_submitted:
                    if reg_password != reg_password_confirm:
                        st.error("비밀번호가 일치하지 않습니다.")
                    elif reg_name and reg_email and reg_password:
                        response = make_api_request("/auth/register", "POST", {
                            "name": reg_name,
                            "email": reg_email,
                            "password": reg_password
                        })
                        if response:
                            st.success("회원가입이 완료되었습니다. 로그인해주세요.")
                    else:
                        st.error("모든 필드를 입력해주세요.")


def sidebar_menu():
    """사이드바 메뉴"""
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.user.get('email', 'User')}")

        st.markdown("---")

        menu = st.selectbox(
            "메뉴 선택",
            ["🏠 홈", "📄 문서 생성", "🔍 법률 검색", "📂 문서 관리",
             "📊 분석 도구", "⚖️ 법률 정보", "🔧 설정"]
        )

        st.markdown("---")

        if st.button("로그아웃", use_container_width=True):
            st.session_state.auth_token = None
            st.session_state.user = None
            st.rerun()

        return menu


def home_page():
    """홈 페이지"""
    st.markdown('<h1 class="main-header">⚖️ Legal AI Assistant</h1>', unsafe_allow_html=True)

    # 주요 기능 소개
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="info-box">
        <h3>📄 문서 자동 생성</h3>
        <p>계약서, 소장, 내용증명 등 법률 문서를 AI가 자동으로 작성합니다.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="info-box">
        <h3>🔍 법률 검색</h3>
        <p>관련 법령, 판례를 검색하고 AI 기반 추천을 받을 수 있습니다.</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="info-box">
        <h3>📊 리스크 분석</h3>
        <p>문서의 법적 리스크를 자동 분석하고 개선 방안을 제시합니다.</p>
        </div>
        """, unsafe_allow_html=True)

    # 최근 활동
    st.markdown("### 📈 최근 활동")

    # 통계 가져오기
    stats = make_api_request("/analysis/statistics", "GET")
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("생성한 문서", stats.get("total_documents_analyzed", 0))
        with col2:
            st.metric("평균 리스크 점수", f"{stats.get('average_risk_score', 0):.2f}")
        with col3:
            st.metric("준수성 검사", stats.get("compliance_check_count", 0))
        with col4:
            st.metric("검토 완료", stats.get("review_count", 0))

    # 최근 문서 목록
    st.markdown("### 📑 최근 문서")
    documents = make_api_request("/documents", "GET", {"limit": 5})
    if documents:
        for doc in documents:
            with st.expander(f"📄 {doc['title']} - {doc['created_at'][:10]}"):
                st.write(f"**유형:** {doc.get('document_type', 'N/A')}")
                st.write(f"**상태:** {doc.get('status', 'N/A')}")
                if doc.get('risk_level'):
                    st.write(f"**리스크 레벨:** {doc['risk_level']}")


def document_generation_page():
    """문서 생성 페이지"""
    st.markdown("## 📄 법률 문서 생성")

    doc_type = st.selectbox(
        "문서 유형",
        ["계약서", "소장", "내용증명", "합의서", "고소장", "위임장", "각서"]
    )

    if doc_type == "계약서":
        contract_generation_form()
    elif doc_type == "소장":
        lawsuit_generation_form()
    elif doc_type == "내용증명":
        notice_generation_form()
    else:
        st.info(f"{doc_type} 생성 기능은 준비 중입니다.")


def contract_generation_form():
    """계약서 생성 폼"""
    st.markdown("### 계약서 생성")

    with st.form("contract_form"):
        col1, col2 = st.columns(2)

        with col1:
            contract_type = st.selectbox(
                "계약 유형",
                ["매매계약", "임대차계약", "용역계약", "근로계약", "비밀유지계약"]
            )
            party1_name = st.text_input("계약 당사자 1 (갑)")
            party1_id = st.text_input("당사자 1 주민번호/사업자번호")
            party1_address = st.text_input("당사자 1 주소")

        with col2:
            contract_date = st.date_input("계약 날짜")
            party2_name = st.text_input("계약 당사자 2 (을)")
            party2_id = st.text_input("당사자 2 주민번호/사업자번호")
            party2_address = st.text_input("당사자 2 주소")

        contract_content = st.text_area("계약 주요 내용", height=200,
            placeholder="예: 매매 대상, 금액, 조건 등을 자세히 입력해주세요.")

        special_terms = st.text_area("특약 사항", height=100)

        submitted = st.form_submit_button("계약서 생성", use_container_width=True)

        if submitted:
            with st.spinner("계약서를 생성 중입니다..."):
                response = make_api_request("/generation/contract", "POST", {
                    "contract_type": contract_type,
                    "party1": {
                        "name": party1_name,
                        "id": party1_id,
                        "address": party1_address
                    },
                    "party2": {
                        "name": party2_name,
                        "id": party2_id,
                        "address": party2_address
                    },
                    "date": str(contract_date),
                    "content": contract_content,
                    "special_terms": special_terms
                })

                if response:
                    st.success("계약서가 성공적으로 생성되었습니다!")
                    st.markdown("### 생성된 계약서")
                    st.text_area("", value=response.get("content", ""), height=400)

                    # 다운로드 버튼
                    st.download_button(
                        label="📥 계약서 다운로드",
                        data=response.get("content", ""),
                        file_name=f"계약서_{contract_type}_{datetime.now().strftime('%Y%m%d')}.txt",
                        mime="text/plain"
                    )

                    # 리스크 분석 제안
                    if st.button("리스크 분석 실행"):
                        analyze_document_risk(response.get("document_id"))


def lawsuit_generation_form():
    """소장 생성 폼"""
    st.markdown("### 소장 생성")

    with st.form("lawsuit_form"):
        lawsuit_type = st.selectbox(
            "소송 유형",
            ["민사소송", "행정소송", "가사소송", "소액심판"]
        )

        col1, col2 = st.columns(2)
        with col1:
            plaintiff_name = st.text_input("원고 이름")
            plaintiff_address = st.text_input("원고 주소")
            plaintiff_phone = st.text_input("원고 연락처")

        with col2:
            defendant_name = st.text_input("피고 이름")
            defendant_address = st.text_input("피고 주소")
            court_name = st.text_input("제출 법원")

        claim_amount = st.number_input("청구 금액", min_value=0, step=100000)

        facts = st.text_area("사실 관계", height=200,
            placeholder="사건의 경위와 사실 관계를 시간 순서대로 자세히 기재해주세요.")

        claims = st.text_area("청구 취지", height=100,
            placeholder="원고가 법원에 요구하는 사항을 구체적으로 기재해주세요.")

        evidence_list = st.text_area("증거 목록", height=100,
            placeholder="제출할 증거 목록을 나열해주세요. (예: 계약서, 영수증, 사진 등)")

        submitted = st.form_submit_button("소장 생성", use_container_width=True)

        if submitted:
            with st.spinner("소장을 생성 중입니다..."):
                response = make_api_request("/generation/lawsuit", "POST", {
                    "lawsuit_type": lawsuit_type,
                    "plaintiff": {
                        "name": plaintiff_name,
                        "address": plaintiff_address,
                        "phone": plaintiff_phone
                    },
                    "defendant": {
                        "name": defendant_name,
                        "address": defendant_address
                    },
                    "court": court_name,
                    "claim_amount": claim_amount,
                    "facts": facts,
                    "claims": claims,
                    "evidence_list": evidence_list
                })

                if response:
                    st.success("소장이 성공적으로 생성되었습니다!")
                    st.markdown("### 생성된 소장")
                    st.text_area("", value=response.get("content", ""), height=400)

                    st.download_button(
                        label="📥 소장 다운로드",
                        data=response.get("content", ""),
                        file_name=f"소장_{lawsuit_type}_{datetime.now().strftime('%Y%m%d')}.txt",
                        mime="text/plain"
                    )


def notice_generation_form():
    """내용증명 생성 폼"""
    st.markdown("### 내용증명 생성")

    with st.form("notice_form"):
        notice_type = st.selectbox(
            "내용증명 유형",
            ["계약해지", "대금청구", "손해배상청구", "원상회복", "기타"]
        )

        col1, col2 = st.columns(2)
        with col1:
            sender_name = st.text_input("발신인 이름")
            sender_address = st.text_input("발신인 주소")
            sender_phone = st.text_input("발신인 연락처")

        with col2:
            receiver_name = st.text_input("수신인 이름")
            receiver_address = st.text_input("수신인 주소")
            deadline = st.date_input("회신 기한")

        content = st.text_area("내용증명 내용", height=300,
            placeholder="내용증명으로 통지할 내용을 구체적으로 작성해주세요.")

        submitted = st.form_submit_button("내용증명 생성", use_container_width=True)

        if submitted:
            with st.spinner("내용증명을 생성 중입니다..."):
                response = make_api_request("/generation/notice", "POST", {
                    "notice_type": notice_type,
                    "sender": {
                        "name": sender_name,
                        "address": sender_address,
                        "phone": sender_phone
                    },
                    "receiver": {
                        "name": receiver_name,
                        "address": receiver_address
                    },
                    "deadline": str(deadline),
                    "content": content
                })

                if response:
                    st.success("내용증명이 성공적으로 생성되었습니다!")
                    st.markdown("### 생성된 내용증명")
                    st.text_area("", value=response.get("content", ""), height=400)

                    st.download_button(
                        label="📥 내용증명 다운로드",
                        data=response.get("content", ""),
                        file_name=f"내용증명_{notice_type}_{datetime.now().strftime('%Y%m%d')}.txt",
                        mime="text/plain"
                    )


def legal_search_page():
    """법률 검색 페이지"""
    st.markdown("## 🔍 법률 검색")

    search_type = st.radio(
        "검색 유형",
        ["법령 검색", "판례 검색", "유사 문서 검색", "AI 추천"]
    )

    if search_type == "법령 검색":
        law_search_section()
    elif search_type == "판례 검색":
        case_search_section()
    elif search_type == "유사 문서 검색":
        similar_document_search()
    elif search_type == "AI 추천":
        ai_recommendation_search()


def law_search_section():
    """법령 검색 섹션"""
    st.markdown("### 법령 검색")

    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input("검색어", placeholder="예: 민법, 상법, 근로기준법")
    with col2:
        search_button = st.button("검색", use_container_width=True)

    category = st.selectbox(
        "카테고리",
        ["전체", "민법", "상법", "형법", "노동법", "세법", "행정법"]
    )

    if search_button and search_query:
        with st.spinner("법령을 검색 중입니다..."):
            response = make_api_request("/laws", "GET", {
                "law_name": search_query,
                "category": category if category != "전체" else None
            })

            if response and response.get("laws"):
                st.markdown(f"### 검색 결과 ({response.get('total', 0)}건)")

                for law in response["laws"]:
                    with st.expander(f"📜 {law['law_name']} - {law.get('article_no', '')}"):
                        st.markdown(f"**조항:** {law.get('article_title', '')}")
                        st.markdown(f"**내용:**\n{law.get('content', '')}")
                        st.markdown(f"**시행일:** {law.get('enforcement_date', '')}")

                        if st.button(f"관련 판례 보기", key=f"case_{law['id']}"):
                            show_related_cases(law['id'])
            else:
                st.info("검색 결과가 없습니다.")


def case_search_section():
    """판례 검색 섹션"""
    st.markdown("### 판례 검색")

    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input("검색어", placeholder="사건번호, 키워드 등")
    with col2:
        search_button = st.button("검색", use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        court_name = st.selectbox(
            "법원",
            ["전체", "대법원", "고등법원", "지방법원", "헌법재판소"]
        )
    with col2:
        case_type = st.selectbox(
            "사건 유형",
            ["전체", "민사", "형사", "행정", "가사", "특허"]
        )

    if search_button and search_query:
        with st.spinner("판례를 검색 중입니다..."):
            response = make_api_request("/laws/cases", "GET", {
                "query": search_query,
                "court_name": court_name if court_name != "전체" else None,
                "case_type": case_type if case_type != "전체" else None
            })

            if response and response.get("cases"):
                st.markdown(f"### 검색 결과")

                for case in response["cases"]:
                    with st.expander(f"⚖️ {case['case_number']} - {case.get('court_name', '')}"):
                        st.markdown(f"**판결일:** {case.get('judgment_date', '')}")
                        st.markdown(f"**사건명:** {case.get('case_name', '')}")
                        st.markdown(f"**판시사항:**\n{case.get('holding', '')}")
                        st.markdown(f"**판결요지:**\n{case.get('summary', '')}")


def similar_document_search():
    """유사 문서 검색"""
    st.markdown("### 유사 문서 검색")

    uploaded_file = st.file_uploader(
        "문서 업로드",
        type=['pdf', 'docx', 'txt', 'hwp']
    )

    if uploaded_file:
        with st.spinner("문서를 분석 중입니다..."):
            files = {"file": uploaded_file}
            response = make_api_request("/search/similar-documents", "POST", files=files)

            if response:
                st.markdown("### 유사 문서")
                for doc in response.get("similar_documents", []):
                    with st.expander(f"📄 {doc['title']} - 유사도: {doc['similarity']:.2%}"):
                        st.write(f"**문서 유형:** {doc['document_type']}")
                        st.write(f"**요약:** {doc['summary']}")
                        st.write(f"**주요 조항:** {', '.join(doc.get('key_provisions', []))}")


def ai_recommendation_search():
    """AI 추천 검색"""
    st.markdown("### AI 기반 법률 추천")

    situation = st.text_area(
        "상황 설명",
        height=200,
        placeholder="현재 상황이나 법적 문제를 자세히 설명해주세요."
    )

    if st.button("AI 추천 받기"):
        if situation:
            with st.spinner("AI가 분석 중입니다..."):
                response = make_api_request("/search/ai-recommend", "POST", {
                    "query": situation,
                    "include_laws": True,
                    "include_cases": True,
                    "include_templates": True
                })

                if response:
                    st.markdown("### AI 추천 결과")

                    # 관련 법령
                    if response.get("laws"):
                        st.markdown("#### 📜 관련 법령")
                        for law in response["laws"]:
                            st.write(f"- **{law['name']}**: {law['relevance']}")

                    # 관련 판례
                    if response.get("cases"):
                        st.markdown("#### ⚖️ 관련 판례")
                        for case in response["cases"]:
                            st.write(f"- **{case['number']}**: {case['summary']}")

                    # 추천 템플릿
                    if response.get("templates"):
                        st.markdown("#### 📝 추천 문서 템플릿")
                        for template in response["templates"]:
                            st.write(f"- **{template['name']}**: {template['description']}")

                    # AI 조언
                    if response.get("advice"):
                        st.markdown("#### 💡 AI 조언")
                        st.info(response["advice"])


def document_management_page():
    """문서 관리 페이지"""
    st.markdown("## 📂 문서 관리")

    tab1, tab2, tab3 = st.tabs(["내 문서", "문서 업로드", "OCR 처리"])

    with tab1:
        my_documents_section()

    with tab2:
        document_upload_section()

    with tab3:
        ocr_processing_section()


def my_documents_section():
    """내 문서 섹션"""
    st.markdown("### 내 문서 목록")

    # 필터링 옵션
    col1, col2, col3 = st.columns(3)
    with col1:
        doc_type_filter = st.selectbox(
            "문서 유형",
            ["전체", "계약서", "소장", "내용증명", "기타"]
        )
    with col2:
        status_filter = st.selectbox(
            "상태",
            ["전체", "작성중", "완료", "검토중"]
        )
    with col3:
        sort_by = st.selectbox(
            "정렬",
            ["최신순", "오래된순", "이름순"]
        )

    # 문서 목록 가져오기
    params = {"limit": 20}
    if doc_type_filter != "전체":
        params["document_type"] = doc_type_filter
    if status_filter != "전체":
        params["status"] = status_filter

    documents = make_api_request("/documents", "GET", params)

    if documents:
        for doc in documents:
            col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])

            with col1:
                st.write(f"📄 **{doc['title']}**")
            with col2:
                st.write(f"{doc['document_type']}")
            with col3:
                st.write(f"{doc['status']}")
            with col4:
                if st.button("보기", key=f"view_{doc['id']}"):
                    view_document(doc['id'])
            with col5:
                if st.button("삭제", key=f"del_{doc['id']}"):
                    delete_document(doc['id'])

            st.markdown("---")


def document_upload_section():
    """문서 업로드 섹션"""
    st.markdown("### 문서 업로드")

    uploaded_file = st.file_uploader(
        "파일 선택",
        type=['pdf', 'docx', 'txt', 'hwp', 'jpg', 'png']
    )

    if uploaded_file:
        doc_title = st.text_input("문서 제목", value=uploaded_file.name)
        doc_type = st.selectbox(
            "문서 유형",
            ["계약서", "소장", "내용증명", "판결문", "기타"]
        )

        if st.button("업로드"):
            with st.spinner("문서를 업로드 중입니다..."):
                files = {"file": uploaded_file}
                data = {
                    "title": doc_title,
                    "document_type": doc_type
                }
                response = make_api_request("/documents/upload", "POST", data=data, files=files)

                if response:
                    st.success("문서가 성공적으로 업로드되었습니다!")
                    st.session_state.current_document = response

                    # 자동 OCR 처리 제안
                    if uploaded_file.type in ['application/pdf', 'image/jpeg', 'image/png']:
                        if st.button("OCR 처리 시작"):
                            process_ocr(response['id'])


def ocr_processing_section():
    """OCR 처리 섹션"""
    st.markdown("### OCR 문서 처리")

    uploaded_file = st.file_uploader(
        "OCR 처리할 파일",
        type=['pdf', 'jpg', 'jpeg', 'png', 'tiff']
    )

    if uploaded_file:
        col1, col2 = st.columns(2)
        with col1:
            extract_metadata = st.checkbox("메타데이터 추출", value=True)
            extract_structure = st.checkbox("문서 구조 추출", value=True)
        with col2:
            ocr_engine = st.selectbox(
                "OCR 엔진",
                ["자동", "Tesseract", "EasyOCR"]
            )

        if st.button("OCR 처리 시작"):
            with st.spinner("문서를 처리 중입니다... (시간이 걸릴 수 있습니다)"):
                files = {"file": uploaded_file}
                params = {
                    "extract_metadata": extract_metadata,
                    "extract_structure": extract_structure,
                    "ocr_engine": ocr_engine.lower()
                }
                response = make_api_request("/ocr/process", "POST", data=params, files=files)

                if response:
                    st.success("OCR 처리가 완료되었습니다!")

                    # 결과 표시
                    st.markdown("### 추출된 텍스트")
                    st.text_area("", value=response.get("text", ""), height=300)

                    if response.get("metadata"):
                        st.markdown("### 메타데이터")
                        st.json(response["metadata"])

                    if response.get("structure"):
                        st.markdown("### 문서 구조")
                        st.json(response["structure"])

                    # 저장 옵션
                    if st.button("문서로 저장"):
                        save_ocr_result(response)


def analysis_tools_page():
    """분석 도구 페이지"""
    st.markdown("## 📊 분석 도구")

    tab1, tab2, tab3, tab4 = st.tabs(["리스크 분석", "준수성 검사", "문서 검토", "비교 분석"])

    with tab1:
        risk_analysis_section()

    with tab2:
        compliance_check_section()

    with tab3:
        document_review_section()

    with tab4:
        comparison_analysis_section()


def risk_analysis_section():
    """리스크 분석 섹션"""
    st.markdown("### 문서 리스크 분석")

    # 문서 선택 또는 업로드
    option = st.radio("문서 선택 방법", ["기존 문서", "새 문서 업로드"])

    document_id = None
    if option == "기존 문서":
        documents = make_api_request("/documents", "GET", {"limit": 50})
        if documents:
            doc_options = {f"{doc['title']} ({doc['id']})": doc['id'] for doc in documents}
            selected = st.selectbox("문서 선택", list(doc_options.keys()))
            document_id = doc_options[selected]
    else:
        uploaded_file = st.file_uploader("문서 업로드", type=['pdf', 'docx', 'txt'])
        if uploaded_file:
            # 파일 업로드 후 document_id 받기
            pass

    deep_analysis = st.checkbox("심층 분석 실행", value=True)

    if st.button("리스크 분석 시작") and document_id:
        with st.spinner("리스크를 분석 중입니다..."):
            response = make_api_request(
                f"/analysis/risk/{document_id}",
                "POST",
                {"deep_analysis": deep_analysis}
            )

            if response:
                st.markdown("### 분석 결과")

                # 리스크 레벨 표시
                risk_level = response['risk_analysis']['risk_level']
                risk_score = response['risk_analysis']['risk_score']

                col1, col2 = st.columns(2)
                with col1:
                    if risk_level == "high":
                        st.error(f"리스크 레벨: {risk_level.upper()}")
                    elif risk_level == "medium":
                        st.warning(f"리스크 레벨: {risk_level.upper()}")
                    else:
                        st.success(f"리스크 레벨: {risk_level.upper()}")

                with col2:
                    st.metric("리스크 점수", f"{risk_score:.2f}/100")

                # 리스크 요인
                st.markdown("#### 주요 리스크 요인")
                for factor in response['risk_analysis']['risk_factors']:
                    st.write(f"- **{factor['category']}**: {factor['description']} (심각도: {factor['severity']})")

                # 완화 전략
                st.markdown("#### 리스크 완화 전략")
                for strategy in response['mitigation_strategies']:
                    with st.expander(f"📋 {strategy['title']}"):
                        st.write(strategy['description'])
                        if strategy.get('action_items'):
                            st.write("**실행 항목:**")
                            for item in strategy['action_items']:
                                st.write(f"  - {item}")


def compliance_check_section():
    """준수성 검사 섹션"""
    st.markdown("### 법률 준수성 검사")

    # 문서 선택
    documents = make_api_request("/documents", "GET", {"limit": 50})
    if documents:
        doc_options = {f"{doc['title']} ({doc['id']})": doc['id'] for doc in documents}
        selected = st.selectbox("검사할 문서", list(doc_options.keys()))
        document_id = doc_options[selected]

        # 검사 카테고리
        categories = st.multiselect(
            "검사 카테고리",
            ["개인정보보호", "전자상거래", "근로계약", "부동산거래", "금융거래"],
            default=["개인정보보호"]
        )

        if st.button("준수성 검사 시작"):
            with st.spinner("준수성을 검사 중입니다..."):
                response = make_api_request(
                    f"/analysis/compliance/{document_id}",
                    "POST",
                    {"check_categories": categories}
                )

                if response:
                    st.markdown("### 검사 결과")

                    # 전체 준수성 점수
                    compliance_score = response['compliance_score']
                    if compliance_score >= 90:
                        st.success(f"준수성 점수: {compliance_score}% - 매우 양호")
                    elif compliance_score >= 70:
                        st.warning(f"준수성 점수: {compliance_score}% - 개선 필요")
                    else:
                        st.error(f"준수성 점수: {compliance_score}% - 심각한 문제")

                    # 카테고리별 결과
                    st.markdown("#### 카테고리별 준수성")
                    for cat, result in response['category_results'].items():
                        with st.expander(f"{cat}: {result['compliance']}"):
                            st.write(f"**준수율:** {result['score']}%")
                            if result.get('issues'):
                                st.write("**발견된 문제:**")
                                for issue in result['issues']:
                                    st.write(f"  - {issue}")

                    # 위반 사항
                    if response.get('violations'):
                        st.markdown("#### ⚠️ 위반 사항")
                        for violation in response['violations']:
                            st.error(f"- {violation['law']}: {violation['description']}")


def document_review_section():
    """문서 검토 섹션"""
    st.markdown("### 종합 문서 검토")

    # 문서 선택
    documents = make_api_request("/documents", "GET", {"limit": 50})
    if documents:
        doc_options = {f"{doc['title']} ({doc['id']})": doc['id'] for doc in documents}
        selected = st.selectbox("검토할 문서", list(doc_options.keys()))
        document_id = doc_options[selected]

        review_depth = st.select_slider(
            "검토 깊이",
            options=["quick", "standard", "thorough"],
            value="standard",
            format_func=lambda x: {"quick": "빠른 검토", "standard": "표준 검토", "thorough": "심층 검토"}[x]
        )

        focus_areas = st.multiselect(
            "중점 검토 영역",
            ["tax", "international"],
            format_func=lambda x: {"tax": "세무 관련", "international": "국제 거래"}[x]
        )

        if st.button("문서 검토 시작"):
            with st.spinner("문서를 검토 중입니다..."):
                params = {
                    "review_depth": review_depth
                }
                if focus_areas:
                    params["focus_areas"] = focus_areas

                response = make_api_request(
                    f"/analysis/review/{document_id}",
                    "POST",
                    params
                )

                if response:
                    st.markdown("### 검토 결과")

                    # 전체 평가
                    st.markdown("#### 전체 평가")
                    st.info(response.get('overall_assessment', ''))

                    # 구조 검토
                    if response.get('structure_review'):
                        st.markdown("#### 문서 구조")
                        st.write(response['structure_review'])

                    # 내용 검토
                    if response.get('content_review'):
                        st.markdown("#### 내용 검토")
                        st.write(response['content_review'])

                    # 법률 검토
                    if response.get('legal_review'):
                        st.markdown("#### 법률적 검토")
                        st.write(response['legal_review'])

                    # 개선 제안
                    if response.get('recommendations'):
                        st.markdown("#### 개선 제안")
                        for rec in response['recommendations']:
                            st.write(f"- {rec}")


def comparison_analysis_section():
    """비교 분석 섹션"""
    st.markdown("### 문서 비교 분석")

    # 문서 선택
    documents = make_api_request("/documents", "GET", {"limit": 50})
    if documents:
        doc_options = {f"{doc['title']} ({doc['id']})": doc['id'] for doc in documents}

        selected_docs = st.multiselect(
            "비교할 문서 선택 (2-5개)",
            list(doc_options.keys()),
            max_selections=5
        )

        if len(selected_docs) >= 2:
            comparison_type = st.selectbox(
                "비교 유형",
                ["risk", "compliance", "similarity"],
                format_func=lambda x: {
                    "risk": "리스크 비교",
                    "compliance": "준수성 비교",
                    "similarity": "유사도 비교"
                }[x]
            )

            if st.button("비교 분석 시작"):
                document_ids = [doc_options[doc] for doc in selected_docs]

                with st.spinner("문서를 비교 분석 중입니다..."):
                    response = make_api_request(
                        "/analysis/compare",
                        "POST",
                        {
                            "document_ids": document_ids,
                            "comparison_type": comparison_type
                        }
                    )

                    if response:
                        st.markdown("### 비교 결과")

                        if comparison_type == "risk":
                            # 리스크 비교 차트
                            risk_data = []
                            for result in response['results']:
                                risk_data.append({
                                    "문서": result['title'],
                                    "리스크 점수": result['risk_score'],
                                    "리스크 레벨": result['risk_level']
                                })

                            df = pd.DataFrame(risk_data)
                            st.dataframe(df)

                            # 막대 차트
                            st.bar_chart(df.set_index("문서")["리스크 점수"])

                        elif comparison_type == "compliance":
                            # 준수성 비교
                            compliance_data = []
                            for result in response['results']:
                                compliance_data.append({
                                    "문서": result['title'],
                                    "준수성 점수": result['compliance_score'],
                                    "위반 건수": result['violations_count']
                                })

                            df = pd.DataFrame(compliance_data)
                            st.dataframe(df)

                        elif comparison_type == "similarity":
                            # 유사도 매트릭스
                            st.markdown("#### 문서 간 유사도")
                            for result in response['results']:
                                st.write(f"**{result['title']}**")
                                for sim in result['similarities']:
                                    st.write(f"  - {sim['title']}: {sim['similarity']:.2%}")
        else:
            st.warning("최소 2개 이상의 문서를 선택해주세요.")


def legal_info_page():
    """법률 정보 페이지"""
    st.markdown("## ⚖️ 법률 정보")

    tab1, tab2, tab3 = st.tabs(["법령", "판례", "법령해석례"])

    with tab1:
        laws_info_section()

    with tab2:
        cases_info_section()

    with tab3:
        interpretations_section()


def laws_info_section():
    """법령 정보 섹션"""
    st.markdown("### 법령 정보")

    # 카테고리별 법령
    categories = make_api_request("/laws/categories", "GET")
    if categories:
        selected_category = st.selectbox(
            "법령 카테고리",
            ["전체"] + [cat['name'] for cat in categories['categories']]
        )

        # 법령 목록
        params = {"limit": 20}
        if selected_category != "전체":
            params["category"] = selected_category

        laws = make_api_request("/laws", "GET", params)
        if laws:
            st.markdown(f"#### {selected_category} 법령 ({laws['total']}건)")

            for law in laws['laws']:
                with st.expander(f"📜 {law['law_name']} - {law.get('article_no', '')}"):
                    st.write(f"**조항:** {law.get('article_title', '')}")
                    st.write(f"**내용:**\n{law.get('content', '')}")
                    st.write(f"**시행일:** {law.get('enforcement_date', '')}")
                    st.write(f"**조회수:** {law.get('view_count', 0)}")


def cases_info_section():
    """판례 정보 섹션"""
    st.markdown("### 판례 정보")

    # 최근 판례
    cases = make_api_request("/laws/cases", "GET", {"limit": 10})
    if cases:
        st.markdown("#### 최근 판례")

        for case in cases['cases']:
            with st.expander(f"⚖️ {case['case_number']} - {case['court_name']}"):
                st.write(f"**판결일:** {case['judgment_date']}")
                st.write(f"**사건명:** {case['case_name']}")
                st.write(f"**판시사항:**\n{case.get('holding', '')}")
                st.write(f"**판결요지:**\n{case.get('summary', '')}")


def interpretations_section():
    """법령해석례 섹션"""
    st.markdown("### 법령해석례")

    interpretations = make_api_request("/laws/interpretations", "GET", {"limit": 10})
    if interpretations:
        for interp in interpretations['interpretations']:
            with st.expander(f"📋 {interp['title']}"):
                st.write(f"**요청기관:** {interp['requesting_agency']}")
                st.write(f"**회신일:** {interp['response_date']}")
                st.write(f"**질의내용:**\n{interp['question']}")
                st.write(f"**해석내용:**\n{interp['answer']}")


def settings_page():
    """설정 페이지"""
    st.markdown("## 🔧 설정")

    tab1, tab2, tab3 = st.tabs(["프로필", "알림", "API 설정"])

    with tab1:
        profile_settings()

    with tab2:
        notification_settings()

    with tab3:
        api_settings()


def profile_settings():
    """프로필 설정"""
    st.markdown("### 프로필 설정")

    user_info = make_api_request("/auth/me", "GET")
    if user_info:
        with st.form("profile_form"):
            name = st.text_input("이름", value=user_info.get('name', ''))
            email = st.text_input("이메일", value=user_info.get('email', ''), disabled=True)
            phone = st.text_input("전화번호", value=user_info.get('phone', ''))
            organization = st.text_input("소속", value=user_info.get('organization', ''))

            if st.form_submit_button("프로필 업데이트"):
                response = make_api_request("/auth/profile", "PUT", {
                    "name": name,
                    "phone": phone,
                    "organization": organization
                })
                if response:
                    st.success("프로필이 업데이트되었습니다.")


def notification_settings():
    """알림 설정"""
    st.markdown("### 알림 설정")

    email_notifications = st.checkbox("이메일 알림", value=True)
    push_notifications = st.checkbox("푸시 알림", value=False)

    st.markdown("#### 알림 유형")
    doc_complete = st.checkbox("문서 생성 완료", value=True)
    risk_alert = st.checkbox("고위험 문서 알림", value=True)
    law_update = st.checkbox("법률 업데이트", value=False)

    if st.button("알림 설정 저장"):
        st.success("알림 설정이 저장되었습니다.")


def api_settings():
    """API 설정"""
    st.markdown("### API 설정")

    st.markdown("#### API 키 관리")
    st.info("API 키를 통해 외부 시스템과 연동할 수 있습니다.")

    if st.button("새 API 키 생성"):
        response = make_api_request("/auth/api-key", "POST")
        if response:
            st.success("새 API 키가 생성되었습니다.")
            st.code(response.get("api_key"))
            st.warning("이 키는 다시 표시되지 않으므로 안전하게 보관하세요.")

    st.markdown("#### 사용량 통계")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("API 호출", "1,234")
    with col2:
        st.metric("생성된 문서", "56")
    with col3:
        st.metric("OCR 처리", "89")


# 헬퍼 함수들
def view_document(doc_id):
    """문서 보기"""
    response = make_api_request(f"/documents/{doc_id}", "GET")
    if response:
        st.session_state.current_document = response
        st.markdown(f"### {response['title']}")
        st.text_area("", value=response.get('content', ''), height=400)


def delete_document(doc_id):
    """문서 삭제"""
    if st.confirm("정말 삭제하시겠습니까?"):
        response = make_api_request(f"/documents/{doc_id}", "DELETE")
        if response:
            st.success("문서가 삭제되었습니다.")
            st.rerun()


def analyze_document_risk(doc_id):
    """문서 리스크 분석"""
    with st.spinner("리스크를 분석 중입니다..."):
        response = make_api_request(f"/analysis/risk/{doc_id}", "POST")
        if response:
            st.markdown("### 리스크 분석 결과")
            st.json(response)


def show_related_cases(law_id):
    """관련 판례 보기"""
    response = make_api_request(f"/laws/{law_id}/cases", "GET")
    if response:
        st.markdown("#### 관련 판례")
        for case in response.get('cases', []):
            st.write(f"- {case['case_number']}: {case['summary']}")


def process_ocr(doc_id):
    """OCR 처리"""
    with st.spinner("OCR 처리 중..."):
        response = make_api_request(f"/documents/{doc_id}/ocr", "POST")
        if response:
            st.success("OCR 처리가 완료되었습니다.")
            st.text_area("추출된 텍스트", value=response.get('text', ''), height=300)


def save_ocr_result(ocr_result):
    """OCR 결과 저장"""
    response = make_api_request("/documents", "POST", {
        "title": f"OCR_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "content": ocr_result.get('text', ''),
        "document_type": "OCR",
        "metadata": ocr_result.get('metadata', {})
    })
    if response:
        st.success("OCR 결과가 저장되었습니다.")


# 메인 앱 실행
def main():
    """메인 애플리케이션"""
    if st.session_state.auth_token is None:
        login_page()
    else:
        menu = sidebar_menu()

        if menu == "🏠 홈":
            home_page()
        elif menu == "📄 문서 생성":
            document_generation_page()
        elif menu == "🔍 법률 검색":
            legal_search_page()
        elif menu == "📂 문서 관리":
            document_management_page()
        elif menu == "📊 분석 도구":
            analysis_tools_page()
        elif menu == "⚖️ 법률 정보":
            legal_info_page()
        elif menu == "🔧 설정":
            settings_page()


if __name__ == "__main__":
    main()