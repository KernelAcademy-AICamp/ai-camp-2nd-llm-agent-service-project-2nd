'use client';

import React, { useState } from 'react';
import { Modal, Button, Input } from '@/components/primitives';

interface AddCaseModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const AddCaseModal: React.FC<AddCaseModalProps> = ({ isOpen, onClose }) => {
  const [title, setTitle] = useState('');
  const [clientName, setClientName] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      // TODO: API 호출로 사건 등록
      onClose();
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    // Reset form on close
    setTitle('');
    setClientName('');
    setDescription('');
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="새로운 사건 정보"
      size="md"
      footer={
        <>
          <Button variant="ghost" onClick={handleClose}>
            취소
          </Button>
          <Button
            type="submit"
            form="add-case-form"
            variant="primary"
            isLoading={isSubmitting}
          >
            등록
          </Button>
        </>
      }
    >
      <form id="add-case-form" onSubmit={handleSubmit} className="space-y-4">
        <Input
          id="case-title"
          label="사건명"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="예: 김철수 이혼 소송"
          required
        />

        <Input
          id="client-name"
          label="의뢰인 이름"
          value={clientName}
          onChange={(e) => setClientName(e.target.value)}
          placeholder="예: 김철수"
          required
        />

        <div>
          <label
            htmlFor="case-description"
            className="block text-sm font-medium text-neutral-700 mb-1.5"
          >
            사건 설명
          </label>
          <textarea
            id="case-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={4}
            className="w-full px-3 py-2 border border-neutral-300 rounded-lg shadow-sm
                       focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary
                       placeholder:text-neutral-400 transition-colors duration-200"
            placeholder="사건에 대한 간단한 설명을 입력하세요"
          />
        </div>
      </form>
    </Modal>
  );
};

export default AddCaseModal;
