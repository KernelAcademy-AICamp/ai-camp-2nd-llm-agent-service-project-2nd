# Research: Role-Based UI System

**Feature ID**: 003-role-based-ui
**Date**: 2025-12-04
**Status**: Complete

---

## Research Tasks

### RT-1: WebSocket Implementation in FastAPI

**Question**: What is the best approach for real-time messaging using WebSocket in FastAPI?

**Decision**: Use FastAPI's native WebSocket support with connection manager pattern

**Rationale**:
- FastAPI has built-in WebSocket support via `@app.websocket()` decorator
- Connection manager pattern allows managing multiple client connections per case
- No additional dependencies required (unlike Socket.IO which would add complexity)
- Integrates cleanly with existing JWT authentication

**Alternatives Considered**:
- Socket.IO: Rejected - adds unnecessary dependency, FastAPI native support is sufficient
- Server-Sent Events (SSE): Rejected - bidirectional messaging required
- Polling: Rejected - inefficient for real-time chat

**Implementation Pattern**:
```python
# backend/app/api/messaging.py
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, case_id: str):
        await websocket.accept()
        if case_id not in self.active_connections:
            self.active_connections[case_id] = []
        self.active_connections[case_id].append(websocket)

    async def broadcast(self, case_id: str, message: dict):
        for connection in self.active_connections.get(case_id, []):
            await connection.send_json(message)
```

---

### RT-2: Kakao Maps API Integration for Detective GPS

**Question**: How to integrate Kakao Maps for GPS tracking in the detective portal?

**Decision**: Use @react-kakao-maps-sdk/core with TypeScript

**Rationale**:
- Official React wrapper maintained by Kakao
- TypeScript support out of the box
- Supports marker placement, current location, and address lookup
- Korean map data (essential for this use case)

**Alternatives Considered**:
- Google Maps: Rejected - less accurate for Korean addresses, higher cost
- Naver Maps: Considered - Kakao has better documentation and React support
- Leaflet with OpenStreetMap: Rejected - poor Korean POI data

**Setup Requirements**:
1. Register app at Kakao Developers Console
2. Get JavaScript API key
3. Add domain to allowed origins
4. Environment variable: `NEXT_PUBLIC_KAKAO_MAP_KEY`

**Implementation Pattern**:
```typescript
// frontend/src/components/detective/GPSTracker.tsx
import { Map, MapMarker, useKakaoLoader } from 'react-kakao-maps-sdk';

export function GPSTracker({ onLocationSelect }: Props) {
    const [loading, error] = useKakaoLoader({
        appkey: process.env.NEXT_PUBLIC_KAKAO_MAP_KEY!,
    });

    // Get current position
    navigator.geolocation.getCurrentPosition(
        (pos) => setCenter({ lat: pos.coords.latitude, lng: pos.coords.longitude })
    );
}
```

---

### RT-3: react-big-calendar Customization

**Question**: How to customize react-big-calendar for case-linked events?

**Decision**: Use react-big-calendar with date-fns localizer and custom event styling

**Rationale**:
- Mature library with good documentation
- Supports month/week/day views required by spec
- Custom event rendering for case-linked events
- date-fns localizer is lighter than moment.js

**Alternatives Considered**:
- FullCalendar: Rejected - commercial license required for some features
- Custom implementation: Rejected - too much effort for standard calendar
- @schedule-x/react: Rejected - less mature ecosystem

**Implementation Pattern**:
```typescript
// frontend/src/components/shared/Calendar.tsx
import { Calendar, dateFnsLocalizer } from 'react-big-calendar';
import { format, parse, startOfWeek, getDay } from 'date-fns';
import ko from 'date-fns/locale/ko';

const localizer = dateFnsLocalizer({
    format,
    parse,
    startOfWeek: () => startOfWeek(new Date(), { locale: ko }),
    getDay,
    locales: { 'ko': ko },
});

// Custom event styling by type
const eventStyleGetter = (event: CalendarEvent) => {
    const colors = {
        court: '#ef4444',    // red
        meeting: '#3b82f6',  // blue
        deadline: '#f59e0b', // amber
        reminder: '#10b981', // green
    };
    return { style: { backgroundColor: colors[event.type] } };
};
```

---

### RT-4: Role-Based Middleware in Next.js 14

**Question**: What is the best pattern for role-based routing in Next.js App Router?

**Decision**: Use middleware.ts with JWT decode + redirect pattern

**Rationale**:
- Runs on Edge Runtime for fast redirects
- Can decode JWT without full verification (verification happens in API)
- Central location for all route protection logic
- Supports pattern matching for route groups

**Alternatives Considered**:
- Per-page getServerSideProps: Rejected - App Router uses server components
- Client-side redirect in layout: Rejected - flash of unauthorized content
- Route handlers: Rejected - adds latency, middleware is faster

