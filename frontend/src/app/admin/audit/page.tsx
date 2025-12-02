'use client';

import React, { useState } from 'react';
import {
  ChevronRight, Shield, Lock, CheckCircle2, AlertCircle,
  Eye, Plus, Edit, Trash2, LogIn, FileDown
} from 'lucide-react';

interface AuditLogEntry {
  id: string;
  timestamp: string;
  user: { name: string; email: string };
  action: 'LOGIN' | 'VIEW' | 'CREATE' | 'UPDATE' | 'DELETE';
  target: string;
  ipAddress: string;
  details?: string;
}

interface SecurityStatus {
  encryption: { enabled: boolean; type: string };
  pipa: { compliant: boolean };
  lastAudit: string;
}

export default function AuditLogPage() {
  const [auditLogs] = useState<AuditLogEntry[]>([
    { id: '1', timestamp: '2025-11-24T10:30:00', user: { name: '홍길동', email: 'hong@example.com' }, action: 'DELETE', target: 'Case #123', ipAddress: '192.168.1.100', details: 'Deleted evidence file' },
    { id: '2', timestamp: '2025-11-24T09:15:00', user: { name: '김철수', email: 'kim@example.com' }, action: 'CREATE', target: 'Case #456', ipAddress: '192.168.1.101', details: 'Created new case' },
    { id: '3', timestamp: '2025-11-24T08:00:00', user: { name: '이영희', email: 'lee@example.com' }, action: 'UPDATE', target: 'Draft #789', ipAddress: '192.168.1.102', details: 'Updated draft content' },
    { id: '4', timestamp: '2025-11-23T17:45:00', user: { name: '박민수', email: 'park@example.com' }, action: 'VIEW', target: 'Evidence #101', ipAddress: '192.168.1.103', details: 'Viewed evidence file' },
    { id: '5', timestamp: '2025-11-23T14:20:00', user: { name: '최지은', email: 'choi@example.com' }, action: 'LOGIN', target: 'System', ipAddress: '192.168.1.104', details: 'User logged in' }
  ]);

  const [securityStatus] = useState<SecurityStatus>({
    encryption: { enabled: true, type: 'AES-256, TLS 1.3' },
    pipa: { compliant: true },
    lastAudit: '2025-11-20'
  });

  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [selectedUser, setSelectedUser] = useState('all');
  const [selectedActions, setSelectedActions] = useState<string[]>(['LOGIN', 'VIEW', 'CREATE', 'UPDATE', 'DELETE']);

  const uniqueUsers = Array.from(new Set(auditLogs.map((log) => log.user.email)));

  const filteredLogs = auditLogs.filter((log) => {
    if (startDate && new Date(log.timestamp) < new Date(startDate)) return false;
    if (endDate && new Date(log.timestamp) > new Date(endDate)) return false;
    if (selectedUser !== 'all' && log.user.email !== selectedUser) return false;
    if (!selectedActions.includes(log.action)) return false;
    return true;
  });

  const hasActiveFilters = startDate !== '' || endDate !== '' || selectedUser !== 'all' || selectedActions.length !== 5;
  const resetFilters = () => { setStartDate(''); setEndDate(''); setSelectedUser('all'); setSelectedActions(['LOGIN', 'VIEW', 'CREATE', 'UPDATE', 'DELETE']); };

  const getActionIcon = (action: AuditLogEntry['action']) => {
    const icons = { LOGIN: <LogIn className="w-4 h-4" />, VIEW: <Eye className="w-4 h-4" />, CREATE: <Plus className="w-4 h-4" />, UPDATE: <Edit className="w-4 h-4" />, DELETE: <Trash2 className="w-4 h-4" /> };
    return icons[action];
  };

  const getActionColor = (action: AuditLogEntry['action']) => {
    const colors = { DELETE: 'text-semantic-error bg-red-50', CREATE: 'text-success-green bg-green-50', UPDATE: 'text-yellow-600 bg-yellow-50', VIEW: 'text-blue-600 bg-blue-50', LOGIN: 'text-neutral-600 bg-gray-50' };
    return colors[action];
  };

  const toggleActionFilter = (action: string) => {
    setSelectedActions(prev => prev.includes(action) ? prev.filter(a => a !== action) : [...prev, action]);
  };

  const handleExportCSV = () => {
    const csvContent = [['Timestamp', 'User', 'Email', 'Action', 'Target', 'IP Address', 'Details'], ...filteredLogs.map((log) => [log.timestamp, log.user.name, log.user.email, log.action, log.target, log.ipAddress, log.details || ''])].map((row) => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit-log-${new Date().toISOString()}.csv`;
    a.click();
  };

  return (
    <div className="min-h-screen bg-neutral-50 p-8">
      <nav aria-label="Breadcrumb" className="mb-6">
        <ol className="flex items-center space-x-2 text-sm">
          <li><a href="/admin" className="text-neutral-600 hover:text-secondary">Admin</a></li>
          <ChevronRight className="w-4 h-4 text-gray-400" />
          <li><span className="text-secondary font-semibold">Audit Log</span></li>
        </ol>
      </nav>

      <div className="mb-8">
        <h1 className="text-3xl font-bold text-secondary">활동 로그</h1>
        <p className="text-neutral-600 mt-2">시스템 사용자 활동 기록 및 보안 상태 모니터링</p>
      </div>

      <section className="lg:col-span-3 bg-white border border-gray-200 rounded-lg p-6 shadow-sm mb-8">
        <h2 className="text-xl font-semibold text-secondary mb-6">보안 상태</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="flex items-start space-x-4">
            <div className="w-12 h-12 bg-success-green bg-opacity-10 rounded-lg flex items-center justify-center"><Lock className="w-6 h-6 text-success-green" /></div>
            <div><p className="text-sm text-neutral-600">암호화 상태</p><p className="text-lg font-semibold text-secondary mt-1">암호화 활성</p><p className="text-xs text-gray-500 mt-1">{securityStatus.encryption.type}</p></div>
          </div>
          <div className="flex items-start space-x-4">
            <div className="w-12 h-12 bg-success-green bg-opacity-10 rounded-lg flex items-center justify-center"><Shield className="w-6 h-6 text-success-green" /></div>
            <div><p className="text-sm text-neutral-600">PIPA 준수</p><p className="text-lg font-semibold text-secondary mt-1">{securityStatus.pipa.compliant ? 'PIPA Compliant' : 'Non-Compliant'}</p><p className="text-xs text-gray-500 mt-1">개인정보보호법 준수</p></div>
          </div>
          <div className="flex items-start space-x-4">
            <div className="w-12 h-12 bg-blue-50 rounded-lg flex items-center justify-center"><CheckCircle2 className="w-6 h-6 text-blue-600" /></div>
            <div><p className="text-sm text-neutral-600">마지막 감사</p><p className="text-lg font-semibold text-secondary mt-1">{securityStatus.lastAudit}</p><p className="text-xs text-gray-500 mt-1">정기 보안 감사 완료</p></div>
          </div>
        </div>
      </section>

      <section className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm mb-6">
        <h2 className="text-lg font-semibold text-secondary mb-4">필터</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div><label className="block text-sm font-medium text-neutral-700 mb-2">시작 날짜</label><input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-md" /></div>
          <div><label className="block text-sm font-medium text-neutral-700 mb-2">종료 날짜</label><input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-md" /></div>
          <div><label className="block text-sm font-medium text-neutral-700 mb-2">사용자 선택</label><select value={selectedUser} onChange={(e) => setSelectedUser(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-md"><option value="all">전체 사용자</option>{uniqueUsers.map((email) => <option key={email} value={email}>{email}</option>)}</select></div>
          <div className="flex items-end">{hasActiveFilters && <button onClick={resetFilters} className="w-full px-4 py-2 bg-gray-200 text-neutral-700 rounded-md hover:bg-gray-300">필터 초기화</button>}</div>
        </div>
        <div className="mt-4">
          <p className="block text-sm font-medium text-neutral-700 mb-2">작업 유형</p>
          <div className="flex flex-wrap gap-3">
            {(['LOGIN', 'VIEW', 'CREATE', 'UPDATE', 'DELETE'] as const).map((action) => (
              <label key={action} className="flex items-center space-x-2 cursor-pointer">
                <input type="checkbox" checked={selectedActions.includes(action)} onChange={() => toggleActionFilter(action)} className="w-4 h-4 text-accent border-gray-300 rounded" />
                <span className="text-sm text-neutral-700">{action}</span>
              </label>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
        <div className="flex items-center justify-between mb-6">
          <div><h2 className="text-xl font-semibold text-secondary">활동 로그</h2><p className="text-sm text-neutral-600 mt-1">총 {filteredLogs.length} 개의 로그</p></div>
          <button onClick={handleExportCSV} className="inline-flex items-center px-4 py-2 bg-accent text-white rounded-md hover:bg-accent-dark"><FileDown className="w-4 h-4 mr-2" />CSV 다운로드</button>
        </div>
        {filteredLogs.length === 0 ? (
          <div className="text-center py-12"><AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" /><p className="text-neutral-600">로그가 없습니다</p></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead><tr className="border-b border-gray-200"><th className="text-left py-3 px-4 text-sm font-semibold text-secondary">날짜/시간</th><th className="text-left py-3 px-4 text-sm font-semibold text-secondary">사용자</th><th className="text-left py-3 px-4 text-sm font-semibold text-secondary">작업</th><th className="text-left py-3 px-4 text-sm font-semibold text-secondary">대상</th><th className="text-left py-3 px-4 text-sm font-semibold text-secondary">IP 주소</th></tr></thead>
              <tbody>
                {filteredLogs.map((log) => (
                  <tr key={log.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4 text-sm text-neutral-700">{new Date(log.timestamp).toLocaleString('ko-KR')}</td>
                    <td className="py-3 px-4"><p className="text-sm font-medium text-gray-900">{log.user.name}</p><p className="text-xs text-gray-500">{log.user.email}</p></td>
                    <td className="py-3 px-4"><span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getActionColor(log.action)}`}>{getActionIcon(log.action)}<span className="ml-1">{log.action}</span></span></td>
                    <td className="py-3 px-4 text-sm text-neutral-700">{log.target}</td>
                    <td className="py-3 px-4 text-sm text-neutral-600 font-mono">{log.ipAddress}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
