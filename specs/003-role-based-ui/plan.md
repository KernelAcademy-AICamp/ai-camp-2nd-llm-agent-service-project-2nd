# Implementation Plan: Role-Based UI System

**Feature ID**: 003-role-based-ui
**Version**: 1.0.0

---

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL (RDS), DynamoDB
- **Auth**: JWT with role-based access control
- **Real-time**: WebSocket (FastAPI)

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS
- **State**: React Context + SWR
- **Charts**: Recharts
- **Calendar**: react-big-calendar
- **Maps**: Kakao Maps API (for detective GPS)

### Shared
- **Validation**: Pydantic (Backend), Zod (Frontend)
- **API Client**: Axios with interceptors

---

## Project Structure

### Backend Changes

```
backend/app/
├── db/
│   └── models.py              # Add CLIENT, DETECTIVE to UserRole
├── api/
│   ├── client_portal.py       # NEW: Client portal endpoints
│   ├── detective_portal.py    # NEW: Detective portal endpoints
│   └── messaging.py           # NEW: Real-time messaging
├── services/
│   ├── messaging_service.py   # NEW: Message handling
│   ├── calendar_service.py    # NEW: Calendar management
│   └── billing_service.py     # NEW: Billing/invoicing
└── schemas/
    ├── messaging.py           # NEW: Message schemas
    ├── calendar.py            # NEW: Calendar schemas
    └── billing.py             # NEW: Billing schemas
```

### Frontend Changes

```
frontend/src/app/
├── lawyer/                    # NEW: Lawyer portal
│   ├── dashboard/
│   │   └── page.tsx
│   ├── cases/
│   │   ├── page.tsx           # Case list
│   │   └── [id]/
│   │       ├── page.tsx       # Case detail
│   │       ├── timeline/
│   │       ├── analysis/
│   │       └── draft/
│   ├── clients/
│   ├── investigators/
│   ├── calendar/
│   ├── billing/
│   └── layout.tsx             # Lawyer layout with nav
├── client/                    # NEW: Client portal
│   ├── dashboard/
│   ├── cases/
│   │   └── [id]/
│   │       ├── page.tsx
│   │       ├── evidence/
│   │       └── timeline/
│   ├── messages/
│   ├── billing/
│   └── layout.tsx
├── detective/                 # NEW: Detective portal
│   ├── dashboard/
│   ├── cases/
│   │   └── [id]/
│   │       ├── page.tsx       # Case detail with accept/reject
│   │       └── evidence/      # Evidence upload
│   ├── messages/
│   ├── calendar/
│   ├── earnings/
│   └── layout.tsx
│   # Note: field/ page removed (GPS/field recording out of scope)
└── middleware.ts              # Role-based routing
```

### New Components

```
frontend/src/components/
├── lawyer/
│   ├── LawyerNav.tsx
│   ├── CaseCard.tsx
│   ├── CaseTable.tsx
│   ├── StatsCard.tsx
│   └── AnalysisDashboard.tsx
├── client/
│   ├── ClientNav.tsx
│   ├── ProgressTracker.tsx
│   ├── EvidenceUploader.tsx
│   └── LawyerChat.tsx
├── detective/
│   ├── DetectiveNav.tsx
│   ├── ReportEditor.tsx
│   └── EvidenceCollector.tsx
│   # Note: GPSTracker, FieldRecorder removed (out of platform scope)
├── shared/
│   ├── MessageThread.tsx
│   ├── Calendar.tsx
│   ├── NotificationBell.tsx
│   └── FileUploader.tsx
└── charts/
    ├── CaseStatsChart.tsx
    └── MonthlyStatsChart.tsx
```

---

## Database Changes

### New Tables

```sql
-- Messages table for real-time communication
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id VARCHAR(50) REFERENCES cases(id),
    sender_id VARCHAR(50) REFERENCES users(id),
    recipient_id VARCHAR(50) REFERENCES users(id),
    content TEXT NOT NULL,
    attachments JSONB DEFAULT '[]',
    read_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Calendar events table
CREATE TABLE calendar_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(50) REFERENCES users(id),
    case_id VARCHAR(50) REFERENCES cases(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    event_type VARCHAR(50) NOT NULL, -- court, meeting, deadline, etc.
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    location VARCHAR(255),
    reminder_minutes INTEGER DEFAULT 30,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Investigation records for detectives
CREATE TABLE investigation_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id VARCHAR(50) REFERENCES cases(id),
    detective_id VARCHAR(50) REFERENCES users(id),
    record_type VARCHAR(50) NOT NULL, -- location, photo, memo, video
    content TEXT,
    location_lat DECIMAL(10, 8),
    location_lng DECIMAL(11, 8),
    location_address VARCHAR(255),
    attachments JSONB DEFAULT '[]',
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Billing/Invoices
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id VARCHAR(50) REFERENCES cases(id),
    client_id VARCHAR(50) REFERENCES users(id),
    amount DECIMAL(12, 2) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending', -- pending, paid, overdue
    due_date DATE,
    paid_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Model Changes

```python
# backend/app/db/models.py

