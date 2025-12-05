'use client';

import { memo } from 'react';
import {
  EdgeProps,
  getBezierPath,
  EdgeLabelRenderer,
  BaseEdge,
} from 'reactflow';
import {
  RelationshipEdge as RelationshipEdgeType,
  RELATIONSHIP_LABELS,
  RelationshipType,
} from '@/types/relationship';

interface RelationshipEdgeData extends RelationshipEdgeType {
  color: string;
}

function RelationshipEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  selected,
}: EdgeProps<RelationshipEdgeData>) {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const relationshipLabel =
    data?.label ||
    RELATIONSHIP_LABELS[data?.relationship as RelationshipType] ||
    '관계';

  const strokeColor = data?.color || '#9E9E9E';

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        style={{
          stroke: strokeColor,
          strokeWidth: selected ? 3 : 2,
          opacity: selected ? 1 : 0.8,
        }}
      />
      <EdgeLabelRenderer>
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            pointerEvents: 'all',
          }}
          className={`
            px-2 py-1 rounded-md text-xs font-medium
            bg-white border shadow-sm cursor-pointer
            transition-all hover:shadow-md
            ${selected ? 'ring-2 ring-blue-500' : ''}
          `}
        >
          <span style={{ color: strokeColor }}>{relationshipLabel}</span>
          {data?.confidence && (
            <span className="ml-1 text-gray-400">
              ({Math.round(data.confidence * 100)}%)
            </span>
          )}
        </div>
      </EdgeLabelRenderer>
    </>
  );
}

export default memo(RelationshipEdge);
