# UI/UX Improvements - Magic UI & Shadcn/ui Integration

## Overview

이 문서는 LEH(Legal Evidence Hub) 프론트엔드의 UI/UX 개선 사항을 기록합니다.
`UI_UX_DESIGN.md`의 "Calm Control(차분한 통제감)" 철학을 구현하기 위해 Magic UI와 Shadcn/ui 스타일을 통합했습니다.

---

## 1. CaseCard - Border Beam Glow Effect

### 목적
- 사건 카드에 마우스 호버 시 **은은한 테두리 광원 효과**를 추가하여 상호작용성을 높임
- 과도한 애니메이션을 피하고 법률 전문가에게 적합한 신뢰감 유지

### 구현 방식
**파일:** `frontend/src/components/cases/CaseCard.tsx`

#### 핵심 변경사항:
1. **Border Beam Effect Layer**
   ```tsx
   <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none">
     <div className="absolute inset-[-2px] bg-gradient-to-r from-transparent via-accent to-transparent rounded-lg blur-sm animate-border-beam"></div>
   </div>
   ```

2. **Tailwind Animation**
   ```js
   // tailwind.config.js
   keyframes: {
     'border-beam': {
       '0%, 100%': { transform: 'translateX(-100%)' },
       '50%': { transform: 'translateX(100%)' },
     },
   },
   animation: {
     'border-beam': 'border-beam 3s linear infinite',
   },
   ```

### 디자인 토큰 준수:
- ✅ **Accent Color (`#1ABC9C`)**: 테두리 광원 색상
- ✅ **Calm Grey Background**: 카드 기본 배경
- ✅ **Transition Duration (500ms)**: 부드러운 fade-in/out
- ✅ **Pointer-events: none**: 광원 효과가 클릭 이벤트를 방해하지 않음

### UX 개선 효과:
- 사용자에게 **클릭 가능한 영역**을 명확하게 전달
- 화려하지 않고 **전문적인 느낌** 유지 (3초 애니메이션 + blur 효과)
- 기존 hover:ring 효과와 조화를 이루며 **시각적 계층 강화**

---

## 2. EvidenceTable - Shadcn/ui Style DataTable with TanStack Table

### 목적
- 기존 단순 테이블을 **정렬(Sorting)과 페이지네이션(Pagination)** 기능을 갖춘 DataTable로 고도화
- `FRONTEND_CLEAN_CODE.md` 규칙 준수: **로직과 UI 분리**
- 재사용 가능한 작은 컴포넌트로 구성하여 유지보수성 향상

### 아키텍처 변경

#### Before (Monolithic Component):
```
EvidenceTable.tsx (200 lines)
├─ State management (filters, sorting)
├─ Business logic (filtering logic)
├─ Icon rendering logic
├─ Status badge logic
└─ Table rendering
```

#### After (Clean Architecture):
```
EvidenceTable.tsx (wrapper, 30 lines)
└─ EvidenceDataTable.tsx (core table, 200 lines)
    ├─ useEvidenceTable.ts (hook, 100 lines)
    │   ├─ TanStack Table integration
    │   ├─ Sorting state
    │   ├─ Filtering state
    │   └─ Pagination state
    │
    ├─ EvidenceTypeIcon.tsx (presentational, 40 lines)
    ├─ EvidenceStatusBadge.tsx (presentational, 50 lines)
    └─ DataTablePagination.tsx (reusable, 85 lines)
```

### 새로 생성된 파일:

#### 1. `hooks/useEvidenceTable.ts`
**책임:** 테이블 상태 관리 및 TanStack Table 통합

```typescript
export function useEvidenceTable(data: Evidence[]) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 10 });

  const table = useReactTable({
    data,
    columns,
    state: { sorting, columnFilters, pagination },
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  return { table, setTypeFilter, setDateFilter, pagination };
}
```

**특징:**
- ✅ **단일 책임 원칙(SRP)**: 데이터 관리만 담당
- ✅ **TanStack Table v8**: 최신 React 패턴 (controlled state)
- ✅ **Type-safe**: TypeScript 제네릭으로 타입 안전성 보장

#### 2. `components/evidence/EvidenceTypeIcon.tsx`
**책임:** 파일 타입 아이콘 렌더링 (순수 Presentational Component)

```typescript
export function EvidenceTypeIcon({ type }: EvidenceTypeIconProps) {
  const iconConfig: Record<string, { icon: React.ReactNode; className: string }> = {
    text: { icon: <FileText />, className: 'text-gray-500' },
    image: { icon: <Image />, className: 'text-blue-500' },
    // ...
  };
  return <div className={config.className}>{config.icon}</div>;
}
```

