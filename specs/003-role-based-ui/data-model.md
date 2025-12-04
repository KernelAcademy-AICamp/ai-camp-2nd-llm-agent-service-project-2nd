# Data Model: Role-Based UI System

**Feature ID**: 003-role-based-ui
**Date**: 2025-12-04
**Database**: PostgreSQL (RDS)

---

## Entity Relationship Diagram

```
┌─────────────┐     ┌─────────────┐     ┌──────────────────────┐
│   users     │────<│ case_members│>────│       cases          │
│ (existing)  │     │ (existing)  │     │    (existing)        │
└──────┬──────┘     └─────────────┘     └──────────┬───────────┘
       │                                           │
       │ sender_id                                 │ case_id
       │ recipient_id                              │
       ▼                                           ▼
┌─────────────┐                           ┌─────────────────────┐
│  messages   │───────────────────────────│ calendar_events     │
│   (NEW)     │                           │      (NEW)          │
└─────────────┘                           └─────────────────────┘
       │
       │ case_id
       ▼
┌─────────────────────┐     ┌─────────────────────┐
│investigation_records│     │      invoices       │
│       (NEW)         │     │       (NEW)         │
└─────────────────────┘     └─────────────────────┘
```

---

## Entities

### 1. UserRole (Enum Extension)

**Table**: `users.role` (existing column)

| Value | Description | Portal Access |
|:------|:------------|:--------------|
| `lawyer` | Attorney/Lawyer | `/lawyer/*` |
| `staff` | Law firm staff | `/lawyer/*` (limited) |
| `admin` | System admin | `/admin/*` |
| `client` | **NEW** - Case client | `/client/*` |
| `detective` | **NEW** - Private investigator | `/detective/*` |

**Validation Rules**:
- Role is set at user creation
- Role change requires admin action
- Single role per user (no multi-role)

---

### 2. Message

**Table**: `messages`

| Field | Type | Constraints | Description |
|:------|:-----|:------------|:------------|
| `id` | UUID | PK, auto-gen | Unique message ID |
| `case_id` | VARCHAR(50) | FK → cases.id, NOT NULL | Associated case |
| `sender_id` | VARCHAR(50) | FK → users.id, NOT NULL | Message author |
| `recipient_id` | VARCHAR(50) | FK → users.id, NULL | Specific recipient (NULL = all case members) |
| `content` | TEXT | NOT NULL, max 10000 chars | Message body |
| `attachments` | JSONB | DEFAULT '[]' | File attachment metadata |
| `read_at` | TIMESTAMPTZ | NULL | When recipient read message |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Creation timestamp |

**Relationships**:
- Many-to-One: Message → Case
- Many-to-One: Message → User (sender)
- Many-to-One: Message → User (recipient, optional)

**Indexes**:
- `idx_messages_case_id` on `case_id`
- `idx_messages_sender_id` on `sender_id`
- `idx_messages_created_at` on `created_at DESC`

**Attachments JSONB Schema**:
```json
[
  {
    "id": "att-uuid",
    "filename": "document.pdf",
    "s3_key": "messages/case-123/att-uuid.pdf",
    "size": 1024000,
    "mime_type": "application/pdf"
  }
]
```

**State Transitions**:
- Created (content filled) → Delivered (WebSocket sent) → Read (read_at set)

---

### 3. CalendarEvent

**Table**: `calendar_events`

| Field | Type | Constraints | Description |
|:------|:-----|:------------|:------------|
| `id` | UUID | PK, auto-gen | Unique event ID |
| `user_id` | VARCHAR(50) | FK → users.id, NOT NULL | Event owner |
| `case_id` | VARCHAR(50) | FK → cases.id, NULL | Linked case (optional) |
| `title` | VARCHAR(255) | NOT NULL | Event title |
| `description` | TEXT | NULL | Event details |
| `event_type` | VARCHAR(50) | NOT NULL, ENUM | Event category |
| `start_time` | TIMESTAMPTZ | NOT NULL | Event start |
| `end_time` | TIMESTAMPTZ | NULL | Event end (NULL = all-day) |
| `location` | VARCHAR(255) | NULL | Event location |
| `reminder_minutes` | INTEGER | DEFAULT 30 | Reminder before event |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Creation timestamp |

