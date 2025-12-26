#!/usr/bin/env python3
"""
Database Seed Script for Development/Testing
005-lawyer-portal-pages Feature

Generates realistic mock data for:
- Users (lawyers, clients, detectives)
- Cases with case members
- Messages between users
- Calendar events
- Invoices
- Investigation records
- Party nodes and relationships (인물관계도)
- Consultations (상담 기록)
- Draft documents (초안 문서)

Usage:
    cd backend
    python -m scripts.seed_dev_data
    # or
    python scripts/seed_dev_data.py
"""

import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add backend to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session  # noqa: E402

from app.db import session as db_session  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db.models import (  # noqa: E402
    User, UserRole, UserStatus,
    Case, CaseStatus,
    CaseMember, CaseMemberRole,
    Message,
    CalendarEvent, CalendarEventType,
    Invoice, InvoiceStatus,
    InvestigationRecord, InvestigationRecordType,
    UserSettings,
    # Party Graph models
    PartyNode, PartyRelationship,
    PartyType, RelationshipType,
    # Consultation models
    Consultation, ConsultationParticipant,
    ConsultationType,
    # Draft models
    DraftDocument, DocumentType, DraftStatus,
)

# ============================================
# Seed Data Definitions
# ============================================

# Default password for all seed users
DEFAULT_PASSWORD = "test1234"

LAWYERS = [
    {"id": "user_lawyer001", "email": "kim.lawyer@leh.dev", "name": "김변호사", "role": UserRole.LAWYER},
    {"id": "user_lawyer002", "email": "lee.lawyer@leh.dev", "name": "이변호사", "role": UserRole.LAWYER},
    {"id": "user_lawyer003", "email": "park.lawyer@leh.dev", "name": "박변호사", "role": UserRole.LAWYER},
]

STAFF = [
    {"id": "user_staff001", "email": "jung.staff@leh.dev", "name": "정사무장", "role": UserRole.STAFF},
    {"id": "user_staff002", "email": "choi.staff@leh.dev", "name": "최파라리걸", "role": UserRole.STAFF},
]

CLIENTS = [
    {"id": "user_client001", "email": "hong.client@example.com", "name": "홍길동", "role": UserRole.CLIENT},
    {"id": "user_client002", "email": "kang.client@example.com", "name": "강감찬", "role": UserRole.CLIENT},
    {"id": "user_client003", "email": "shin.client@example.com", "name": "신사임당", "role": UserRole.CLIENT},
    {"id": "user_client004", "email": "yoo.client@example.com", "name": "유관순", "role": UserRole.CLIENT},
    {"id": "user_client005", "email": "ahn.client@example.com", "name": "안중근", "role": UserRole.CLIENT},
    {"id": "user_client006", "email": "kim.client@example.com", "name": "김유신", "role": UserRole.CLIENT},
    {"id": "user_client007", "email": "lee.client2@example.com", "name": "이순신", "role": UserRole.CLIENT},
    {"id": "user_client008", "email": "jang.client@example.com", "name": "장영실", "role": UserRole.CLIENT},
]

DETECTIVES = [
    {"id": "user_det001", "email": "oh.detective@leh.dev", "name": "오탐정", "role": UserRole.DETECTIVE},
    {"id": "user_det002", "email": "han.detective@leh.dev", "name": "한조사원", "role": UserRole.DETECTIVE},
    {"id": "user_det003", "email": "min.detective@leh.dev", "name": "민조사원", "role": UserRole.DETECTIVE},
]

ADMIN = [
    {"id": "user_admin001", "email": "admin@leh.dev", "name": "관리자", "role": UserRole.ADMIN},
]

