# PLAN.md - AI Worker V2 리팩토링

## 개요

**목표**: 4가지 약점 개선 + 3종 V2 파서 구현
**예상 기간**: 4-6주
**상태**: 계획 수립 중
**브랜치**: L-work
**담당**: L (AI Worker)

### 현재 상태
- 기본 V2 파서 구현 완료 (KakaoTalk, PDF, Image, Audio)
- LegalAnalyzer 키워드 기반 분석 구현
- 테스트 59개 통과
- AI 분석 (_analyze_ai_based) 스텁 상태

### 개선 목표
| 영역 | 현재 | 목표 |
|------|------|------|
| AI 분석 | 스텁/Fallback | GPT-4o-mini + Instructor |
| 키워드 매칭 | 단순 정규식 | Kiwi 형태소 + 문맥 인식 |
| 벡터 검색 | 스텁 메서드 | Qdrant + KURE-v1 하이브리드 |
| 에러 처리 | 기본 try/except | 커스텀 예외 계층 |
| PDF 파서 | PyPDF2 기본 | PyMuPDF + OCR |
| Audio 파서 | Whisper API | WhisperX + 화자분리 |
| Image 파서 | EXIF만 | PaddleOCR + GPT-4V |

---

## 성공 지표

- [ ] 모든 기존 테스트 통과 (59개)
- [ ] 새 테스트 커버리지 >80%
- [ ] API 응답 시간 유지 (<3초)
- [ ] False Positive 50% 감소
- [ ] AI 분석 정확도 >85%

---

## Phase 1: 기반 구축 [1주차]

### 1.1 커스텀 예외 계층
- [ ] `src/exceptions/__init__.py` 생성
- [ ] `ParserError` 기본 클래스 정의
- [ ] `ErrorContext` 데이터클래스 정의
- [ ] 특화 예외 클래스 구현
  - [ ] `EncodingError` - 인코딩 감지/디코딩 실패
  - [ ] `FileCorruptionError` - 파일 손상
  - [ ] `ParseError` - 파싱 실패 (부분 결과 포함)
  - [ ] `ValidationError` - Pydantic 검증 실패
- [ ] 테스트 작성

### 1.2 인코딩 처리 유틸리티
- [ ] `src/utils/encoding.py` 생성
- [ ] `detect_encoding_with_fallback()` 구현
  - [ ] BOM 체크
  - [ ] charset-normalizer 연동
  - [ ] 한국어 인코딩 폴백 체인 (utf-8, cp949, euc-kr)
- [ ] 기존 파서에 적용
- [ ] 테스트 작성

### 1.3 구조화된 로깅
- [ ] `src/utils/logging.py` 생성
- [ ] `JSONFormatter` 클래스 구현
- [ ] 로깅 설정 딕셔너리 정의
- [ ] 파서별 컨텍스트 로깅 적용
- [ ] 테스트 작성

### 1.4 Pydantic 모델 정리
- [ ] `DivorceGround` Enum 정의 (민법 840조)
- [ ] `EvidenceClassification` 모델 정의
- [ ] 기존 `LegalCategory`와 매핑
- [ ] 테스트 작성

**Phase 1 완료 기준:**
- [ ] 모든 예외가 `ParserError` 상속
- [ ] 인코딩 자동 감지 동작
- [ ] JSON 로그 출력 확인

---

## Phase 2: AI 분석 강화 [2주차]

### 2.1 _analyze_ai_based 메서드 구현
- [ ] Instructor 라이브러리 설치 및 설정
- [ ] 시스템 프롬프트 작성 (민법 840조 Few-shot)
- [ ] 사용자 프롬프트 템플릿 작성
- [ ] GPT-4o-mini 호출 구현
  - [ ] temperature=0.1 설정
  - [ ] Structured Output 적용
  - [ ] max_retries=3 설정
- [ ] 응답 파싱 및 LegalAnalysis 변환
- [ ] 테스트 작성 (API 모킹)

### 2.2 키워드 Fallback 개선
- [ ] `keyword_fallback_classify()` 함수 구현
- [ ] 정규식 패턴 확장
- [ ] 낮은 신뢰도(0.6) 표시
- [ ] 테스트 작성

