'use client';

import { useCallback, useEffect, useState } from 'react';
import { ArrowLeft, Loader2, AlertCircle, RefreshCw, Users } from 'lucide-react';
import Link from 'next/link';
import { RelationshipGraph } from '@/types/relationship';
import { analyzeRelationships } from '@/lib/api/relationship';
import RelationshipFlow from '@/components/relationship/RelationshipFlow';
import RelationshipLegend from '@/components/relationship/RelationshipLegend';

interface RelationshipClientProps {
  caseId: string;
}

export default function RelationshipClient({ caseId }: RelationshipClientProps) {
  const [graph, setGraph] = useState<RelationshipGraph | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 데모용 샘플 텍스트 (실제로는 증거 데이터에서 가져옴)
  const sampleText = `
    김철수(원고)와 이영희(피고)는 2015년에 결혼했습니다.
    두 사람 사이에는 김민수(자녀)가 있습니다.
    2023년 김철수는 이영희가 박지훈과 외도했다는 사실을 알게 되었습니다.
  `;

  const fetchRelationships = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await analyzeRelationships(sampleText);

      if (response.error) {
        setError(response.error);
        setGraph(null);
      } else if (response.data) {
        setGraph(response.data);
      }
    } catch (err) {
      console.error('Failed to fetch relationships:', err);
      setError('관계 정보를 불러오는데 실패했습니다.');
      setGraph(null);
    } finally {
      setIsLoading(false);
    }
  }, [sampleText]);

  useEffect(() => {
    fetchRelationships();
  }, [fetchRelationships]);

  const hasData = graph && graph.nodes.length > 0;

  return (
    <div className="min-h-screen bg-neutral-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center">
            <Link
              href={`/cases/${caseId}`}
              className="mr-4 text-gray-500 hover:text-gray-800 transition-colors"
            >
              <ArrowLeft className="w-6 h-6" />
            </Link>
            <div>
              <h1 className="text-xl font-bold text-secondary">인물 관계도</h1>
              <p className="text-xs text-gray-500">Case ID: {caseId}</p>
            </div>
          </div>
          <button
            onClick={fetchRelationships}
            disabled={isLoading}
            className="flex items-center text-sm text-neutral-600 hover:text-gray-900 bg-white border border-gray-300 px-3 py-1.5 rounded-md shadow-sm disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            새로고침
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Loading State */}
        {isLoading && (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-12 flex flex-col items-center justify-center">
            <Loader2 className="w-8 h-8 text-accent animate-spin mb-4" />
            <p className="text-gray-500">관계 정보를 분석하고 있습니다...</p>
          </div>
        )}

        {/* Error State */}
        {!isLoading && error && (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-red-500 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-red-700">{error}</p>
                <button
                  onClick={fetchRelationships}
                  className="text-sm text-red-600 hover:text-red-800 underline mt-1"
                >
                  다시 시도
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!isLoading && !error && !hasData && (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-12 flex flex-col items-center justify-center">
            <Users className="w-12 h-12 text-gray-300 mb-4" />
            <h2 className="text-lg font-semibold text-gray-700 mb-2">
              관계 정보가 없습니다
            </h2>
            <p className="text-sm text-gray-500 text-center max-w-md">
              증거 자료에서 인물 관계를 분석할 수 없습니다.
              카카오톡 대화나 관련 문서를 업로드하면 자동으로 관계도가 생성됩니다.
            </p>
          </div>
        )}

        {/* Graph View */}
        {!isLoading && !error && hasData && (
          <div className="space-y-6">
            {/* Info Card */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <Users className="w-5 h-5 text-accent" />
                  <div>
                    <p className="text-sm font-semibold text-gray-900">
                      {graph.nodes.length}명의 인물, {graph.edges.length}개의 관계
                    </p>
                    <p className="text-xs text-gray-500">
                      노드를 클릭하면 상세 정보를 확인할 수 있습니다.
                    </p>
                  </div>
                </div>
                <RelationshipLegend />
              </div>
            </div>

            {/* Graph Container */}
            <div
              className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden"
              style={{ height: '600px' }}
              data-testid="relationship-flow"
            >
              <RelationshipFlow graph={graph} />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
