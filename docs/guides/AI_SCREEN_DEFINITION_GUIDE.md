# AI 화면정의서 작성 가이드

> Claude/GPT가 풍성하고 완성도 높은 UI를 생성하도록 하는 화면정의서 작성법

---

## 1. 화면정의서 기본 구조

```markdown
# [페이지명] 화면정의서

## 1. 페이지 개요
## 2. 레이아웃 구조
## 3. 섹션별 상세 정의
## 4. 컴포넌트 명세
## 5. 상태(State) 정의
## 6. 인터랙션 정의
## 7. 반응형 브레이크포인트
## 8. Mock 데이터
## 9. 스타일 토큰
```

---

## 2. 섹션별 작성 요령

### 2.1 페이지 개요

```markdown
## 1. 페이지 개요

### 목적
- 사용자가 [무엇을] [어떻게] 할 수 있는 페이지

### 진입 경로
- 사이드바 메뉴 > "콘텐츠 관리" 클릭
- URL: /contents

### 사용자 시나리오
1. 사용자가 페이지 진입
2. 전체 콘텐츠 목록 확인
3. 필터/검색으로 원하는 콘텐츠 찾기
4. 수정/삭제/복제 작업 수행
```

**왜 필요한가:** AI가 페이지의 맥락을 이해하고 적절한 UI 요소를 선택함

---

### 2.2 레이아웃 구조

```markdown
## 2. 레이아웃 구조

### 전체 레이아웃
┌─────────────────────────────────────────────┐
│  Header (고정, 64px)                         │
├──────────┬──────────────────────────────────┤
│          │  Page Header                      │
│  Sidebar │  [제목] [액션 버튼]                │
│  (240px) ├──────────────────────────────────┤
│  고정     │  Controls Bar                    │
│          │  [검색] [필터 탭]                  │
│          ├──────────────────────────────────┤
│          │  Main Content Area               │
│          │  [테이블/카드 그리드/리스트]        │
│          ├──────────────────────────────────┤
│          │  Pagination                       │
└──────────┴──────────────────────────────────┘

### 그리드 시스템
- 컨테이너 최대 너비: 1200px (또는 1400px)
- 기본 여백(padding): 24px
- 컬럼 간격(gap): 16px ~ 24px
```

**팁:** ASCII 다이어그램으로 레이아웃을 시각화하면 AI가 구조를 정확히 파악

---

### 2.3 섹션별 상세 정의

```markdown
## 3. 섹션별 상세 정의

### 3.1 Page Header 섹션

#### 구성 요소
| 요소 | 타입 | 내용 | 스타일 |
|------|------|------|--------|
| 제목 | h2 | "콘텐츠 관리" | 28px, bold, #1a1a1a |
| 서브타이틀 | p | "총 24개의 콘텐츠" | 14px, #6b7280 |
| 메인 버튼 | button | "새 콘텐츠 만들기" | Primary, 아이콘: ➕ |

#### 레이아웃
- display: flex
- justify-content: space-between
- align-items: center
- margin-bottom: 24px

---

### 3.2 Controls Bar 섹션

#### 구성 요소
| 요소 | 타입 | 설명 |
|------|------|------|
| 검색창 | input | 아이콘(🔍) + placeholder "콘텐츠 검색..." |
| 필터 탭 | button group | 전체, 발행됨, 예약됨, 작성 중 |

#### 필터 탭 상태
- 기본: 흰 배경, 회색 테두리
- 활성: 파란 배경(#e8f0fe), 파란 테두리(#1967d2)
- 호버: 연회색 배경(#f9fafb)

---

### 3.3 Main Content 섹션 - 테이블 형태

#### 테이블 컬럼 정의
| 컬럼명 | 너비 | 정렬 | 내용 |
|--------|------|------|------|
| 제목 | flex-1 | left | 텍스트 (bold) |
| 유형 | 100px | center | 텍스트 |
| 플랫폼 | 120px | center | 텍스트 |
| 상태 | 100px | center | 상태 배지 |
| 날짜 | 120px | center | YYYY-MM-DD |
| 조회수 | 80px | right | 숫자 (천단위 콤마) |
| 작업 | 100px | center | 아이콘 버튼 3개 |

#### 상태 배지 스타일
| 상태 | 배경색 | 텍스트색 | 아이콘 |
|------|--------|----------|--------|
| 발행됨 | #d1fae5 | #065f46 | ✅ (선택) |
| 예약됨 | #dbeafe | #1e40af | 📅 (선택) |
| 작성 중 | #fef3c7 | #92400e | ✏️ (선택) |

#### 행(Row) 스타일
- 기본: 흰 배경, 하단 border 1px #e5e7eb
- 호버: 연회색 배경(#f9fafb)
- 높이: 56px ~ 64px
```

