/**
 * Plan 3.17 - AI 투명성 및 감사 로그 (Compliance)
 *
 * GREEN 단계: 테스트를 통과시키는 최소 구현
 */

import React, { useState } from 'react';
import {
  ChevronRight,
  Shield,
  Lock,
  CheckCircle2,
  AlertCircle,
  Eye,
  Plus,
  Edit,
  Trash2,
  LogIn,
  Download,
  FileDown
} from 'lucide-react';

interface AuditLogEntry {
  id: string;
  timestamp: string;
  user: {
    name: string;
    email: string;
  };
  action: 'LOGIN' | 'VIEW' | 'CREATE' | 'UPDATE' | 'DELETE';
  target: string;
  ipAddress: string;
  details?: string;
}

interface SecurityStatus {
  encryption: {
    enabled: boolean;
    type: string;
  };
  pipa: {
    compliant: boolean;
  };
  lastAudit: string;
}

export default function AuditLogPage() {
  // Mock data - 실제로는 API에서 가져올 데이터
  const [auditLogs] = useState<AuditLogEntry[]>([
    {
      id: '1',
      timestamp: '2025-11-24T10:30:00',
      user: { name: '홍길동', email: 'hong@example.com' },
      action: 'DELETE',
      target: 'Case #123',
      ipAddress: '192.168.1.100',
      details: 'Deleted evidence file'
    },
    {
      id: '2',
      timestamp: '2025-11-24T09:15:00',
      user: { name: '김철수', email: 'kim@example.com' },
      action: 'CREATE',
      target: 'Case #456',
      ipAddress: '192.168.1.101',
      details: 'Created new case'
    },
    {
      id: '3',
      timestamp: '2025-11-24T08:00:00',
      user: { name: '이영희', email: 'lee@example.com' },
      action: 'UPDATE',
      target: 'Draft #789',
      ipAddress: '192.168.1.102',
      details: 'Updated draft content'
    },
    {
      id: '4',
      timestamp: '2025-11-23T17:45:00',
      user: { name: '박민수', email: 'park@example.com' },
      action: 'VIEW',
      target: 'Evidence #101',
      ipAddress: '192.168.1.103',
      details: 'Viewed evidence file'
    },
    {
      id: '5',
      timestamp: '2025-11-23T14:20:00',
      user: { name: '최지은', email: 'choi@example.com' },
      action: 'LOGIN',
      target: 'System',
      ipAddress: '192.168.1.104',
      details: 'User logged in'
    }
  ]);

  const [securityStatus] = useState<SecurityStatus>({
    encryption: {
      enabled: true,
      type: 'AES-256, TLS 1.3'
    },
    pipa: {
      compliant: true
    },
    lastAudit: '2025-11-20'
  });

  // Filter states
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [selectedUser, setSelectedUser] = useState('all');
  const [selectedActions, setSelectedActions] = useState<string[]>([
    'LOGIN',
    'VIEW',
    'CREATE',
    'UPDATE',
    'DELETE'
  ]);

  // Unique users for filter dropdown
  const uniqueUsers = Array.from(
    new Set(auditLogs.map((log) => log.user.email))
  );

  // Filter logs based on selected criteria
  const filteredLogs = auditLogs.filter((log) => {
    // Date filter
    if (startDate && new Date(log.timestamp) < new Date(startDate)) return false;
    if (endDate && new Date(log.timestamp) > new Date(endDate)) return false;

    // User filter
    if (selectedUser !== 'all' && log.user.email !== selectedUser) return false;

    // Action type filter
    if (!selectedActions.includes(log.action)) return false;

    return true;
  });

  const hasActiveFilters =
    startDate !== '' ||
    endDate !== '' ||
    selectedUser !== 'all' ||
    selectedActions.length !== 5;

  const resetFilters = () => {
    setStartDate('');
    setEndDate('');
    setSelectedUser('all');
    setSelectedActions(['LOGIN', 'VIEW', 'CREATE', 'UPDATE', 'DELETE']);
  };

  const getActionIcon = (action: AuditLogEntry['action']) => {
    switch (action) {
      case 'LOGIN':
        return <LogIn className="w-4 h-4" />;
      case 'VIEW':
        return <Eye className="w-4 h-4" />;
      case 'CREATE':
        return <Plus className="w-4 h-4" />;
      case 'UPDATE':
        return <Edit className="w-4 h-4" />;
      case 'DELETE':
        return <Trash2 className="w-4 h-4" />;
      default:
        return null;
    }
  };

  const getActionColor = (action: AuditLogEntry['action']) => {
    switch (action) {
      case 'DELETE':
        return 'text-semantic-error bg-red-50';
      case 'CREATE':
        return 'text-success-green bg-green-50';
      case 'UPDATE':
        return 'text-yellow-600 bg-yellow-50';
      case 'VIEW':
        return 'text-blue-600 bg-blue-50';
      case 'LOGIN':
        return 'text-gray-600 bg-gray-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const toggleActionFilter = (action: string) => {
    if (selectedActions.includes(action)) {
      setSelectedActions(selectedActions.filter((a) => a !== action));
    } else {
      setSelectedActions([...selectedActions, action]);
    }
  };

  const handleExportCSV = () => {
    // CSV 내보내기 로직 (실제로는 CSV 생성 후 다운로드)
    console.log('Exporting audit logs to CSV...');
    const csvContent = [
      ['Timestamp', 'User', 'Email', 'Action', 'Target', 'IP Address', 'Details'],
      ...filteredLogs.map((log) => [
        log.timestamp,
        log.user.name,
        log.user.email,
        log.action,
        log.target,
        log.ipAddress,
        log.details || ''
      ])
    ]
      .map((row) => row.join(','))
      .join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit-log-${new Date().toISOString()}.csv`;
    a.click();
  };

  return (
    <div className="min-h-screen bg-calm-grey p-8">
      {/* Breadcrumb Navigation */}
      <nav aria-label="Breadcrumb" className="mb-6">
        <ol className="flex items-center space-x-2 text-sm">
          <li>
            <a href="/admin" className="text-gray-600 hover:text-deep-trust-blue">
              Admin
            </a>
          </li>
          <ChevronRight className="w-4 h-4 text-gray-400" />
          <li>
            <span className="text-deep-trust-blue font-semibold">Audit Log</span>
          </li>
        </ol>
      </nav>

      {/* Page Title */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-deep-trust-blue">활동 로그</h1>
        <p className="text-gray-600 mt-2">
          시스템 사용자 활동 기록 및 보안 상태 모니터링
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Security Status Dashboard */}
        <section
          className="lg:col-span-3 bg-white border border-gray-200 rounded-lg p-6 shadow-sm"
          aria-labelledby="security-status-title"
        >
          <h2
            id="security-status-title"
            className="text-xl font-semibold text-deep-trust-blue mb-6"
          >
            보안 상태
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Encryption Status */}
            <div className="flex items-start space-x-4">
              <div className="w-12 h-12 bg-success-green bg-opacity-10 rounded-lg flex items-center justify-center flex-shrink-0">
                <Lock className="w-6 h-6 text-success-green" />
              </div>
              <div>
                <p className="text-sm text-gray-600">암호화 상태</p>
                <p className="text-lg font-semibold text-deep-trust-blue mt-1">
                  암호화 활성
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {securityStatus.encryption.type}
                </p>
              </div>
            </div>

            {/* PIPA Compliance */}
            <div className="flex items-start space-x-4">
              <div className="w-12 h-12 bg-success-green bg-opacity-10 rounded-lg flex items-center justify-center flex-shrink-0">
                <Shield className="w-6 h-6 text-success-green" />
              </div>
              <div>
                <p className="text-sm text-gray-600">PIPA 준수</p>
                <p className="text-lg font-semibold text-deep-trust-blue mt-1">
                  {securityStatus.pipa.compliant ? 'PIPA Compliant' : 'Non-Compliant'}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  개인정보보호법 준수
                </p>
              </div>
            </div>

            {/* Last Audit */}
            <div className="flex items-start space-x-4">
              <div className="w-12 h-12 bg-blue-50 rounded-lg flex items-center justify-center flex-shrink-0">
                <CheckCircle2 className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">마지막 감사</p>
                <p className="text-lg font-semibold text-deep-trust-blue mt-1">
                  {securityStatus.lastAudit}
                </p>
                <p className="text-xs text-gray-500 mt-1">정기 보안 감사 완료</p>
              </div>
            </div>
          </div>
        </section>
      </div>

      {/* Filters Section */}
      <section
        className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm mb-6"
        aria-labelledby="filters-title"
      >
        <h2 id="filters-title" className="text-lg font-semibold text-deep-trust-blue mb-4">
          필터
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Date Range Filter */}
          <div>
            <label htmlFor="start-date" className="block text-sm font-medium text-gray-700 mb-2">
              시작 날짜
            </label>
            <input
              type="date"
              id="start-date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-accent focus:border-accent"
              aria-label="시작 날짜"
            />
          </div>

          <div>
            <label htmlFor="end-date" className="block text-sm font-medium text-gray-700 mb-2">
              종료 날짜
            </label>
            <input
              type="date"
              id="end-date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-accent focus:border-accent"
              aria-label="종료 날짜"
            />
          </div>

          {/* User Filter */}
          <div>
            <label htmlFor="user-filter" className="block text-sm font-medium text-gray-700 mb-2">
              사용자 선택
            </label>
            <select
              id="user-filter"
              value={selectedUser}
              onChange={(e) => setSelectedUser(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-accent focus:border-accent"
              aria-label="사용자 선택"
            >
              <option value="all">전체 사용자</option>
              {uniqueUsers.map((email) => (
                <option key={email} value={email}>
                  {email}
                </option>
              ))}
            </select>
          </div>

          {/* Reset Filters Button */}
          <div className="flex items-end">
            {hasActiveFilters && (
              <button
                onClick={resetFilters}
                className="w-full px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
              >
                필터 초기화
              </button>
            )}
          </div>
        </div>

        {/* Action Type Filters */}
        <div className="mt-4">
          <p className="block text-sm font-medium text-gray-700 mb-2">작업 유형</p>
          <div className="flex flex-wrap gap-3">
            {(['LOGIN', 'VIEW', 'CREATE', 'UPDATE', 'DELETE'] as const).map((action) => (
              <label key={action} className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={selectedActions.includes(action)}
                  onChange={() => toggleActionFilter(action)}
                  className="w-4 h-4 text-accent border-gray-300 rounded focus:ring-accent"
                  aria-label={action}
                />
                <span className="text-sm text-gray-700">{action}</span>
              </label>
            ))}
          </div>
        </div>
      </section>

      {/* Activity Log Table */}
      <section
        className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm"
        aria-labelledby="audit-log-title"
      >
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 id="audit-log-title" className="text-xl font-semibold text-deep-trust-blue">
              활동 로그
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              총 {filteredLogs.length} 개의 로그
            </p>
          </div>

          <button
            onClick={handleExportCSV}
            className="inline-flex items-center px-4 py-2 bg-accent text-white rounded-md hover:bg-accent-dark transition-colors"
            aria-label="CSV 다운로드"
          >
            <FileDown className="w-4 h-4 mr-2" />
            CSV 다운로드
          </button>
        </div>

        {filteredLogs.length === 0 ? (
          <div className="text-center py-12">
            <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">로그가 없습니다</p>
            <p className="text-sm text-gray-500 mt-2">
              필터 조건을 변경하거나 초기화해 주세요
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full" role="table" aria-label="Activity log table">
              <thead>
                <tr className="border-b border-gray-200">
                  <th
                    scope="col"
                    className="text-left py-3 px-4 text-sm font-semibold text-deep-trust-blue"
                  >
                    날짜/시간
                  </th>
                  <th
                    scope="col"
                    className="text-left py-3 px-4 text-sm font-semibold text-deep-trust-blue"
                  >
                    사용자
                  </th>
                  <th
                    scope="col"
                    className="text-left py-3 px-4 text-sm font-semibold text-deep-trust-blue"
                  >
                    작업
                  </th>
                  <th
                    scope="col"
                    className="text-left py-3 px-4 text-sm font-semibold text-deep-trust-blue"
                  >
                    대상
                  </th>
                  <th
                    scope="col"
                    className="text-left py-3 px-4 text-sm font-semibold text-deep-trust-blue"
                  >
                    IP 주소
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredLogs.map((log) => (
                  <tr key={log.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4 text-sm text-gray-700">
                      {new Date(log.timestamp).toLocaleString('ko-KR')}
                    </td>
                    <td className="py-3 px-4">
                      <div>
                        <p className="text-sm font-medium text-gray-900">{log.user.name}</p>
                        <p className="text-xs text-gray-500">{log.user.email}</p>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getActionColor(
                          log.action
                        )}`}
                      >
                        {getActionIcon(log.action)}
                        <span className="ml-1">{log.action}</span>
                      </span>
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-700">{log.target}</td>
                    <td className="py-3 px-4 text-sm text-gray-600 font-mono">
                      {log.ipAddress}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination (placeholder for future implementation) */}
        <div className="mt-6 flex items-center justify-between">
          <p className="text-sm text-gray-600">페이지 1 / 1</p>
          <div className="flex space-x-2">
            <button
              disabled
              className="px-3 py-1 bg-gray-100 text-gray-400 rounded-md cursor-not-allowed"
              aria-label="이전 페이지"
            >
              이전
            </button>
            <button
              disabled
              className="px-3 py-1 bg-gray-100 text-gray-400 rounded-md cursor-not-allowed"
              aria-label="다음 페이지"
            >
              다음
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
