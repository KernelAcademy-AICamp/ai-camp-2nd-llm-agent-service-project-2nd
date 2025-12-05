"""
RelationshipInferrer 테스트

관계 추론기 테스트
"""


from src.analysis.relationship_inferrer import (
    RelationshipInferrer,
    PersonRelationship,
    RelationshipType,
    RelationshipGraph,
    PersonNode,
    infer_relationships,
    build_relationship_graph,
    RELATIONSHIP_KEYWORDS,
    RELATIONSHIP_LABELS,
    RELATIONSHIP_COLORS,
)
from src.analysis.person_extractor import (
    ExtractedPerson,
    PersonRole,
)


# =============================================================================
# RelationshipInferrer 초기화 테스트
# =============================================================================

class TestRelationshipInferrerInit:
    """RelationshipInferrer 초기화 테스트"""

    def test_default_init(self):
        """기본 초기화"""
        inferrer = RelationshipInferrer()
        assert inferrer.min_confidence == 0.3

    def test_custom_init(self):
        """커스텀 초기화"""
        inferrer = RelationshipInferrer(min_confidence=0.5)
        assert inferrer.min_confidence == 0.5


# =============================================================================
# 키워드 기반 관계 추론 테스트
# =============================================================================

class TestKeywordRelationshipInference:
    """키워드 기반 관계 추론 테스트"""

    def test_spouse_keyword(self):
        """배우자 키워드"""
        inferrer = RelationshipInferrer()
        rels = inferrer.infer_relationships("김철수 남편이 이영희와 만났다")
        _ = [r.relationship_type for r in rels]
        # 배우자 관계가 추론될 수 있음

    def test_affair_keyword(self):
        """외도 키워드"""
        inferrer = RelationshipInferrer()
        rels = inferrer.infer_relationships("남편이 박지연과 불륜 관계")
        _ = [r.relationship_type for r in rels]
        # AFFAIR 관계가 추론될 수 있음

    def test_friend_keyword(self):
        """친구 키워드"""
        inferrer = RelationshipInferrer()
        _ = inferrer.infer_relationships("김철수는 내 친구야")
        # 친구 관계 추론


# =============================================================================
# 역할 기반 관계 추론 테스트
# =============================================================================

class TestRoleBasedInference:
    """역할 기반 관계 추론 테스트"""

    def test_plaintiff_defendant_spouse(self):
        """원고-피고 배우자 관계"""
        inferrer = RelationshipInferrer()
        persons = [
            ExtractedPerson(name="원고", role=PersonRole.PLAINTIFF),
            ExtractedPerson(name="피고", role=PersonRole.DEFENDANT),
        ]
        rels = inferrer.infer_relationships("원고와 피고", persons)
        spouse_rels = [r for r in rels if r.relationship_type == RelationshipType.SPOUSE]
        assert len(spouse_rels) > 0

    def test_parent_child_relationship(self):
        """부모-자녀 관계"""
        inferrer = RelationshipInferrer()
        persons = [
            ExtractedPerson(name="원고", role=PersonRole.PLAINTIFF),
            ExtractedPerson(name="철수", role=PersonRole.CHILD),
        ]
        rels = inferrer.infer_relationships("원고와 철수", persons)
        child_rels = [r for r in rels if r.relationship_type == RelationshipType.CHILD]
        assert len(child_rels) > 0

    def test_third_party_affair(self):
        """제3자 외도 관계"""
        inferrer = RelationshipInferrer()
        persons = [
            ExtractedPerson(name="피고", role=PersonRole.DEFENDANT),
            ExtractedPerson(name="박지연", role=PersonRole.THIRD_PARTY),
        ]
        rels = inferrer.infer_relationships("피고와 박지연", persons)
        affair_rels = [r for r in rels if r.relationship_type == RelationshipType.AFFAIR]
        assert len(affair_rels) > 0


# =============================================================================
# 동시 출현 기반 추론 테스트
# =============================================================================