CASES = [
    {
        "id": "case_divorce001",
        "title": "홍길동 vs 심청 이혼소송",
        "client_name": "홍길동",
        "description": "협의이혼 불성립으로 재판이혼 진행. 재산분할 및 양육권 쟁점.",
        "status": CaseStatus.ACTIVE,
        "created_by": "user_lawyer001",
        "members": [
            ("user_lawyer001", CaseMemberRole.OWNER),
            ("user_client001", CaseMemberRole.MEMBER),
            ("user_det001", CaseMemberRole.MEMBER),
            ("user_staff001", CaseMemberRole.VIEWER),
        ]
    },
    {
        "id": "case_divorce002",
        "title": "강감찬 vs 배우자 이혼소송",
        "client_name": "강감찬",
        "description": "배우자 불륜으로 인한 이혼소송. 위자료 청구 포함.",
        "status": CaseStatus.ACTIVE,
        "created_by": "user_lawyer001",
        "members": [
            ("user_lawyer001", CaseMemberRole.OWNER),
            ("user_client002", CaseMemberRole.MEMBER),
            ("user_det002", CaseMemberRole.MEMBER),
        ]
    },
    {
        "id": "case_divorce003",
        "title": "신사임당 이혼 및 재산분할",
        "client_name": "신사임당",
        "description": "고액 재산분할 사건. 부동산 감정 필요.",
        "status": CaseStatus.ACTIVE,
        "created_by": "user_lawyer002",
        "members": [
            ("user_lawyer002", CaseMemberRole.OWNER),
            ("user_client003", CaseMemberRole.MEMBER),
            ("user_staff002", CaseMemberRole.VIEWER),
        ]
    },
    {
        "id": "case_divorce004",
        "title": "유관순 양육권 분쟁",
        "client_name": "유관순",
        "description": "양육권 변경 청구. 면접교섭권 조정 필요.",
        "status": CaseStatus.IN_PROGRESS,
        "created_by": "user_lawyer002",
        "members": [
            ("user_lawyer002", CaseMemberRole.OWNER),
            ("user_client004", CaseMemberRole.MEMBER),
            ("user_det003", CaseMemberRole.MEMBER),
        ]
    },
    {
        "id": "case_divorce005",
        "title": "안중근 vs 배우자 협의이혼",
        "client_name": "안중근",
        "description": "협의이혼 진행 중. 재산분할 합의 대기.",
        "status": CaseStatus.ACTIVE,
        "created_by": "user_lawyer001",
        "members": [
            ("user_lawyer001", CaseMemberRole.OWNER),
            ("user_client005", CaseMemberRole.MEMBER),
        ]
    },
    {
        "id": "case_closed001",
        "title": "김유신 이혼소송 (완료)",
        "client_name": "김유신",
        "description": "이혼 확정. 재산분할 완료.",
        "status": CaseStatus.CLOSED,
        "created_by": "user_lawyer003",
        "members": [
            ("user_lawyer003", CaseMemberRole.OWNER),
            ("user_client006", CaseMemberRole.MEMBER),
        ]
    },
]


def create_messages(db: Session) -> list:
    """Create sample messages between users"""
    messages = []
    now = datetime.now(timezone.utc)

    message_data = [
        # Case 1 messages
        ("case_divorce001", "user_lawyer001", "user_client001", "안녕하세요, 홍길동님. 소송 준비 상황 안내드립니다.", now - timedelta(days=5)),
        ("case_divorce001", "user_client001", "user_lawyer001", "네, 감사합니다. 서류 준비는 어떻게 하면 될까요?", now - timedelta(days=5, hours=1)),
        ("case_divorce001", "user_lawyer001", "user_client001", "첨부파일로 필요 서류 목록 보내드렸습니다. 확인 부탁드립니다.", now - timedelta(days=4)),
        ("case_divorce001", "user_det001", "user_lawyer001", "김변호사님, 현장조사 완료했습니다. 보고서 정리 중입니다.", now - timedelta(days=2)),
        ("case_divorce001", "user_lawyer001", "user_det001", "수고하셨습니다. 빠른 시일 내에 보고서 부탁드립니다.", now - timedelta(days=2, hours=2)),

        # Case 2 messages
        ("case_divorce002", "user_lawyer001", "user_client002", "강감찬님, 상대방 측에서 조정을 제안해왔습니다.", now - timedelta(days=3)),
        ("case_divorce002", "user_client002", "user_lawyer001", "조정은 원하지 않습니다. 재판으로 진행해주세요.", now - timedelta(days=3, hours=5)),
        ("case_divorce002", "user_det002", "user_lawyer001", "증거자료 추가 확보했습니다. 중요한 내용입니다.", now - timedelta(days=1)),

        # Case 3 messages
        ("case_divorce003", "user_lawyer002", "user_client003", "부동산 감정 결과가 나왔습니다. 시가 15억원으로 평가되었습니다.", now - timedelta(hours=12)),
        ("case_divorce003", "user_client003", "user_lawyer002", "예상보다 높게 나왔네요. 분할 비율은 어떻게 될까요?", now - timedelta(hours=10)),
    ]

    for case_id, sender_id, recipient_id, content, created_at in message_data:
        msg = Message(
            case_id=case_id,
            sender_id=sender_id,
            recipient_id=recipient_id,
            content=content,
            created_at=created_at
        )
        messages.append(msg)

    return messages


