'use client';

import React, { useState } from 'react';
import {
  ChevronRight,
  TrendingUp,
  RefreshCw,
  Download,
  ArrowUp,
  ArrowDown
} from 'lucide-react';

interface KPIMetric {
  label: string;
  value: number;
  unit: string;
  change: number;
  trend: 'up' | 'down';
}

interface TeamMember {
  id: string;
  name: string;
  email: string;
  casesHandled: number;
  evidenceUploaded: number;
  activityLevel: 'high' | 'medium' | 'low';
  lastActive: string;
}

interface MonthlyData {
  month: string;
  caseCount: number;
}

interface EvidenceTypeData {
  type: string;
  count: number;
  color: string;
}

export default function AnalyticsDashboard() {
  const [kpiMetrics] = useState<KPIMetric[]>([
    { label: '절약된 시간', value: 240, unit: '시간', change: 15.3, trend: 'up' },
    { label: '처리된 증거', value: 1847, unit: '건', change: 22.5, trend: 'up' },
    { label: '처리된 사건', value: 156, unit: '건', change: 8.2, trend: 'up' }
  ]);

  const [monthlyData] = useState<MonthlyData[]>([
    { month: '1월', caseCount: 12 },
    { month: '2월', caseCount: 15 },
    { month: '3월', caseCount: 18 },
    { month: '4월', caseCount: 14 },
    { month: '5월', caseCount: 20 },
    { month: '6월', caseCount: 22 }
  ]);

  const [evidenceTypes] = useState<EvidenceTypeData[]>([
    { type: '이미지', count: 450, color: '#1ABC9C' },
    { type: '문서', count: 320, color: '#3498DB' },
    { type: '오디오', count: 180, color: '#9B59B6' },
    { type: '비디오', count: 120, color: '#E74C3C' },
    { type: '텍스트', count: 280, color: '#F39C12' }
  ]);

  const [teamMembers] = useState<TeamMember[]>([
    { id: '1', name: '홍길동', email: 'hong@example.com', casesHandled: 45, evidenceUploaded: 320, activityLevel: 'high', lastActive: '2025-11-24T10:30:00' },
    { id: '2', name: '김철수', email: 'kim@example.com', casesHandled: 38, evidenceUploaded: 280, activityLevel: 'high', lastActive: '2025-11-24T09:15:00' },
    { id: '3', name: '이영희', email: 'lee@example.com', casesHandled: 25, evidenceUploaded: 180, activityLevel: 'medium', lastActive: '2025-11-23T17:45:00' }
  ]);

  const [lastUpdated] = useState(new Date().toLocaleString('ko-KR'));
  const [selectedDateRange, setSelectedDateRange] = useState('last-6-months');

  const handleRefresh = () => {
    // TODO: Implement analytics data refresh via API
  };
  const handleExportPDF = () => {
    // TODO: Implement PDF export functionality
  };

  const getActivityLevelColor = (level: string) => {
    switch (level) {
      case 'high': return 'text-success-green bg-green-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      default: return 'text-neutral-600 bg-gray-50';
    }
  };

  const getActivityLevelText = (level: string) => {
    switch (level) {
      case 'high': return '높음';
      case 'medium': return '보통';
      default: return '낮음';
    }
  };

  const maxCaseCount = Math.max(...monthlyData.map((d) => d.caseCount));
  const totalEvidence = evidenceTypes.reduce((sum, type) => sum + type.count, 0);

  return (
    <div className="min-h-screen bg-neutral-50 p-8">
      <nav aria-label="Breadcrumb" className="mb-6">
        <ol className="flex items-center space-x-2 text-sm">
          <li><a href="/admin" className="text-neutral-600 hover:text-secondary">Admin</a></li>
          <ChevronRight className="w-4 h-4 text-gray-400" />
          <li><span className="text-secondary font-semibold">Analytics</span></li>
        </ol>
      </nav>

      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-secondary">성과 분석</h1>
          <p className="text-neutral-600 mt-2">시스템 효율성 및 팀 활동 현황</p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="text-sm text-neutral-600">마지막 업데이트: {lastUpdated}</div>
          <button onClick={handleRefresh} className="inline-flex items-center px-4 py-2 bg-white border border-gray-300 text-neutral-700 rounded-md hover:bg-gray-50">
            <RefreshCw className="w-4 h-4 mr-2" />새로고침
          </button>
          <button onClick={handleExportPDF} className="inline-flex items-center px-4 py-2 bg-accent text-white rounded-md hover:bg-accent-dark">
            <Download className="w-4 h-4 mr-2" />PDF 다운로드
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {kpiMetrics.map((metric, index) => (
          <div key={index} className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
            <div className="flex items-start justify-between mb-4">
              <div>
                <p className="text-sm text-neutral-600">{metric.label}</p>
                <div className="flex items-baseline mt-2">
                  <p className="text-5xl font-bold text-secondary">{metric.value.toLocaleString()}</p>
                  <span className="text-xl text-neutral-600 ml-2">{metric.unit}</span>
                </div>
              </div>
              <div className="w-12 h-12 bg-success-green bg-opacity-10 rounded-lg flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-success-green" />
              </div>
            </div>
            <div className="flex items-center">
              {metric.trend === 'up' ? <ArrowUp className="w-4 h-4 text-success-green mr-1" /> : <ArrowDown className="w-4 h-4 text-semantic-error mr-1" />}
              <span className="text-sm font-medium text-success-green">+{metric.change}%</span>
              <span className="text-sm text-neutral-600 ml-2">지난 달 대비</span>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <section className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-secondary">월별 사건 수</h2>
            <select value={selectedDateRange} onChange={(e) => setSelectedDateRange(e.target.value)} className="px-3 py-1 border border-gray-300 rounded-md text-sm">
              <option value="last-3-months">최근 3개월</option>
              <option value="last-6-months">최근 6개월</option>
              <option value="last-12-months">최근 12개월</option>
            </select>
          </div>
          <div className="space-y-3">
            {monthlyData.map((data, index) => (
              <div key={index} className="flex items-center">
                <div className="w-12 text-sm text-neutral-600">{data.month}</div>
                <div className="flex-1 mx-4">
                  <div className="w-full bg-gray-200 rounded-full h-8 relative">
                    <div className="bg-accent h-8 rounded-full flex items-center justify-end pr-3" style={{ width: `${(data.caseCount / maxCaseCount) * 100}%` }}>
                      <span className="text-xs font-medium text-white">{data.caseCount}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-secondary mb-6">증거 유형별 분포</h2>
          <div className="space-y-3">
            {evidenceTypes.map((type, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex items-center flex-1">
                  <div className="w-4 h-4 rounded-sm mr-3" style={{ backgroundColor: type.color }}></div>
                  <span className="text-sm text-neutral-700">{type.type}</span>
                </div>
                <div className="flex items-center">
                  <span className="text-sm font-medium text-secondary mr-3">{type.count}건</span>
                  <span className="text-sm text-neutral-600 w-16 text-right">{((type.count / totalEvidence) * 100).toFixed(1)}%</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
        <h2 className="text-xl font-semibold text-secondary mb-6">팀 활동</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 text-sm font-semibold text-secondary">팀원</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-secondary">처리 사건</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-secondary">업로드 증거</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-secondary">활동 레벨</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-secondary">마지막 활동</th>
              </tr>
            </thead>
            <tbody>
              {teamMembers.sort((a, b) => ({ high: 3, medium: 2, low: 1 }[b.activityLevel] - { high: 3, medium: 2, low: 1 }[a.activityLevel])).map((member) => (
                <tr key={member.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-4">
                    <p className="text-sm font-medium text-gray-900">{member.name}</p>
                    <p className="text-xs text-gray-500">{member.email}</p>
                  </td>
                  <td className="py-3 px-4 text-sm text-neutral-700">{member.casesHandled}건</td>
                  <td className="py-3 px-4 text-sm text-neutral-700">{member.evidenceUploaded}건</td>
                  <td className="py-3 px-4">
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getActivityLevelColor(member.activityLevel)}`}>
                      {getActivityLevelText(member.activityLevel)}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-sm text-neutral-600">{new Date(member.lastActive).toLocaleString('ko-KR')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
