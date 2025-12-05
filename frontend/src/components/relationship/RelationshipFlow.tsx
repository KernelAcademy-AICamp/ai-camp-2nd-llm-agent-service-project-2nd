'use client';

import { useCallback, useMemo } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  useNodesState,
  useEdgesState,
  MarkerType,
  ConnectionMode,
} from 'reactflow';
import 'reactflow/dist/style.css';

import {
  RelationshipGraph,
  PersonNode as PersonNodeType,
  RelationshipEdge as RelationshipEdgeType,
  ROLE_COLORS,
  RELATIONSHIP_COLORS,
  PersonRole,
  RelationshipType,
} from '@/types/relationship';
import PersonNode from './PersonNode';
import RelationshipEdge from './RelationshipEdge';

// 커스텀 노드/엣지 타입 등록
const nodeTypes = {
  person: PersonNode,
};

const edgeTypes = {
  relationship: RelationshipEdge,
};

interface RelationshipFlowProps {
  graph: RelationshipGraph;
  onNodeClick?: (node: PersonNodeType) => void;
  onEdgeClick?: (edge: RelationshipEdgeType) => void;
}

/**
 * 원형 레이아웃으로 노드 배치
 */
function calculateCircularLayout(
  nodes: PersonNodeType[],
  centerX: number,
  centerY: number,
  radius: number
): Node[] {
  const angleStep = (2 * Math.PI) / nodes.length;

  return nodes.map((node, index) => {
    const angle = index * angleStep - Math.PI / 2; // 12시 방향부터 시작
    const x = centerX + radius * Math.cos(angle);
    const y = centerY + radius * Math.sin(angle);

    return {
      id: node.id,
      type: 'person',
      position: { x, y },
      data: {
        ...node,
        color: node.color || ROLE_COLORS[node.role as PersonRole] || ROLE_COLORS[PersonRole.UNKNOWN],
      },
    };
  });
}

/**
 * 엣지 데이터를 React Flow 형식으로 변환
 */
function convertEdges(edges: RelationshipEdgeType[]): Edge[] {
  return edges.map((edge, index) => ({
    id: `edge-${index}`,
    source: edge.source,
    target: edge.target,
    type: 'relationship',
    label: edge.label,
    data: {
      ...edge,
      color:
        RELATIONSHIP_COLORS[edge.relationship as RelationshipType] ||
        '#9E9E9E',
    },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      width: 15,
      height: 15,
      color:
        RELATIONSHIP_COLORS[edge.relationship as RelationshipType] ||
        '#9E9E9E',
    },
    style: {
      stroke:
        RELATIONSHIP_COLORS[edge.relationship as RelationshipType] ||
        '#9E9E9E',
      strokeWidth: 2,
    },
    labelStyle: {
      fontSize: 12,
      fontWeight: 500,
    },
    labelBgStyle: {
      fill: 'white',
      fillOpacity: 0.9,
    },
  }));
}

export default function RelationshipFlow({
  graph,
  onNodeClick,
  onEdgeClick,
}: RelationshipFlowProps) {
  // 노드/엣지 계산 (메모이제이션)
  const initialNodes = useMemo(
    () => calculateCircularLayout(graph.nodes, 300, 250, 200),
    [graph.nodes]
  );

  const initialEdges = useMemo(() => convertEdges(graph.edges), [graph.edges]);

  // React Flow 상태
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // 노드 클릭 핸들러
  const handleNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      if (onNodeClick) {
        const personNode = graph.nodes.find((n) => n.id === node.id);
        if (personNode) {
          onNodeClick(personNode);
        }
      }
    },
    [graph.nodes, onNodeClick]
  );

  // 엣지 클릭 핸들러
  const handleEdgeClick = useCallback(
    (_: React.MouseEvent, edge: Edge) => {
      if (onEdgeClick) {
        const relationshipEdge = graph.edges.find(
          (e) => e.source === edge.source && e.target === edge.target
        );
        if (relationshipEdge) {
          onEdgeClick(relationshipEdge);
        }
      }
    },
    [graph.edges, onEdgeClick]
  );

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onNodeClick={handleNodeClick}
      onEdgeClick={handleEdgeClick}
      nodeTypes={nodeTypes}
      edgeTypes={edgeTypes}
      connectionMode={ConnectionMode.Loose}
      fitView
      fitViewOptions={{
        padding: 0.2,
        minZoom: 0.5,
        maxZoom: 2,
      }}
      minZoom={0.3}
      maxZoom={3}
      defaultViewport={{ x: 0, y: 0, zoom: 1 }}
    >
      <Background color="#f0f0f0" gap={16} />
      <Controls showInteractive={false} />
      <MiniMap
        nodeColor={(node) => node.data?.color || '#9E9E9E'}
        maskColor="rgba(0, 0, 0, 0.1)"
        style={{
          backgroundColor: 'white',
          border: '1px solid #e0e0e0',
          borderRadius: '8px',
        }}
      />
    </ReactFlow>
  );
}