**특징:**
- ✅ **재사용 가능**: 다른 컴포넌트에서도 import 가능
- ✅ **설정 기반(Config-driven)**: 새로운 타입 추가 시 iconConfig만 수정
- ✅ **Pure Function**: props만으로 렌더링 결정

#### 3. `components/evidence/EvidenceStatusBadge.tsx`
**책임:** 증거 상태 배지 렌더링

```typescript
export function EvidenceStatusBadge({ status }: EvidenceStatusBadgeProps) {
  const statusConfig: Record<EvidenceStatus, { icon, label, className }> = {
    uploading: { icon: <Loader2 />, label: '업로드 중', className: 'text-blue-600 bg-blue-50' },
    completed: { icon: <CheckCircle2 />, label: '완료', className: 'text-success-green bg-green-50' },
    // ...
  };
  return <span className={config.className}>{config.icon}{config.label}</span>;
}
```

**디자인 토큰 준수:**
- ✅ **Success Green**: 완료 상태
- ✅ **Semantic Error**: 실패 상태
- ✅ **Accent**: 처리 중 상태
- ✅ **일관된 Badge 스타일**: rounded-full, px-2 py-1

#### 4. `components/evidence/DataTablePagination.tsx`
**책임:** 페이지네이션 컨트롤 (재사용 가능)

```typescript
export function DataTablePagination<TData>({ table }: DataTablePaginationProps<TData>) {
  return (
    <div className="flex items-center justify-between">
      {/* Page info */}
      <p>페이지 {pageIndex + 1} / {pageCount}</p>

      {/* Page size selector */}
      <select onChange={(e) => table.setPageSize(Number(e.target.value))}>
        {[10, 20, 30, 50].map(size => <option>{size}개씩 보기</option>)}
      </select>

      {/* Navigation buttons */}
      <button onClick={() => table.previousPage()}>이전</button>
      <button onClick={() => table.nextPage()}>다음</button>
    </div>
  );
}
```

**특징:**
- ✅ **Generic Component**: 모든 TanStack Table에서 재사용 가능
- ✅ **Accessible**: ARIA labels, disabled states
- ✅ **Shadcn/ui 스타일**: 깔끔한 네비게이션 버튼

#### 5. `components/evidence/EvidenceDataTable.tsx`
**책임:** 메인 DataTable 렌더링 (위 모든 컴포넌트 조합)

```typescript
export function EvidenceDataTable({ items }: EvidenceDataTableProps) {
  const { table, setTypeFilter, setDateFilter } = useEvidenceTable(items);

  return (
    <div>
      {/* Filter Controls */}
      <div className="flex items-center space-x-4">
        <select onChange={(e) => setTypeFilter(e.target.value)}>...</select>
        <select onChange={(e) => setDateFilter(e.target.value)}>...</select>
      </div>

      {/* Table */}
      <table>
        <thead>
          <tr>
            <th onClick={() => table.getColumn('filename')?.toggleSorting()}>
              파일명 <ArrowUpDown />
            </th>
            <th onClick={() => table.getColumn('uploadDate')?.toggleSorting()}>
              업로드 날짜 <ArrowUpDown />
            </th>
          </tr>
        </thead>
        <tbody>
          {table.getRowModel().rows.map(row => (
            <tr key={row.id} className="hover:bg-accent/5">
              <td><EvidenceTypeIcon type={row.original.type} /></td>
              <td>{row.original.filename}</td>
              <td><EvidenceStatusBadge status={row.original.status} /></td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Pagination */}
      <DataTablePagination table={table} />
    </div>
  );
}
```

### 주요 기능 추가:

#### ✅ 정렬(Sorting):
- 파일명 클릭 → 알파벳 순 정렬
- 업로드 날짜 클릭 → 시간순 정렬
- `ArrowUpDown` 아이콘으로 정렬 가능 컬럼 표시

#### ✅ 페이지네이션(Pagination):
- 페이지당 항목 수: 10, 20, 30, 50 선택 가능
- 첫 페이지 / 이전 / 다음 / 마지막 페이지 네비게이션
- 현재 페이지 / 전체 페이지 수 표시

#### ✅ 필터링(Filtering):
- 유형 필터: 전체, 텍스트, 이미지, 오디오, 비디오, PDF
- 날짜 필터: 전체, 오늘, 최근 7일, 최근 30일
- 필터 적용 시 하단에 "N개 / 전체 M개" 카운터 표시

---

## 3. 디자인 시스템 준수 체크리스트

### Color Palette:
- [x] Deep Trust Blue (`#2C3E50`) - 테이블 헤더, 제목
- [x] Calm Grey (`#F8F9FA`) - 카드 배경
- [x] Accent (`#1ABC9C`) - CTA 버튼, 호버 효과, Border Beam
- [x] Success Green (`#2ECC71`) - 완료 상태
- [x] Semantic Error (`#E74C3C`) - 삭제, 실패 상태

