'use client';

import { useMemo, useState } from 'react';

type AdminRole = 'Admin' | 'Attorney' | 'Staff';
type PermissionKey = 'viewCases' | 'editCases' | 'accessAdmin' | 'manageBilling';

type RolePermission = {
  id: string;
  role: AdminRole;
  label: string;
  permissions: Record<PermissionKey, boolean>;
};

const PERMISSION_LABELS: Record<PermissionKey, string> = {
  viewCases: '사건 보기',
  editCases: '사건 편집',
  accessAdmin: 'Admin 메뉴 접근',
  manageBilling: 'Billing 관리',
};

const MOCK_ROLE_PERMISSIONS: RolePermission[] = [
  { id: 'role-admin', role: 'Admin', label: 'Admin', permissions: { viewCases: true, editCases: true, accessAdmin: true, manageBilling: true } },
  { id: 'role-attorney', role: 'Attorney', label: 'Attorney', permissions: { viewCases: true, editCases: true, accessAdmin: false, manageBilling: false } },
  { id: 'role-staff', role: 'Staff', label: 'Staff', permissions: { viewCases: true, editCases: false, accessAdmin: false, manageBilling: false } },
];

export default function AdminRolesPage() {
  const [roles, setRoles] = useState<RolePermission[]>(MOCK_ROLE_PERMISSIONS);
  const [saveMessage, setSaveMessage] = useState('');

  const permissionKeys = useMemo(() => Object.keys(PERMISSION_LABELS) as PermissionKey[], []);

  const handleToggle = (roleId: string, key: PermissionKey) => {
    setRoles((prev) => prev.map((role) => role.id === roleId ? { ...role, permissions: { ...role.permissions, [key]: !role.permissions[key] } } : role));
    setSaveMessage('권한 설정이 저장되었습니다.');
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
                        <input type="checkbox" aria-label={`${role.label} ${PERMISSION_LABELS[key]}`} className="h-4 w-4 text-accent focus:ring-accent border-gray-300 rounded" checked={role.permissions[key]} onChange={() => handleToggle(role.id, key)} />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {saveMessage && <div className="mt-4 rounded-md bg-accent/10 text-secondary px-4 py-3 text-sm">{saveMessage}</div>}
        </section>
      </main>
    </div>
  );
}