**핵심:** 각 요소의 **크기, 색상, 간격**을 구체적으로 명시

---

### 2.4 컴포넌트 명세

```markdown
## 4. 컴포넌트 명세

### 4.1 StatCard 컴포넌트

#### Props
| Prop | Type | Required | Description |
|------|------|----------|-------------|
| icon | string (emoji) | Yes | 카드 아이콘 |
| label | string | Yes | 지표 이름 |
| value | string | Yes | 지표 값 |
| change | string | No | 변화율 (+12%, -5%) |
| trend | 'up' \| 'down' \| 'neutral' | No | 트렌드 방향 |

#### 렌더링 구조
```jsx
<div className="stat-card">
  <div className="stat-icon">{icon}</div>
  <div className="stat-content">
    <span className="stat-label">{label}</span>
    <span className="stat-value">{value}</span>
    {change && (
      <span className={`stat-change ${trend}`}>{change}</span>
    )}
  </div>
</div>
```

#### 스타일 명세
- 카드: 흰 배경, border-radius 12px, shadow-sm, padding 20px
- 아이콘 영역: 56x56px, 연파랑 배경(#f0f4ff), border-radius 12px
- 값: 28px, bold
- 변화율(up): 초록(#059669), 변화율(down): 빨강(#dc2626)

---

### 4.2 ActionButton 컴포넌트

#### Variants
| Variant | 용도 | 스타일 |
|---------|------|--------|
| primary | 주요 액션 | 파란 배경(#1967d2), 흰 텍스트 |
| secondary | 보조 액션 | 흰 배경, 회색 테두리 |
| ghost | 테이블 내 액션 | 투명 배경, 호버 시 회색 배경 |
| danger | 삭제 등 위험 | 빨간 배경(#dc2626), 흰 텍스트 |
| ai | AI 기능 | 그라데이션(#667eea → #764ba2) |

#### 크기(Size)
| Size | padding | font-size | border-radius |
|------|---------|-----------|---------------|
| sm | 6px 12px | 12px | 6px |
| md | 10px 20px | 14px | 8px |
| lg | 14px 28px | 16px | 10px |
```

---

### 2.5 상태(State) 정의

```markdown
## 5. 상태(State) 정의

### 로컬 상태
| State | Type | Initial | Description |
|-------|------|---------|-------------|
| filter | string | 'all' | 현재 선택된 필터 |
| searchTerm | string | '' | 검색어 |
| currentPage | number | 1 | 현재 페이지 |
| selectedItems | string[] | [] | 선택된 항목 ID 배열 |
| isModalOpen | boolean | false | 모달 표시 여부 |

### 파생 상태 (Computed)
| State | 계산 로직 |
|-------|----------|
| filteredContents | filter, searchTerm 적용한 목록 |
| totalPages | Math.ceil(filteredContents.length / pageSize) |
| isEmpty | filteredContents.length === 0 |

### 로딩/에러 상태
| State | UI 표현 |
|-------|---------|
| isLoading | 스켈레톤 UI 또는 스피너 |
| error | 에러 메시지 카드 + 재시도 버튼 |
| isEmpty | Empty State (아이콘 + 메시지 + CTA) |
```

