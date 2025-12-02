'use client';

import { Suspense, useMemo, useState } from 'react';
import { useSearchParams } from 'next/navigation';

type EvidenceShareItem = {
  id: string;
  title: string;
  type: string;
  uploadedAt: string;
  summary: string;
};

const SHARED_EVIDENCES: EvidenceShareItem[] = [
  { id: 'ev-1', title: '녹취록_20240501.mp3', type: '오디오', uploadedAt: '2024-05-01', summary: '전화 통화 중 폭언 녹취' },
  { id: 'ev-2', title: '카카오톡_대화내역.txt', type: '텍스트', uploadedAt: '2024-05-02', summary: '양육 관련 대화 기록' },
];

type TabKey = 'info' | 'share';

function CommunicationsContent() {
  const searchParams = useSearchParams();
  const caseId = searchParams?.get('caseId');
  const client = searchParams?.get('client');
  const clientName = client && client.length > 0 ? client : '의뢰인';
  const caseLabel = caseId && caseId.length > 0 ? caseId : '사건';

  const [activeTab, setActiveTab] = useState<TabKey>('info');
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [notes, setNotes] = useState('');
  const [savedMessage, setSavedMessage] = useState('');

  const isFormValid = useMemo(
    () => name.trim() !== '' && phone.trim() !== '' && email.trim() !== '' && notes.trim() !== '',
    [name, phone, email, notes],
  );

  const handleSave = (event: React.FormEvent) => {
    event.preventDefault();
    if (!isFormValid) return;
    setSavedMessage('의뢰인 정보가 저장되었습니다. 고지사항을 확인해 주세요.');
  };

  return (
    <>
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-6 py-5 flex items-center justify-between">
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide">Client Communication</p>
            <h1 className="text-2xl font-bold text-secondary">의뢰인 소통 허브</h1>
            <p className="text-sm text-neutral-600 mt-1">{clientName}님의 {caseLabel} 사건 정보를 확인하고 공유하세요.</p>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8">
        <div role="tablist" aria-label="Communication tabs" className="flex gap-2 mb-6">
          <button
            role="tab"
            aria-selected={activeTab === 'info'}
            className={`px-4 py-2 rounded-lg text-sm font-medium border ${activeTab === 'info' ? 'bg-white text-secondary border-deep-trust-blue' : 'bg-gray-100 text-neutral-600 border-transparent'}`}
            onClick={() => setActiveTab('info')}
          >
            의뢰인 정보
          </button>
          <button
            role="tab"
            aria-selected={activeTab === 'share'}
            className={`px-4 py-2 rounded-lg text-sm font-medium border ${activeTab === 'share' ? 'bg-white text-secondary border-deep-trust-blue' : 'bg-gray-100 text-neutral-600 border-transparent'}`}
            onClick={() => setActiveTab('share')}
          >
            증거 공유
          </button>
        </div>

        {activeTab === 'info' && (
          <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 space-y-4" aria-label="Client info form">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">의뢰인 정보 입력</h2>
                <p className="text-sm text-neutral-600 mt-1">사건을 원활히 진행하기 위해 연락처를 최신으로 유지해 주세요.</p>
              </div>
            </div>

            <form className="grid grid-cols-1 md:grid-cols-2 gap-4" onSubmit={handleSave}>
              <label className="flex flex-col text-sm text-neutral-700">
                <span className="font-medium mb-1">의뢰인 이름</span>
                <input aria-label="의뢰인 이름" type="text" value={name} onChange={(e) => setName(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent" />
              </label>
              <label className="flex flex-col text-sm text-neutral-700">
                <span className="font-medium mb-1">연락처</span>
                <input aria-label="연락처" type="text" value={phone} onChange={(e) => setPhone(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent" placeholder="010-1234-5678" />
              </label>
              <label className="flex flex-col text-sm text-neutral-700">
                <span className="font-medium mb-1">이메일</span>
                <input aria-label="이메일" type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent" placeholder="client@example.com" />
              </label>
              <label className="flex flex-col text-sm text-neutral-700 md:col-span-2">
                <span className="font-medium mb-1">사건 메모</span>
                <textarea aria-label="사건 메모" value={notes} onChange={(e) => setNotes(e.target.value)} rows={3} className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent" placeholder="주요 일정, 전달 사항 등을 기록하세요." />
              </label>

              <div className="md:col-span-2 flex justify-end">
                <button type="submit" disabled={!isFormValid} className="btn-primary px-5 py-3 text-sm font-semibold disabled:opacity-60 disabled:cursor-not-allowed">정보 저장</button>
              </div>
            </form>

            {savedMessage && <div className="rounded-lg bg-accent/10 text-secondary px-4 py-3 text-sm">{savedMessage}</div>}
          </section>
        )}

        {activeTab === 'share' && (
          <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 space-y-4" aria-label="Evidence sharing">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">증거 목록 공유</h2>
                <p className="text-sm text-neutral-600 mt-1">제공된 증거는 열람용이며 수정할 수 없습니다. 고지사항을 확인해 주세요.</p>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 border border-gray-100 rounded-lg" aria-label="증거 목록 공유 테이블">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-neutral-600 uppercase tracking-wider">제목</th>
                    <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-neutral-600 uppercase tracking-wider">유형</th>
                    <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-neutral-600 uppercase tracking-wider">업로드 일시</th>
                    <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-neutral-600 uppercase tracking-wider">요약</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-100">
                  {SHARED_EVIDENCES.map((item) => (
                    <tr key={item.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm text-gray-900">{item.title}</td>
                      <td className="px-4 py-3 text-sm text-neutral-600">{item.type}</td>
                      <td className="px-4 py-3 text-sm text-neutral-600">{item.uploadedAt}</td>
                      <td className="px-4 py-3 text-sm text-neutral-700">{item.summary}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </main>
    </>
  );
}

export default function ClientCommunicationHub() {
  return (
    <div className="min-h-screen bg-neutral-50">
      <Suspense fallback={<div className="flex items-center justify-center min-h-screen text-gray-500">로딩 중...</div>}>
        <CommunicationsContent />
      </Suspense>
    </div>
  );
}
