"""
SQLAlchemy Enum definitions for LEH Backend
"""

import enum


# ============================================
# User & Auth Enums
# ============================================
class UserRole(str, enum.Enum):
    """User role enum"""
    LAWYER = "lawyer"
    STAFF = "staff"
    ADMIN = "admin"
    CLIENT = "client"          # 의뢰인
    DETECTIVE = "detective"    # 탐정/조사원


class UserStatus(str, enum.Enum):
    """User status enum"""
    ACTIVE = "active"
    INACTIVE = "inactive"


class AgreementType(str, enum.Enum):
    """Agreement type enum for user consent tracking"""
    TERMS_OF_SERVICE = "terms_of_service"  # 이용약관
    PRIVACY_POLICY = "privacy_policy"       # 개인정보처리방침


# ============================================
# Case Enums
# ============================================
class CaseStatus(str, enum.Enum):
    """Case status enum"""
    ACTIVE = "active"
    OPEN = "open"              # 진행 중 (open and active)
    IN_PROGRESS = "in_progress"  # 검토 대기 (being actively worked)
    REVIEW = "review"          # 변호사 검토 단계
    CLOSED = "closed"


class CaseMemberRole(str, enum.Enum):
    """Case member role enum"""
    OWNER = "owner"
    MEMBER = "member"
    VIEWER = "viewer"

    def to_permission(self) -> "CaseMemberPermission":
        """Converts CaseMemberRole to CaseMemberPermission.

        OWNER and MEMBER roles get READ_WRITE permission.
        VIEWER role gets READ permission.
        """
        from app.db.schemas import CaseMemberPermission
        if self in (CaseMemberRole.OWNER, CaseMemberRole.MEMBER):
            return CaseMemberPermission.READ_WRITE
        return CaseMemberPermission.READ


# ============================================
# Draft & Document Enums
# ============================================
class DocumentType(str, enum.Enum):
    """Legal document type enum (민법 840조 관련)"""
    COMPLAINT = "complaint"      # 소장
    MOTION = "motion"            # 신청서
    BRIEF = "brief"              # 준비서면
    RESPONSE = "response"        # 답변서


class DraftStatus(str, enum.Enum):
    """Draft document status enum"""
    DRAFT = "draft"              # Initial AI-generated
    REVIEWED = "reviewed"        # Lawyer has reviewed/edited
    EXPORTED = "exported"        # Has been exported at least once


class ExportFormat(str, enum.Enum):
    """Export file format enum"""
    DOCX = "docx"
    PDF = "pdf"


class ExportJobStatus(str, enum.Enum):
    """Export job status enum"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ============================================
# Calendar & Schedule Enums
# ============================================
class CalendarEventType(str, enum.Enum):
    """Calendar event type enum"""
    COURT = "court"          # 재판/출석
    MEETING = "meeting"      # 상담/회의
    DEADLINE = "deadline"    # 마감
    INTERNAL = "internal"    # 내부 업무
    OTHER = "other"


# ============================================
# Investigation & Detective Enums
# ============================================
class InvestigationRecordType(str, enum.Enum):
    """Investigation record type enum"""
    LOCATION = "location"    # 위치 기록
    PHOTO = "photo"          # 사진
    VIDEO = "video"          # 영상
    AUDIO = "audio"          # 음성 메모
    MEMO = "memo"            # 텍스트 메모
    EVIDENCE = "evidence"    # 증거 수집


class EarningsStatus(str, enum.Enum):
    """Detective earnings status enum"""
    PENDING = "pending"      # 정산 대기
    PAID = "paid"            # 정산 완료


# ============================================
# Billing Enums
# ============================================
class InvoiceStatus(str, enum.Enum):
    """Invoice status enum"""
    PENDING = "pending"      # 대기중
    PAID = "paid"            # 결제완료
    OVERDUE = "overdue"      # 연체
    CANCELLED = "cancelled"  # 취소


# ============================================
# Property & Asset Enums
# ============================================
class PropertyType(str, enum.Enum):
    """Property type enum for asset division"""
    REAL_ESTATE = "real_estate"    # 부동산
    SAVINGS = "savings"            # 예금/적금
    STOCKS = "stocks"              # 주식/펀드
    RETIREMENT = "retirement"      # 퇴직금/연금
    VEHICLE = "vehicle"            # 자동차
    INSURANCE = "insurance"        # 보험
    DEBT = "debt"                  # 부채
    OTHER = "other"                # 기타


class PropertyOwner(str, enum.Enum):
    """Property owner enum"""
    PLAINTIFF = "plaintiff"        # 원고(의뢰인)
    DEFENDANT = "defendant"        # 피고(상대방)
    JOINT = "joint"                # 공동 소유


class AssetCategory(str, enum.Enum):
    """Asset category enum for property division"""
    REAL_ESTATE = "real_estate"    # 부동산
    SAVINGS = "savings"            # 예금/적금
    STOCKS = "stocks"              # 주식/펀드
    RETIREMENT = "retirement"      # 퇴직금/연금
    VEHICLE = "vehicle"            # 자동차
    INSURANCE = "insurance"        # 보험
    DEBT = "debt"                  # 부채
    OTHER = "other"                # 기타


class AssetOwnership(str, enum.Enum):
    """Asset ownership enum"""
    PLAINTIFF = "plaintiff"        # 원고(의뢰인)
    DEFENDANT = "defendant"        # 피고(상대방)
    JOINT = "joint"                # 공동 소유


class AssetNature(str, enum.Enum):
    """Asset nature enum - premarital vs marital"""
    PREMARITAL = "premarital"      # 혼전 재산 (특유재산)
    MARITAL = "marital"            # 혼인 중 취득 (공유재산)
    MIXED = "mixed"                # 혼합 재산
    SEPARATE = "separate"          # 특유재산 (분할 대상 제외 가능)


class ConfidenceLevel(str, enum.Enum):
    """Prediction confidence level"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ============================================