def create_calendar_events(db: Session) -> list:
    """Create sample calendar events"""
    events = []
    now = datetime.now(timezone.utc)

    event_data = [
        # Lawyer 1 events
        ("user_lawyer001", "case_divorce001", "홍길동 사건 변론기일", CalendarEventType.COURT,
         now + timedelta(days=7, hours=10), "서울가정법원 301호", "첫 번째 변론기일"),
        ("user_lawyer001", "case_divorce002", "강감찬 사건 조정기일", CalendarEventType.COURT,
         now + timedelta(days=14, hours=14), "서울가정법원 조정실 2", "조정 불성립 시 본안 진행"),
        ("user_lawyer001", None, "신규 상담 - 박OO", CalendarEventType.MEETING,
         now + timedelta(days=2, hours=15), "사무실 상담실", "이혼 상담 예약"),
        ("user_lawyer001", "case_divorce005", "안중근 서류 검토 마감", CalendarEventType.DEADLINE,
         now + timedelta(days=5), None, "재산분할 합의서 최종 검토"),

        # Lawyer 2 events
        ("user_lawyer002", "case_divorce003", "신사임당 사건 감정인 심문", CalendarEventType.COURT,
         now + timedelta(days=21, hours=11), "서울가정법원 402호", "부동산 감정인 출석"),
        ("user_lawyer002", "case_divorce004", "유관순 면접교섭 조정", CalendarEventType.COURT,
         now + timedelta(days=10, hours=14), "가정법원 조정실", "양육권 관련 조정"),
        ("user_lawyer002", None, "변호사 교육 세미나", CalendarEventType.OTHER,
         now + timedelta(days=30, hours=9), "대한변호사협회", "가사소송 실무 교육"),

        # Detective events
        ("user_det001", "case_divorce001", "홍길동 사건 현장조사", CalendarEventType.OTHER,
         now - timedelta(days=2, hours=9), "강남구 역삼동", "상대방 거주지 조사"),
        ("user_det002", "case_divorce002", "강감찬 사건 증거수집", CalendarEventType.OTHER,
         now + timedelta(days=3, hours=10), "서초구 서초동", "추가 증거 확보"),
    ]

    for user_id, case_id, title, event_type, start_time, location, description in event_data:
        event = CalendarEvent(
            user_id=user_id,
            case_id=case_id,
            title=title,
            event_type=event_type,
            start_time=start_time,
            end_time=start_time + timedelta(hours=2) if event_type != CalendarEventType.DEADLINE else None,
            location=location,
            description=description,
        )
        events.append(event)

    return events


def create_invoices(db: Session) -> list:
    """Create sample invoices"""
    invoices = []
    now = datetime.now(timezone.utc)

    invoice_data = [
        # Case 1 invoices
        ("case_divorce001", "user_client001", "user_lawyer001", "3000000", InvoiceStatus.PAID,
         "착수금", now - timedelta(days=30), now - timedelta(days=28)),
        ("case_divorce001", "user_client001", "user_lawyer001", "2000000", InvoiceStatus.PENDING,
         "변론기일 수임료", now + timedelta(days=14), None),

        # Case 2 invoices
        ("case_divorce002", "user_client002", "user_lawyer001", "5000000", InvoiceStatus.PAID,
         "착수금", now - timedelta(days=20), now - timedelta(days=18)),
        ("case_divorce002", "user_client002", "user_lawyer001", "3000000", InvoiceStatus.PENDING,
         "추가 증거수집 비용", now + timedelta(days=7), None),

        # Case 3 invoices
        ("case_divorce003", "user_client003", "user_lawyer002", "10000000", InvoiceStatus.PAID,
         "착수금 (고액재산분할)", now - timedelta(days=15), now - timedelta(days=14)),
        ("case_divorce003", "user_client003", "user_lawyer002", "2000000", InvoiceStatus.PENDING,
         "감정비용", now + timedelta(days=10), None),

        # Case 4 invoices
        ("case_divorce004", "user_client004", "user_lawyer002", "2000000", InvoiceStatus.PENDING,
         "양육권 변경 착수금", now + timedelta(days=7), None),

        # Closed case - all paid
        ("case_closed001", "user_client006", "user_lawyer003", "4000000", InvoiceStatus.PAID,
         "착수금", now - timedelta(days=90), now - timedelta(days=88)),
        ("case_closed001", "user_client006", "user_lawyer003", "6000000", InvoiceStatus.PAID,
         "성공보수", now - timedelta(days=30), now - timedelta(days=25)),
    ]

    for case_id, client_id, lawyer_id, amount, status, desc, due_date, paid_at in invoice_data:
        invoice = Invoice(
            case_id=case_id,
            client_id=client_id,
            lawyer_id=lawyer_id,
            amount=amount,
            status=status,
            description=desc,
            due_date=due_date,
            paid_at=paid_at,
        )
        invoices.append(invoice)

    return invoices


