'use client';

/**
 * PersonNode Component
 * Custom React Flow node for displaying a person
 */

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { PersonNodeData, ROLE_LABELS } from '@/types/relationship';

function PersonNodeComponent({ data, selected }: NodeProps<PersonNodeData>) {
  const roleLabel = ROLE_LABELS[data.role] || '미상';

  // Determine text color based on background brightness
  const getTextColor = (bgColor: string): string => {
    // Simple brightness check - colors starting with darker hex values get white text
    const darkColors = ['#F44336', '#E91E63', '#9C27B0', '#673AB7', '#3F51B5', '#4CAF50'];
    return darkColors.some(c => bgColor.toUpperCase().includes(c.substring(1))) ? 'white' : 'white';
  };

  return (
    <div
      className={`
        relative px-4 py-3 rounded-xl border-2 shadow-lg cursor-pointer
        transition-all duration-200 min-w-[100px] text-center
        hover:shadow-xl hover:scale-105
        ${selected ? 'ring-2 ring-offset-2 ring-blue-500 scale-105' : ''}
      `}
      style={{
        backgroundColor: data.color,
        borderColor: data.color,
      }}
    >
      {/* Top Handle */}
      <Handle
        type="target"
        position={Position.Top}
        className="!w-3 !h-3 !bg-white !border-2 !border-neutral-400"
      />

      {/* Content */}
      <div className="flex flex-col items-center gap-1">
        <p
          className="font-bold text-sm leading-tight"
          style={{ color: getTextColor(data.color) }}
        >
          {data.label}
        </p>
        <span
          className="text-xs px-2 py-0.5 rounded-full bg-black/20"
          style={{ color: getTextColor(data.color) }}
        >
          {roleLabel}
        </span>
      </div>

      {/* Bottom Handle */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-3 !h-3 !bg-white !border-2 !border-neutral-400"
      />

      {/* Left Handle for horizontal connections */}
      <Handle
        type="target"
        position={Position.Left}
        id="left"
        className="!w-3 !h-3 !bg-white !border-2 !border-neutral-400"
      />

      {/* Right Handle for horizontal connections */}
      <Handle
        type="source"
        position={Position.Right}
        id="right"
        className="!w-3 !h-3 !bg-white !border-2 !border-neutral-400"
      />
    </div>
  );
}

export default memo(PersonNodeComponent);
