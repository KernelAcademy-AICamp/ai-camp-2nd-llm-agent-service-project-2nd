/**
 * PartyGraph - Main React Flow component for party relationship visualization
 * User Story 1: Party Relationship Graph
 */

'use client';

import { useCallback, useState, useMemo, useEffect } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  type Connection,
  type OnNodesChange,
  type OnEdgesChange,
  BackgroundVariant,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import toast from 'react-hot-toast';

import { usePartyGraph, type SaveStatus } from '@/hooks/usePartyGraph';
import { getEvidence, type Evidence } from '@/lib/api/evidence';
import { useTheme } from '@/contexts/ThemeContext';
import { useEvidenceLinks } from '@/hooks/useEvidenceLinks';
import type {
  PartyNode as PartyNodeData,
  PartyRelationship,
  PartyNodeCreate,
  PartyNodeUpdate,
  RelationshipCreate,
  RelationshipUpdate,
  EvidenceLinkCreate,
} from '@/types/party';
import { PartyNode, type PartyNodeType, type PartyNodeData as FlowNodeData } from './PartyNode';
import { PartyEdge, type PartyEdgeType, type PartyEdgeData } from './PartyEdge';
import { PartyModal } from './PartyModal';
import { RelationshipModal } from './RelationshipModal';
import { EvidenceLinkModal } from './EvidenceLinkModal';
import { EvidenceLinkPopover } from './EvidenceLinkPopover';

interface PartyGraphProps {
  caseId: string;
}

// Custom node types
const nodeTypes = {
  party: PartyNode,
};

// Custom edge types
const edgeTypes = {
  relationship: PartyEdge,
};

// Convert backend data to React Flow format
function toFlowNodes(parties: PartyNodeData[]): PartyNodeType[] {
  return parties.map((party) => ({
    id: party.id,
    type: 'party' as const,
    position: party.position || { x: 0, y: 0 },
    data: {
      id: party.id,
      name: party.name,
      type: party.type,
      alias: party.alias,
      occupation: party.occupation,
      birth_year: party.birth_year,
      // 012-precedent-integration: T048-T050 자동 추출 필드 전달
      is_auto_extracted: party.is_auto_extracted,
      extraction_confidence: party.extraction_confidence,
      source_evidence_id: party.source_evidence_id,
    },
  }));
}

function toFlowEdges(relationships: PartyRelationship[]): PartyEdgeType[] {
  return relationships.map((rel) => ({
    id: rel.id,
    source: rel.source_party_id,
    target: rel.target_party_id,
    type: 'relationship' as const,
    data: {
      type: rel.type,
      start_date: rel.start_date,
      end_date: rel.end_date,
      notes: rel.notes,
      // 012-precedent-integration: T048-T050 자동 추출 필드 전달
      is_auto_extracted: rel.is_auto_extracted,
      extraction_confidence: rel.extraction_confidence,
      evidence_text: rel.evidence_text,
    },
  }));
}

// Save status indicator component
function SaveStatusIndicator({ status }: { status: SaveStatus }) {
  const statusConfig = {
    idle: { text: '', className: '' },
    saving: { text: '저장 중...', className: 'text-gray-500 dark:text-gray-400' },
    saved: { text: '저장됨 ✓', className: 'text-green-600 dark:text-green-400' },
    error: { text: '저장 실패 ⚠️', className: 'text-red-600 dark:text-red-400' },
  };

  const config = statusConfig[status];
  if (!config.text) return null;

  return (
    <div className={`absolute top-4 right-4 px-3 py-1 bg-white dark:bg-neutral-800 rounded-full shadow dark:shadow-neutral-900/50 text-sm ${config.className}`}>
      {config.text}
    </div>
  );
}

// Empty state component
function EmptyState({ onAddParty }: { onAddParty: () => void }) {
  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-50 dark:bg-neutral-900">
      <div className="text-center">
        <div className="text-6xl mb-4">👥</div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
          당사자 관계도
        </h3>
        <p className="text-gray-500 dark:text-gray-400 mb-6 max-w-sm">
          당사자를 추가하여 관계도를 시작하세요.<br />
          원고, 피고, 제3자 등을 추가하고 관계를 연결할 수 있습니다.
        </p>
        <button
          onClick={onAddParty}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          원고/피고 추가하기
        </button>
      </div>
    </div>
  );
}

// Loading state component
function LoadingState() {
  return (
    <div className="absolute inset-0 flex items-center justify-center bg-gray-50 dark:bg-neutral-900">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
        <p className="text-gray-500 dark:text-gray-400">관계도를 불러오는 중...</p>
      </div>
    </div>
  );
}

