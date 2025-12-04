'use client';

/**
 * RelationshipEdge Component
 * Custom React Flow edge for displaying relationships
 */

import { memo } from 'react';
import { EdgeProps, getBezierPath, EdgeLabelRenderer } from 'reactflow';
import { RelationshipEdgeData } from '@/types/relationship';

function RelationshipEdgeComponent({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  style,
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

  // Show confidence percentage if less than 100%
  const confidenceText = data && data.confidence < 1
    ? ` (${Math.round(data.confidence * 100)}%)`
    : '';

  return (
    <>
      {/* Main edge path */}
      <path
        id={id}
        className={`react-flow__edge-path transition-all duration-200 ${
          selected ? 'stroke-[3px]' : ''
        }`}
        d={edgePath}
        style={{
          ...style,
          strokeWidth: selected ? 3 : 2,
        }}
        fill="none"
      />

      {/* Invisible wider path for easier selection */}
      <path
        d={edgePath}
        fill="none"
        strokeWidth={20}
        stroke="transparent"
        className="cursor-pointer"
      />

      {/* Edge Label */}
      <EdgeLabelRenderer>
        <div
          className={`
            absolute px-2 py-1 rounded shadow-sm text-xs font-medium
            pointer-events-auto cursor-pointer select-none
            transition-all duration-200
            ${selected
              ? 'bg-white border-2 scale-110 z-10'
              : 'bg-white/90 border hover:bg-white hover:scale-105'
            }
          `}
          style={{
            transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
            borderColor: data?.color || '#9E9E9E',
            color: data?.color || '#666',
          }}
        >
          {data?.label || '관계'}
          <span className="text-neutral-400 ml-0.5">
            {confidenceText}
          </span>
        </div>
      </EdgeLabelRenderer>
    </>
  );
}

export default memo(RelationshipEdgeComponent);
