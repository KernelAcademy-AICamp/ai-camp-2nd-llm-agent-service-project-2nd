// src/components/cases/AddCaseModal.tsx
import React, { useState } from 'react';
import { X } from 'lucide-react';

interface AddCaseModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const AddCaseModal: React.FC<AddCaseModalProps> = ({ isOpen, onClose }) => {
  const [title, setTitle] = useState('');
  const [clientName, setClientName] = useState('');
  const [description, setDescription] = useState('');

  if (!isOpen) {
    return null;
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: API 호출로 사건 등록
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-800" id="modal-title">새로운 사건 정보</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
            aria-label="Close modal"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="case-title" className="block text-sm font-medium text-gray-700 mb-1">
              사건명
            </label>
            <input
              type="text"
              id="case-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="예: 김철수 이혼 소송"
            />
          </div>

          <div className="mb-4">
            <label htmlFor="client-name" className="block text-sm font-medium text-gray-700 mb-1">
              의뢰인 이름
            </label>
            <input
              type="text"
              id="client-name"
              value={clientName}
              onChange={(e) => setClientName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="예: 김철수"
            />
          </div>

          <div className="mb-6">
            <label htmlFor="case-description" className="block text-sm font-medium text-gray-700 mb-1">
              사건 설명
            </label>
            <textarea
              id="case-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="사건에 대한 간단한 설명을 입력하세요"
            />
          </div>

          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
            >
              취소
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              등록
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddCaseModal;