# Job & Processing Enums
# ============================================
class JobType(str, enum.Enum):
    """Job type enum for async processing"""
    OCR = "ocr"                      # Image/PDF text extraction
    STT = "stt"                      # Audio transcription
    VISION_ANALYSIS = "vision"       # GPT-4o image understanding
    DRAFT_GENERATION = "draft"       # RAG + GPT-4o legal document
    EVIDENCE_ANALYSIS = "analysis"   # Evidence re-analysis
    PDF_EXPORT = "pdf_export"        # Export draft to PDF
    DOCX_EXPORT = "docx_export"      # Export draft to DOCX


class JobStatus(str, enum.Enum):
    """Job status enum"""
    QUEUED = "queued"          # Waiting to be processed
    PROCESSING = "processing"  # Currently running
    COMPLETED = "completed"    # Success
    FAILED = "failed"          # Error occurred
    RETRY = "retry"            # Waiting to retry
    CANCELLED = "cancelled"    # User cancelled


class EvidenceStatus(str, enum.Enum):
    """Evidence processing status enum"""
    PENDING = "pending"        # Upload URL generated, waiting for file
    UPLOADED = "uploaded"      # File uploaded, waiting for processing
    PROCESSING = "processing"  # AI processing in progress
    COMPLETED = "completed"    # AI processing complete
    FAILED = "failed"          # Processing failed


# ============================================
# Settings Enums
# ============================================
class NotificationFrequency(str, enum.Enum):
    """Notification frequency enum"""
    IMMEDIATE = "immediate"
    DAILY = "daily"
    WEEKLY = "weekly"


class ProfileVisibility(str, enum.Enum):
    """Profile visibility enum"""
    PUBLIC = "public"
    TEAM = "team"
    PRIVATE = "private"


# ============================================
# Party Graph Enums (v1 Lawyer Portal)
# ============================================
class PartyType(str, enum.Enum):
    """Party type enum for relationship graph"""
    PLAINTIFF = "plaintiff"       # 원고 (의뢰인)
    DEFENDANT = "defendant"       # 피고 (상대방)
    THIRD_PARTY = "third_party"   # 제3자 (불륜상대, 증인 등)
    CHILD = "child"               # 자녀
    FAMILY = "family"             # 친족


class RelationshipType(str, enum.Enum):
    """Relationship type enum for party connections"""
    MARRIAGE = "marriage"         # 혼인
    AFFAIR = "affair"             # 불륜관계
    PARENT_CHILD = "parent_child" # 부모-자녀
    SIBLING = "sibling"           # 형제자매
    IN_LAW = "in_law"             # 인척
    COHABIT = "cohabit"           # 동거


class LinkType(str, enum.Enum):
    """Link type enum for evidence-party connections"""
    MENTIONS = "mentions"         # 언급
    PROVES = "proves"             # 증명
    INVOLVES = "involves"         # 관련
    CONTRADICTS = "contradicts"   # 반박


# ============================================
# Procedure Stage Enums (US3)
# ============================================
class ProcedureStageType(str, enum.Enum):
    """Korean family litigation procedure stages"""
    FILED = "filed"                       # 소장 접수
    SERVED = "served"                     # 송달
    ANSWERED = "answered"                 # 답변서
    MEDIATION = "mediation"               # 조정 회부
    MEDIATION_CLOSED = "mediation_closed" # 조정 종결
    TRIAL = "trial"                       # 본안 이행
    JUDGMENT = "judgment"                 # 판결 선고
    APPEAL = "appeal"                     # 항소심
    FINAL = "final"                       # 확정


class StageStatus(str, enum.Enum):
    """Status of a procedure stage"""
    PENDING = "pending"           # 대기
    IN_PROGRESS = "in_progress"   # 진행중
    COMPLETED = "completed"       # 완료
    SKIPPED = "skipped"           # 건너뜀


# ============================================
# Notification Enums
# ============================================
class NotificationType(str, enum.Enum):
    """Notification type enum"""
    CASE_UPDATE = "case_update"
    MESSAGE = "message"
    EVIDENCE = "evidence"
    DEADLINE = "deadline"
    SYSTEM = "system"


# ============================================
# Consultation Enums
# ============================================
class ConsultationType(str, enum.Enum):
    """Consultation type enum"""
    PHONE = "phone"           # 전화 상담
    IN_PERSON = "in_person"   # 대면 상담
    ONLINE = "online"         # 화상 상담