### 2.3 문맥 인식 키워드 매칭
- [ ] Kiwi (kiwipiepy) 설치
- [ ] `ContextAwareKeywordMatcher` 클래스 구현
  - [ ] 형태소 분석기 초기화
  - [ ] 부정어 사전 정의
  - [ ] 윈도우 기반 문맥 분석
- [ ] 부정문 패턴 감지
  - [ ] prefix: "안", "못"
  - [ ] suffix: "지 않", "지 못"
  - [ ] predicate: "아니", "없"
- [ ] 스코어링 로직 구현
- [ ] 기존 Article840Tagger와 통합
- [ ] 테스트 작성 (False Positive 케이스)

**Phase 2 완료 기준:**
- [ ] AI 분석 API 호출 동작
- [ ] API 실패 시 키워드 Fallback
- [ ] "외도하지 않았다" → 부정 인식

---

## Phase 3: SearchEngineV2 구현 [2-3주차]

### 3.1 Qdrant 인프라 설정
- [ ] Qdrant 클라이언트 설정
- [ ] 컬렉션 스키마 정의
  - [ ] Dense 벡터 설정 (1024 dim)
  - [ ] Sparse 벡터 설정 (BM25 + IDF)
- [ ] 페이로드 스키마 정의
  - [ ] filename, line_number, page_number
  - [ ] category, confidence, person
- [ ] 페이로드 인덱스 생성
- [ ] 테스트 작성

### 3.2 임베딩 모델 설정
- [ ] KURE-v1 모델 로드 (nlpai-lab/KURE-v1)
- [ ] 임베딩 생성 함수 구현
- [ ] 배치 임베딩 지원
- [ ] OpenAI 임베딩 폴백
- [ ] 테스트 작성

### 3.3 하이브리드 검색 구현
- [ ] `hybrid_search()` 메서드 구현
  - [ ] Dense + Sparse Prefetch
  - [ ] RRF 융합
  - [ ] 필터 조건 적용
- [ ] `search_by_category()` 구현
- [ ] `search_by_person()` 구현
- [ ] `search_by_confidence()` 구현
- [ ] `get_evidence_by_citation()` 구현
- [ ] 테스트 작성

### 3.4 인덱싱 파이프라인
- [ ] 청크 → Qdrant 저장 파이프라인
- [ ] Point ID 전략 (`{filename}_line{line}`)
- [ ] 기존 StorageManagerV2와 연동
- [ ] 테스트 작성

**Phase 3 완료 기준:**
- [ ] 하이브리드 검색 동작
- [ ] 카테고리/인물별 필터링
- [ ] "카톡_배우자.txt 247번째 줄" 직접 조회

---

## Phase 4: V2 파서 강화 [3-4주차]

### 4.1 PDF Parser V2 강화
- [ ] PyMuPDF (fitz) 적용
- [ ] 페이지별 텍스트 추출 개선
- [ ] 섹션 헤더 감지 (폰트 크기 기반)
- [ ] OCR 필요 여부 감지
- [ ] OCRmyPDF + Tesseract 연동
  - [ ] tesseract-ocr-kor 설치
  - [ ] 한국어 OCR 처리
- [ ] 손상된 PDF 처리
- [ ] 테스트 작성

### 4.2 Audio Parser V2 강화
- [ ] WhisperX 설치 및 설정
- [ ] 오디오 전처리 (16kHz, 모노)
- [ ] 전사 구현
  - [ ] language="ko" 설정
  - [ ] 정밀 타임스탬프 정렬
- [ ] 화자 분리 (pyannote-audio)
  - [ ] HuggingFace 토큰 설정
  - [ ] 화자별 세그먼트 할당
- [ ] 법적 증거 형식 변환
- [ ] 테스트 작성

### 4.3 Image Parser V2 강화
- [ ] PaddleOCR 설치 (한국어)
- [ ] 텍스트 추출 구현
  - [ ] bbox, confidence 포함
  - [ ] 평균 신뢰도 계산
- [ ] GPT-4V 채팅 스크린샷 분석
  - [ ] 카카오톡 UI 인식
  - [ ] 발신자 구분 (좌/우)
  - [ ] JSON 구조화 출력