def create_investigation_records(db: Session) -> list:
    """Create sample investigation records"""
    records = []
    now = datetime.now(timezone.utc)

    record_data = [
        # Case 1 - Detective 1
        ("case_divorce001", "user_det001", InvestigationRecordType.LOCATION,
         "상대방 차량 이동 경로 추적", "37.5012", "127.0396", "서울시 강남구 역삼동", now - timedelta(days=3)),
        ("case_divorce001", "user_det001", InvestigationRecordType.PHOTO,
         "상대방 거주지 외관 촬영", "37.5015", "127.0400", "서울시 강남구 역삼동 123-45", now - timedelta(days=2)),
        ("case_divorce001", "user_det001", InvestigationRecordType.MEMO,
         "상대방은 평일 오후 6시경 퇴근, 주말에는 외출 빈번함", None, None, None, now - timedelta(days=1)),

        # Case 2 - Detective 2
        ("case_divorce002", "user_det002", InvestigationRecordType.PHOTO,
         "불륜 증거 사진 확보", "37.4979", "127.0276", "서울시 서초구 서초동", now - timedelta(days=5)),
        ("case_divorce002", "user_det002", InvestigationRecordType.AUDIO,
         "목격자 진술 녹음", None, None, None, now - timedelta(days=4)),
        ("case_divorce002", "user_det002", InvestigationRecordType.MEMO,
         "추가 목격자 2명 확인. 연락처 확보 완료.", None, None, None, now - timedelta(days=1)),

        # Case 4 - Detective 3
        ("case_divorce004", "user_det003", InvestigationRecordType.LOCATION,
         "아이 등하교 경로 확인", "37.5665", "126.9780", "서울시 중구 명동", now - timedelta(days=7)),
        ("case_divorce004", "user_det003", InvestigationRecordType.MEMO,
         "양육환경 적합성 조사 진행 중", None, None, None, now - timedelta(days=3)),
    ]

    for case_id, det_id, record_type, content, lat, lng, address, recorded_at in record_data:
        record = InvestigationRecord(
            case_id=case_id,
            detective_id=det_id,
            record_type=record_type,
            content=content,
            location_lat=lat,
            location_lng=lng,
            location_address=address,
            recorded_at=recorded_at,
        )
        records.append(record)

    return records


def create_party_nodes(db: Session) -> list:
    """Create sample party nodes for relationship graphs (인물관계도)"""
    nodes = []

    # Case 1 parties (홍길동 vs 심청)
    parties_case1 = [
        ("party_001", "case_divorce001", PartyType.PLAINTIFF, "홍길동", "홍○○", 1980, "회사원", 100, 100),
        ("party_002", "case_divorce001", PartyType.DEFENDANT, "심청", "심○○", 1983, "주부", 400, 100),
        ("party_003", "case_divorce001", PartyType.CHILD, "홍민수", None, 2015, "초등학생", 250, 250),
        ("party_004", "case_divorce001", PartyType.THIRD_PARTY, "김철수", "김○○", 1978, "사업가", 600, 200),
    ]

    # Case 2 parties (강감찬 vs 배우자)
    parties_case2 = [
        ("party_005", "case_divorce002", PartyType.PLAINTIFF, "강감찬", "강○○", 1975, "의사", 100, 100),
        ("party_006", "case_divorce002", PartyType.DEFENDANT, "이영희", "이○○", 1978, "간호사", 400, 100),
        ("party_007", "case_divorce002", PartyType.THIRD_PARTY, "박지훈", "박○○", 1980, "병원동료", 600, 200),
    ]

    # Case 3 parties (신사임당 - 고액재산분할)
    parties_case3 = [
        ("party_008", "case_divorce003", PartyType.PLAINTIFF, "신사임당", "신○○", 1970, "사업가", 100, 100),
        ("party_009", "case_divorce003", PartyType.DEFENDANT, "이율곡", "이○○", 1968, "교수", 400, 100),
        ("party_010", "case_divorce003", PartyType.CHILD, "이현수", None, 1998, "대학생", 250, 250),
        ("party_011", "case_divorce003", PartyType.CHILD, "이현지", None, 2001, "고등학생", 250, 350),
    ]

    # Case 4 parties (유관순 양육권)
    parties_case4 = [
        ("party_012", "case_divorce004", PartyType.PLAINTIFF, "유관순", "유○○", 1985, "교사", 100, 100),
        ("party_013", "case_divorce004", PartyType.DEFENDANT, "김영훈", "김○○", 1982, "회계사", 400, 100),
        ("party_014", "case_divorce004", PartyType.CHILD, "김소율", None, 2018, "유치원생", 250, 250),
    ]

    all_parties = parties_case1 + parties_case2 + parties_case3 + parties_case4

    for party_id, case_id, p_type, name, alias, birth_year, occupation, pos_x, pos_y in all_parties:
        node = PartyNode(
            id=party_id,
            case_id=case_id,
            type=p_type,
            name=name,
            alias=alias,
            birth_year=birth_year,
            occupation=occupation,
            position_x=pos_x,
            position_y=pos_y,
        )
        nodes.append(node)

    return nodes