**Event Types** (ENUM):
| Value | Color | Description |
|:------|:------|:------------|
| `court` | Red (#ef4444) | Court hearing |
| `meeting` | Blue (#3b82f6) | Client/case meeting |
| `deadline` | Amber (#f59e0b) | Filing deadline |
| `reminder` | Green (#10b981) | General reminder |
| `investigation` | Purple (#8b5cf6) | Investigation task |

**Relationships**:
- Many-to-One: CalendarEvent → User
- Many-to-One: CalendarEvent → Case (optional)

**Indexes**:
- `idx_calendar_user_id` on `user_id`
- `idx_calendar_start_time` on `start_time`
- `idx_calendar_case_id` on `case_id` WHERE case_id IS NOT NULL

**Validation Rules**:
- `end_time` must be after `start_time` if provided
- `reminder_minutes` must be >= 0
- `event_type` must be valid enum value

---

### 4. InvestigationRecord

**Table**: `investigation_records`

| Field | Type | Constraints | Description |
|:------|:-----|:------------|:------------|
| `id` | UUID | PK, auto-gen | Unique record ID |
| `case_id` | VARCHAR(50) | FK → cases.id, NOT NULL | Associated case |
| `detective_id` | VARCHAR(50) | FK → users.id, NOT NULL | Recording detective |
| `record_type` | VARCHAR(50) | NOT NULL, ENUM | Record category |
| `content` | TEXT | NULL | Text notes/description |
| `location_lat` | DECIMAL(10,8) | NULL | GPS latitude |
| `location_lng` | DECIMAL(11,8) | NULL | GPS longitude |
| `location_address` | VARCHAR(255) | NULL | Reverse-geocoded address |
| `attachments` | JSONB | DEFAULT '[]' | Photo/video attachments |
| `recorded_at` | TIMESTAMPTZ | NOT NULL | When record was made |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Upload timestamp |

**Record Types** (ENUM):
| Value | Description | Required Fields |
|:------|:------------|:----------------|
| `location` | GPS checkpoint | lat, lng, address |
| `photo` | Photo evidence | attachments |
| `video` | Video evidence | attachments |
| `memo` | Text observation | content |
| `audio` | Audio recording | attachments |

**Relationships**:
- Many-to-One: InvestigationRecord → Case
- Many-to-One: InvestigationRecord → User (detective)

**Indexes**:
- `idx_investigation_case_id` on `case_id`
- `idx_investigation_detective_id` on `detective_id`
- `idx_investigation_recorded_at` on `recorded_at DESC`

**Attachments JSONB Schema**:
```json
[
  {
    "id": "att-uuid",
    "filename": "photo_001.jpg",
    "s3_key": "investigation/case-123/photo_001.jpg",
    "size": 2048000,
    "mime_type": "image/jpeg",
    "metadata": {
      "width": 1920,
      "height": 1080,
      "taken_at": "2025-01-15T10:30:00Z"
    }
  }
]
```

**GPS Precision**:
- Latitude: 10 digits total, 8 after decimal (accuracy ~1.1mm)
- Longitude: 11 digits total, 8 after decimal

---

### 5. Invoice

**Table**: `invoices`

| Field | Type | Constraints | Description |
|:------|:-----|:------------|:------------|
| `id` | UUID | PK, auto-gen | Unique invoice ID |
| `case_id` | VARCHAR(50) | FK → cases.id, NOT NULL | Associated case |
| `client_id` | VARCHAR(50) | FK → users.id, NOT NULL | Billing client |
| `lawyer_id` | VARCHAR(50) | FK → users.id, NOT NULL | Issuing lawyer |
| `invoice_number` | VARCHAR(50) | UNIQUE, NOT NULL | Human-readable number |
| `amount` | DECIMAL(12,2) | NOT NULL, > 0 | Invoice amount (KRW) |
| `description` | TEXT | NULL | Service description |
| `status` | VARCHAR(50) | DEFAULT 'pending', ENUM | Payment status |
| `due_date` | DATE | NOT NULL | Payment due date |
| `paid_at` | TIMESTAMPTZ | NULL | Payment timestamp |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Creation timestamp |

**Invoice Status** (ENUM):
| Value | Description | Transitions To |
|:------|:------------|:---------------|
| `draft` | Not yet sent | pending |
| `pending` | Awaiting payment | paid, overdue |
| `paid` | Payment received | (terminal) |
| `overdue` | Past due date | paid |
| `cancelled` | Invoice cancelled | (terminal) |

**Relationships**:
- Many-to-One: Invoice → Case
- Many-to-One: Invoice → User (client)
- Many-to-One: Invoice → User (lawyer)

**Indexes**:
- `idx_invoice_case_id` on `case_id`
- `idx_invoice_client_id` on `client_id`
- `idx_invoice_status` on `status`
- `idx_invoice_due_date` on `due_date`

**Invoice Number Format**: `INV-{YYYYMM}-{sequence}` (e.g., `INV-202501-0042`)

**Validation Rules**:
- `amount` must be positive
- `due_date` must be in the future at creation
- `paid_at` can only be set when transitioning to `paid` status

---

## Existing Entity Extensions

### User Model Extension

```python
# backend/app/db/models.py

class UserRole(str, enum.Enum):
    LAWYER = "lawyer"
    STAFF = "staff"
    ADMIN = "admin"
    CLIENT = "client"      # NEW
    DETECTIVE = "detective" # NEW

# Role permissions mapping
ROLE_PERMISSIONS = {
    UserRole.LAWYER: ["cases:*", "evidence:*", "messages:*", "calendar:*", "billing:*"],
    UserRole.STAFF: ["cases:read", "evidence:read", "messages:read"],
    UserRole.ADMIN: ["*"],
    UserRole.CLIENT: ["cases:read:own", "evidence:upload:own", "messages:*:own", "billing:read:own"],
    UserRole.DETECTIVE: ["cases:read:assigned", "investigation:*:assigned", "messages:*:assigned"],
}
```

### Case Model Extension

Add relationship to new entities:

```python
class Case(Base):
    # ... existing fields ...

    # New relationships
    messages = relationship("Message", back_populates="case")
    calendar_events = relationship("CalendarEvent", back_populates="case")
    investigation_records = relationship("InvestigationRecord", back_populates="case")
    invoices = relationship("Invoice", back_populates="case")
```

---

## Migration Plan

### Migration File: `versions/xxx_add_role_based_ui_tables.py`

```python
"""Add tables for role-based UI system

Revision ID: xxx
Revises: [previous]
Create Date: 2025-01-XX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

def upgrade():
    # 1. Update UserRole enum
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'client'")
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'detective'")

    # 2. Create messages table
    op.create_table('messages', ...)

    # 3. Create calendar_events table
    op.create_table('calendar_events', ...)

    # 4. Create investigation_records table
    op.create_table('investigation_records', ...)

    # 5. Create invoices table
    op.create_table('invoices', ...)

def downgrade():
    op.drop_table('invoices')
    op.drop_table('investigation_records')
    op.drop_table('calendar_events')
    op.drop_table('messages')
    # Note: Cannot remove enum values in PostgreSQL
```

---

## Audit Logging Requirements (Constitution Principle I)

All entities MUST log to `audit_logs` table:

| Entity | Actions to Log |
|:-------|:---------------|
| Message | CREATE |
| CalendarEvent | CREATE, UPDATE, DELETE |
| InvestigationRecord | CREATE, UPDATE |
| Invoice | CREATE, UPDATE (status change) |

**Audit Log Entry Format**:
```json
{
  "action": "CREATE",
  "resource_type": "message",
  "resource_id": "msg-uuid",
  "user_id": "user-uuid",
  "case_id": "case-uuid",
  "timestamp": "2025-01-15T10:30:00Z",
  "details": {
    "content_length": 150,
    "has_attachments": true
  }
}
```

---

## Data Retention

| Entity | Retention Policy |
|:-------|:-----------------|
| Message | Retained for case lifetime + 7 years |
| CalendarEvent | Deleted when case closed |
| InvestigationRecord | Retained for case lifetime + 7 years |
| Invoice | Retained for 10 years (tax requirement) |

---

**Model Status**: Complete
**Next Step**: Generate API contracts
