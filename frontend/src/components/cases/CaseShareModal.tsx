import { useMemo, useState } from 'react';

type PermissionLevel = 'read' | 'read_write';

type TeamMember = {
  id: string;
  name: string;
  email: string;
  role: string;
};

const TEAM_MEMBERS: TeamMember[] = [
  { id: 'member-1', name: '홍길동', email: 'hong@example.com', role: 'Attorney' },
  { id: 'member-2', name: '이영희', email: 'lee@example.com', role: 'Paralegal' },
  { id: 'member-3', name: '박민수', email: 'park@example.com', role: 'Staff' },
];

interface CaseShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  caseTitle?: string;
}

export default function CaseShareModal({ isOpen, onClose, caseTitle }: CaseShareModalProps) {
  const [search, setSearch] = useState('');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [permissions, setPermissions] = useState<Record<string, PermissionLevel>>(() =>
    TEAM_MEMBERS.reduce<Record<string, PermissionLevel>>((acc, member) => {
      acc[member.id] = 'read';
      return acc;
    }, {}),
  );
  const [shareMessage, setShareMessage] = useState('');

  const filteredMembers = useMemo(() => {
    const keyword = search.trim().toLowerCase();
    if (!keyword) return TEAM_MEMBERS;
    return TEAM_MEMBERS.filter(
      (member) =>
        member.name.toLowerCase().includes(keyword) ||
        member.email.toLowerCase().includes(keyword),
    );
  }, [search]);

  if (!isOpen) {
    return null;
  }

  const toggleSelect = (memberId: string) => {
    setSelectedIds((prev) =>
      prev.includes(memberId) ? prev.filter((id) => id !== memberId) : [...prev, memberId],
    );
  };

  const handlePermissionChange = (memberId: string, level: PermissionLevel) => {
    setPermissions((prev) => ({
      ...prev,
      [memberId]: level,
    }));
  };

  const handleShare = (event: React.FormEvent) => {
    event.preventDefault();
    if (selectedIds.length === 0) {
      return;
    }
    setShareMessage('케이스가 선택한 팀원과 공유되었습니다.');
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      role="dialog"
      aria-modal="true"
      aria-label="케이스 공유 모달"
    >
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6">
        <header className="mb-4">
          <h2 className="text-xl font-bold text-deep-trust-blue">
            케이스 공유
          </h2>
          <p className="mt-1 text-sm text-gray-600">
            {caseTitle
              ? `${caseTitle}를 팀원과 공유할 권한을 설정합니다.`
              : '선택한 케이스를 함께 볼 팀원과 권한을 설정합니다.'}
          </p>
        </header>

        <form className="space-y-4" onSubmit={handleShare}>
          <div className="flex items-center gap-2">
            <input
              type="search"
              placeholder="팀원 검색"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-accent focus:border-accent bg-white"
            />
          </div>

          <div className="max-h-64 overflow-y-auto border border-gray-100 rounded-lg">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    팀원
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    역할
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    권한
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredMembers.map((member) => {
                  const isSelected = selectedIds.includes(member.id);
                  const permissionId = `permission-${member.id}`;
                  return (
                    <tr key={member.id} className="hover:bg-gray-50">
                      <td className="px-3 py-2">
                        <div className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            aria-label={`${member.name} 선택`}
                            className="h-4 w-4 text-accent focus:ring-accent border-gray-300 rounded"
                            checked={isSelected}
                            onChange={() => toggleSelect(member.id)}
                          />
                          <div>
                            <div className="font-medium text-gray-900">
                              {member.name}
                            </div>
                            <div className="text-xs text-gray-500">
                              {member.email}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-3 py-2 text-gray-700">
                        {member.role}
                      </td>
                      <td className="px-3 py-2">
                        <label
                          htmlFor={permissionId}
                          className="block text-xs font-medium text-gray-700 mb-1"
                        >
                          {member.name} 권한
                        </label>
                        <select
                          id={permissionId}
                          value={permissions[member.id]}
                          onChange={(event) =>
                            handlePermissionChange(
                              member.id,
                              event.target.value as PermissionLevel,
                            )
                          }
                          className="mt-1 block w-full rounded-md border border-gray-300 py-1.5 px-2 text-xs shadow-sm focus:border-accent focus:ring-accent"
                        >
                          <option value="read">읽기</option>
                          <option value="read_write">읽기/쓰기</option>
                        </select>
                      </td>
                    </tr>
                  );
                })}
                {filteredMembers.length === 0 && (
                  <tr>
                    <td
                      colSpan={3}
                      className="px-3 py-4 text-center text-sm text-gray-500"
                    >
                      조건에 맞는 팀원이 없습니다.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              className="px-4 py-2 text-sm text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
              onClick={onClose}
            >
              취소
            </button>
            <button
              type="submit"
              className="btn-primary text-sm px-4 py-2 disabled:opacity-60 disabled:cursor-not-allowed"
              disabled={selectedIds.length === 0}
            >
              공유하기
            </button>
          </div>

          {shareMessage && (
            <div className="mt-3 rounded-md bg-accent/10 text-deep-trust-blue px-4 py-3 text-sm">
              {shareMessage}
            </div>
          )}
        </form>
      </div>
    </div>
  );
}

