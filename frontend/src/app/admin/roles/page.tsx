'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { Loader2, AlertCircle, RefreshCw } from 'lucide-react';
import { getRoles, updateRolePermissions } from '@/lib/api/admin';
import {
  RolePermission,
  PermissionKey,
  PERMISSION_LABELS,
  mapApiRolePermissionToRolePermission,
  mapPermissionsToApiFormat,
  mapRoleToApiRole,
} from '@/lib/utils/adminMapper';

export default function AdminRolesPage() {
  const [roles, setRoles] = useState<RolePermission[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState('');
  const [isSaving, setIsSaving] = useState<string | null>(null);

  const permissionKeys = useMemo(() => Object.keys(PERMISSION_LABELS) as PermissionKey[], []);

  // Fetch roles from API
  const fetchRoles = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await getRoles();
      if (response.error) {
        setError(response.error);
        setRoles([]);
      } else if (response.data) {
        const mappedRoles = response.data.roles.map(mapApiRolePermissionToRolePermission);
        setRoles(mappedRoles);
      }
    } catch (err) {
      console.error('Failed to fetch roles:', err);
      setError('권한 목록을 불러오는데 실패했습니다.');
      setRoles([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Load roles on mount
  useEffect(() => {
    fetchRoles();
  }, [fetchRoles]);

  const handleToggle = async (roleId: string, key: PermissionKey) => {
    const role = roles.find((r) => r.id === roleId);
    if (!role) return;

    // Optimistic update
    const newPermissions = { ...role.permissions, [key]: !role.permissions[key] };
    setRoles((prev) =>
      prev.map((r) =>
        r.id === roleId ? { ...r, permissions: newPermissions } : r
      )
    );

    setIsSaving(roleId);
    try {
      const apiPermissions = mapPermissionsToApiFormat(newPermissions);
      const apiRole = mapRoleToApiRole(role.role);
      const response = await updateRolePermissions(apiRole, apiPermissions);

      if (response.error) {
        // Revert on error
        setRoles((prev) =>
          prev.map((r) =>
            r.id === roleId ? { ...r, permissions: role.permissions } : r
          )
        );
        setError(response.error);
      } else {
        setSaveMessage('권한 설정이 저장되었습니다.');
        setTimeout(() => setSaveMessage(''), 3000);
      }
    } catch (err) {
      console.error('Failed to update permissions:', err);
      // Revert on error
      setRoles((prev) =>
        prev.map((r) =>
          r.id === roleId ? { ...r, permissions: role.permissions } : r
        )
      );
      setError('권한 수정에 실패했습니다.');
    } finally {
      setIsSaving(null);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-6 py-5 flex items-center justify-between">
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide">Admin</p>
            <h1 className="text-2xl font-bold text-secondary">권한 설정</h1>
            <p className="text-sm text-neutral-600 mt-1">역할별 권한 매트릭스를 통해 Admin, Attorney, Staff 권한을 관리합니다.</p>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 space-y-4">
        <section aria-label="역할별 권한 매트릭스" className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-gray-900">역할별 권한 매트릭스</h2>
            <p className="text-sm text-neutral-600 mt-1">각 역할별로 사건 접근 및 관리자 기능 권한을 세밀하게 제어합니다.</p>
          </div>

          {error && !isLoading && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start space-x-3 mb-4">
              <AlertCircle className="w-5 h-5 text-red-500 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-red-700">{error}</p>
                <button
                  onClick={fetchRoles}
                  className="text-sm text-red-600 hover:text-red-800 underline mt-1"
                >
                  다시 시도
                </button>
              </div>
            </div>
          )}

          {isLoading && (
            <div className="flex items-center justify-center py-4 text-sm text-neutral-600">
              <Loader2 className="w-4 h-4 mr-2 animate-spin text-accent" />
              권한 정보를 불러오는 중입니다...
            </div>
          )}

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 border border-gray-100 rounded-lg bg-white text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-semibold text-neutral-600 uppercase tracking-wider">역할</th>
                  {permissionKeys.map((key) => (
                    <th key={key} scope="col" className="px-4 py-3 text-center text-xs font-semibold text-neutral-600 uppercase tracking-wider">{PERMISSION_LABELS[key]}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-100">
                {roles.map((role) => (
                  <tr key={role.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">{role.label}</td>
                    {permissionKeys.map((key) => (
                      <td key={key} className="px-4 py-3 text-center">
                        <input
                          type="checkbox"
                          aria-label={`${role.label} ${PERMISSION_LABELS[key]}`}
                          className="h-4 w-4 text-accent focus:ring-accent border-gray-300 rounded disabled:opacity-50"
                          checked={role.permissions[key]}
                          disabled={isSaving === role.id || isLoading}
                          onChange={() => handleToggle(role.id, key)}
                        />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>

            {!isLoading && roles.length === 0 && !error && (
              <p className="text-center text-sm text-neutral-500 py-4">표시할 권한 정보가 없습니다.</p>
            )}
          </div>

          {saveMessage && <div className="mt-4 rounded-md bg-accent/10 text-secondary px-4 py-3 text-sm">{saveMessage}</div>}
        </section>
      </main>
    </div>
  );
}