def create_party_relationships(db: Session) -> list:
    """Create sample party relationships (관계)"""
    relationships = []
    now = datetime.now(timezone.utc)

    rel_data = [
        # Case 1: 홍길동-심청 혼인, 홍길동-홍민수 부모자녀, 심청-김철수 불륜
        ("rel_001", "case_divorce001", "party_001", "party_002", RelationshipType.MARRIAGE,
         now - timedelta(days=3650), None, "2014년 혼인, 결혼생활 10년"),
        ("rel_002", "case_divorce001", "party_001", "party_003", RelationshipType.PARENT_CHILD,
         now - timedelta(days=3285), None, "친자관계"),
        ("rel_003", "case_divorce001", "party_002", "party_003", RelationshipType.PARENT_CHILD,
         now - timedelta(days=3285), None, "친자관계"),
        ("rel_004", "case_divorce001", "party_002", "party_004", RelationshipType.AFFAIR,
         now - timedelta(days=365), None, "2023년경부터 불륜관계 시작"),

        # Case 2: 강감찬-이영희 혼인, 이영희-박지훈 불륜
        ("rel_005", "case_divorce002", "party_005", "party_006", RelationshipType.MARRIAGE,
         now - timedelta(days=5475), None, "2009년 혼인, 결혼생활 15년"),
        ("rel_006", "case_divorce002", "party_006", "party_007", RelationshipType.AFFAIR,
         now - timedelta(days=730), None, "병원 동료로 만남, 2022년경 불륜"),

        # Case 3: 신사임당-이율곡 혼인, 부모자녀 관계들
        ("rel_007", "case_divorce003", "party_008", "party_009", RelationshipType.MARRIAGE,
         now - timedelta(days=9490), None, "1998년 혼인, 결혼생활 26년"),
        ("rel_008", "case_divorce003", "party_008", "party_010", RelationshipType.PARENT_CHILD,
         now - timedelta(days=9490), None, "친자관계"),
        ("rel_009", "case_divorce003", "party_008", "party_011", RelationshipType.PARENT_CHILD,
         now - timedelta(days=8395), None, "친자관계"),
        ("rel_010", "case_divorce003", "party_009", "party_010", RelationshipType.PARENT_CHILD,
         now - timedelta(days=9490), None, "친자관계"),
        ("rel_011", "case_divorce003", "party_009", "party_011", RelationshipType.PARENT_CHILD,
         now - timedelta(days=8395), None, "친자관계"),
        ("rel_012", "case_divorce003", "party_010", "party_011", RelationshipType.SIBLING,
         None, None, "남매 관계"),

        # Case 4: 유관순-김영훈 혼인, 부모자녀 관계
        ("rel_013", "case_divorce004", "party_012", "party_013", RelationshipType.MARRIAGE,
         now - timedelta(days=2920), None, "2016년 혼인"),
        ("rel_014", "case_divorce004", "party_012", "party_014", RelationshipType.PARENT_CHILD,
         now - timedelta(days=2190), None, "친자관계"),
        ("rel_015", "case_divorce004", "party_013", "party_014", RelationshipType.PARENT_CHILD,
         now - timedelta(days=2190), None, "친자관계"),
    ]

    for rel_id, case_id, source_id, target_id, rel_type, start_date, end_date, notes in rel_data:
        rel = PartyRelationship(
            id=rel_id,
            case_id=case_id,
            source_party_id=source_id,
            target_party_id=target_id,
            type=rel_type,
            start_date=start_date,
            end_date=end_date,
            notes=notes,
        )
        relationships.append(rel)

    return relationships


