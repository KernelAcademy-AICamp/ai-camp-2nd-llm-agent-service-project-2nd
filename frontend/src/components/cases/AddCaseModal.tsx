'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Modal, Button } from '@/components/primitives';
import { createCase } from '@/lib/api/cases';

interface AddCaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

const AddCaseModal: React.FC<AddCaseModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const formRef = useRef<HTMLFormElement>(null);

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen && formRef.current) {
      formRef.current.reset();
    }
  }, [isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    const formData = new FormData(formRef.current!);
    const title = formData.get('title') as string;
    const clientName = formData.get('clientName') as string;
    const description = formData.get('description') as string;

    try {
      const response = await createCase({
        title,
        client_name: clientName,
        description: description || undefined,
      });

      if (response.error) {
        alert(`사건 등록 실패: ${response.error}`);
        return;
      }

      // 성공 시 폼 초기화 및 콜백 호출
      formRef.current?.reset();
      onSuccess?.();
      onClose();
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    formRef.current?.reset();
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
      <form ref={formRef} id="add-case-form" onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label
            htmlFor="case-title"
            className="block text-sm font-medium text-neutral-700 mb-1.5"
          >
            사건명 <span className="text-red-500">*</span>
          </label>
          <input
            id="case-title"
            name="title"
            type="text"
            placeholder="예: 김철수 이혼 소송"
            required
            className="w-full h-11 px-3 text-base block rounded-lg border bg-white text-neutral-900
                       border-neutral-300 hover:border-neutral-400
                       focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary
                       placeholder:text-neutral-400 transition-colors duration-200"
          />
        </div>

        <div>
          <label
            htmlFor="client-name"
            className="block text-sm font-medium text-neutral-700 mb-1.5"
          >
            의뢰인 이름 <span className="text-red-500">*</span>
          </label>
          <input
            id="client-name"
            name="clientName"
            type="text"
            placeholder="예: 김철수"
            required
            className="w-full h-11 px-3 text-base block rounded-lg border bg-white text-neutral-900
                       border-neutral-300 hover:border-neutral-400
                       focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary
                       placeholder:text-neutral-400 transition-colors duration-200"
          />
        </div>

        <div>
          <label
            htmlFor="case-description"
            className="block text-sm font-medium text-neutral-700 mb-1.5"
          >
            사건 설명
          </label>
          <textarea
            id="case-description"
            name="description"
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
