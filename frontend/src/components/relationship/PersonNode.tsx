'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { User } from 'lucide-react';
import { PersonNode as PersonNodeType, ROLE_LABELS, PersonRole } from '@/types/relationship';

interface PersonNodeData extends PersonNodeType {
  color: string;
}

function PersonNode({ data, selected }: NodeProps<PersonNodeData>) {
  const roleLabel = ROLE_LABELS[data.role as PersonRole] || '미상';

  return (
    <div
      className={`
        relative px-4 py-3 rounded-xl shadow-md border-2 transition-all cursor-pointer
        ${selected ? 'ring-2 ring-offset-2 ring-blue-500' : ''}
      `}
      style={{
        backgroundColor: 'white',
        borderColor: data.color,
        minWidth: '120px',
      }}
    >
      {/* 연결 핸들 (상하좌우) */}
      <Handle
        type="target"
        position={Position.Top}
        className="!w-2 !h-2 !bg-gray-400"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-2 !h-2 !bg-gray-400"
      />
      <Handle
        type="target"
        position={Position.Left}
        className="!w-2 !h-2 !bg-gray-400"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="!w-2 !h-2 !bg-gray-400"
      />

      {/* 노드 내용 */}
      <div className="flex items-center space-x-2">
        <div
          className="w-8 h-8 rounded-full flex items-center justify-center"
          style={{ backgroundColor: data.color }}
        >
          <User className="w-4 h-4 text-white" />
        </div>
        <div className="flex flex-col">
          <span className="text-sm font-semibold text-gray-900 whitespace-nowrap">
            {data.name}
          </span>
          <span
            className="text-xs px-1.5 py-0.5 rounded-full text-white font-medium"
            style={{ backgroundColor: data.color }}
          >
            {roleLabel}
          </span>
        </div>
      </div>

      {/* 별칭 (있는 경우) */}
      {data.aliases && data.aliases.length > 0 && (
        <div className="mt-1 text-xs text-gray-500">
          별칭: {data.aliases.join(', ')}
        </div>
      )}
    </div>
  );
}

export default memo(PersonNode);