def create_consultations(db: Session) -> tuple:
    """Create sample consultation records (상담 기록)"""
    consultations = []
    participants_list = []
    now = datetime.now(timezone.utc)

    consult_data = [
        # Case 1 consultations
        ("consult_001", "case_divorce001", now - timedelta(days=30), "10:00", ConsultationType.IN_PERSON,
         "초기 상담: 이혼 사유 및 재산분할 논의", "협의이혼 시도 후 실패, 재판이혼 진행 결정",
         "user_lawyer001", [("홍길동", "client"), ("김변호사", "lawyer")]),
        ("consult_002", "case_divorce001", now - timedelta(days=14), "14:00", ConsultationType.PHONE,
         "증거자료 검토 상담", "카카오톡 대화 내역 및 사진 증거 검토 완료",
         "user_lawyer001", [("홍길동", "client"), ("김변호사", "lawyer")]),
        ("consult_003", "case_divorce001", now - timedelta(days=3), "11:00", ConsultationType.ONLINE,
         "변론 준비 화상 상담", "1차 변론기일 준비, 쟁점 정리",
         "user_lawyer001", [("홍길동", "client"), ("김변호사", "lawyer"), ("정사무장", "staff")]),

        # Case 2 consultations
        ("consult_004", "case_divorce002", now - timedelta(days=20), "15:00", ConsultationType.IN_PERSON,
         "긴급 상담: 불륜 증거 확보", "목격자 진술 및 사진 증거 검토",
         "user_lawyer001", [("강감찬", "client"), ("김변호사", "lawyer")]),
        ("consult_005", "case_divorce002", now - timedelta(days=7), "09:00", ConsultationType.PHONE,
         "위자료 청구 금액 논의", "3천만원 위자료 청구 결정",
         "user_lawyer001", [("강감찬", "client"), ("김변호사", "lawyer")]),

        # Case 3 consultations
        ("consult_006", "case_divorce003", now - timedelta(days=15), "10:30", ConsultationType.IN_PERSON,
         "재산분할 초기 상담", "고액 재산 목록 작성, 감정 필요 부동산 식별",
         "user_lawyer002", [("신사임당", "client"), ("이변호사", "lawyer")]),
        ("consult_007", "case_divorce003", now - timedelta(days=2), "14:30", ConsultationType.IN_PERSON,
         "감정결과 설명 및 분할비율 논의", "부동산 감정가 15억, 50:50 분할 요청 예정",
         "user_lawyer002", [("신사임당", "client"), ("이변호사", "lawyer"), ("최파라리걸", "staff")]),

        # Case 4 consultations
        ("consult_008", "case_divorce004", now - timedelta(days=10), "16:00", ConsultationType.IN_PERSON,
         "양육권 변경 상담", "현 양육환경 문제점 논의, 변경 사유 정리",
         "user_lawyer002", [("유관순", "client"), ("이변호사", "lawyer")]),
    ]

    for consult_id, case_id, date, time_str, c_type, summary, notes, created_by, ppts in consult_data:
        consult = Consultation(
            id=consult_id,
            case_id=case_id,
            date=date.date(),
            time=datetime.strptime(time_str, "%H:%M").time(),
            type=c_type,
            summary=summary,
            notes=notes,
            created_by=created_by,
        )
        consultations.append(consult)

        # Create participants
        for ppt_name, ppt_role in ppts:
            participant = ConsultationParticipant(
                consultation_id=consult_id,
                name=ppt_name,
                role=ppt_role,
            )
            participants_list.append(participant)

    return consultations, participants_list


