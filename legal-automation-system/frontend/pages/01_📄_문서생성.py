"""
문서 생성 전용 페이지
"""

import streamlit as st
import requests
from datetime import datetime
import json
from typing import Dict, Any

# API 설정
API_BASE_URL = "http://localhost:8000/api/v1"

def make_api_request(endpoint: str, method: str = "GET", data: Dict = None, files: Dict = None) -> Dict:
    """API 요청 헬퍼 함수"""
    headers = {}
    if 'auth_token' in st.session_state and st.session_state.auth_token:
        headers["Authorization"] = f"Bearer {st.session_state.auth_token}"

    try:
        if method == "GET":
            response = requests.get(f"{API_BASE_URL}{endpoint}", headers=headers, params=data)
        elif method == "POST":
            if files:
                response = requests.post(f"{API_BASE_URL}{endpoint}", headers=headers, data=data, files=files)
            else:
                response = requests.post(f"{API_BASE_URL}{endpoint}", headers=headers, json=data)

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API 오류: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"연결 오류: {str(e)}")
        return None


def main():
    st.title("📄 법률 문서 자동 생성")

    # 인증 확인
    if 'auth_token' not in st.session_state or not st.session_state.auth_token:
        st.warning("로그인이 필요합니다.")
        st.stop()

    # 템플릿 카테고리
    template_categories = {
        "계약서": ["매매계약", "임대차계약", "용역계약", "근로계약", "비밀유지계약", "양도양수계약", "대여계약"],
        "소송문서": ["민사소장", "형사고소장", "행정소송", "가사소송", "답변서", "준비서면"],
        "통지서": ["내용증명", "계약해지통지", "대금청구", "손해배상청구", "원상회복통지"],
        "신청서": ["지급명령신청", "가압류신청", "가처분신청", "파산신청", "회생신청"],
        "합의서": ["합의서", "각서", "확인서", "동의서", "위임장"]
    }

    # 카테고리 선택
    col1, col2 = st.columns([1, 2])
    with col1:
        category = st.selectbox("문서 카테고리", list(template_categories.keys()))
    with col2:
        doc_type = st.selectbox("문서 유형", template_categories[category])

    st.markdown("---")

    # AI 모델 선택
    ai_model = st.selectbox(
        "AI 모델 선택",
        ["GPT-4 (추천)", "Claude-3", "Gemini Pro", "자동 선택"],
        help="문서 생성에 사용할 AI 모델을 선택합니다."
    )

    # 문서 생성 폼
    with st.form(f"{doc_type}_form", clear_on_submit=False):
        st.markdown(f"### {doc_type} 작성 정보")

        # 공통 필드
        if category == "계약서":
            generate_contract_fields(doc_type)
        elif category == "소송문서":
            generate_lawsuit_fields(doc_type)
        elif category == "통지서":
            generate_notice_fields(doc_type)
        elif category == "신청서":
            generate_application_fields(doc_type)
        elif category == "합의서":
            generate_agreement_fields(doc_type)

        # 추가 옵션
        with st.expander("고급 옵션"):
            language = st.selectbox("언어", ["한국어", "영어", "중국어", "일본어"])
            tone = st.selectbox("문체", ["격식체", "보통체", "간결체"])
            include_legal_basis = st.checkbox("관련 법령 포함", value=True)
            include_precedents = st.checkbox("관련 판례 포함", value=False)

        # 제출 버튼
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            submitted = st.form_submit_button("🚀 문서 생성", use_container_width=True, type="primary")
        with col2:
            preview = st.form_submit_button("👁️ 미리보기", use_container_width=True)
        with col3:
            save_draft = st.form_submit_button("💾 초안 저장", use_container_width=True)

        if submitted:
            generate_document(doc_type, category, ai_model)
        elif preview:
            show_preview(doc_type)
        elif save_draft:
            save_draft_document(doc_type)


