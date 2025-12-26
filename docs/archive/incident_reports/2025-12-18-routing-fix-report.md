# Next.js Static Export 라우팅 장애 분석 리포트

**작성일:** 2025-12-18  
**작성자:** Claude (AI Assistant)  
**프로젝트:** LEH (Legal Evidence Hub)  
**환경:** Next.js 14 + S3 + CloudFront

---

## 1. 문제 (Problem)

### 1.1 증상
프로덕션 환경(CloudFront)에서 케이스 상세 페이지 접근 시 **랜딩 페이지가 표시**되는 현상 발생.

```
요청: https://dpbf86zqulqfy.cloudfront.net/lawyer/cases/case_c768.../
기대: 케이스 상세 페이지
실제: 랜딩 페이지 (/)
```

### 1.2 영향 범위
- `/lawyer/cases/{caseId}/` - 케이스 상세
- `/lawyer/cases/{caseId}/procedure/` - 절차 정보
- `/lawyer/cases/{caseId}/assets/` - 증거자료
- `/lawyer/cases/{caseId}/relations/` - 관계인 정보
- `/lawyer/cases/{caseId}/relationship/` - 관계도

**모든 동적 케이스 ID 경로가 영향받음.**

---

## 2. 원인 (Root Cause)

### 2.1 기술적 원인

**Next.js Static Export의 한계:**
```
output: 'export' 모드에서는 빌드 시점에 알려진 경로만 HTML 생성
```

**generateStaticParams 동작:**
```typescript
// 빌드 시 생성되는 경로
export async function generateStaticParams() {
  return [
    { caseId: '1' },
    { caseId: '2' },
    { caseId: 'test-case-001' },
    // ... 하드코딩된 ID만 생성
  ];
}
```

**S3 실제 구조:**
```
s3://leh-frontend-prod/lawyer/cases/
├── 1/index.html          ✅ 존재
├── 2/index.html          ✅ 존재
├── test-case-001/        ✅ 존재
├── case_c768.../         ❌ 없음 (동적 ID)
```

### 2.2 CloudFront 설정 문제

**CustomErrorResponses 설정:**
```json
{
  "ErrorCode": 403,
  "ResponseCode": 200,
  "ResponsePagePath": "/index.html"
}
```

S3가 존재하지 않는 경로에 403 반환 → CloudFront가 `/index.html`(랜딩 페이지)을 200으로 서빙.

### 2.3 근본 원인 요약

| 계층 | 문제 |
|------|------|
| Next.js | Static export는 빌드 시점 경로만 생성 |
| S3 | 동적 케이스 ID 경로에 HTML 파일 없음 |
| CloudFront | 404/403 → 랜딩 페이지로 fallback |

---

## 3. 추적 과정 (Investigation)

### 3.1 Phase 1: 증상 확인
```bash
# CloudFront 응답 확인
curl -sI "https://dpbf86zqulqfy.cloudfront.net/lawyer/cases/case_c768.../"
# 결과: 200 OK, content-length: 랜딩 페이지 크기
```

### 3.2 Phase 2: S3 구조 분석
```bash
aws s3 ls s3://leh-frontend-prod/lawyer/cases/ --recursive
# 발견: 동적 ID 폴더 없음, generateStaticParams ID만 존재
```

### 3.3 Phase 3: Next.js 빌드 출력 확인
```bash
ls -la /frontend/out/lawyer/cases/
# 확인: detail/, procedure/, assets/ 등 정적 페이지 존재
# 부재: 실제 케이스 ID 폴더
```

### 3.4 Phase 4: 코드 분석
- `portalPaths.ts`: 동적 세그먼트 URL 생성 확인
- 각 섹션 페이지: redirect 기반 구현 확인
- `useCaseIdFromUrl.ts`: pathname 기반 ID 추출 확인

---

## 4. 해결 방법 (Solution)

### 4.1 아키텍처 전환

**Before (동적 세그먼트):**
```
/lawyer/cases/{caseId}/detail/
       ↓
S3에서 /lawyer/cases/{caseId}/detail/index.html 찾음
       ↓
없음 → 403 → CloudFront fallback → 랜딩 페이지
```

**After (쿼리 파라미터):**
```
/lawyer/cases/detail/?caseId={caseId}
       ↓
S3에서 /lawyer/cases/detail/index.html 찾음
       ↓
있음 → 200 → React에서 caseId 파라미터로 데이터 fetch
```

### 4.2 코드 변경 사항

