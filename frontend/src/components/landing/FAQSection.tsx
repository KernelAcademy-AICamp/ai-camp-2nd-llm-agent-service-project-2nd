/**
 * FAQSection Component
 * Plan 3.19.1 - FAQ (우려 해소)
 *
 * Features:
 * - Section title: "자주 묻는 질문"
 * - Accordion format with 5 FAQ items
 * - Expandable/collapsible answers
 * - Chevron icon rotation on expand
 * - Concise answers (2-3 sentences)
 */

'use client';

import { useState } from 'react';
import { ChevronDown } from 'lucide-react';

export default function FAQSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  const faqs = [
    {
      id: 1,
      question: 'AI가 생성한 초안은 법적 효력이 있나요?',
      answer:
        'AI는 초안 작성을 보조하는 도구입니다. 최종 검토와 수정은 반드시 변호사님께서 직접 진행하셔야 하며, 법적 책임은 변호사님께 있습니다.',
    },
    {
      id: 2,
      question: '개인정보는 안전하게 보호되나요?',
      answer:
        '모든 데이터는 AES-256 암호화로 보호되며, PIPA(개인정보보호법)를 준수합니다. ISO 27001 인증 준비 중이며, 증거 데이터는 AWS 인프라 내에서만 처리됩니다.',
    },
    {
      id: 3,
      question: '기존 시스템과 연동 가능한가요?',
      answer:
        'Enterprise 플랜에서 REST API 연동을 지원합니다. 기존 케이스 관리 시스템과 연동하여 증거 자동 동기화가 가능하며, 상세한 API 문서를 제공해 드립니다.',
    },
    {
      id: 4,
      question: '환불 정책은 어떻게 되나요?',
      answer:
        '14일 무료 체험 기간 동안 언제든 해지 가능합니다. 유료 구독 후에도 30일 이내 환불 요청 시 전액 환불해 드립니다.',
    },
    {
      id: 5,
      question: '어떤 파일 형식을 지원하나요?',
      answer:
        '이미지(JPG, PNG), 음성(MP3, WAV), 영상(MP4, AVI), 문서(PDF, TXT, CSV) 형식을 지원합니다. 카카오톡 대화 내보내기(TXT) 파일도 자동으로 인식합니다.',
    },
  ];

  const toggleFAQ = (index: number) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <section
      className="py-20 px-6 bg-white"
      aria-label="자주 묻는 질문"
    >
      <div className="max-w-3xl mx-auto">
        <div className="space-y-8">
          {/* Section Title */}
          <h2 className="text-4xl font-bold text-deep-trust-blue text-center">
            자주 묻는 질문
          </h2>

          {/* FAQ Accordion */}
          <div className="divide-y divide-gray-200">
            {faqs.map((faq, index) => (
              <div key={faq.id} className="py-6">
                {/* Question Button */}
                <button
                  onClick={() => toggleFAQ(index)}
                  className="w-full flex justify-between items-center text-left"
                  aria-expanded={openIndex === index}
                >
                  <h3 className="text-lg font-semibold text-deep-trust-blue pr-8">
                    {faq.question}
                  </h3>
                  <ChevronDown
                    className={`w-5 h-5 text-accent flex-shrink-0 transition-transform ${
                      openIndex === index ? 'rotate-180' : ''
                    }`}
                    aria-label="펼치기 아이콘"
                  />
                </button>

                {/* Answer */}
                <div
                  className={`overflow-hidden transition-all duration-300 ${
                    openIndex === index ? 'max-h-96 mt-4' : 'max-h-0'
                  }`}
                >
                  <p className="text-gray-600 leading-relaxed">
                    {faq.answer}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
