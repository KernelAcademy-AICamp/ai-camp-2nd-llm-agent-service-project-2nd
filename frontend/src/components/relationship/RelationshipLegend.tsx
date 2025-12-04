'use client';

/**
 * RelationshipLegend Component
 * Displays legend for node colors and edge types
 */

import { useMemo } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import {
  RelationshipGraph,
  PersonRole,
  RelationshipType,
  ROLE_LABELS,
  RELATIONSHIP_LABELS,
  ROLE_COLORS,
  RELATIONSHIP_COLORS,
} from '@/types/relationship';

interface RelationshipLegendProps {
  graph: RelationshipGraph;
}

export default function RelationshipLegend({ graph }: RelationshipLegendProps) {
  const [showNodes, setShowNodes] = useState(true);
  const [showEdges, setShowEdges] = useState(true);

  // Extract unique roles from nodes
  const uniqueRoles = useMemo(() => {
    const roles = new Set<PersonRole>();
    graph.nodes.forEach((node) => roles.add(node.role));
    return Array.from(roles);
  }, [graph.nodes]);

  // Extract unique relationship types from edges
  const uniqueRelationships = useMemo(() => {
    const types = new Set<RelationshipType>();
    graph.edges.forEach((edge) => types.add(edge.relationship));
    return Array.from(types);
  }, [graph.edges]);

  return (
    <div className="p-4 space-y-4">
      <h2 className="font-bold text-neutral-900">범례</h2>

      {/* Node Legend */}
      <div>
        <button
          onClick={() => setShowNodes(!showNodes)}
          className="flex items-center justify-between w-full text-sm font-medium text-neutral-700 hover:text-neutral-900"
        >
          <span>인물 ({graph.nodes.length}명)</span>
          {showNodes ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </button>

        {showNodes && (
          <div className="mt-2 space-y-2">
            {uniqueRoles.map((role) => (
              <div key={role} className="flex items-center gap-2">
                <div
                  className="w-4 h-4 rounded-full"
                  style={{ backgroundColor: ROLE_COLORS[role] }}
                />
                <span className="text-sm text-neutral-600">
                  {ROLE_LABELS[role]}
                </span>
                <span className="text-xs text-neutral-400">
                  ({graph.nodes.filter((n) => n.role === role).length})
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Edge Legend */}
      <div>
        <button
          onClick={() => setShowEdges(!showEdges)}
          className="flex items-center justify-between w-full text-sm font-medium text-neutral-700 hover:text-neutral-900"
        >
          <span>관계 ({graph.edges.length}개)</span>
          {showEdges ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </button>

        {showEdges && (
          <div className="mt-2 space-y-2">
            {uniqueRelationships.map((type) => (
              <div key={type} className="flex items-center gap-2">
                <div
                  className="w-8 h-0.5"
                  style={{ backgroundColor: RELATIONSHIP_COLORS[type] }}
                />
                <span className="text-sm text-neutral-600">
                  {RELATIONSHIP_LABELS[type]}
                </span>
                <span className="text-xs text-neutral-400">
                  ({graph.edges.filter((e) => e.relationship === type).length})
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Stats Summary */}
      <div className="pt-4 border-t">
        <h3 className="text-sm font-medium text-neutral-700 mb-2">요약</h3>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="bg-neutral-50 rounded p-2 text-center">
            <p className="text-2xl font-bold text-neutral-900">
              {graph.nodes.length}
            </p>
            <p className="text-xs text-neutral-500">인물</p>
          </div>
          <div className="bg-neutral-50 rounded p-2 text-center">
            <p className="text-2xl font-bold text-neutral-900">
              {graph.edges.length}
            </p>
            <p className="text-xs text-neutral-500">관계</p>
          </div>
        </div>
      </div>

      {/* Instructions */}
      <div className="text-xs text-neutral-500 bg-neutral-50 rounded-lg p-3">
        <p className="font-medium mb-1">사용법</p>
        <ul className="space-y-1">
          <li>• 노드를 드래그하여 위치 이동</li>
          <li>• 마우스 휠로 확대/축소</li>
          <li>• 노드/엣지 클릭 시 상세 정보</li>
        </ul>
      </div>
    </div>
  );
}
