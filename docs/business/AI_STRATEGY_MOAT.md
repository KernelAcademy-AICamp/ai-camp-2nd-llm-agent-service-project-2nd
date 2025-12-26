# 🧠 AI Business Strategy & Moat

> **Mentor's Perspective**: "AI는 단순히 유행이 아니라, 높은 영업이익률(Gross Margin)과 데이터 주권(Sovereignty)을 동시에 확보하는 핵심 엔진이어야 합니다."

## 1. High-Margin AI Architecture (FinOps)
LEH의 AI 아키텍처는 모든 요청에 LLM을 사용하는 대신, **계층형 분석(Layered Analysis)** 방식을 채택하여 비용 효율성을 극대화합니다.

- **Layer 1: Deterministic Tagging (Low Cost)**: 
    - `Article840Tagger`를 통한 키워드 기반 사전 분류.
    - LLM 호출 없이도 민법 840조 유책 사유를 1차 필터링하여 토큰 비용 80% 절감.
- **Layer 2: AI Summarization (High Value)**:
    - 1차 분류된 결과를 바탕으로 GPT-4o가 최종 요약 및 증거 가치 판단.
    - 필요한 맥락만 LLM에 전달하여 처리 속도 및 비용 최적화.
- **Deterministic Fallback**: 
    - OpenAI API 장애 시 SHA-256 기반 의사 임베딩(Pseudo-embedding)과 키워드 태깅으로 시스템 가용성 99.9% 유지.

## 2. Competitive Moats (Business Value)

### 2.1 Multi-Tenant RAG Isolation
- **Case-Level Indexing**: 각 사건별로 Qdrant Collection(`case_rag_{id}`)을 물리적으로 분리.
- **Benefit**: 데이터 간섭(Data Leakage) 원천 차단. 변호사가 자신의 사건 데이터가 다른 사건에 영향을 미치지 않는다는 확신을 가짐으로써 신뢰도 제고.

### 2.2 Data Sovereignty & Evidence Integrity
- **Audit-Ready AI**: 분석 전후의 SHA-256 해시 추적 및 JobTracker를 통한 단계별 로깅.
- **Legal Admissibility**: 단순히 '좋은 결과'를 내는 것을 넘어, 법정에 제출 가능한 수준의 증거 무결성(Chain of Custody)을 시스템적으로 보장.

### 2.3 Domain-Specific Logic (Article 840)
- **Expertise Encoding**: 한국 민법 840조(이혼 사유)에 특화된 키워드 및 가중치 사전을 보유. 이는 범용 AI 서비스가 따라오기 힘든 전문성 기반의 진입 장벽.

### 2.4 LSSP Standard (Legal Service Standardization Protocol)
- **Protocol-Oriented Analysis**: LSSP v2.x를 통해 증거 추출-쟁점 매핑-초안 작성을 표준화된 파이프라인으로 연결. 이는 단순 챗봇을 넘어선 '엔터프라이즈급 법률 업무 표준'을 선점하는 효과.

## 3. Future Roadmap (Strategic Evolution)

- **Step 1: SLM (Small Language Model) Fine-tuning**: 
    - 누적된 태깅 데이터를 기반으로, OpenAI가 아닌 자체 온프레미스/개별 계정 SLM으로 전환하여 마진율 추가 확보.
- **Step 2: Prompt Governance & Eval**: 
    - 프롬프트 버전 관리 및 자동화된 품질 검증(Prompt Evaluation) 프로세스 도입.
- **Step 3: Multi-Region & Localization**: 
    - 한국 민법 840조 엔진을 추상화하여, 글로벌 가사 사건(Matrimonial Law) 시장으로의 확장 가능한 범용 엔진화.

> 💡 **Current Progress**: Graph-AI (Step 3 in v1.0)는 현재 `PersonExtractor` 및 `RelationshipService`를 통해 **Active Development(1단계: 관계망 자동 추출)** 단계에 진입함.