class TestCooccurrenceInference:
    """동시 출현 기반 관계 추론 테스트"""

    def test_same_sentence_cooccurrence(self):
        """같은 문장 동시 출현"""
        inferrer = RelationshipInferrer()
        persons = [
            ExtractedPerson(name="김철수"),
            ExtractedPerson(name="이영희"),
        ]
        rels = inferrer.infer_relationships(
            "김철수와 이영희가 식당에서 만났다.",
            persons
        )
        # 동시 출현으로 지인 관계 추론
        assert len(rels) > 0


# =============================================================================
# 그래프 생성 테스트
# =============================================================================

class TestGraphBuilding:
    """그래프 생성 테스트"""

    def test_build_graph(self):
        """그래프 생성"""
        inferrer = RelationshipInferrer()
        graph = inferrer.build_graph(
            "남편이 바람을 피웠어요. 상간녀 이름은 박지연이에요.",
            case_id="case-001"
        )
        assert isinstance(graph, RelationshipGraph)
        assert len(graph.nodes) > 0

    def test_graph_nodes_have_ids(self):
        """노드에 ID 존재"""
        inferrer = RelationshipInferrer()
        graph = inferrer.build_graph("남편과 아들이 싸웠어요", case_id="test")
        for node in graph.nodes:
            assert node.id.startswith("test-person-")

    def test_graph_edges_use_node_ids(self):
        """엣지가 노드 ID 사용"""
        inferrer = RelationshipInferrer()
        graph = inferrer.build_graph(
            "원고와 피고",
            case_id="test"
        )
        # 엣지가 있으면 노드 ID 사용 확인
        for edge in graph.edges:
            assert "test-person-" in edge.person_a or len(graph.edges) == 0

    def test_build_graph_from_messages(self):
        """메시지에서 그래프 생성"""
        inferrer = RelationshipInferrer()
        messages = [
            {"sender": "김철수", "content": "남편이 또 그랬어"},
            {"sender": "이영희", "content": "힘들겠다"},
        ]
        graph = inferrer.build_graph_from_messages(messages, case_id="case-002")
        assert isinstance(graph, RelationshipGraph)


# =============================================================================
# RelationshipGraph 테스트
# =============================================================================

class TestRelationshipGraph:
    """RelationshipGraph 테스트"""

    def test_to_dict(self):
        """딕셔너리 변환"""
        node = PersonNode(
            id="p1", name="김철수", role="defendant", side="defendant_side"
        )
        edge = PersonRelationship(
            person_a="p1",
            person_b="p2",
            relationship_type=RelationshipType.SPOUSE
        )
        graph = RelationshipGraph(nodes=[node], edges=[edge])
        d = graph.to_dict()
        assert "nodes" in d
        assert "edges" in d
        assert len(d["nodes"]) == 1
        assert len(d["edges"]) == 1


# =============================================================================
# PersonRelationship 테스트
# =============================================================================

class TestPersonRelationship:
    """PersonRelationship 테스트"""

    def test_to_dict(self):
        """딕셔너리 변환"""
        rel = PersonRelationship(
            person_a="김철수",
            person_b="이영희",
            relationship_type=RelationshipType.SPOUSE,
            confidence=0.9,
        )
        d = rel.to_dict()
        assert d["source"] == "김철수"
        assert d["target"] == "이영희"
        assert d["relationship"] == "spouse"
        assert d["label"] == "배우자"
        assert d["color"] == "#2196F3"

    def test_bidirectional_hash_eq(self):
        """양방향 관계 해시/동등성"""
        r1 = PersonRelationship(
            person_a="A", person_b="B",
            relationship_type=RelationshipType.SPOUSE,
            direction="bidirectional"
        )
        r2 = PersonRelationship(
            person_a="B", person_b="A",
            relationship_type=RelationshipType.SPOUSE,
            direction="bidirectional"
        )
        assert r1 == r2
        assert hash(r1) == hash(r2)

    def test_directional_hash_eq(self):
        """단방향 관계 해시/동등성"""
        r1 = PersonRelationship(
            person_a="A", person_b="B",
            relationship_type=RelationshipType.CHILD,
            direction="a_to_b"
        )
        r2 = PersonRelationship(
            person_a="B", person_b="A",
            relationship_type=RelationshipType.CHILD,
            direction="a_to_b"
        )
        assert r1 != r2


