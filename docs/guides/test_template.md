# test_template.md — LEH 테스트 작성 템플릿

> 이 템플릿은 **백엔드, AI Worker, 프론트엔드, CI/CD** 전 구간에서  
> Kent Beck 스타일 TDD를 적용하기 위한 공통 양식이다.

---

## 1. 테스트 이름

- 명확한 행동 기반 이름 사용

예시:

- `test_should_issue_presigned_url_for_valid_case`
- `test_should_store_ocr_result_to_dynamodb`
- `test_should_show_ai_disclaimer_on_draft_tab`
- `test_ci_blocks_deploy_when_tests_fail_on_dev_branch`

---

## 2. 테스트 목적 (Behavior 중심 설명)

> 이 테스트가 **사용자/시스템 관점에서 어떤 행동을 검증하는지** 한 문장으로 쓴다.

예시:

- “유효한 사건에 대해 Presigned URL 발급 API가 S3 업로드 정보를 반환하는지 검증한다.”
- “이미지 증거가 업로드되면 AI Worker가 OCR 결과를 DynamoDB에 저장하는지 검증한다.”
- “Draft 탭에서 AI 생성 초안에 항상 책임 한계 Disclaimer가 표시되는지 검증한다.”
- “dev 브랜치에서 테스트가 실패하면 GitHub Actions CD job 이 실행되지 않는지 검증한다.”

---

## 3. Given (준비 단계)

- 필요한 **입력/환경/Mock** 준비

예시:

### Backend 예시

- 가짜 `case_id` 및 사용자 JWT 토큰
- S3 client mock (boto3 Stubber)
- DynamoDB / Qdrant mock client

### AI Worker 예시

- S3 Event 샘플 JSON fixture
- S3에 저장된 테스트 파일 경로(또는 in-memory file)
- Vision/STT/Embedding 모듈 mock

### Frontend 예시

- React Testing Library 로 렌더링된 컴포넌트
- Mocked API client (MSW or jest mock)
- 테스트용 디자인 토큰 테마 provider

### CI/CD 예시

- `.github/workflows/ci.yml` 파싱용 YAML loader
- 가짜 Git ref (`refs/heads/dev` 등)
- 최소한의 파일 시스템 fixture (워크플로우 내용)

---

## 4. When (행동 / 실행)

- 테스트 대상 함수/엔드포인트/컴포넌트를 호출하는 부분

예시:

- FastAPI `TestClient` 로 `POST /evidence/presigned-url` 요청
- Worker `handler.handle_s3_event(event)` 호출
- React 컴포넌트에 `userEvent.click(button)` 수행
- CI 설정 검사 스크립트 실행 (예: `validate_workflows()`)

---

## 5. Then (검증)

- **가장 중요한 결과부터** assert 한다.
- 내부 구현이 아니라 **외부에서 관찰 가능한 행동**을 검증한다.

예시:

### Backend

- HTTP status code == 200/201/4xx
- 응답 JSON에 필요한 필드가 포함되어 있는지
- DB 쿼리 결과가 의도대로 변경되었는지

### AI Worker

- DynamoDB에 evidence 레코드가 생성/업데이트되었는지
- Qdrant `index()` 가 지정된 인자들로 호출되었는지
- `labels` 필드 타입이 list 인지

### Frontend

- 특정 텍스트/버튼/아이콘이 화면에 렌더링됐는지
- Draft 탭 상단에 AI Disclaimer 텍스트가 보이는지
- 삭제 버튼 클릭 시 확인 모달이 나타나는지
- 업로드 진행 상태(로더/스피너)가 올바르게 표시되는지

### CI/CD

- `ci.yml` 에 `on.push.branches` 에 `dev`, `main` 이 포함되어 있는지
- `cd-dev.yml` 이 `needs: [ci]` 를 통해 CI 성공 이후에만 실행되도록 돼 있는지
- 워크플로우 내에 `OPENAI_API_KEY` 와 같은 문자열 literal 이 없는지(Secret 사용 검증)

---

## 6. Cleanup (정리)

- 테스트 간 독립성을 위해 생성한 데이터를 정리한다.

예시:

- 테스트용 DB 레코드 삭제 / 트랜잭션 롤백
- 임시 파일 제거
- Mock reset

---

## 7. 스타일 가이드 (LEH 전용)

### 7.1 행동 중심 이름

- “무엇을 테스트하는지” + “기대 결과” 조합
  - `should_...`, `returns_...`, `blocks_...` 등의 패턴 허용
- 나쁜 예: `test_case1`, `test_function_x`

### 7.2 AI 관련 테스트

- GPT/Whisper/Vision 호출은 **항상 mock** 하고:
  - 입력 prompt 형식
  - 결과 구조 (필드 유무)
  만 테스트한다.
- Latency / 품질 평가는 자동 테스트에서 다루지 않는다 (수동 QA로 분리).

### 7.3 UI/UX 테스트 (Calm Control, 피로도 없는 UX 반영)

- 색상/폰트는 “토큰 레벨”만 검증한다.
  - 예: Theme provider에서 primary color가 `#2C3E50` 인지 같은 형태.
- 레이아웃 세부 픽셀 값(e.g., margin-left: 12px)은 테스트하지 않는다.
- 대신 아래를 중점적으로 본다:
  - 정보 위계: 제목, 서브제목, 본문이 시맨틱 태그/컴포넌트로 구분되는지
  - 피드백: 업로드/분석/오류 상태를 사용자에게 즉시 알려주는지
  - 제어권: 파괴적 행동 전에 확실한 확인 단계가 있는지

### 7.4 보안 테스트

- 에러 메시지가 **구체적인 시스템 내부 정보**를 노출하지 않는지
- 로깅 시 민감 정보가 포함되지 않는지
- CORS, HTTPS, 보안 헤더 설정이 켜져 있는지 (적어도 유닛/통합테스트에서 기본값 검증)

### 7.5 CI/CD 테스트

- 배포 job 이 test job 에 `needs` 로 의존하고 있는지
- main/prod 배포에 manual approval 이 요구되는지
- GitHub Secrets 를 plaintext 로 출력하지 않는지

---

## 8. 예시: Backend + FE + CI 각각의 샘플 테스트 스켈레톤

### 8.1 Backend 예시 (pytest)

'''
def test_should_issue_presigned_url_for_valid_case(client, valid_case, s3_stub):
    # Given
    token = issue_jwt_for_user(valid_case.owner)

    # When
    resp = client.post(
        "/evidence/presigned-url",
        headers={"Authorization": f"Bearer {token}"},
        json={"case_id": valid_case.id, "filename": "chat.txt", "content_type": "text/plain"},
    )

    # Then
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "upload_url" in data
    assert data["fields"]["key"].startswith(f"cases/{valid_case.id}/raw/")
'''

### 8.2 Frontend 예시 (React Testing Library)

'''
it("should show AI disclaimer in draft tab", () => {
  render(<DraftTab/>);
  expect(
    screen.getByText(/이 문서는 AI가 생성한 초안이며/i)
  ).toBeInTheDocument();
});
'''

### 8.3 CI 설정 검사 예시 (Python + PyYAML)

'''
def test_ci_workflow_blocks_deploy_on_test_failure():
    wf = load_yaml(".github/workflows/ci.yml")
    jobs = wf["jobs"]
    assert "test" in jobs
    assert "build" in jobs
    assert "deploy" not in jobs  # 배포는 별도 cd 워크플로우에서만
'''
