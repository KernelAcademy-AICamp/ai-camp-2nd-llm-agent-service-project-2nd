/**
 * Relationship Types Tests
 * TDD: Red phase - 테스트 먼저 작성
 */

import {
  PersonRole,
  RelationshipType,
  type PersonNode,
  type RelationshipEdge,
  type RelationshipGraph,
} from '../relationship';

describe('Relationship Types', () => {
  describe('PersonRole enum', () => {
    it('should have PLAINTIFF value', () => {
      expect(PersonRole.PLAINTIFF).toBe('plaintiff');
    });

    it('should have DEFENDANT value', () => {
      expect(PersonRole.DEFENDANT).toBe('defendant');
    });

    it('should have CHILD value', () => {
      expect(PersonRole.CHILD).toBe('child');
    });

    it('should have THIRD_PARTY value', () => {
      expect(PersonRole.THIRD_PARTY).toBe('third_party');
    });

    it('should have UNKNOWN value', () => {
      expect(PersonRole.UNKNOWN).toBe('unknown');
    });
  });

  describe('RelationshipType enum', () => {
    it('should have SPOUSE value', () => {
      expect(RelationshipType.SPOUSE).toBe('spouse');
    });

    it('should have AFFAIR value', () => {
      expect(RelationshipType.AFFAIR).toBe('affair');
    });

    it('should have PARENT value', () => {
      expect(RelationshipType.PARENT).toBe('parent');
    });

    it('should have CHILD value', () => {
      expect(RelationshipType.CHILD).toBe('child');
    });

    it('should have SIBLING value', () => {
      expect(RelationshipType.SIBLING).toBe('sibling');
    });
  });

  describe('PersonNode interface', () => {
    it('should create valid PersonNode object', () => {
      const node: PersonNode = {
        id: 'person-0',
        name: '김철수',
        role: PersonRole.PLAINTIFF,
        side: 'plaintiff',
        color: '#4CAF50',
      };

      expect(node.id).toBe('person-0');
      expect(node.name).toBe('김철수');
      expect(node.role).toBe(PersonRole.PLAINTIFF);
      expect(node.side).toBe('plaintiff');
      expect(node.color).toBe('#4CAF50');
    });

    it('should allow optional aliases field', () => {
      const node: PersonNode = {
        id: 'person-1',
        name: '이영희',
        role: PersonRole.DEFENDANT,
        side: 'defendant',
        color: '#F44336',
        aliases: ['영희', '처'],
      };

      expect(node.aliases).toEqual(['영희', '처']);
    });
  });

  describe('RelationshipEdge interface', () => {
    it('should create valid RelationshipEdge object', () => {
      const edge: RelationshipEdge = {
        source: 'person-0',
        target: 'person-1',
        relationship: RelationshipType.SPOUSE,
        label: '배우자',
        confidence: 0.95,
      };

      expect(edge.source).toBe('person-0');
      expect(edge.target).toBe('person-1');
      expect(edge.relationship).toBe(RelationshipType.SPOUSE);
      expect(edge.label).toBe('배우자');
      expect(edge.confidence).toBe(0.95);
    });

    it('should allow optional evidence field', () => {
      const edge: RelationshipEdge = {
        source: 'person-0',
        target: 'person-2',
        relationship: RelationshipType.AFFAIR,
        label: '외도 상대',
        confidence: 0.8,
        evidence: '카카오톡 대화 내역',
      };

      expect(edge.evidence).toBe('카카오톡 대화 내역');
    });
  });

  describe('RelationshipGraph interface', () => {
    it('should create valid RelationshipGraph with nodes and edges', () => {
      const graph: RelationshipGraph = {
        nodes: [
          {
            id: 'person-0',
            name: '김철수',
            role: PersonRole.PLAINTIFF,
            side: 'plaintiff',
            color: '#4CAF50',
          },
          {
            id: 'person-1',
            name: '이영희',
            role: PersonRole.DEFENDANT,
            side: 'defendant',
            color: '#F44336',
          },
        ],
        edges: [
          {
            source: 'person-0',
            target: 'person-1',
            relationship: RelationshipType.SPOUSE,
            label: '배우자',
            confidence: 0.95,
          },
        ],
      };

      expect(graph.nodes).toHaveLength(2);
      expect(graph.edges).toHaveLength(1);
    });

    it('should allow empty nodes and edges', () => {
      const emptyGraph: RelationshipGraph = {
        nodes: [],
        edges: [],
      };

      expect(emptyGraph.nodes).toHaveLength(0);
      expect(emptyGraph.edges).toHaveLength(0);
    });
  });
});