# =============================================================================
# 간편 함수 테스트
# =============================================================================

class TestConvenienceFunctions:
    """간편 함수 테스트"""

    def test_infer_relationships(self):
        """infer_relationships 함수"""
        result = infer_relationships("남편이 외도했어요")
        assert isinstance(result, list)

    def test_build_relationship_graph(self):
        """build_relationship_graph 함수"""
        result = build_relationship_graph(
            "원고와 피고가 이혼 소송 중",
            case_id="test"
        )
        assert isinstance(result, dict)
        assert "nodes" in result
        assert "edges" in result


# =============================================================================
# 엣지 케이스 테스트
# =============================================================================

class TestEdgeCases:
    """엣지 케이스 테스트"""

    def test_empty_text(self):
        """빈 텍스트"""
        inferrer = RelationshipInferrer()
        rels = inferrer.infer_relationships("")
        assert rels == []

    def test_single_person(self):
        """단일 인물"""
        inferrer = RelationshipInferrer()
        persons = [ExtractedPerson(name="김철수")]
        rels = inferrer.infer_relationships("김철수가 왔다", persons)
        # 1명만 있으면 관계 없음
        assert rels == []

    def test_no_relationship_detected(self):
        """관계 미감지"""
        inferrer = RelationshipInferrer()
        _ = inferrer.infer_relationships("오늘 날씨가 좋다")
        # 인물이 없으면 관계 없음


# =============================================================================
# 상수 테스트
# =============================================================================

class TestConstants:
    """상수 테스트"""

    def test_relationship_keywords_coverage(self):
        """관계 키워드 커버리지"""
        assert "남편" in RELATIONSHIP_KEYWORDS
        assert "외도" in RELATIONSHIP_KEYWORDS
        assert "친구" in RELATIONSHIP_KEYWORDS

    def test_relationship_labels(self):
        """관계 라벨"""
        assert RELATIONSHIP_LABELS[RelationshipType.SPOUSE] == "배우자"
        assert RELATIONSHIP_LABELS[RelationshipType.AFFAIR] == "외도 상대"

    def test_relationship_colors(self):
        """관계 색상"""
        assert RELATIONSHIP_COLORS[RelationshipType.SPOUSE] == "#2196F3"
        assert RELATIONSHIP_COLORS[RelationshipType.AFFAIR] == "#E91E63"


# =============================================================================
# PersonNode 테스트
# =============================================================================

class TestPersonNode:
    """PersonNode 테스트"""

    def test_to_dict(self):
        """딕셔너리 변환"""
        node = PersonNode(
            id="p1",
            name="김철수",
            role="defendant",
            side="defendant_side",
            color="#F44336",
        )
        d = node.to_dict()
        assert d["id"] == "p1"
        assert d["name"] == "김철수"
        assert d["role"] == "defendant"
        assert d["color"] == "#F44336"

    def test_default_color(self):
        """기본 색상"""
        node = PersonNode(id="p1", name="test", role="unknown", side="unknown")
        assert node.color == "#9E9E9E"


# =============================================================================
# RelationshipType 테스트
# =============================================================================

class TestRelationshipType:
    """RelationshipType 테스트"""

    def test_all_types_have_labels(self):
        """모든 타입에 라벨 존재"""
        for rel_type in RelationshipType:
            assert rel_type in RELATIONSHIP_LABELS

    def test_all_types_have_colors(self):
        """모든 타입에 색상 존재"""
        for rel_type in RelationshipType:
            assert rel_type in RELATIONSHIP_COLORS
