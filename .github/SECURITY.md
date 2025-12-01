# Security Policy — Legal Evidence Hub (LEH)

LEH는 이혼 사건 관련 민감 데이터를 다루는 서비스입니다.  
취약점을 발견했다면, 아래 절차에 따라 **조용히(private)** 알려주세요.

---

## 📬 1. 취약점 제보 방법 (How to Report)

1. GitHub **Security Advisories** 기능 사용 (Preferences에 따라)
2. 또는 레포 Maintainer에게 개인 채널(이메일/DM)로 제보  
   - 이슈 공개 등록( Issues )는 되도록 피해주세요.  
   - 불가피하게 Issue를 쓸 경우, **민감 정보/구체적인 공격 방법은 적지 말고 개략만 작성**해주세요.

제보 시 포함해주면 좋은 정보:

- 재현 방법 (가능하면 단계별)
- 영향 범위 (누가, 무엇을 할 수 있게 되는지)
- 로그/스크린샷 (개인정보/증거 원문 제거 후)

---

## 🧭 2. 범위(Scope)

보안 제보 대상:

- Backend API (FastAPI)
- AI Worker (Lambda/ECS)
- Qdrant / DynamoDB / RDS 연동
- Frontend (React/Next)
- 인프라(IaC) 설정

비대상(일반 이슈 또는 피쳐 요청으로 등록):

- UI/UX 개선
- 성능 튜닝 제안
- 문서/오타 수정

---

## 🔐 3. 기대하는 보안 기준

LEH는 다음과 같은 보안 목표를 가진다:

- 민감 사건/증거 데이터에 대한 **무단 접근 차단**
- Presigned URL 오·남용 방지
- JWT 위·변조 방지
- Qdrant / DynamoDB / RDS 직접 노출 차단
- AI 모델 호출 시 민감정보 최소 전송

자세한 내용은 레포의 `SECURITY_COMPLIANCE.md`를 참고해주세요.

---

## 🕒 4. 응답 정책

취약점 제보를 받으면 가능한 한 빠르게:

1. 접수 확인
2. 재현 및 영향도 분석
3. 수정 일정 공유
4. 패치 후 공지 (필요 시)

을 진행합니다.

---

감사합니다.  
LEH 보안을 함께 지켜주셔서 감사합니다.