---

### 2.6 인터랙션 정의

```markdown
## 6. 인터랙션 정의

### 6.1 버튼 인터랙션

| 요소 | 이벤트 | 동작 |
|------|--------|------|
| "새 콘텐츠 만들기" | click | /create 페이지로 이동 |
| 필터 탭 | click | filter 상태 변경, 목록 필터링 |
| 검색창 | input | searchTerm 상태 변경 (debounce 300ms) |
| 행 수정 버튼(✏️) | click | /edit/{id} 페이지로 이동 |
| 행 복제 버튼(📋) | click | 복제 확인 모달 표시 |
| 행 삭제 버튼(🗑️) | click | 삭제 확인 모달 표시 |

### 6.2 호버/포커스 효과

| 요소 | 호버 효과 | 전환 시간 |
|------|----------|----------|
| 버튼(Primary) | 배경색 어둡게 (#1557b0) | 0.2s |
| 버튼(AI) | translateY(-2px), shadow 증가 | 0.2s |
| 테이블 행 | 배경색 #f9fafb | 0.15s |
| 카드 | shadow 증가, translateY(-2px) | 0.2s |
| 링크 | 밑줄 표시 | 즉시 |

### 6.3 애니메이션

| 상황 | 애니메이션 |
|------|-----------|
| 페이지 진입 | fade-in (opacity 0→1, 0.3s) |
| 모달 열림 | scale(0.95→1) + fade-in, 0.2s |
| 모달 닫힘 | scale(1→0.95) + fade-out, 0.15s |
| 토스트 알림 | slide-in from top + fade-in |
| 목록 필터링 | 부드러운 높이 변화 (선택) |
```

---

### 2.7 반응형 브레이크포인트

```markdown
## 7. 반응형 브레이크포인트

### 브레이크포인트 정의
| 이름 | 범위 | 주요 변경 |
|------|------|----------|
| Desktop | ≥1024px | 기본 레이아웃 |
| Tablet | 768px~1023px | 사이드바 축소/숨김 |
| Mobile | <768px | 단일 컬럼, 카드 전환 |

### 레이아웃 변경 상세

#### Desktop (≥1024px)
- 사이드바: 240px 고정
- 콘텐츠: 나머지 영역
- 테이블: 전체 컬럼 표시
- 그리드: 4열

#### Tablet (768px~1023px)
- 사이드바: 64px (아이콘만)
- 페이지 헤더: flex-row 유지
- 테이블: 일부 컬럼 숨김 (조회수, 날짜)
- 그리드: 2열

#### Mobile (<768px)
- 사이드바: 숨김 (햄버거 메뉴)
- 페이지 헤더: flex-column (버튼 아래로)
- 테이블 → 카드 리스트로 전환
- 그리드: 1열
- 검색/필터: 스택 레이아웃

### 숨김/표시 규칙
| 요소 | Desktop | Tablet | Mobile |
|------|---------|--------|--------|
| 사이드바 라벨 | ✅ | ❌ | ❌ |
| 테이블 조회수 컬럼 | ✅ | ❌ | ❌ |
| 테이블 날짜 컬럼 | ✅ | ✅ | ❌ |
| 카드형 목록 | ❌ | ❌ | ✅ |
```

---

### 2.8 Mock 데이터