**Implementation Pattern**:
```typescript
// frontend/src/middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { jwtDecode } from 'jwt-decode';

const ROLE_ROUTES = {
    lawyer: ['/lawyer', '/cases'],
    client: ['/client'],
    detective: ['/detective'],
    admin: ['/admin'],
};

export function middleware(request: NextRequest) {
    const token = request.cookies.get('access_token')?.value;
    if (!token) return NextResponse.redirect(new URL('/login', request.url));

    const { role } = jwtDecode<{ role: string }>(token);
    const path = request.nextUrl.pathname;

    // Redirect to role-specific dashboard after login
    if (path === '/dashboard') {
        return NextResponse.redirect(new URL(`/${role}/dashboard`, request.url));
    }

    // Check role permissions
    const allowedRoutes = ROLE_ROUTES[role] || [];
    if (!allowedRoutes.some(route => path.startsWith(route))) {
        return NextResponse.redirect(new URL(`/${role}/dashboard`, request.url));
    }

    return NextResponse.next();
}

export const config = {
    matcher: ['/lawyer/:path*', '/client/:path*', '/detective/:path*', '/admin/:path*', '/dashboard'],
};
```

---

### RT-5: Real-Time Messaging Patterns

**Question**: How to handle message synchronization and offline support?

**Decision**: Optimistic UI updates with WebSocket + REST fallback

**Rationale**:
- Optimistic updates provide instant feedback
- WebSocket for real-time push
- REST API for initial load and offline recovery
- SWR for caching and revalidation

**Alternatives Considered**:
- WebSocket-only: Rejected - need REST for reconnection recovery
- Polling: Rejected - inefficient, delays user experience
- IndexedDB offline storage: Deferred to future enhancement

**Implementation Pattern**:
```typescript
// frontend/src/hooks/useMessages.ts
export function useMessages(caseId: string) {
    const { data, mutate } = useSWR(`/messages/${caseId}`, fetcher);
    const ws = useRef<WebSocket | null>(null);

    useEffect(() => {
        ws.current = new WebSocket(`${WS_URL}/ws/messages/${caseId}`);
        ws.current.onmessage = (event) => {
            const newMessage = JSON.parse(event.data);
            mutate((prev) => [...prev, newMessage], false);
        };
        return () => ws.current?.close();
    }, [caseId]);

    const sendMessage = async (content: string) => {
        // Optimistic update
        const tempId = crypto.randomUUID();
        mutate((prev) => [...prev, { id: tempId, content, pending: true }], false);

        // Send via REST (WebSocket will broadcast to others)
        await api.post('/messages', { case_id: caseId, content });
        mutate(); // Revalidate
    };

    return { messages: data, sendMessage };
}
```

---

### RT-6: Audit Logging Integration (Constitution Principle I)

**Question**: How to integrate audit logging for new endpoints per constitution requirements?

**Decision**: Reuse existing AuditLogMiddleware pattern with endpoint-specific decorators

**Rationale**:
- Constitution Principle I requires all CRUD operations logged
- Existing `audit_logs` table and middleware already exist
- Decorator pattern allows endpoint-specific logging metadata
- Maintains consistency with existing implementation

**Implementation Pattern**:
```python
# backend/app/core/audit.py
from functools import wraps
from app.db.models import AuditLog

def audit_action(action: str, resource_type: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            # Log action to audit_logs table
            await AuditLog.create(
                action=action,
                resource_type=resource_type,
                resource_id=kwargs.get('id'),
                user_id=kwargs.get('current_user_id'),
                details={"endpoint": func.__name__}
            )
            return result
        return wrapper
    return decorator

# Usage in endpoints
@router.post("/messages")
@audit_action("CREATE", "message")
async def send_message(message: MessageCreate, user_id: str = Depends(get_current_user_id)):
    ...
```

---

## Constitution Compliance Check

| Principle | Status | Notes |
|:----------|:-------|:------|
| I. Evidence Integrity | ✅ Compliant | Audit logging decorator pattern defined |
| II. Case Isolation | ✅ Compliant | All queries scoped by case_id |
| III. No Auto-Submit | ✅ Compliant | No AI auto-submit in this feature |
| IV. AWS-Only Storage | ✅ Compliant | All data in PostgreSQL/S3 |
| V. Clean Architecture | ✅ Compliant | Router → Service → Repository pattern |
| VI. Branch Protection | ✅ Compliant | PR workflow maintained |

---

## Dependencies Summary

| Package | Version | Purpose |
|:--------|:--------|:--------|
| react-kakao-maps-sdk | ^1.1.27 | Kakao Maps for detective GPS |
| react-big-calendar | ^1.8.5 | Calendar component |
| date-fns | ^2.30.0 | Date localization (ko) |
| recharts | ^2.10.3 | Dashboard charts |
| jwt-decode | ^4.0.0 | JWT parsing in middleware |

---

## Unresolved Questions

None - all NEEDS CLARIFICATION items resolved.

---

**Research Status**: Complete
**Next Step**: Proceed to Phase 1 (data-model.md, contracts/)
