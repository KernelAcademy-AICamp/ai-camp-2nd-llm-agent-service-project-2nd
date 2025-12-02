'use client';

import { useMemo, useState } from 'react';
import { Modal, Button, Input } from '@/components/primitives';
import { Search } from 'lucide-react';

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
    }, {})
  );
  const [shareMessage, setShareMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const filteredMembers = useMemo(() => {
    const keyword = search.trim().toLowerCase();
    if (!keyword) return TEAM_MEMBERS;
    return TEAM_MEMBERS.filter(
      (member) =>
        member.name.toLowerCase().includes(keyword) ||
        member.email.toLowerCase().includes(keyword)
    );
  }, [search]);

  const toggleSelect = (memberId: string) => {
    setSelectedIds((prev) =>
      prev.includes(memberId)
        ? prev.filter((id) => id !== memberId)
        : [...prev, memberId]
    );
  };

  const handlePermissionChange = (memberId: string, level: PermissionLevel) => {
    setPermissions((prev) => ({
      ...prev,
      [memberId]: level,
    }));
  };

  const handleShare = async (event: React.FormEvent) => {
    event.preventDefault();
    if (selectedIds.length === 0) {
      return;
    }
    setIsSubmitting(true);
    try {
      // FUTURE: Implement case sharing API (backend endpoint needed)
      // Planned: POST /cases/{caseId}/share with { userIds, permissions }
      setShareMessage('케이스가 선택한 팀원과 공유되었습니다.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setShareMessage('');
    setSearch('');
    setSelectedIds([]);
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="케이스 공유"
      description={
        caseTitle
          ? `${caseTitle}를 팀원과 공유할 권한을 설정합니다.`
          : '선택한 케이스를 함께 볼 팀원과 권한을 설정합니다.'
      }
      size="lg"
      footer={
        <>
          <Button variant="ghost" onClick={handleClose}>
            취소
          </Button>
          <Button
            type="submit"
            form="share-form"
            variant="primary"
            isLoading={isSubmitting}
            disabled={selectedIds.length === 0}
          >
            공유하기
          </Button>
        </>
      }
    >
      <form id="share-form" className="space-y-4" onSubmit={handleShare}>
        <Input
          type="search"
          placeholder="팀원 검색"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          leftIcon={<Search className="w-4 h-4" />}
        />

        <div className="max-h-64 overflow-y-auto border border-neutral-100 rounded-lg">
          <table className="min-w-full text-sm">
            <thead className="bg-neutral-50 sticky top-0">
              <tr>
                <th
                  scope="col"
                  className="px-3 py-2 text-left text-xs font-semibold text-neutral-600 uppercase tracking-wider"
                >
                  팀원
                </th>
                <th
                  scope="col"
                  className="px-3 py-2 text-left text-xs font-semibold text-neutral-600 uppercase tracking-wider"
                >
                  역할
                </th>
                <th
                  scope="col"
                  className="px-3 py-2 text-left text-xs font-semibold text-neutral-600 uppercase tracking-wider"
                >
                  권한
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {filteredMembers.map((member) => {
                const isSelected = selectedIds.includes(member.id);
                const permissionId = `permission-${member.id}`;
                const checkboxId = `select-${member.id}`;
                return (
                  <tr key={member.id} className="hover:bg-neutral-50">
                    <td className="px-3 py-2">
                      <div className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          id={checkboxId}
                          aria-label={`${member.name} 선택`}
                          className="h-4 w-4 text-primary focus:ring-primary border-neutral-300 rounded
                                     cursor-pointer"
                          checked={isSelected}
                          onChange={() => toggleSelect(member.id)}
                        />
                        <label htmlFor={checkboxId} className="cursor-pointer">
                          <div className="font-medium text-neutral-900">
                            {member.name}
                          </div>
                          <div className="text-xs text-neutral-500">
                            {member.email}
                          </div>
                        </label>
                      </div>
                    </td>
                    <td className="px-3 py-2 text-neutral-700">{member.role}</td>
                    <td className="px-3 py-2">
                      <label htmlFor={permissionId} className="sr-only">
                        {member.name} 권한
                      </label>
                      <select
                        id={permissionId}
                        value={permissions[member.id]}
                        onChange={(event) =>
                          handlePermissionChange(
                            member.id,
                            event.target.value as PermissionLevel
                          )
                        }
                        className="block w-full rounded-md border border-neutral-300 py-1.5 px-2 text-xs
                                   focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary
                                   transition-colors duration-200"
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
                    className="px-3 py-4 text-center text-sm text-neutral-500"
                  >
                    조건에 맞는 팀원이 없습니다.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {shareMessage && (
          <div
            className="rounded-lg bg-primary-light text-secondary px-4 py-3 text-sm"
            role="status"
          >
            {shareMessage}
          </div>
        )}
      </form>
    </Modal>
  );
}
