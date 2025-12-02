'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { Loader2, AlertCircle, RefreshCw } from 'lucide-react';
import { getAdminUsers, deleteUser as deleteUserApi } from '@/lib/api/admin';
import { mapApiAdminUsersToAdminUsers, AdminUser } from '@/lib/utils/adminMapper';

export default function AdminUsersPage() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [inviteMessage, setInviteMessage] = useState('');
  const [isDeleting, setIsDeleting] = useState<string | null>(null);

  // Fetch users from API
  const fetchUsers = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await getAdminUsers();
      if (response.error) {
        setError(response.error);
        setUsers([]);
      } else if (response.data) {
        const mappedUsers = mapApiAdminUsersToAdminUsers(response.data.users);
        setUsers(mappedUsers);
      }
    } catch (err) {
      console.error('Failed to fetch users:', err);
      setError('사용자 목록을 불러오는데 실패했습니다.');
      setUsers([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Load users on mount
  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const filteredUsers = useMemo(() => {
    const keyword = search.trim().toLowerCase();
    if (!keyword) return users;
    return users.filter(
      (user) =>
        user.name.toLowerCase().includes(keyword) ||
        user.email.toLowerCase().includes(keyword),
    );
  }, [search, users]);

  const handleDeleteUser = async (userId: string) => {
    setIsDeleting(userId);
    try {
      const response = await deleteUserApi(userId);
      if (response.error) {
        setError(response.error);
      } else {
        // Remove from local state after successful API call
        setUsers((prev) => prev.filter((user) => user.id !== userId));
        setInviteMessage('사용자가 삭제되었습니다.');
        setTimeout(() => setInviteMessage(''), 3000);
      }
    } catch (err) {
      console.error('Failed to delete user:', err);
      setError('사용자 삭제에 실패했습니다.');
    } finally {
      setIsDeleting(null);
    }
  };

  const handleInvite = () => {
    // FUTURE: Implement invite modal with email input (POST /admin/users/invite)
    setInviteMessage('초대 기능은 준비 중입니다.');
    setTimeout(() => setInviteMessage(''), 3000);
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
              <button
                type="button"
                onClick={fetchUsers}
                disabled={isLoading}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm bg-white hover:bg-gray-50 disabled:opacity-50"
                aria-label="새로고침"
              >
                <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              </button>
              <button type="button" className="btn-primary text-sm px-4 py-2" onClick={handleInvite}>
                사용자 초대
              </button>
            </div>
          </div>

          {/* Loading State */}
          {isLoading && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 text-accent animate-spin" />
              <span className="ml-2 text-gray-500">사용자 목록을 불러오는 중...</span>
            </div>
          )}

          {/* Error State */}
          {error && !isLoading && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start space-x-3 mb-4">
              <AlertCircle className="w-5 h-5 text-red-500 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-red-700">{error}</p>
                <button
                  onClick={fetchUsers}
                  className="text-sm text-red-600 hover:text-red-800 underline mt-1"
                >
                  다시 시도
                </button>
              </div>
            </div>
          )}

          {/* Table */}
          {!isLoading && <div className="overflow-x-auto">
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
                        disabled={isDeleting === user.id}
                        className="btn-danger text-xs px-3 py-1.5 disabled:opacity-50 inline-flex items-center"
                        aria-label={`${user.name} 삭제`}
                      >
                        {isDeleting === user.id && <Loader2 className="w-3 h-3 mr-1 animate-spin" />}
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
          </div>}

          {inviteMessage && (
            <div className="mt-4 rounded-md bg-accent/10 text-secondary px-4 py-3 text-sm">{inviteMessage}</div>
          )}
        </section>
      </main>
    </div>
  );
}
