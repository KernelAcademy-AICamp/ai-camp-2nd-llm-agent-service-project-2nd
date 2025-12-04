'use client';

/**
 * RelationshipFlow Component
 * Main React Flow container for relationship visualization
 */

import { useCallback, useMemo, useState } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
  NodeMouseHandler,
  EdgeMouseHandler,
  BackgroundVariant,
} from 'reactflow';
import 'reactflow/dist/style.css';

import PersonNode from './PersonNode';
import RelationshipEdge from './RelationshipEdge';
import PersonDetailModal from './PersonDetailModal';
import RelationshipDetailModal from './RelationshipDetailModal';
import {
  RelationshipGraph,
  PersonNode as PersonNodeType,
  RelationshipEdge as RelationshipEdgeType,
  PersonNodeData,
  RelationshipEdgeData,
} from '@/types/relationship';

interface RelationshipFlowProps {
  graph: RelationshipGraph;
}

// Custom node types
const nodeTypes = {
  person: PersonNode,
};

// Custom edge types
const edgeTypes = {
  relationship: RelationshipEdge,
};

// Calculate circular layout positions
function calculateCircularLayout(
  nodes: PersonNodeType[],
  centerX: number = 400,
  centerY: number = 300,
  radius: number = 200
): { x: number; y: number }[] {
  return nodes.map((_, index) => {
    const angle = (2 * Math.PI * index) / nodes.length - Math.PI / 2;
    return {
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
    };
  });
}

// Transform API data to React Flow nodes
function transformToNodes(persons: PersonNodeType[]): Node<PersonNodeData>[] {
  const positions = calculateCircularLayout(persons);

  return persons.map((person, index) => ({
    id: person.id,
    type: 'person',
    position: positions[index],
    data: {
      label: person.name,
      role: person.role,
      side: person.side,
      color: person.color,
      originalNode: person,
    },
  }));
}

// Transform API data to React Flow edges
function transformToEdges(edges: RelationshipEdgeType[]): Edge<RelationshipEdgeData>[] {
  return edges.map((edge, index) => ({
    id: `edge-${index}`,
    source: edge.source,
    target: edge.target,
    type: 'relationship',
    animated: edge.relationship === 'affair',
    markerEnd: edge.direction !== 'bidirectional' ? {
      type: MarkerType.ArrowClosed,
      color: edge.color,
    } : undefined,
    style: {
      stroke: edge.color,
      strokeWidth: 2,
    },
    data: {
      label: edge.label,
      relationship: edge.relationship,
      direction: edge.direction,
      confidence: edge.confidence,
      color: edge.color,
      evidence: edge.evidence,
      originalEdge: edge,
    },
  }));
}

export default function RelationshipFlow({ graph }: RelationshipFlowProps) {
  // Transform graph data to React Flow format
  const initialNodes = useMemo(() => transformToNodes(graph.nodes), [graph.nodes]);
  const initialEdges = useMemo(() => transformToEdges(graph.edges), [graph.edges]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Modal states
  const [selectedPerson, setSelectedPerson] = useState<PersonNodeType | null>(null);
  const [selectedRelationship, setSelectedRelationship] = useState<RelationshipEdgeType | null>(null);

  // Node click handler
  const onNodeClick: NodeMouseHandler = useCallback((_, node) => {
    const personData = node.data as PersonNodeData;
    setSelectedPerson(personData.originalNode);
  }, []);

  // Edge click handler
  const onEdgeClick: EdgeMouseHandler = useCallback((_, edge) => {
    const edgeData = edge.data as RelationshipEdgeData;
    if (edgeData?.originalEdge) {
      setSelectedRelationship(edgeData.originalEdge);
    }
  }, []);

  // Close modals
  const handleClosePersonModal = useCallback(() => {
    setSelectedPerson(null);
  }, []);

  const handleCloseRelationshipModal = useCallback(() => {
    setSelectedRelationship(null);
  }, []);

  return (
    <div className="w-full h-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        onEdgeClick={onEdgeClick}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.1}
        maxZoom={2}
        defaultEdgeOptions={{
          type: 'relationship',
        }}
        proOptions={{ hideAttribution: true }}
      >
        <Background variant={BackgroundVariant.Dots} gap={16} size={1} />
        <Controls position="bottom-left" />
        <MiniMap
          position="bottom-right"
          nodeColor={(node) => {
            const data = node.data as PersonNodeData;
            return data.color || '#9E9E9E';
          }}
          maskColor="rgba(255, 255, 255, 0.8)"
        />
      </ReactFlow>

      {/* Person Detail Modal */}
      {selectedPerson && (
        <PersonDetailModal
          person={selectedPerson}
          isOpen={!!selectedPerson}
          onClose={handleClosePersonModal}
        />
      )}

      {/* Relationship Detail Modal */}
      {selectedRelationship && (
        <RelationshipDetailModal
          relationship={selectedRelationship}
          nodes={graph.nodes}
          isOpen={!!selectedRelationship}
          onClose={handleCloseRelationshipModal}
        />
      )}
    </div>
  );
}