```markdown
## 8. Mock 데이터

### 통계 데이터
```javascript
const stats = [
  { icon: '📝', label: '총 콘텐츠', value: '24', change: '+12%', trend: 'up' },
  { icon: '✨', label: '이번 주 생성', value: '8', change: '+25%', trend: 'up' },
  { icon: '📅', label: '예약된 포스트', value: '12', change: '+8%', trend: 'up' },
  { icon: '👀', label: '총 조회수', value: '1.2K', change: '+15%', trend: 'up' },
];
```

### 콘텐츠 목록 데이터
```javascript
const contents = [
  {
    id: '1',
    title: '신제품 런칭 홍보 콘텐츠',
    type: '소셜 미디어',
    platform: 'Instagram',
    status: '발행됨',    // '발행됨' | '예약됨' | '작성 중'
    date: '2025-11-10',
    views: 1250,
    thumbnail: '/images/thumb-1.jpg',  // 선택
  },
  {
    id: '2',
    title: '할인 이벤트 안내',
    type: '블로그',
    platform: 'Naver Blog',
    status: '예약됨',
    date: '2025-11-15',
    views: 0,
  },
  // ... 최소 5개 이상의 다양한 상태 데이터
];
```

### 필터 옵션
```javascript
const filterOptions = [
  { id: 'all', label: '전체', count: 24 },
  { id: 'published', label: '발행됨', count: 15 },
  { id: 'scheduled', label: '예약됨', count: 6 },
  { id: 'draft', label: '작성 중', count: 3 },
];
```
```

**중요:** Mock 데이터는 **다양한 케이스**를 포함해야 함 (긴 제목, 0 조회수, 다양한 상태 등)

---

### 2.9 스타일 토큰

```markdown
## 9. 스타일 토큰

### 색상 (Colors)
```css
/* Primary */
--color-primary: #1967d2;
--color-primary-hover: #1557b0;
--color-primary-light: #e8f0fe;

/* Neutral */
--color-text-primary: #1a1a1a;
--color-text-secondary: #6b7280;
--color-text-muted: #9ca3af;
--color-border: #e5e7eb;
--color-border-hover: #cbd5e1;
--color-background: #f9fafb;
--color-surface: #ffffff;

/* Status */
--color-success: #059669;
--color-success-bg: #d1fae5;
--color-warning: #d97706;
--color-warning-bg: #fef3c7;
--color-error: #dc2626;
--color-error-bg: #fee2e2;
--color-info: #1e40af;
--color-info-bg: #dbeafe;

/* Gradients */
--gradient-ai: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### 타이포그래피
```css
/* Headings */
--font-h1: 32px / 1.2 / 700;
--font-h2: 28px / 1.3 / 700;
--font-h3: 20px / 1.4 / 600;
--font-h4: 16px / 1.4 / 600;

/* Body */
--font-body: 14px / 1.6 / 400;
--font-body-sm: 13px / 1.5 / 400;
--font-body-lg: 16px / 1.6 / 400;

/* Labels */
--font-label: 12px / 1.4 / 500;
--font-button: 14px / 1 / 600;
```

### 간격 (Spacing)
```css
--space-xs: 4px;
--space-sm: 8px;
--space-md: 12px;
--space-lg: 16px;
--space-xl: 24px;
--space-2xl: 32px;
--space-3xl: 48px;
```

### 그림자 (Shadows)
```css
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
--shadow-md: 0 1px 3px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 4px 6px rgba(0, 0, 0, 0.1);
--shadow-xl: 0 10px 15px rgba(0, 0, 0, 0.1);
```

### 모서리 (Border Radius)
```css
--radius-sm: 4px;
--radius-md: 8px;
--radius-lg: 12px;
--radius-xl: 16px;
--radius-full: 9999px;
```

### 전환 (Transitions)
```css
--transition-fast: 0.15s ease;
--transition-normal: 0.2s ease;
--transition-slow: 0.3s ease;
```
```

---

## 3. AI 프롬프트 최적화 표현법

### 3.1 피해야 할 표현 (모호함)

```markdown
❌ "예쁜 대시보드 만들어줘"
❌ "통계 보여주는 화면"
❌ "사용자가 편하게 쓸 수 있게"
❌ "적절한 색상으로"
❌ "반응형으로"
```

### 3.2 권장하는 표현 (구체적)

```markdown
✅ "4개의 통계 카드를 가로 그리드로 배치, 각 카드는 아이콘(32px) + 라벨 + 값(28px bold) + 변화율 포함"

