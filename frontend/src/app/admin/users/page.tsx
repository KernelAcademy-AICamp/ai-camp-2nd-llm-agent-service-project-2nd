'use client';

import { useMemo, useState } from 'react';

type AdminRole = 'Admin' | 'Attorney' | 'Staff';
type AdminUserStatus = 'active' | 'invited' | 'inactive';

type AdminUser = {
  id: string;
  name: string;
  email: string;
  role: AdminRole;
  status: AdminUserStatus;
};

const MOCK_USERS: AdminUser[] = [
  { id: 'user-1', name: '홍길동', email: 'hong@example.com', role: 'Admin', status: 'active' },
  { id: 'user-2', name: '이영희', email: 'lee@example.com', role: 'Attorney', status: 'active' },
  { id: 'user-3', name: '김철수', email: 'kim@example.com', role: 'Staff', status: 'invited' },
];

export default function AdminUsersPage() {
  const [users, setUsers] = useState<AdminUser[]>(MOCK_USERS);
  const [search, setSearch] = useState('');
  const [inviteMessage, setInviteMessage] = useState('');

  const filteredUsers = useMemo(() => {
    const keyword = search.trim().toLowerCase();
    if (!keyword) return users;
    return users.filter(
      (user) =>
        user.name.toLowerCase().includes(keyword) ||
        user.email.toLowerCase().includes(keyword),
    );
  }, [search, users]);

  const handleDeleteUser = (userId: string) => {
    setUsers((prev) => prev.filter((user) => user.id !== userId));
  };

  const handleInvite = () => {
    setInviteMessage('초대 링크가 전송되었습니다.');
  };

  return (
    <div className="min-h-screen bg-neutral-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-6 py-5 flex items-center justify-between">
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide">Admin</p>
            <h1 className="text-2xl font-bold text-secondary">사용자 및 역할 관리</h1>
            <p className="text-sm text-neutral-600 mt-1">로펌 내 사용자 현황을 한눈에 보고, 초대 및 권한을 관리합니다.</p>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 space-y-4">
        <section aria-label="사용자 목록" className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-4">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">사용자 목록</h2>
              <p className="text-sm text-neutral-600 mt-1">이름, 이메일, 역할, 상태를 기준으로 사용자를 관리합니다.</p>
            </div>
            <div className="flex gap-2">
              <input
                type="search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="이름 또는 이메일으로 검색"
                className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-accent focus:border-accent bg-white"
              />
              <button type="button" className="btn-primary text-sm px-4 py-2" onClick={handleInvite}>
                사용자 초대
              </button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 border border-gray-100 rounded-lg bg-white text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-neutral-600 uppercase tracking-wider">이름</th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-neutral-600 uppercase tracking-wider">이메일</th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-neutral-600 uppercase tracking-wider">역할</th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-neutral-600 uppercase tracking-wider">상태</th>
                  <th scope="col" className="px-4 py-3 text-right text-xs font-semibold text-neutral-600 uppercase tracking-wider">액션</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-100">
                {filteredUsers.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50" aria-label={user.name}>
                    <td className="px-4 py-3 text-gray-900">{user.name}</td>
                    <td className="px-4 py-3 text-neutral-700">{user.email}</td>
                    <td className="px-4 py-3 text-neutral-700">{user.role}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        user.status === 'active' ? 'bg-emerald-50 text-emerald-700' :
                        user.status === 'invited' ? 'bg-blue-50 text-blue-700' :
                        'bg-gray-100 text-neutral-600'
                      }`}>
                        {user.status === 'active' ? '활성' : user.status === 'invited' ? '초대됨' : '비활성'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        type="button"
                        onClick={() => handleDeleteUser(user.id)}
                        className="btn-danger text-xs px-3 py-1.5"
                        aria-label={`${user.name} 삭제`}
                      >
                        삭제
                      </button>
                    </td>
                  </tr>
                ))}
                {filteredUsers.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-4 py-6 text-center text-sm text-gray-500">
                      조건에 맞는 사용자가 없습니다.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {inviteMessage && (
            <div className="mt-4 rounded-md bg-accent/10 text-secondary px-4 py-3 text-sm">{inviteMessage}</div>
          )}
        </section>
      </main>
    </div>
  );
}
