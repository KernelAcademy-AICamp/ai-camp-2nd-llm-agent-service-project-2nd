'use client';

import { useState } from 'react';
import { Info } from 'lucide-react';
import {
  ROLE_COLORS,
  ROLE_LABELS,
  RELATIONSHIP_COLORS,
  RELATIONSHIP_LABELS,
  PersonRole,
  RelationshipType,
} from '@/types/relationship';

export default function RelationshipLegend() {
  const [isOpen, setIsOpen] = useState(false);

  const roleEntries = Object.entries(ROLE_LABELS) as [PersonRole, string][];
  const relationshipEntries = Object.entries(RELATIONSHIP_LABELS) as [
    RelationshipType,
    string
  ][];

  return (
    <div className="relative">
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center text-sm text-gray-500 hover:text-gray-700 transition-colors"
      >
        <Info className="w-4 h-4 mr-1" />
        범례
      </button>

      {/* Legend Panel */}
      {isOpen && (
        <div className="absolute right-0 top-8 z-50 bg-white rounded-lg shadow-lg border border-gray-200 p-4 min-w-[200px]">
          {/* 역할별 색상 */}
          <div className="mb-4">
            <h4 className="text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wider">
              인물 역할
            </h4>
            <div className="space-y-1">
              {roleEntries.map(([role, label]) => (
                <div key={role} className="flex items-center space-x-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: ROLE_COLORS[role] }}
                  />
                  <span className="text-xs text-gray-600">{label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* 관계별 색상 */}
          <div>
            <h4 className="text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wider">
              관계 유형
            </h4>
            <div className="space-y-1">
              {relationshipEntries.map(([type, label]) => (
                <div key={type} className="flex items-center space-x-2">
                  <div
                    className="w-6 h-0.5"
                    style={{ backgroundColor: RELATIONSHIP_COLORS[type] }}
                  />
                  <span className="text-xs text-gray-600">{label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Close on outside click */}
          <button
            onClick={() => setIsOpen(false)}
            className="mt-3 w-full text-xs text-gray-400 hover:text-gray-600 text-center"
          >
            닫기
          </button>
        </div>
      )}
    </div>
  );
}