**4.2.1 URL 생성 함수 (`portalPaths.ts`):**
```typescript
// Before
export const getCaseDetailPath = (caseId: string) => 
  `/lawyer/cases/${caseId}`;

// After
export const getCaseDetailPath = (caseId: string) => 
  `/lawyer/cases/detail/?caseId=${encodeURIComponent(caseId)}`;
```

**4.2.2 섹션 페이지 (5개 파일):**
```typescript
// Before: redirect 기반
export default function Page() {
  const caseId = useCaseIdFromUrl();
  if (caseId) redirect(`/lawyer/cases/${caseId}`);
  return null;
}

// After: 직접 렌더링
function PageContent() {
  const searchParams = useSearchParams();
  const caseId = searchParams.get('caseId');
  
  if (!caseId) {
    return <ErrorState message="케이스 ID가 필요합니다" />;
  }
  
  return <ClientComponent caseId={caseId} />;
}
```

**4.2.3 수정된 파일 목록:**
| 파일 | 변경 내용 |
|------|----------|
| `src/lib/portalPaths.ts` | 쿼리 파라미터 URL 생성 |
| `src/hooks/useCaseIdFromUrl.ts` | searchParams 지원 추가 |
| `src/app/lawyer/cases/detail/page.tsx` | 직접 렌더링 |
| `src/app/lawyer/cases/procedure/page.tsx` | 직접 렌더링 |
| `src/app/lawyer/cases/assets/page.tsx` | 직접 렌더링 |
| `src/app/lawyer/cases/relations/page.tsx` | 직접 렌더링 |
| `src/app/lawyer/cases/relationship/page.tsx` | 직접 렌더링 |

### 4.3 배포 프로세스
```bash
# 1. 빌드
cd /frontend && npm run build

# 2. S3 동기화
aws s3 sync out/ s3://leh-frontend-prod/ --delete

# 3. CloudFront 캐시 무효화
aws cloudfront create-invalidation \
  --distribution-id E2ZX184AQP0EL5 \
  --paths "/*"
```

### 4.4 검증 결과
```bash
# 모든 섹션 200 OK 확인
curl -sI ".../detail/?caseId=case_c768..."     # 200, 20.7KB
curl -sI ".../procedure/?caseId=case_c768..." # 200, 20.2KB
curl -sI ".../assets/?caseId=case_c768..."    # 200, 20.1KB
curl -sI ".../relations/?caseId=case_c768..." # 200, 21.0KB
curl -sI ".../relationship/?caseId=case_c768..." # 200, 21.2KB
```

---

## 5. 결론 (Conclusion)

### 5.1 핵심 교훈

| # | 교훈 |
|---|------|
| 1 | **Next.js static export는 진정한 동적 라우팅을 지원하지 않음** |
| 2 | S3+CloudFront 환경에서 SPA 라우팅은 쿼리 파라미터 방식이 안전 |
| 3 | CloudFront CustomErrorResponses는 SPA fallback용이지 동적 라우팅 해결책 아님 |
| 4 | generateStaticParams는 빌드 시점에 알려진 유한 집합에만 유효 |

### 5.2 향후 권장사항

**단기:**
- 기존 북마크/링크 대응: 301 redirect 규칙 추가 고려
- SEO 영향 모니터링

**중기:**
- Vercel 배포 전환 검토 (진정한 동적 라우팅 지원)
- 또는 CloudFront Functions로 URL rewrite 구현

**장기:**
- ISR(Incremental Static Regeneration) 활용 가능한 인프라 전환
- 또는 API Gateway + Lambda@Edge 조합

### 5.3 변경 영향도

| 항목 | 영향 |
|------|------|
| URL 구조 | `/cases/{id}` → `/cases/detail/?caseId={id}` |
| 기존 링크 | 깨짐 (redirect 필요) |
| SEO | 쿼리 파라미터 URL은 일반적으로 SEO 불리 |
| UX | 변화 없음 (내부 네비게이션은 자동 적용) |
| 성능 | 변화 없음 |

---

## 부록: 타임라인

| 시간 | 작업 |
|------|------|
| 01:30 | 문제 인지 및 원인 분석 시작 |
| 01:45 | S3 구조 및 CloudFront 설정 확인 |
| 02:00 | 솔루션 설계 (쿼리 파라미터 전환) |
| 02:05 | portalPaths.ts, detail/page.tsx 수정 |
| 02:10 | procedure, assets, relations, relationship 수정 |
| 02:15 | 빌드 및 S3 배포 |
| 02:17 | CloudFront 캐시 무효화 |
| 02:18 | 검증 완료 |

**총 소요시간: 약 48분**
