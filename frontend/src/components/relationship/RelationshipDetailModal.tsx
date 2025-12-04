'use client';

/**
 * RelationshipDetailModal Component
 * Modal for displaying relationship details when clicking an edge
 */

import { X, Link2, FileText, Percent } from 'lucide-react';
import { Button } from '@/components/primitives';
import {
  RelationshipEdge,
  PersonNode,
  RELATIONSHIP_LABELS,
  ROLE_LABELS,
} from '@/types/relationship';

interface RelationshipDetailModalProps {
  relationship: RelationshipEdge;
  nodes: PersonNode[];
  isOpen: boolean;
  onClose: () => void;
}

export default function RelationshipDetailModal({
  relationship,
  nodes,
  isOpen,
  onClose,
}: RelationshipDetailModalProps) {
  if (!isOpen) return null;

  // Find source and target persons
  const sourcePerson = nodes.find((n) => n.id === relationship.source);
  const targetPerson = nodes.find((n) => n.id === relationship.target);

  const relationshipLabel = RELATIONSHIP_LABELS[relationship.relationship] || '관계';
  const confidencePercent = Math.round(relationship.confidence * 100);

  // Direction label
  const directionLabel =
    relationship.direction === 'bidirectional'
      ? '양방향'
      : relationship.direction === 'a_to_b'
      ? `${sourcePerson?.name || '?'} → ${targetPerson?.name || '?'}`
      : `${targetPerson?.name || '?'} → ${sourcePerson?.name || '?'}`;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-labelledby="relationship-modal-title"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal Content */}
      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
        {/* Header */}
        <div
          className="px-6 py-4 flex items-center justify-between"
          style={{ backgroundColor: relationship.color }}
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
              <Link2 className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2
                id="relationship-modal-title"
                className="text-lg font-bold text-white"
              >
                {relationshipLabel}
              </h2>
              <p className="text-sm text-white/80">관계 정보</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/20 rounded-full transition-colors"
            aria-label="닫기"
          >
            <X className="w-5 h-5 text-white" />
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-4 space-y-4">
          {/* Connected Persons */}
          <div>
            <p className="text-sm text-neutral-500 mb-2">연결된 인물</p>
            <div className="flex items-center gap-3">
              {/* Source Person */}
              <div
                className="flex-1 px-3 py-2 rounded-lg text-center text-white text-sm font-medium"
                style={{ backgroundColor: sourcePerson?.color || '#9E9E9E' }}
              >
                <p className="font-bold">{sourcePerson?.name || '?'}</p>
                <p className="text-xs opacity-80">
                  {ROLE_LABELS[sourcePerson?.role || 'unknown']}
                </p>
              </div>

              {/* Connection Arrow */}
              <div className="text-neutral-400">
                {relationship.direction === 'bidirectional' ? '⟷' : '→'}
              </div>

              {/* Target Person */}
              <div
                className="flex-1 px-3 py-2 rounded-lg text-center text-white text-sm font-medium"
                style={{ backgroundColor: targetPerson?.color || '#9E9E9E' }}
              >
                <p className="font-bold">{targetPerson?.name || '?'}</p>
                <p className="text-xs opacity-80">
                  {ROLE_LABELS[targetPerson?.role || 'unknown']}
                </p>
              </div>
            </div>
          </div>

          {/* Confidence Score */}
          <div className="flex items-center gap-3 p-3 bg-neutral-50 rounded-lg">
            <Percent className="w-5 h-5 text-neutral-500" />
            <div className="flex-1">
              <p className="text-sm text-neutral-500">신뢰도</p>
              <div className="flex items-center gap-2">
                <div className="flex-1 h-2 bg-neutral-200 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${confidencePercent}%`,
                      backgroundColor: relationship.color,
                    }}
                  />
                </div>
                <span className="font-medium text-neutral-900">
                  {confidencePercent}%
                </span>
              </div>
            </div>
          </div>

          {/* Direction */}
          <div className="flex items-center gap-3 p-3 bg-neutral-50 rounded-lg">
            <Link2 className="w-5 h-5 text-neutral-500" />
            <div>
              <p className="text-sm text-neutral-500">방향</p>
              <p className="font-medium text-neutral-900">{directionLabel}</p>
            </div>
          </div>

          {/* Evidence */}
          {relationship.evidence && (
            <div className="p-3 bg-neutral-50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <FileText className="w-4 h-4 text-neutral-500" />
                <p className="text-sm text-neutral-500">추론 근거</p>
              </div>
              <p className="text-sm text-neutral-700">{relationship.evidence}</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t bg-neutral-50 flex justify-end">
          <Button variant="outline" onClick={onClose}>
            닫기
          </Button>
        </div>
      </div>
    </div>
  );
}