// Error state component
function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="absolute inset-0 flex items-center justify-center bg-gray-50 dark:bg-neutral-900">
      <div className="text-center">
        <div className="text-6xl mb-4">⚠️</div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
          오류가 발생했습니다
        </h3>
        <p className="text-gray-500 dark:text-gray-400 mb-6">{message}</p>
        <button
          onClick={onRetry}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          다시 시도
        </button>
      </div>
    </div>
  );
}

// Evidence item interface for EvidenceLinkModal
interface EvidenceItem {
  id: string;
  summary?: string;
  filename?: string;
  type: string;
  timestamp: string;
  labels?: string[];
}

// Convert backend Evidence to modal EvidenceItem
function toEvidenceItem(evidence: Evidence): EvidenceItem {
  return {
    id: evidence.id,
    summary: evidence.ai_summary,
    filename: evidence.filename,
    type: evidence.type,
    timestamp: evidence.timestamp || evidence.created_at,
    labels: evidence.labels,
  };
}

export function PartyGraph({ caseId }: PartyGraphProps) {
  const { isDark } = useTheme();
  const {
    nodes: partyNodes,
    relationships,
    isLoading,
    error,
    saveStatus,
    addNode,
    updateNode,
    deleteNode,
    addRelationship,
    updateRelationshipData,
    deleteRelationshipById,
    updateNodePosition,
    refresh,
  } = usePartyGraph(caseId);

  // Evidence links hook
  const {
    links: evidenceLinks,
    isLoading: isLoadingLinks,
    addLink,
    removeLink,
  } = useEvidenceLinks({ caseId });

  // Helper to get links for a specific party
  const getLinksForParty = useCallback(
    (partyId: string) => evidenceLinks.filter((link) => link.party_id === partyId),
    [evidenceLinks]
  );

  // React Flow state
  const initialNodes = useMemo(() => toFlowNodes(partyNodes), [partyNodes]);
  const initialEdges = useMemo(() => toFlowEdges(relationships), [relationships]);

  const [nodes, setNodes, onNodesChange] = useNodesState<PartyNodeType>(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState<PartyEdgeType>(initialEdges);

  // Sync with backend data
  useMemo(() => {
    setNodes(toFlowNodes(partyNodes));
    setEdges(toFlowEdges(relationships));
  }, [partyNodes, relationships, setNodes, setEdges]);

  // Modal state
  const [partyModalOpen, setPartyModalOpen] = useState(false);
  const [relationshipModalOpen, setRelationshipModalOpen] = useState(false);
  const [evidenceLinkModalOpen, setEvidenceLinkModalOpen] = useState(false);
  const [selectedParty, setSelectedParty] = useState<PartyNodeData | null>(null);
  const [selectedRelationship, setSelectedRelationship] = useState<PartyRelationship | null>(null);
  const [pendingConnection, setPendingConnection] = useState<{
    source: string;
    target: string;
  } | null>(null);

  // Evidence popover state
  const [popoverParty, setPopoverParty] = useState<PartyNodeData | null>(null);
  const [popoverPosition, setPopoverPosition] = useState<{ x: number; y: number } | null>(null);

  // Evidence list state for EvidenceLinkModal
  const [evidenceList, setEvidenceList] = useState<EvidenceItem[]>([]);
  const [isLoadingEvidence, setIsLoadingEvidence] = useState(false);

  // Fetch evidence when modal opens
  useEffect(() => {
    if (evidenceLinkModalOpen && caseId) {
      setIsLoadingEvidence(true);
      getEvidence(caseId)
        .then((res) => {
          if (res.data?.evidence) {
            setEvidenceList(res.data.evidence.map(toEvidenceItem));
          }
        })
        .catch((err) => {
          console.error('Failed to fetch evidence:', err);
          toast.error('증거 목록을 불러오지 못했습니다.');
        })
        .finally(() => {
          setIsLoadingEvidence(false);
        });
    }
  }, [evidenceLinkModalOpen, caseId]);

  // Handle node position change (drag)
  const handleNodesChange: OnNodesChange<PartyNodeType> = useCallback(
    (changes) => {
      onNodesChange(changes);

      // Save position updates
      changes.forEach((change) => {
        if (change.type === 'position' && change.position && !change.dragging) {
          updateNodePosition(change.id, change.position);
        }
      });
    },
    [onNodesChange, updateNodePosition]
  );

  // Handle edge changes
  const handleEdgesChange: OnEdgesChange<PartyEdgeType> = useCallback(
    (changes) => {
      onEdgesChange(changes);
    },
    [onEdgesChange]
  );

  // Handle new connection (edge creation)
  const handleConnect = useCallback(
    (connection: Connection) => {
      if (connection.source && connection.target) {
        setPendingConnection({
          source: connection.source,
          target: connection.target,
        });
        setRelationshipModalOpen(true);
      }
    },
    []
  );

  // Handle node click (edit)
  const handleNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      const party = partyNodes.find((p) => p.id === node.id);
      if (party) {
        setSelectedParty(party);
        setPartyModalOpen(true);
      }
    },
    [partyNodes]
  );

  // Handle edge click (edit relationship)
  const handleEdgeClick = useCallback(
    (_: React.MouseEvent, edge: Edge) => {
      const rel = relationships.find((r) => r.id === edge.id);
      if (rel) {
        setSelectedRelationship(rel);
        setRelationshipModalOpen(true);
      }
    },
    [relationships]
  );

  // Add party button click
  const handleAddPartyClick = useCallback(() => {
    setSelectedParty(null);
    setPartyModalOpen(true);
  }, []);

  // Save party (create or update)
  const handleSaveParty = useCallback(
    async (data: PartyNodeCreate | PartyNodeUpdate) => {
      if (selectedParty) {
        await updateNode(selectedParty.id, data as PartyNodeUpdate);
      } else {
        await addNode(data as PartyNodeCreate);
      }
    },
    [selectedParty, addNode, updateNode]
  );

  // Delete party
  const handleDeleteParty = useCallback(async () => {
    if (selectedParty) {
      await deleteNode(selectedParty.id);
    }
  }, [selectedParty, deleteNode]);

  // Save relationship (create or update)
  const handleSaveRelationship = useCallback(
    async (data: RelationshipCreate | RelationshipUpdate) => {
      if (selectedRelationship) {
        await updateRelationshipData(selectedRelationship.id, data as RelationshipUpdate);
      } else if (pendingConnection) {
        await addRelationship({
          ...(data as RelationshipCreate),
          source_party_id: pendingConnection.source,
          target_party_id: pendingConnection.target,
        });
      } else {
        await addRelationship(data as RelationshipCreate);
      }
    },
    [selectedRelationship, pendingConnection, addRelationship, updateRelationshipData]
  );

  // Delete relationship
  const handleDeleteRelationship = useCallback(async () => {
    if (selectedRelationship) {
      await deleteRelationshipById(selectedRelationship.id);
    }
  }, [selectedRelationship, deleteRelationshipById]);

  // Close modals
  const handleClosePartyModal = useCallback(() => {
    setPartyModalOpen(false);
    setSelectedParty(null);
  }, []);

  const handleCloseRelationshipModal = useCallback(() => {
    setRelationshipModalOpen(false);
    setSelectedRelationship(null);
    setPendingConnection(null);
  }, []);

  // Evidence link handlers
  const handleOpenEvidenceLinkModal = useCallback(() => {
    setPopoverParty(null);
    setPopoverPosition(null);
    setEvidenceLinkModalOpen(true);
  }, []);

  const handleCloseEvidenceLinkModal = useCallback(() => {
    setEvidenceLinkModalOpen(false);
  }, []);

  const handleSaveEvidenceLink = useCallback(
    async (data: EvidenceLinkCreate) => {
      await addLink(data);
    },
    [addLink]
  );

  // Handle right-click on node for evidence popover
  const handleNodeContextMenu = useCallback(
    (event: React.MouseEvent, node: Node) => {
      event.preventDefault();
      const party = partyNodes.find((p) => p.id === node.id);
      if (party) {
        setPopoverParty(party);
        setPopoverPosition({ x: event.clientX, y: event.clientY });
      }
    },
    [partyNodes]
  );

  const handleClosePopover = useCallback(() => {
    setPopoverParty(null);
    setPopoverPosition(null);
  }, []);

  const handleViewEvidence = useCallback((_evidenceId: string) => {
    // TODO: Navigate to evidence detail or open a viewer
  }, []);

  // Render states
  if (isLoading) {
    return (
      <div className="relative w-full h-[600px] border border-gray-200 dark:border-neutral-700 rounded-lg overflow-hidden">
        <LoadingState />
      </div>
    );
  }

  if (error) {
    return (
      <div className="relative w-full h-[600px] border border-gray-200 dark:border-neutral-700 rounded-lg overflow-hidden">
        <ErrorState message={error} onRetry={refresh} />
      </div>
    );
  }

  if (partyNodes.length === 0) {
    return (
      <div className="relative w-full h-[600px] border border-gray-200 dark:border-neutral-700 rounded-lg overflow-hidden">
        <EmptyState onAddParty={handleAddPartyClick} />
        <PartyModal
          isOpen={partyModalOpen}
          onClose={handleClosePartyModal}
          onSave={handleSaveParty}
          party={null}
        />
      </div>
    );
  }

  return (
    <div className="relative w-full h-[600px] border border-gray-200 dark:border-neutral-700 rounded-lg overflow-hidden">
      {/* Toolbar */}
      <div className="absolute top-4 left-4 z-10 flex gap-2">
        <button
          onClick={handleAddPartyClick}
          className="px-4 py-2 bg-white dark:bg-neutral-800 text-gray-700 dark:text-gray-200 rounded-lg shadow dark:shadow-neutral-900/50 hover:bg-gray-50 dark:hover:bg-neutral-700 transition-colors text-sm font-medium"
        >
          + 당사자 추가
        </button>
        <button
          onClick={handleOpenEvidenceLinkModal}
          className="px-4 py-2 bg-white dark:bg-neutral-800 text-gray-700 dark:text-gray-200 rounded-lg shadow dark:shadow-neutral-900/50 hover:bg-gray-50 dark:hover:bg-neutral-700 transition-colors text-sm font-medium"
        >
          📎 증거 연결
        </button>
        {/* 017-party-graph-improvement: AI 자동 추출 상태 표시 */}
        {partyNodes.some(p => p.is_auto_extracted) && (
          <div className="px-3 py-2 bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-lg shadow dark:shadow-neutral-900/50 text-sm font-medium flex items-center gap-1.5">
            <span>🤖</span>
            <span>AI 추출 {partyNodes.filter(p => p.is_auto_extracted).length}명</span>
          </div>
        )}
      </div>

      {/* Save status */}
      <SaveStatusIndicator status={saveStatus} />

      {/* React Flow */}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={handleNodesChange}
        onEdgesChange={handleEdgesChange}
        onConnect={handleConnect}
        onNodeClick={handleNodeClick}
        onEdgeClick={handleEdgeClick}
        onNodeContextMenu={handleNodeContextMenu}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        defaultEdgeOptions={{
          type: 'relationship',
        }}
        className={isDark ? 'dark-flow' : ''}
      >
        <Controls className={isDark ? 'dark-controls' : ''} />
        <Background
          variant={BackgroundVariant.Dots}
          gap={16}
          size={1}
          color={isDark ? '#404040' : '#e5e5e5'}
        />
        <MiniMap
          nodeColor={(node) => {
            const data = node.data as FlowNodeData;
            switch (data.type) {
              case 'plaintiff':
                return '#10B981'; // emerald-500
              case 'defendant':
                return '#EC4899'; // pink-500
              case 'third_party':
                return '#10B981'; // emerald-500
              case 'child':
                return '#0EA5E9'; // sky-500
              case 'family':
                return '#9CA3AF'; // gray-400
              default:
                return '#6B7280';
            }
          }}
          maskColor={isDark ? 'rgba(38, 38, 38, 0.8)' : 'rgba(255, 255, 255, 0.8)'}
          style={{
            backgroundColor: isDark ? '#262626' : '#ffffff',
          }}
        />
      </ReactFlow>

      {/* Party Modal */}
      <PartyModal
        isOpen={partyModalOpen}
        onClose={handleClosePartyModal}
        onSave={handleSaveParty}
        party={selectedParty}
      />

      {/* Relationship Modal */}
      <RelationshipModal
        isOpen={relationshipModalOpen}
        onClose={handleCloseRelationshipModal}
        onSave={handleSaveRelationship}
        onDelete={selectedRelationship ? handleDeleteRelationship : undefined}
        relationship={selectedRelationship}
        parties={partyNodes}
        sourcePartyId={pendingConnection?.source}
        targetPartyId={pendingConnection?.target}
      />

      {/* Evidence Link Modal */}
      <EvidenceLinkModal
        isOpen={evidenceLinkModalOpen}
        onClose={handleCloseEvidenceLinkModal}
        onSave={handleSaveEvidenceLink}
        parties={partyNodes}
        relationships={relationships}
        evidenceList={evidenceList}
        isLoadingEvidence={isLoadingEvidence}
        preSelectedPartyId={popoverParty?.id}
      />

      {/* Evidence Link Popover */}
      {popoverParty && popoverPosition && (
        <div
          style={{
            position: 'fixed',
            left: popoverPosition.x,
            top: popoverPosition.y,
            zIndex: 100,
          }}
        >
          <EvidenceLinkPopover
            party={popoverParty}
            links={getLinksForParty(popoverParty.id)}
            isLoading={isLoadingLinks}
            onClose={handleClosePopover}
            onLinkEvidence={handleOpenEvidenceLinkModal}
            onRemoveLink={async (linkId) => { await removeLink(linkId); }}
            onViewEvidence={handleViewEvidence}
          />
        </div>
      )}
    </div>
  );
}