def create_draft_documents(db: Session) -> list:
    """Create sample draft documents (초안 문서)"""
    drafts = []

    draft_data = [
        # Case 1 drafts
        ("draft_001", "case_divorce001", "이혼 소장 초안", DocumentType.COMPLAINT, DraftStatus.REVIEWED,
         "user_lawyer001", {
             "title": "소장",
             "court": "서울가정법원",
             "case_type": "이혼 등 청구",
             "sections": [
                 {"heading": "청구취지", "content": "1. 원고와 피고는 이혼한다.\n2. 사건 본인의 친권자 및 양육자를 원고로 지정한다."},
                 {"heading": "청구원인", "content": "피고는 혼인 기간 중 제3자와 부정행위를 하였으며..."},
                 {"heading": "입증방법", "content": "1. 카카오톡 대화 내역\n2. 목격자 진술서"},
             ]
         }),
        ("draft_002", "case_divorce001", "준비서면 1차", DocumentType.BRIEF, DraftStatus.DRAFT,
         "user_lawyer001", {
             "title": "준비서면",
             "sections": [
                 {"heading": "1. 피고의 유책사유", "content": "피고는 2023년경부터 불륜관계를 유지하였음..."},
                 {"heading": "2. 재산분할 청구", "content": "혼인 중 취득 재산에 대해 50% 분할 청구..."},
             ]
         }),

        # Case 2 drafts
        ("draft_003", "case_divorce002", "위자료 청구 소장", DocumentType.COMPLAINT, DraftStatus.REVIEWED,
         "user_lawyer001", {
             "title": "소장",
             "court": "서울가정법원",
             "case_type": "위자료 청구",
             "sections": [
                 {"heading": "청구취지", "content": "1. 피고는 원고에게 금 30,000,000원을 지급하라."},
                 {"heading": "청구원인", "content": "피고는 혼인 기간 중 병원 동료와 부정행위..."},
             ]
         }),

        # Case 3 drafts
        ("draft_004", "case_divorce003", "재산분할 청구 소장", DocumentType.COMPLAINT, DraftStatus.DRAFT,
         "user_lawyer002", {
             "title": "소장",
             "court": "서울가정법원",
             "case_type": "재산분할 청구",
             "sections": [
                 {"heading": "청구취지", "content": "1. 피고는 원고에게 금 750,000,000원을 지급하라."},
                 {"heading": "재산목록", "content": "1. 서울시 강남구 소재 아파트 (감정가 15억원)\n2. 예금 2억원"},
             ]
         }),

        # Case 4 drafts
        ("draft_005", "case_divorce004", "양육권 변경 신청서", DocumentType.MOTION, DraftStatus.DRAFT,
         "user_lawyer002", {
             "title": "양육자 변경 신청서",
             "court": "서울가정법원",
             "sections": [
                 {"heading": "신청취지", "content": "사건 본인의 양육자를 피고에서 원고로 변경한다."},
                 {"heading": "신청이유", "content": "피고의 양육환경이 사건 본인의 복리에 부적합함..."},
             ]
         }),
    ]

    for draft_id, case_id, title, doc_type, status, created_by, content in draft_data:
        draft = DraftDocument(
            id=draft_id,
            case_id=case_id,
            title=title,
            document_type=doc_type,
            status=status,
            created_by=created_by,
            content=content,
        )
        drafts.append(draft)

    return drafts


def create_user_settings(db: Session, users: list) -> list:
    """Create default settings for all users"""
    settings = []
    for user in users:
        setting = UserSettings(
            user_id=user.id,
            notification_email=True,
            notification_push=True,
            notification_sms=False,
            theme="light",
            language="ko",
        )
        settings.append(setting)
    return settings


