'use client';

/**
 * Relationship Visualization Client Component
 * Main container for the relationship graph visualization
 */

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Loader2, AlertCircle, RefreshCw, Users } from 'lucide-react';
import { Button } from '@/components/primitives';
import RelationshipFlow from '@/components/relationship/RelationshipFlow';
import RelationshipLegend from '@/components/relationship/RelationshipLegend';
import { getCaseRelationships, getMockRelationshipGraph } from '@/lib/api/relationship';
import { RelationshipGraph } from '@/types/relationship';

interface RelationshipClientProps {
  caseId: string;
}

export default function RelationshipClient({ caseId }: RelationshipClientProps) {
  const router = useRouter();
  const [graph, setGraph] = useState<RelationshipGraph | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [useMockData, setUseMockData] = useState(false);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await getCaseRelationships(caseId);

      if (response.error) {
        // If backend API not available, use mock data for demo
        console.warn('Backend API not available, using mock data:', response.error);
        setGraph(getMockRelationshipGraph());
        setUseMockData(true);
      } else if (response.data) {
        setGraph(response.data);
        setUseMockData(false);
      }
    } catch (err) {
      console.error('Failed to load relationships:', err);
      // Fallback to mock data
      setGraph(getMockRelationshipGraph());
      setUseMockData(true);
    } finally {
      setIsLoading(false);
    }
  }, [caseId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleBack = () => {
    router.push(`/lawyer/cases/${caseId}`);
  };

  const handleRefresh = () => {
    loadData();
  };

  return (
    <div className="h-screen flex flex-col bg-neutral-50">
      {/* Header */}
      <header className="bg-white border-b px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            onClick={handleBack}
            className="p-2"
            aria-label="사건 상세로 돌아가기"
          >
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div className="flex items-center gap-2">
            <Users className="w-5 h-5 text-deep-trust-blue" />
            <h1 className="text-xl font-bold text-neutral-900">인물 관계도</h1>
          </div>
          {useMockData && (
            <span className="px-2 py-1 text-xs bg-yellow-100 text-yellow-700 rounded">
              데모 데이터
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={isLoading}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            새로고침
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex overflow-hidden">
        {/* Graph Area */}
        <div className="flex-1 relative">
          {isLoading ? (
            <div className="absolute inset-0 flex items-center justify-center bg-white">
              <div className="text-center">
                <Loader2 className="w-8 h-8 animate-spin text-deep-trust-blue mx-auto mb-2" />
                <p className="text-neutral-600">관계도를 불러오는 중...</p>
              </div>
            </div>
          ) : error ? (
            <div className="absolute inset-0 flex items-center justify-center bg-white">
              <div className="text-center max-w-md p-6">
                <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
                <h2 className="text-lg font-semibold text-neutral-900 mb-2">
                  관계도를 불러올 수 없습니다
                </h2>
                <p className="text-neutral-600 mb-4">{error}</p>
                <Button variant="primary" onClick={handleRefresh}>
                  다시 시도
                </Button>
              </div>
            </div>
          ) : graph && graph.nodes.length > 0 ? (
            <RelationshipFlow graph={graph} />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center bg-white">
              <div className="text-center max-w-md p-6">
                <Users className="w-12 h-12 text-neutral-400 mx-auto mb-4" />
                <h2 className="text-lg font-semibold text-neutral-900 mb-2">
                  추출된 인물이 없습니다
                </h2>
                <p className="text-neutral-600">
                  증거 자료를 업로드하면 AI가 자동으로 인물과 관계를 추출합니다.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Legend Panel */}
        {graph && graph.nodes.length > 0 && (
          <aside className="w-64 border-l bg-white overflow-y-auto">
            <RelationshipLegend graph={graph} />
          </aside>
        )}
      </main>
    </div>
  );
}
