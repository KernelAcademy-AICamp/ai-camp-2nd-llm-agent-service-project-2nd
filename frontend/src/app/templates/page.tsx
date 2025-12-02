'use client';

import { useMemo, useState } from 'react';
import { Upload, CheckCircle2, Trash2 } from 'lucide-react';

type TemplateItem = {
  id: string;
  name: string;
  updatedAt: string;
  uses: number;
};

const INITIAL_TEMPLATES: TemplateItem[] = [
  { id: 'default', name: '기본 양식', updatedAt: '2024-05-01', uses: 12 },
  { id: 'defense-v1', name: '이혼 소송 답변서 v1', updatedAt: '2024-05-10', uses: 7 },
  { id: 'prep-memo', name: '준비서면 템플릿', updatedAt: '2024-05-12', uses: 4 },
];

export default function TemplateManagerPage() {
  const [templates, setTemplates] = useState<TemplateItem[]>(INITIAL_TEMPLATES);
  const [templateName, setTemplateName] = useState('');
  const [file, setFile] = useState<File | null>(null);

  const isUploadDisabled = useMemo(() => templateName.trim().length === 0 || !file, [templateName, file]);

  const handleUpload = (event: React.FormEvent) => {
    event.preventDefault();
    if (isUploadDisabled || !file) return;

    const newTemplate: TemplateItem = {
      id: `${Date.now()}`,
      name: templateName,
      updatedAt: new Date().toISOString().slice(0, 10),
      uses: 0,
    };
    setTemplates((prev) => [newTemplate, ...prev]);
    setTemplateName('');
    setFile(null);
  };

  const handleDelete = (id: string) => {
    setTemplates((prev) => prev.filter((t) => t.id !== id));
  };

  const handleApply = (id: string) => {
    setTemplates((prev) =>
      prev.map((t) => (t.id === id ? { ...t, uses: t.uses + 1, updatedAt: t.updatedAt } : t)),
    );
  };

  return (
    <div className="min-h-screen bg-neutral-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-6 py-5 flex items-center justify-between">
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide">Template Center</p>
            <h1 className="text-2xl font-bold text-secondary">템플릿 관리</h1>
            <p className="text-sm text-neutral-600 mt-1">변호사 전용 문서 양식을 업로드하고 재사용하세요.</p>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 space-y-8">
        <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <form className="space-y-4" onSubmit={handleUpload}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <label className="flex flex-col text-sm text-neutral-700">
                <span className="font-semibold mb-2">양식 이름</span>
                <input
                  aria-label="양식 이름"
                  type="text"
                  value={templateName}
                  onChange={(e) => setTemplateName(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-accent focus:outline-none"
                  placeholder="예: 이혼 소송 답변서"
                />
              </label>

              <label className="flex flex-col text-sm text-neutral-700">
                <span className="font-semibold mb-2">템플릿 파일</span>
                <input
                  aria-label="템플릿 파일"
                  type="file"
                  accept=".doc,.docx,.hwp,.pdf"
                  onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                  className="w-full px-4 py-2 border border-dashed border-gray-300 rounded-lg bg-gray-50 focus:border-accent focus:ring-1 focus:ring-accent"
                />
              </label>
            </div>

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={isUploadDisabled}
                className="btn-primary inline-flex items-center gap-2 px-5 py-3 text-sm disabled:opacity-60 disabled:cursor-not-allowed"
              >
                <Upload className="w-4 h-4" />
                템플릿 업로드
              </button>
            </div>
          </form>
        </section>

        <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">업로드된 템플릿</h2>
            <p className="text-sm text-gray-500">총 {templates.length}건</p>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200" aria-label="템플릿 목록">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">이름</th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">마지막 업데이트</th>
                  <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">사용 횟수</th>
                  <th scope="col" className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {templates.map((template) => (
                  <tr key={template.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">{template.name}</td>
                    <td className="px-4 py-3 text-sm text-neutral-600">{template.updatedAt}</td>
                    <td className="px-4 py-3 text-sm text-neutral-600">{template.uses}회</td>
                    <td className="px-4 py-3 text-right text-sm text-neutral-600 space-x-2">
                      <button
                        type="button"
                        onClick={() => handleApply(template.id)}
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md border border-accent text-accent hover:bg-accent/10 transition-colors"
                      >
                        <CheckCircle2 className="w-4 h-4" />
                        적용
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDelete(template.id)}
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md border border-error text-error hover:bg-error/10 transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                        삭제
                      </button>
                    </td>
                  </tr>
                ))}
                {templates.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-4 py-6 text-center text-sm text-gray-500">등록된 템플릿이 없습니다.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  );
}