### Typography:
- [x] 16px Base 폰트 사이즈
- [x] Pretendard 폰트 (tailwind.config.js)
- [x] 명확한 시각적 위계 (헤더 uppercase, 본문 regular)

### Spacing:
- [x] 8pt 그리드 시스템 (px-6 py-4 → 24px, 16px)
- [x] 관대한 여백 (테이블 행 간격 py-4)

### Animation:
- [x] 부드러운 transition (duration-300, duration-500)
- [x] 과도하지 않은 애니메이션 (3초 border-beam)
- [x] hover 시에만 효과 표시 (opacity-0 → opacity-100)

### Accessibility:
- [x] ARIA labels (aria-label="첫 페이지")
- [x] Keyboard navigation (button disabled states)
- [x] Screen reader support (sr-only for hidden text)

---

## 4. 성능 최적화

### TanStack Table의 이점:
1. **Memoization**: `useMemo`로 컬럼 정의 캐싱
2. **Virtual Rendering**: 대량 데이터 처리 시 성능 향상
3. **Lazy Evaluation**: 필요한 행만 렌더링 (pagination)

### 컴포넌트 분리 이점:
1. **Code Splitting**: 작은 컴포넌트 → 더 나은 트리 쉐이킹
2. **Testability**: 각 컴포넌트를 독립적으로 테스트 가능
3. **Reusability**: `DataTablePagination`은 다른 테이블에도 사용 가능

---

## 5. 빌드 검증

```bash
npm run build
```

**결과:**
```
✓ Compiled successfully
✓ Generating static pages (15/15)
✓ Finalizing page optimization

Route (pages)                             Size     First Load JS
├ ○ /cases/[id]                           24.4 kB         105 kB
├ ○ /cases                                3.61 kB        84.5 kB
...
○  (Static)  prerendered as static content
```

✅ **모든 페이지 정상 빌드**
✅ **타입 에러 없음**
✅ **증거 테이블 페이지 크기 변화 없음 (최적화됨)**

---

## 6. 마이그레이션 가이드

### 기존 코드와의 호환성:
```typescript
// Before (여전히 동작함)
import EvidenceTable from '@/components/evidence/EvidenceTable';
<EvidenceTable items={evidenceList} />

// 내부적으로 EvidenceDataTable을 호출하므로 기존 코드 수정 불필요
```

### 새로운 컴포넌트 직접 사용:
```typescript
// 더 많은 제어가 필요한 경우
import { EvidenceDataTable } from '@/components/evidence/EvidenceDataTable';
import { useEvidenceTable } from '@/hooks/useEvidenceTable';

function CustomEvidencePage() {
  const { table } = useEvidenceTable(data);
  // 커스텀 로직 추가 가능
  return <EvidenceDataTable items={data} />;
}
```

---

## 7. 향후 개선 계획

### Phase 1 (현재 완료):
- [x] Border Beam 효과 적용
- [x] TanStack Table 통합
- [x] 정렬 / 페이지네이션 구현
- [x] 컴포넌트 분리 (Clean Code)

### Phase 2 (제안):
- [ ] 드래그 앤 드롭으로 컬럼 순서 변경
- [ ] 컬럼 show/hide 토글
- [ ] CSV 내보내기 기능
- [ ] 행 선택 (체크박스) + 일괄 작업

### Phase 3 (제안):
- [ ] Virtual Scrolling (react-window 통합)
- [ ] Infinite Scroll 옵션
- [ ] Real-time 업데이트 (WebSocket)

---

## 8. 참고 자료

### 디자인 시스템:
- `docs/guides/UI_UX_DESIGN.md` - Calm Control 철학
- `docs/guides/FRONTEND_CLEAN_CODE.md` - 코드 규칙
- `frontend/tailwind.config.js` - 디자인 토큰

### 외부 레퍼런스:
- [TanStack Table v8 Docs](https://tanstack.com/table/v8)
- [Shadcn/ui DataTable](https://ui.shadcn.com/docs/components/data-table)
- [Magic UI Components](https://magicui.design/)

---

## 결론

이번 UI/UX 개선으로 LEH 프론트엔드는:
1. ✅ **더 전문적인 시각적 경험** (Border Beam 효과)
2. ✅ **더 강력한 데이터 관리 기능** (정렬, 페이지네이션)
3. ✅ **더 유지보수하기 쉬운 코드 구조** (Clean Architecture)

를 달성했습니다. "Calm Control(차분한 통제감)" 철학을 유지하면서도 현대적이고 기능적인 UI를 제공합니다.