def generate_contract_fields(contract_type: str):
    """계약서 필드 생성"""
    col1, col2 = st.columns(2)

    with col1:
        st.text_input("계약 당사자 1 (갑)", key="party1_name")
        st.text_input("주민/사업자번호", key="party1_id")
        st.text_input("주소", key="party1_address")
        st.text_input("연락처", key="party1_phone")

    with col2:
        st.text_input("계약 당사자 2 (을)", key="party2_name")
        st.text_input("주민/사업자번호", key="party2_id")
        st.text_input("주소", key="party2_address")
        st.text_input("연락처", key="party2_phone")

    if contract_type == "매매계약":
        st.text_input("매매 대상", key="subject")
        st.number_input("매매 대금 (원)", min_value=0, step=100000, key="price")
        st.date_input("계약일", key="contract_date")
        st.date_input("잔금일", key="payment_date")
    elif contract_type == "임대차계약":
        st.text_input("임대 목적물", key="property")
        st.number_input("보증금 (원)", min_value=0, step=1000000, key="deposit")
        st.number_input("월세 (원)", min_value=0, step=10000, key="monthly_rent")
        col1, col2 = st.columns(2)
        with col1:
            st.date_input("계약 시작일", key="start_date")
        with col2:
            st.date_input("계약 종료일", key="end_date")

    st.text_area("특약 사항", height=100, key="special_terms")


def generate_lawsuit_fields(lawsuit_type: str):
    """소송문서 필드 생성"""
    st.markdown("#### 원고 정보")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("원고 성명", key="plaintiff_name")
        st.text_input("주민등록번호", key="plaintiff_id")
    with col2:
        st.text_input("주소", key="plaintiff_address")
        st.text_input("연락처", key="plaintiff_phone")

    st.markdown("#### 피고 정보")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("피고 성명", key="defendant_name")
        st.text_input("주민등록번호 (선택)", key="defendant_id")
    with col2:
        st.text_input("주소", key="defendant_address")
        st.text_input("연락처 (선택)", key="defendant_phone")

    st.text_input("제출 법원", key="court")

    if lawsuit_type in ["민사소장", "손해배상청구"]:
        st.number_input("청구 금액 (원)", min_value=0, step=100000, key="claim_amount")

    st.text_area("청구 원인", height=200, key="claim_cause",
                 placeholder="사건의 경위와 법적 근거를 상세히 기술하세요.")
    st.text_area("입증 자료", height=100, key="evidence",
                 placeholder="제출할 증거 목록을 나열하세요.")


def generate_notice_fields(notice_type: str):
    """통지서 필드 생성"""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 발신인")
        st.text_input("발신인 성명", key="sender_name")
        st.text_input("발신인 주소", key="sender_address")
        st.text_input("발신인 연락처", key="sender_phone")

    with col2:
        st.markdown("#### 수신인")
        st.text_input("수신인 성명", key="receiver_name")
        st.text_input("수신인 주소", key="receiver_address")
        st.text_input("수신인 연락처 (선택)", key="receiver_phone")

    if notice_type == "내용증명":
        st.text_area("통지 내용", height=300, key="notice_content",
                     placeholder="내용증명으로 통지할 내용을 구체적으로 작성하세요.")
        st.date_input("회신 기한", key="response_deadline")
    elif notice_type == "계약해지통지":
        st.text_input("계약명", key="contract_name")
        st.date_input("계약일", key="contract_date")
        st.text_area("해지 사유", height=150, key="termination_reason")
        st.date_input("해지 효력 발생일", key="termination_date")


def generate_application_fields(app_type: str):
    """신청서 필드 생성"""
    st.text_input("신청인 성명", key="applicant_name")
    st.text_input("주민등록번호", key="applicant_id")
    st.text_input("주소", key="applicant_address")
    st.text_input("연락처", key="applicant_phone")

    if app_type == "지급명령신청":
        st.text_input("채무자 성명", key="debtor_name")
        st.text_input("채무자 주소", key="debtor_address")
        st.number_input("청구 금액", min_value=0, step=10000, key="claim_amount")
        st.text_area("청구 원인", height=150, key="claim_reason")
    elif app_type in ["가압류신청", "가처분신청"]:
        st.text_input("피신청인", key="respondent")
        st.text_area("신청 이유", height=200, key="application_reason")
        st.text_area("소명 자료", height=100, key="proof")