def seed_database():
    """Main seeding function"""
    print("=" * 60)
    print("LEH Database Seed Script")
    print("=" * 60)

    # Initialize database connection
    print("\nInitializing database connection...")
    db_session.init_db()

    db = db_session.SessionLocal()

    try:
        # Check if data already exists
        existing_users = db.query(User).count()
        if existing_users > 0:
            response = input(f"\n{existing_users} users already exist. Clear and reseed? (y/N): ")
            if response.lower() != 'y':
                print("Aborted.")
                return

            # Clear existing data in order (respecting foreign keys)
            print("\nClearing existing data...")
            # New models first (due to FK dependencies)
            db.query(DraftDocument).delete()
            db.query(ConsultationParticipant).delete()
            db.query(Consultation).delete()
            db.query(PartyRelationship).delete()
            db.query(PartyNode).delete()
            # Original models
            db.query(InvestigationRecord).delete()
            db.query(Invoice).delete()
            db.query(CalendarEvent).delete()
            db.query(Message).delete()
            db.query(UserSettings).delete()
            db.query(CaseMember).delete()
            db.query(Case).delete()
            db.query(User).delete()
            db.commit()
            print("Existing data cleared.")

        # Create users
        print("\n[1/11] Creating users...")
        all_user_data = ADMIN + LAWYERS + STAFF + CLIENTS + DETECTIVES
        users = []
        hashed_pw = hash_password(DEFAULT_PASSWORD)

        for user_data in all_user_data:
            user = User(
                id=user_data["id"],
                email=user_data["email"],
                name=user_data["name"],
                role=user_data["role"],
                status=UserStatus.ACTIVE,
                hashed_password=hashed_pw,
            )
            users.append(user)
            db.add(user)

        db.commit()
        print(f"  Created {len(users)} users")

        # Create cases
        print("\n[2/11] Creating cases...")
        cases = []
        for case_data in CASES:
            case = Case(
                id=case_data["id"],
                title=case_data["title"],
                client_name=case_data["client_name"],
                description=case_data["description"],
                status=case_data["status"],
                created_by=case_data["created_by"],
            )
            cases.append(case)
            db.add(case)

        db.commit()
        print(f"  Created {len(cases)} cases")

        # Create case members
        print("\n[3/11] Creating case members...")
        member_count = 0
        for case_data in CASES:
            for user_id, role in case_data["members"]:
                member = CaseMember(
                    case_id=case_data["id"],
                    user_id=user_id,
                    role=role,
                )
                db.add(member)
                member_count += 1

        db.commit()
        print(f"  Created {member_count} case memberships")

        # Create messages
        print("\n[4/11] Creating messages...")
        messages = create_messages(db)
        for msg in messages:
            db.add(msg)
        db.commit()
        print(f"  Created {len(messages)} messages")

        # Create calendar events
        print("\n[5/11] Creating calendar events...")
        events = create_calendar_events(db)
        for event in events:
            db.add(event)
        db.commit()
        print(f"  Created {len(events)} calendar events")

        # Create invoices
        print("\n[6/11] Creating invoices...")
        invoices = create_invoices(db)
        for invoice in invoices:
            db.add(invoice)
        db.commit()
        print(f"  Created {len(invoices)} invoices")

        # Create investigation records
        print("\n[7/11] Creating investigation records...")
        records = create_investigation_records(db)
        for record in records:
            db.add(record)
        db.commit()
        print(f"  Created {len(records)} investigation records")

        # Create party nodes (인물관계도 노드)
        print("\n[8/11] Creating party nodes...")
        party_nodes = create_party_nodes(db)
        for node in party_nodes:
            db.add(node)
        db.commit()
        print(f"  Created {len(party_nodes)} party nodes")

        # Create party relationships (인물관계도 관계)
        print("\n[9/11] Creating party relationships...")
        party_rels = create_party_relationships(db)
        for rel in party_rels:
            db.add(rel)
        db.commit()
        print(f"  Created {len(party_rels)} party relationships")

        # Create consultations (상담 기록)
        print("\n[10/11] Creating consultations...")
        consultations, participants = create_consultations(db)
        for consult in consultations:
            db.add(consult)
        db.commit()
        for ppt in participants:
            db.add(ppt)
        db.commit()
        print(f"  Created {len(consultations)} consultations with {len(participants)} participants")

        # Create draft documents (초안 문서)
        print("\n[11/11] Creating draft documents...")
        drafts = create_draft_documents(db)
        for draft in drafts:
            db.add(draft)
        db.commit()
        print(f"  Created {len(drafts)} draft documents")

        # Summary
        print("\n" + "=" * 60)
        print("SEED COMPLETE!")
        print("=" * 60)
        print(f"""
Summary:
  - Users: {len(users)}
    - Admins: {len(ADMIN)}
    - Lawyers: {len(LAWYERS)}
    - Staff: {len(STAFF)}
    - Clients: {len(CLIENTS)}
    - Detectives: {len(DETECTIVES)}
  - Cases: {len(cases)}
  - Case Members: {member_count}
  - Messages: {len(messages)}
  - Calendar Events: {len(events)}
  - Invoices: {len(invoices)}
  - Investigation Records: {len(records)}
  - Party Nodes: {len(party_nodes)}
  - Party Relationships: {len(party_rels)}
  - Consultations: {len(consultations)} ({len(participants)} participants)
  - Draft Documents: {len(drafts)}

Default login credentials:
  Email: kim.lawyer@leh.dev
  Password: {DEFAULT_PASSWORD}

Other test accounts:
  - lee.lawyer@leh.dev (Lawyer)
  - hong.client@example.com (Client)
  - oh.detective@leh.dev (Detective)
  - admin@leh.dev (Admin)
  All use password: {DEFAULT_PASSWORD}
""")

    except Exception as e:
        print(f"\nError during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