class UserRole(str, enum.Enum):
    LAWYER = "lawyer"
    STAFF = "staff"
    ADMIN = "admin"
    CLIENT = "client"      # NEW
    DETECTIVE = "detective" # NEW
```

---

## API Endpoints

### Client Portal

```
GET  /client/dashboard          # Dashboard stats
GET  /client/cases              # Client's cases
GET  /client/cases/{id}         # Case detail (limited view)
POST /client/cases/{id}/evidence # Upload evidence
GET  /client/messages           # Messages with lawyer
POST /client/messages           # Send message
GET  /client/billing            # Invoices
POST /client/billing/{id}/pay   # Pay invoice
```

### Detective Portal

```
GET  /detective/dashboard       # Dashboard stats
GET  /detective/cases           # Assigned investigations
GET  /detective/cases/{id}      # Investigation detail
POST /detective/cases/{id}/accept # Accept assignment
POST /detective/cases/{id}/reject # Reject assignment
POST /detective/cases/{id}/records # Add field record
GET  /detective/cases/{id}/records # Get all records
POST /detective/cases/{id}/report  # Submit report
GET  /detective/earnings        # Earnings summary
```

### Messaging (Shared)

```
GET  /messages/{case_id}        # Get messages for case
POST /messages                  # Send message
PUT  /messages/{id}/read        # Mark as read
WS   /ws/messages/{case_id}     # Real-time messages
```

### Calendar

```
GET  /calendar/events           # Get events
POST /calendar/events           # Create event
PUT  /calendar/events/{id}      # Update event
DELETE /calendar/events/{id}    # Delete event
```

---

## Implementation Phases

### Phase 1: Foundation (US1)
1. Add CLIENT, DETECTIVE roles to backend
2. Update role permissions
3. Create role-based middleware (frontend)
4. Role-specific layouts

### Phase 2: Lawyer MVP (US2, US3)
1. Lawyer dashboard
2. Case list with filters
3. Case detail page
4. Integration with existing features

### Phase 3: Client Portal (US4)
1. Client dashboard
2. Case status view
3. Evidence upload
4. Lawyer messaging

### Phase 4: Detective Portal (US5)
1. Detective dashboard
2. Investigation management
3. Field recording
4. Report submission

### Phase 5: Cross-Cutting (US6, US7)
1. Real-time messaging
2. Calendar system
3. Notification system

### Phase 6: Billing (US8)
1. Invoice management
2. Payment tracking

---

## File Summary

### New Files to Create

| Category | File | Purpose |
|:---------|:-----|:--------|
| Backend | `backend/app/api/client_portal.py` | Client portal endpoints |
| Backend | `backend/app/api/detective_portal.py` | Detective portal endpoints |
| Backend | `backend/app/api/messaging.py` | Messaging endpoints |
| Backend | `backend/app/api/calendar.py` | Calendar endpoints |
| Backend | `backend/app/services/messaging_service.py` | Message handling |
| Backend | `backend/app/services/calendar_service.py` | Calendar logic |
| Backend | `backend/app/schemas/messaging.py` | Message schemas |
| Backend | `backend/app/schemas/calendar.py` | Calendar schemas |
| Frontend | `frontend/src/app/lawyer/layout.tsx` | Lawyer portal layout |
| Frontend | `frontend/src/app/lawyer/dashboard/page.tsx` | Lawyer dashboard |
| Frontend | `frontend/src/app/client/layout.tsx` | Client portal layout |
| Frontend | `frontend/src/app/client/dashboard/page.tsx` | Client dashboard |
| Frontend | `frontend/src/app/detective/layout.tsx` | Detective portal layout |
| Frontend | `frontend/src/app/detective/dashboard/page.tsx` | Detective dashboard |
| Frontend | `frontend/src/components/shared/MessageThread.tsx` | Messaging UI |
| Frontend | `frontend/src/components/shared/Calendar.tsx` | Calendar UI |

### Files to Modify

| File | Changes |
|:-----|:--------|
| `backend/app/db/models.py` | Add CLIENT, DETECTIVE roles |
| `backend/app/main.py` | Register new routers |
| `frontend/src/middleware.ts` | Role-based routing |

---

## Performance Considerations

- Lazy load role-specific bundles
- WebSocket connection pooling
- Calendar event caching
- GPS data batching (detective)
- Message pagination

## Security Considerations

- Role-based route guards
- Case access validation
- Evidence upload validation
- Message encryption (future)
- GPS data privacy
- **Audit Logging (Constitution Principle I)**: All new endpoints (messaging, calendar, billing, field records) MUST integrate with existing `audit_logs` table. All CRUD operations require immutable audit trail for legal compliance.