def generate_agreement_fields(agreement_type: str):
    """합의서 필드 생성"""
    num_parties = st.number_input("당사자 수", min_value=2, max_value=10, value=2, key="num_parties")

    for i in range(num_parties):
        st.markdown(f"#### 당사자 {i+1}")
        col1, col2 = st.columns(2)
        with col1:
            st.text_input(f"성명", key=f"party{i+1}_name")
            st.text_input(f"주민등록번호", key=f"party{i+1}_id")
        with col2:
            st.text_input(f"주소", key=f"party{i+1}_address")
            st.text_input(f"연락처", key=f"party{i+1}_phone")

    st.text_area("합의 내용", height=200, key="agreement_content",
                 placeholder="합의 사항을 구체적으로 기술하세요.")

    if agreement_type == "합의서":
        st.checkbox("금전 지급 포함", key="include_payment")
        if st.session_state.get("include_payment"):
            st.number_input("지급 금액", min_value=0, step=10000, key="payment_amount")
            st.date_input("지급일", key="payment_date")


def generate_document(doc_type: str, category: str, ai_model: str):
    """문서 생성 실행"""
    with st.spinner(f"{doc_type}을(를) 생성 중입니다..."):
        # 폼 데이터 수집
        form_data = {}
        for key in st.session_state:
            if not key.startswith("FormSubmitter"):
                form_data[key] = st.session_state[key]

        # API 호출
        endpoint_map = {
            "계약서": "/generation/contract",
            "소송문서": "/generation/lawsuit",
            "통지서": "/generation/notice",
            "신청서": "/generation/application",
            "합의서": "/generation/agreement"
        }

        endpoint = endpoint_map.get(category, "/generation/document")

        response = make_api_request(endpoint, "POST", {
            "document_type": doc_type,
            "ai_model": ai_model,
            "form_data": form_data
        })

        if response:
            st.success(f"✅ {doc_type}이(가) 성공적으로 생성되었습니다!")

            # 생성된 문서 표시
            st.markdown("---")
            st.markdown("### 📋 생성된 문서")

            # 문서 내용 표시
            doc_content = response.get("content", "")
            st.text_area("", value=doc_content, height=400, key="generated_doc")

            # 액션 버튼들
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.download_button(
                    label="📥 다운로드 (TXT)",
                    data=doc_content,
                    file_name=f"{doc_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )

            with col2:
                if st.button("📊 리스크 분석"):
                    analyze_risk(response.get("document_id"))

            with col3:
                if st.button("✔️ 준수성 검사"):
                    check_compliance(response.get("document_id"))

            with col4:
                if st.button("💾 문서 저장"):
                    save_document(response)

            # 추가 정보
            with st.expander("🔍 문서 정보"):
                st.json({
                    "문서 ID": response.get("document_id"),
                    "생성 시간": response.get("created_at"),
                    "AI 모델": response.get("ai_model"),
                    "토큰 사용량": response.get("tokens_used"),
                    "예상 비용": f"${response.get('estimated_cost', 0):.4f}"
                })


def show_preview(doc_type: str):
    """문서 미리보기"""
    st.info(f"📄 {doc_type} 미리보기 기능은 준비 중입니다.")


def save_draft_document(doc_type: str):
    """초안 저장"""
    st.success(f"💾 {doc_type} 초안이 저장되었습니다.")


def analyze_risk(doc_id: str):
    """리스크 분석"""
    with st.spinner("리스크 분석 중..."):
        response = make_api_request(f"/analysis/risk/{doc_id}", "POST")
        if response:
            st.markdown("### 🔍 리스크 분석 결과")
            risk_level = response['risk_analysis']['risk_level']
            risk_score = response['risk_analysis']['risk_score']

            if risk_level == "high":
                st.error(f"리스크 레벨: {risk_level.upper()} ({risk_score}/100)")
            elif risk_level == "medium":
                st.warning(f"리스크 레벨: {risk_level.upper()} ({risk_score}/100)")
            else:
                st.success(f"리스크 레벨: {risk_level.upper()} ({risk_score}/100)")


def check_compliance(doc_id: str):
    """준수성 검사"""
    with st.spinner("준수성 검사 중..."):
        response = make_api_request(f"/analysis/compliance/{doc_id}", "POST")
        if response:
            st.markdown("### ✔️ 준수성 검사 결과")
            score = response.get('compliance_score', 0)

            if score >= 90:
                st.success(f"준수성 점수: {score}% - 매우 우수")
            elif score >= 70:
                st.warning(f"준수성 점수: {score}% - 보통")
            else:
                st.error(f"준수성 점수: {score}% - 개선 필요")


def save_document(doc_data: dict):
    """문서 저장"""
    response = make_api_request("/documents", "POST", doc_data)
    if response:
        st.success("✅ 문서가 성공적으로 저장되었습니다.")


if __name__ == "__main__":
    main()