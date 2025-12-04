# Quickstart: Role-Based UI System

**Feature ID**: 003-role-based-ui
**Date**: 2025-12-04

This guide helps developers quickly set up and start working on the Role-Based UI feature.

---

## Prerequisites

### Tools Required
- Node.js 18+ (frontend)
- Python 3.11+ (backend)
- PostgreSQL 14+ (database)
- Docker (optional, for local services)

### Accounts/Keys
- Kakao Developers account (for Maps API)
- Existing LEH development environment

---

## Quick Setup

### 1. Create Feature Branch

```bash
git checkout dev
git pull origin dev
git checkout -b 003-role-based-ui
```

### 2. Install New Dependencies

**Frontend:**
```bash
cd frontend
npm install react-kakao-maps-sdk react-big-calendar date-fns recharts jwt-decode
npm install -D @types/react-big-calendar
```

**Backend:**
No new Python dependencies required.

### 3. Environment Variables

Add to root `.env`:
```bash
# Kakao Maps API (get from https://developers.kakao.com)
NEXT_PUBLIC_KAKAO_MAP_KEY=your_kakao_javascript_key
```

### 4. Database Migration

```bash
cd backend

# Create migration
alembic revision --autogenerate -m "add_role_based_ui_tables"

# Review and run migration
alembic upgrade head
```

### 5. Verify Setup

```bash
# Start backend
cd backend
uvicorn app.main:app --reload

# In another terminal, start frontend
cd frontend
npm run dev

# Test new role redirect
# Login as existing user, should redirect to /lawyer/dashboard
```

---

## Development Workflow

### Phase Order

1. **Phase 1: Foundation** (US1) - Role system
2. **Phase 2: Lawyer MVP** (US2, US3) - Lawyer dashboard & cases
3. **Phase 3: Client Portal** (US4)
4. **Phase 4: Detective Portal** (US5)
5. **Phase 5: Cross-Cutting** (US6, US7) - Messaging, Calendar
6. **Phase 6: Billing** (US8)

### Starting Point (US1 - Foundation)

#### Backend: Add Roles

```python
# backend/app/db/models.py
class UserRole(str, enum.Enum):
    LAWYER = "lawyer"
    STAFF = "staff"
    ADMIN = "admin"
    CLIENT = "client"      # Add
    DETECTIVE = "detective" # Add
```

#### Frontend: Role Middleware

```typescript
// frontend/src/middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { jwtDecode } from 'jwt-decode';

export function middleware(request: NextRequest) {
    const token = request.cookies.get('access_token')?.value;

    if (!token) {
        return NextResponse.redirect(new URL('/login', request.url));
    }

    const { role } = jwtDecode<{ role: string }>(token);
    const path = request.nextUrl.pathname;

    // Role-based redirects
    if (path === '/dashboard') {
        return NextResponse.redirect(new URL(`/${role}/dashboard`, request.url));
    }

    return NextResponse.next();
}

export const config = {
    matcher: ['/lawyer/:path*', '/client/:path*', '/detective/:path*', '/dashboard'],
};
```

#### Frontend: Portal Layouts

Create layout for each portal:

```typescript
// frontend/src/app/lawyer/layout.tsx
export default function LawyerLayout({ children }: { children: React.ReactNode }) {
    return (
        <div className="flex min-h-screen">
            <LawyerNav />
            <main className="flex-1 p-6">{children}</main>
        </div>
    );
}
```

---

## Key Files to Create

### Priority 1 (Foundation)
| File | Purpose |
|:-----|:--------|
| `frontend/src/middleware.ts` | Role-based routing |
| `frontend/src/app/lawyer/layout.tsx` | Lawyer portal layout |
| `frontend/src/app/client/layout.tsx` | Client portal layout |
| `frontend/src/app/detective/layout.tsx` | Detective portal layout |
| `frontend/src/hooks/useRole.ts` | Role checking hook |

### Priority 2 (Lawyer MVP)
| File | Purpose |
|:-----|:--------|
| `frontend/src/app/lawyer/dashboard/page.tsx` | Lawyer dashboard |
| `frontend/src/components/lawyer/StatsCard.tsx` | Stats display |
| `frontend/src/components/charts/CaseStatsChart.tsx` | Charts |
| `backend/app/api/lawyer_portal.py` | Lawyer endpoints |

### Priority 3 (Client Portal)
| File | Purpose |
|:-----|:--------|
| `frontend/src/app/client/dashboard/page.tsx` | Client dashboard |
| `frontend/src/components/client/ProgressTracker.tsx` | Progress display |
| `backend/app/api/client_portal.py` | Client endpoints |

---

## Testing New Features

### Create Test Users

```sql
-- Add CLIENT role user
INSERT INTO users (id, email, role, password_hash, is_active)
VALUES ('client-test-001', 'client@test.com', 'client', 'hashed_pw', true);

-- Add DETECTIVE role user
INSERT INTO users (id, email, role, password_hash, is_active)
VALUES ('detective-test-001', 'detective@test.com', 'detective', 'hashed_pw', true);

-- Associate client with a case
INSERT INTO case_members (case_id, user_id, role)
VALUES ('case-001', 'client-test-001', 'member');
```

### API Testing

```bash
# Test client dashboard
curl -H "Authorization: Bearer $CLIENT_TOKEN" \
     http://localhost:8000/client/dashboard

# Test detective dashboard
curl -H "Authorization: Bearer $DETECTIVE_TOKEN" \
     http://localhost:8000/detective/dashboard
```

---

## Common Issues

### Issue: Kakao Maps not loading
**Solution**: Ensure domain is added to allowed origins in Kakao Developers Console

### Issue: WebSocket connection fails
**Solution**: Check CORS settings in backend and ensure WebSocket is enabled

### Issue: Role redirect loop
**Solution**: Check middleware matcher patterns and ensure role is correctly decoded from JWT

---

## Reference Documents

| Document | Path |
|:---------|:-----|
| Feature Spec | `specs/003-role-based-ui/spec.md` |
| Implementation Plan | `specs/003-role-based-ui/plan.md` |
| Research Notes | `specs/003-role-based-ui/research.md` |
| Data Model | `specs/003-role-based-ui/data-model.md` |
| API Contracts | `specs/003-role-based-ui/contracts/` |
| Tasks | `specs/003-role-based-ui/tasks.md` |
| UX Checklist | `specs/003-role-based-ui/checklists/ux.md` |

---

## Next Steps

1. Review `tasks.md` for detailed implementation checklist
2. Start with Phase 1 (Foundation) tasks
3. Test role-based routing before proceeding to portal pages
4. Follow user story order for incremental delivery

---

**Questions?** Refer to `CLAUDE.md` for project conventions or ask in team chat.