✅ "테이블 헤더는 #f9fafb 배경, 본문 행은 호버 시 같은 색상, 행 높이 56px"

✅ "상태 배지: 발행됨(#d1fae5 배경, #065f46 텍스트), 예약됨(#dbeafe, #1e40af)"

✅ "768px 미만에서 테이블을 카드 리스트로 전환, 각 카드에 제목/상태/날짜 표시"

✅ "Primary 버튼 호버 시 배경 #1557b0으로 변경, transition 0.2s"
```

### 3.3 AI 지시문 템플릿

```markdown
## 구현 요청

### 페이지: [페이지명]

### 참조 문서
- 화면정의서: `docs/screens/[페이지명].md`
- 스타일 토큰: `docs/design/tokens.md`
- 컴포넌트 라이브러리: `src/components/`

### 구현 범위
1. 페이지 컴포넌트 (`src/pages/[PageName].js`)
2. 페이지 스타일 (`src/pages/[PageName].css`)
3. 필요한 하위 컴포넌트

### 필수 요구사항
- [ ] Mock 데이터로 작동하는 UI
- [ ] 정의된 모든 상태(state) 구현
- [ ] 호버/포커스 인터랙션
- [ ] 반응형 (Desktop/Tablet/Mobile)
- [ ] Empty State UI
- [ ] Loading State UI (스켈레톤)

### 스타일 가이드
- CSS 파일 분리 (컴포넌트당 1개)
- BEM 또는 컴포넌트 기반 클래스명
- CSS 변수 활용 (색상, 간격)
- 모든 transition에 시간 명시