- [ ] EXIF 추출 개선
  - [ ] GPS 좌표 파싱
  - [ ] is_original 플래그 (EXIF 삭제 감지)
- [ ] 테스트 작성

**Phase 4 완료 기준:**
- [ ] 스캔 PDF OCR 처리
- [ ] 오디오 화자 분리 동작
- [ ] 이미지 OCR + 채팅 분석

---

## Phase 5: 통합 및 마이그레이션 [4-6주차]

### 5.1 ParserFacade 구현
- [ ] `src/parsers/facade.py` 생성
- [ ] Feature Flag 기반 V1/V2 라우팅
- [ ] V2 실패 시 V1 폴백
- [ ] 로깅 및 메트릭 수집
- [ ] 테스트 작성

### 5.2 점진적 트래픽 전환
- [ ] Feature Flag 설정 파일
- [ ] 파서별 V2 활성화
  - [ ] kakao: True
  - [ ] pdf: True
  - [ ] audio: True
  - [ ] image: True
- [ ] 모니터링 및 롤백 준비
- [ ] 성능 비교 테스트

### 5.3 V1 코드 정리
- [ ] V1 파서 사용처 확인
- [ ] V1 코드 deprecated 마킹
- [ ] 문서 업데이트
- [ ] (선택) V1 코드 제거

### 5.4 최종 검증
- [ ] 전체 테스트 실행
- [ ] 커버리지 확인 (>80%)
- [ ] 성능 벤치마크
- [ ] 문서화 완료

**Phase 5 완료 기준:**
- [ ] 모든 파서 V2로 전환
- [ ] 테스트 커버리지 80%+
- [ ] 성능 저하 없음

---

## 기술 스택 요약

| 영역 | 라이브러리 | 버전 |
|------|-----------|------|
| AI 분석 | openai + instructor | latest |
| 형태소 분석 | kiwipiepy | >=0.16 |
| 벡터 DB | qdrant-client | >=1.7 |
| 임베딩 | sentence-transformers | >=2.2 |
| PDF | pymupdf | >=1.23 |
| OCR | paddleocr, ocrmypdf | latest |
| Audio | whisperx, pyannote-audio | latest |
| 인코딩 | charset-normalizer | >=3.0 |

---

## 의존성 추가 (requirements.txt)

```
# Phase 1
charset-normalizer>=3.0

# Phase 2
instructor>=1.0
kiwipiepy>=0.16

# Phase 3
qdrant-client>=1.7
sentence-transformers>=2.2

# Phase 4
pymupdf>=1.23
paddleocr>=2.7
paddlepaddle  # or paddlepaddle-gpu
ocrmypdf>=16.0
whisperx @ git+https://github.com/m-bain/whisperX.git
pyannote.audio>=3.1
```

---

## 주의사항

### API 키 관리
- `OPENAI_API_KEY`: GPT-4o-mini, GPT-4V
- `HF_TOKEN`: WhisperX 화자 분리 (pyannote)

### 라이선스
- PyMuPDF: AGPL 3.0 (상용 시 별도 라이선스)
- PaddleOCR: Apache 2.0

### 테스트
- OpenAI API 모킹: `openai-responses` 또는 `unittest.mock`
- 큰 파일 테스트: `tests/fixtures/` 에 샘플 데이터

### 성능
- WhisperX large-v3: ~10GB VRAM 필요
- PaddleOCR GPU: CUDA 필요
- Qdrant: 로컬 또는 클라우드

---

## 이슈 템플릿

### 기능 구현 이슈
```markdown
## 설명
[기능 설명]

## 태스크
- [ ] 구현
- [ ] 테스트
- [ ] 문서화

## 관련 파일
- `src/...`

## 완료 기준
- [ ] 테스트 통과
- [ ] 코드 리뷰
```

### 버그 수정 이슈
```markdown
## 버그 설명
[현상 설명]

## 재현 방법
1. ...

## 예상 동작
[정상 동작]

## 실제 동작
[버그 동작]
```

---

## 변경 이력

| 날짜 | 변경 내용 | 작성자 |
|------|----------|--------|
| 2025-12-01 | 최초 작성 | L |

