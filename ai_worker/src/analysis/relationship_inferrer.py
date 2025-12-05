"""
RelationshipInferrer - 인물 간 관계 추론

규칙 기반 관계 추론기
- 키워드 기반 관계 감지
- 동시 출현 분석
- 관계 그래프 생성

LLM 의존 없이 규칙 기반으로 구현
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Set
from enum import Enum

from .person_extractor import (
    PersonExtractor,
    ExtractedPerson,
    PersonRole,
)


# =============================================================================
# 상수 정의
# =============================================================================

class RelationshipType(Enum):
    """관계 유형"""
    SPOUSE = "spouse"                 # 배우자
    EX_SPOUSE = "ex_spouse"           # 전 배우자
    PARENT = "parent"                 # 부모
    CHILD = "child"                   # 자녀
    SIBLING = "sibling"               # 형제자매
    IN_LAW = "in_law"                 # 시/처가
    RELATIVE = "relative"             # 친척
    FRIEND = "friend"                 # 친구
    COLLEAGUE = "colleague"           # 직장동료
    AFFAIR = "affair"                 # 외도 상대
    ACQUAINTANCE = "acquaintance"     # 지인
    UNKNOWN = "unknown"               # 미상


# 관계 키워드 → RelationshipType 매핑
RELATIONSHIP_KEYWORDS: Dict[str, RelationshipType] = {
    # 배우자
    "남편": RelationshipType.SPOUSE,
    "아내": RelationshipType.SPOUSE,
    "배우자": RelationshipType.SPOUSE,
    "신랑": RelationshipType.SPOUSE,
    "신부": RelationshipType.SPOUSE,

    # 부모-자녀
    "아버지": RelationshipType.PARENT,
    "어머니": RelationshipType.PARENT,
    "아빠": RelationshipType.PARENT,
    "엄마": RelationshipType.PARENT,
    "부모님": RelationshipType.PARENT,
    "아들": RelationshipType.CHILD,
    "딸": RelationshipType.CHILD,
    "자녀": RelationshipType.CHILD,

    # 시가/처가
    "시어머니": RelationshipType.IN_LAW,
    "시아버지": RelationshipType.IN_LAW,
    "시누이": RelationshipType.IN_LAW,
    "시동생": RelationshipType.IN_LAW,
    "장모": RelationshipType.IN_LAW,
    "장인": RelationshipType.IN_LAW,
    "처남": RelationshipType.IN_LAW,
    "처제": RelationshipType.IN_LAW,

    # 형제자매
    "형": RelationshipType.SIBLING,
    "오빠": RelationshipType.SIBLING,
    "언니": RelationshipType.SIBLING,
    "누나": RelationshipType.SIBLING,
    "동생": RelationshipType.SIBLING,

    # 외도
    "바람": RelationshipType.AFFAIR,
    "외도": RelationshipType.AFFAIR,
    "불륜": RelationshipType.AFFAIR,
    "상간녀": RelationshipType.AFFAIR,
    "상간남": RelationshipType.AFFAIR,
    "내연녀": RelationshipType.AFFAIR,
    "내연남": RelationshipType.AFFAIR,

    # 친구/동료
    "친구": RelationshipType.FRIEND,
    "동료": RelationshipType.COLLEAGUE,
    "직장동료": RelationshipType.COLLEAGUE,
}

# 관계 라벨 (한글)
RELATIONSHIP_LABELS: Dict[RelationshipType, str] = {
    RelationshipType.SPOUSE: "배우자",
    RelationshipType.EX_SPOUSE: "전 배우자",
    RelationshipType.PARENT: "부모",
    RelationshipType.CHILD: "자녀",
    RelationshipType.SIBLING: "형제자매",
    RelationshipType.IN_LAW: "시/처가",
    RelationshipType.RELATIVE: "친척",
    RelationshipType.FRIEND: "친구",
    RelationshipType.COLLEAGUE: "직장동료",
    RelationshipType.AFFAIR: "외도 상대",
    RelationshipType.ACQUAINTANCE: "지인",
    RelationshipType.UNKNOWN: "관계 미상",
}

# 관계 색상 (시각화용)
RELATIONSHIP_COLORS: Dict[RelationshipType, str] = {
    RelationshipType.SPOUSE: "#2196F3",       # 파랑
    RelationshipType.EX_SPOUSE: "#9E9E9E",    # 회색
    RelationshipType.PARENT: "#4CAF50",       # 초록
    RelationshipType.CHILD: "#4CAF50",        # 초록
    RelationshipType.SIBLING: "#8BC34A",      # 연두
    RelationshipType.IN_LAW: "#FF9800",       # 주황
    RelationshipType.RELATIVE: "#FFEB3B",     # 노랑
    RelationshipType.FRIEND: "#03A9F4",       # 하늘
    RelationshipType.COLLEAGUE: "#00BCD4",    # 청록
    RelationshipType.AFFAIR: "#E91E63",       # 핑크
    RelationshipType.ACQUAINTANCE: "#9E9E9E", # 회색
    RelationshipType.UNKNOWN: "#BDBDBD",      # 연회색
}


# =============================================================================
# 데이터 클래스
# =============================================================================

@dataclass
class PersonRelationship:
    """인물 간 관계"""
    person_a: str                                # 인물 A 이름
    person_b: str                                # 인물 B 이름
    relationship_type: RelationshipType          # 관계 유형
    direction: str = "bidirectional"             # "a_to_b", "b_to_a", "bidirectional"
    confidence: float = 0.5                      # 신뢰도 (0~1)
    evidence: str = ""                           # 관계 증거 (문맥)

    def to_dict(self) -> Dict:
        """딕셔너리 변환"""
        return {
            "source": self.person_a,
            "target": self.person_b,
            "relationship": self.relationship_type.value,
            "label": RELATIONSHIP_LABELS.get(
                self.relationship_type,
                self.relationship_type.value
            ),
            "direction": self.direction,
            "confidence": self.confidence,
            "color": RELATIONSHIP_COLORS.get(
                self.relationship_type,
                "#BDBDBD"
            ),
            "evidence": self.evidence,
        }

    def __hash__(self):
        # 양방향 관계이면 순서 무관하게 동일하게 처리
        if self.direction == "bidirectional":
            names = tuple(sorted([self.person_a, self.person_b]))
            return hash((names, self.relationship_type))
        return hash((self.person_a, self.person_b, self.relationship_type))

    def __eq__(self, other):
        if isinstance(other, PersonRelationship):
            if self.direction == "bidirectional" and other.direction == "bidirectional":
                return (
                    set([self.person_a, self.person_b]) ==
                    set([other.person_a, other.person_b]) and
                    self.relationship_type == other.relationship_type
                )
            return (
                self.person_a == other.person_a and
                self.person_b == other.person_b and
                self.relationship_type == other.relationship_type
            )
        return False


@dataclass
class PersonNode:
    """인물 노드 (그래프 시각화용)"""
    id: str
    name: str
    role: str
    side: str
    color: str = "#9E9E9E"

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "side": self.side,
            "color": self.color,
        }


@dataclass
class RelationshipGraph:
    """관계 그래프"""
    nodes: List[PersonNode]
    edges: List[PersonRelationship]

    def to_dict(self) -> Dict:
        """딕셔너리 변환 (API 응답용)"""
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
        }


# =============================================================================
# RelationshipInferrer 클래스
# =============================================================================

class RelationshipInferrer:
    """인물 간 관계를 추론하는 클래스"""

    # 역할별 노드 색상
    ROLE_COLORS = {
        "plaintiff": "#4CAF50",       # 초록 (원고)
        "defendant": "#F44336",       # 빨강 (피고)
        "child": "#2196F3",           # 파랑 (자녀)
        "plaintiff_parent": "#81C784", # 연초록
        "defendant_parent": "#EF5350", # 연빨강
        "third_party": "#E91E63",     # 핑크 (제3자/외도)
        "relative": "#FF9800",        # 주황
        "friend": "#03A9F4",          # 하늘
        "colleague": "#00BCD4",       # 청록
        "unknown": "#9E9E9E",         # 회색
    }

    def __init__(self, min_confidence: float = 0.3):
        """
        Args:
            min_confidence: 최소 신뢰도 (이하는 제외)
        """
        self.min_confidence = min_confidence
        self.person_extractor = PersonExtractor()

    def infer_relationships(
        self,
        text: str,
        persons: List[ExtractedPerson] = None
    ) -> List[PersonRelationship]:
        """
        텍스트에서 인물 간 관계 추론

        Args:
            text: 분석할 텍스트
            persons: 이미 추출된 인물 목록 (없으면 자동 추출)

        Returns:
            PersonRelationship 리스트
        """
        if not text:
            return []

        # 인물 추출
        if persons is None:
            result = self.person_extractor.extract(text)
            persons = result.persons

        if len(persons) < 2:
            return []

        relationships: Set[PersonRelationship] = set()

        # 1. 키워드 기반 관계 추론
        keyword_rels = self._infer_from_keywords(text, persons)
        relationships.update(keyword_rels)

        # 2. 역할 기반 관계 추론
        role_rels = self._infer_from_roles(persons)
        relationships.update(role_rels)

        # 3. 동시 출현 기반 관계 추론
        cooccur_rels = self._infer_from_cooccurrence(text, persons)
        relationships.update(cooccur_rels)

        # 신뢰도 필터링
        filtered = [
            r for r in relationships
            if r.confidence >= self.min_confidence
        ]

        return filtered

    def _infer_from_keywords(
        self,
        text: str,
        persons: List[ExtractedPerson]
    ) -> List[PersonRelationship]:
        """키워드 기반 관계 추론"""
        relationships = []

        # 관계 키워드 검색
        for keyword, rel_type in RELATIONSHIP_KEYWORDS.items():
            if keyword not in text:
                continue

            # 키워드 주변 문맥에서 인물 찾기
            pattern = rf"(.{{0,30}}){re.escape(keyword)}(.{{0,30}})"
            for match in re.finditer(pattern, text):
                context = match.group()

                # 문맥에서 인물 이름 찾기
                found_persons = []
                for person in persons:
                    if person.name in context:
                        found_persons.append(person)

                # 2명 이상이면 관계 생성
                if len(found_persons) >= 2:
                    rel = PersonRelationship(
                        person_a=found_persons[0].name,
                        person_b=found_persons[1].name,
                        relationship_type=rel_type,
                        confidence=0.8,
                        evidence=context.strip(),
                    )
                    relationships.append(rel)

                # 원고/피고와 키워드 조합
                elif len(found_persons) == 1:
                    # 외도 관련 키워드 + 제3자
                    if rel_type == RelationshipType.AFFAIR:
                        # 피고와의 외도 관계로 추정
                        defendant = self._find_defendant(persons)
                        if defendant and found_persons[0].name != defendant:
                            rel = PersonRelationship(
                                person_a=defendant,
                                person_b=found_persons[0].name,
                                relationship_type=rel_type,
                                confidence=0.7,
                                evidence=context.strip(),
                            )
                            relationships.append(rel)

        return relationships

    def _infer_from_roles(
        self,
        persons: List[ExtractedPerson]
    ) -> List[PersonRelationship]:
        """역할 기반 관계 추론"""
        relationships = []

        plaintiff = None
        defendant = None
        children = []
        third_parties = []
        in_laws = []

        for person in persons:
            if person.role == PersonRole.PLAINTIFF:
                plaintiff = person
            elif person.role == PersonRole.DEFENDANT:
                defendant = person
            elif person.role == PersonRole.CHILD:
                children.append(person)
            elif person.role == PersonRole.THIRD_PARTY:
                third_parties.append(person)
            elif person.role in [PersonRole.DEFENDANT_PARENT, PersonRole.PLAINTIFF_PARENT]:
                in_laws.append(person)

        # 원고-피고 = 배우자
        if plaintiff and defendant:
            rel = PersonRelationship(
                person_a=plaintiff.name,
                person_b=defendant.name,
                relationship_type=RelationshipType.SPOUSE,
                confidence=0.95,
                evidence="원고-피고 관계",
            )
            relationships.append(rel)

        # 자녀 관계
        for child in children:
            if plaintiff:
                rel = PersonRelationship(
                    person_a=plaintiff.name,
                    person_b=child.name,
                    relationship_type=RelationshipType.CHILD,
                    direction="a_to_b",
                    confidence=0.9,
                    evidence="원고의 자녀",
                )
                relationships.append(rel)

            if defendant:
                rel = PersonRelationship(
                    person_a=defendant.name,
                    person_b=child.name,
                    relationship_type=RelationshipType.CHILD,
                    direction="a_to_b",
                    confidence=0.9,
                    evidence="피고의 자녀",
                )
                relationships.append(rel)

        # 제3자(외도 상대)와 피고
        for third in third_parties:
            if defendant:
                rel = PersonRelationship(
                    person_a=defendant.name,
                    person_b=third.name,
                    relationship_type=RelationshipType.AFFAIR,
                    confidence=0.85,
                    evidence="외도 상대로 추정",
                )
                relationships.append(rel)

        # 시/처가 관계
        for in_law in in_laws:
            if in_law.role == PersonRole.DEFENDANT_PARENT and defendant:
                rel = PersonRelationship(
                    person_a=defendant.name,
                    person_b=in_law.name,
                    relationship_type=RelationshipType.PARENT,
                    direction="b_to_a",
                    confidence=0.9,
                    evidence="피고의 부모",
                )
                relationships.append(rel)
            elif in_law.role == PersonRole.PLAINTIFF_PARENT and plaintiff:
                rel = PersonRelationship(
                    person_a=plaintiff.name,
                    person_b=in_law.name,
                    relationship_type=RelationshipType.PARENT,
                    direction="b_to_a",
                    confidence=0.9,
                    evidence="원고의 부모",
                )
                relationships.append(rel)

        return relationships

    def _infer_from_cooccurrence(
        self,
        text: str,
        persons: List[ExtractedPerson]
    ) -> List[PersonRelationship]:
        """동시 출현 기반 관계 추론"""
        relationships = []

        # 같은 문장에 2명 이상 등장하면 연관 있음
        sentences = re.split(r"[.!?\n]", text)

        for sentence in sentences:
            found_in_sentence = []
            for person in persons:
                if person.name in sentence:
                    found_in_sentence.append(person)

            # 2명이 같은 문장에 등장
            if len(found_in_sentence) == 2:
                # 이미 다른 관계로 추론되지 않은 경우만
                p1, p2 = found_in_sentence

                # 지인 관계로 추가 (낮은 신뢰도)
                rel = PersonRelationship(
                    person_a=p1.name,
                    person_b=p2.name,
                    relationship_type=RelationshipType.ACQUAINTANCE,
                    confidence=0.4,
                    evidence=sentence.strip()[:50],
                )
                relationships.append(rel)

        return relationships

    def _find_defendant(self, persons: List[ExtractedPerson]) -> Optional[str]:
        """피고 찾기"""
        for person in persons:
            if person.role == PersonRole.DEFENDANT:
                return person.name
            # 키워드로 추정
            if person.name in ["남편", "아내", "배우자", "상대방"]:
                return person.name
        return None

    def build_graph(
        self,
        text: str,
        case_id: str = None
    ) -> RelationshipGraph:
        """
        관계 그래프 생성

        Args:
            text: 분석할 텍스트
            case_id: 사건 ID (노드 ID 생성용)

        Returns:
            RelationshipGraph: 노드와 엣지로 구성된 그래프
        """
        # 인물 추출
        person_result = self.person_extractor.extract(text)
        persons = person_result.persons

        # 관계 추론
        relationships = self.infer_relationships(text, persons)

        # 노드 생성
        nodes = []
        for i, person in enumerate(persons):
            node_id = f"{case_id or 'case'}-person-{i}"
            color = self.ROLE_COLORS.get(person.role.value, "#9E9E9E")

            node = PersonNode(
                id=node_id,
                name=person.name,
                role=person.role.value,
                side=person.side.value,
                color=color,
            )
            nodes.append(node)

        # 엣지의 인물 이름을 노드 ID로 매핑
        name_to_id = {n.name: n.id for n in nodes}
        edges = []
        for rel in relationships:
            # 이름을 ID로 변환
            if rel.person_a in name_to_id and rel.person_b in name_to_id:
                mapped_rel = PersonRelationship(
                    person_a=name_to_id[rel.person_a],
                    person_b=name_to_id[rel.person_b],
                    relationship_type=rel.relationship_type,
                    direction=rel.direction,
                    confidence=rel.confidence,
                    evidence=rel.evidence,
                )
                edges.append(mapped_rel)

        return RelationshipGraph(nodes=nodes, edges=edges)

    def build_graph_from_messages(
        self,
        messages: List[Dict],
        case_id: str = None
    ) -> RelationshipGraph:
        """
        메시지 목록에서 관계 그래프 생성

        Args:
            messages: [{"sender": "...", "content": "..."}] 형식
            case_id: 사건 ID

        Returns:
            RelationshipGraph
        """
        # 전체 텍스트로 합치기
        full_text = "\n".join([
            f"[{m.get('sender', '')}] {m.get('content', '')}"
            for m in messages
        ])

        return self.build_graph(full_text, case_id)


# =============================================================================
# 간편 함수
# =============================================================================

def infer_relationships(text: str) -> List[Dict]:
    """
    텍스트에서 관계 추론 (간편 함수)

    Args:
        text: 분석할 텍스트

    Returns:
        관계 정보 딕셔너리 리스트
    """
    inferrer = RelationshipInferrer()
    relationships = inferrer.infer_relationships(text)
    return [r.to_dict() for r in relationships]


def build_relationship_graph(text: str, case_id: str = None) -> Dict:
    """
    관계 그래프 생성 (간편 함수)

    Args:
        text: 분석할 텍스트
        case_id: 사건 ID

    Returns:
        {"nodes": [...], "edges": [...]} 형식
    """
    inferrer = RelationshipInferrer()
    graph = inferrer.build_graph(text, case_id)
    return graph.to_dict()