### 품질 체크리스트
- [ ] 아이콘은 이모지 또는 지정된 아이콘 라이브러리 사용
- [ ] 버튼에 hover 상태 있음
- [ ] 입력 필드에 focus 스타일 있음
- [ ] 클릭 가능한 요소에 cursor: pointer
- [ ] 적절한 여백과 간격
```

---

## 4. 화면정의서 체크리스트

구현 요청 전 다음 항목이 모두 정의되었는지 확인:

### 필수 항목
- [ ] 페이지 목적과 사용자 시나리오
- [ ] ASCII 레이아웃 다이어그램
- [ ] 모든 섹션별 구성 요소
- [ ] 각 요소의 크기/색상/간격 명시
- [ ] 상태(state) 목록과 초기값
- [ ] 주요 인터랙션 (클릭, 호버)
- [ ] 반응형 브레이크포인트별 변경사항
- [ ] 충분한 Mock 데이터 (다양한 케이스)

### 권장 항목
- [ ] 스타일 토큰 정의
- [ ] 컴포넌트 Props 명세
- [ ] 애니메이션 상세
- [ ] Empty/Loading/Error 상태 UI
- [ ] 접근성 고려사항 (ARIA)

---

## 5. 예시: 대시보드 화면정의서

아래는 실제 작성 예시입니다.

---

# Dashboard 화면정의서

## 1. 페이지 개요

### 목적
콘텐츠 현황을 한눈에 파악하고 빠른 작업에 접근하는 메인 페이지

### URL
`/` 또는 `/dashboard`

### 사용자 시나리오
1. 로그인 후 첫 진입
2. 주요 지표 확인 (총 콘텐츠, 주간 생성, 예약, 조회수)
3. 최근 콘텐츠 상태 확인
4. 빠른 작업 버튼으로 기능 이동

---

## 2. 레이아웃 구조

```
┌─────────────────────────────────────────────────────┐
│  Page Header                                        │
│  [대시보드 h2]                    [새 콘텐츠 만들기]  │
├─────────────────────────────────────────────────────┤
│  Stats Grid (4열)                                   │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │ 📝 24   │ │ ✨ 8    │ │ 📅 12   │ │ 👀 1.2K │   │
│  │ +12%    │ │ +25%    │ │ +8%     │ │ +15%    │   │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘   │
├────────────────────────────┬────────────────────────┤
│  Recent Contents           │  Quick Actions         │
│  ┌──────────────────────┐  │  ┌────────┐ ┌────────┐│
│  │ 콘텐츠1    발행됨    │  │  │✨ 생성 │ │📋 템플릿││
│  │ 콘텐츠2    예약됨    │  │  ├────────┤ ├────────┤│
│  │ 콘텐츠3    작성 중   │  │  │📅 예약 │ │📊 분석 ││
│  └──────────────────────┘  │  └────────┘ └────────┘│
└────────────────────────────┴────────────────────────┘
```

---

## 3. 섹션별 상세

### 3.1 Stats Grid

| 카드 | 아이콘 | 라벨 | 값 | 변화율 |
|------|--------|------|-----|--------|
| 1 | 📝 | 총 콘텐츠 | 24 | +12% |
| 2 | ✨ | 이번 주 생성 | 8 | +25% |
| 3 | 📅 | 예약된 포스트 | 12 | +8% |
| 4 | 👀 | 총 조회수 | 1.2K | +15% |

**카드 스타일:**
- 배경: white
- padding: 20px
- border-radius: 12px
- shadow: 0 1px 3px rgba(0,0,0,0.1)
- 아이콘 영역: 56x56px, #f0f4ff 배경

### 3.2 Recent Contents

| 컬럼 | 내용 |
|------|------|
| 제목 | 텍스트, 16px, bold |
| 메타 | 유형 + 날짜, 13px, #6b7280 |
| 상태 | 상태 배지 |

**리스트 아이템 스타일:**
- padding: 16px
- border-bottom: 1px solid #e5e7eb
- 호버: 배경 #f9fafb

### 3.3 Quick Actions

| 버튼 | 아이콘 | 라벨 | 이동 |
|------|--------|------|------|
| 1 | ✨ | 콘텐츠 생성 | /create |
| 2 | 📋 | 템플릿 선택 | /templates |
| 3 | 📅 | 스케줄 설정 | /schedule |
| 4 | 📊 | 분석 보기 | /analytics |

**버튼 스타일:**
- display: flex, flex-direction: column
- align-items: center
- gap: 8px
- padding: 20px
- border: 1px solid #e5e7eb
- border-radius: 12px
- 호버: border-color #1967d2, 배경 #f0f4ff

---

## 4. Mock 데이터

```javascript
const stats = [
  { icon: '📝', label: '총 콘텐츠', value: '24', change: '+12%' },
  { icon: '✨', label: '이번 주 생성', value: '8', change: '+25%' },
  { icon: '📅', label: '예약된 포스트', value: '12', change: '+8%' },
  { icon: '👀', label: '총 조회수', value: '1.2K', change: '+15%' },
];

const recentContents = [
  { id: 1, title: '신제품 런칭 홍보 콘텐츠', type: '소셜 미디어', status: '발행됨', date: '2025-11-10' },
  { id: 2, title: '할인 이벤트 안내', type: '블로그', status: '예약됨', date: '2025-11-15' },
  { id: 3, title: '고객 리뷰 소개 영상', type: '비디오', status: '작성 중', date: '2025-11-12' },
];

const quickActions = [
  { icon: '✨', label: '콘텐츠 생성', path: '/create' },
  { icon: '📋', label: '템플릿 선택', path: '/templates' },
  { icon: '📅', label: '스케줄 설정', path: '/schedule' },
  { icon: '📊', label: '분석 보기', path: '/analytics' },
];
```

---

## 5. 반응형

| 요소 | Desktop | Tablet | Mobile |
|------|---------|--------|--------|
| Stats Grid | 4열 | 2열 | 1열 |
| Content/Actions | 2열 | 1열 | 1열 |
| Quick Actions | 2x2 그리드 | 4x1 | 2x2 |

---

이 가이드를 따라 화면정의서를 작성하면 AI가 풍성하고 완성도 높은 UI를 생성합니다.
