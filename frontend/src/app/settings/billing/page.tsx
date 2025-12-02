'use client';

import React, { useState } from 'react';
import {
  CreditCard,
  Calendar,
  TrendingUp,
  Database,
  Download,
  ChevronRight,
  AlertCircle,
  CheckCircle2,
  X
} from 'lucide-react';

interface SubscriptionPlan {
  name: string;
  price: number;
  billingCycle: 'monthly' | 'yearly';
  nextBillingDate: string;
}

interface PaymentMethod {
  type: string;
  last4: string;
  expiryDate: string;
}

interface UsageMetric {
  used: number;
  limit: number;
  unit: string;
}

interface BillingHistory {
  id: string;
  date: string;
  amount: number;
  status: 'paid' | 'pending' | 'failed';
  invoiceUrl: string;
}

export default function BillingPage() {
  const [currentPlan] = useState<SubscriptionPlan>({
    name: 'Professional',
    price: 99000,
    billingCycle: 'monthly',
    nextBillingDate: '2025-12-24'
  });

  const [paymentMethod] = useState<PaymentMethod>({
    type: 'Visa',
    last4: '4242',
    expiryDate: '12/25'
  });

  const [aiTokenUsage] = useState<UsageMetric>({
    used: 75000,
    limit: 100000,
    unit: 'tokens'
  });

  const [storageUsage] = useState<UsageMetric>({
    used: 4.2,
    limit: 10,
    unit: 'GB'
  });

  const [billingHistory] = useState<BillingHistory[]>([
    { id: 'INV-2025-001', date: '2025-11-24', amount: 99000, status: 'paid', invoiceUrl: '/invoices/INV-2025-001.pdf' },
    { id: 'INV-2025-002', date: '2025-10-24', amount: 99000, status: 'paid', invoiceUrl: '/invoices/INV-2025-002.pdf' }
  ]);

  const [isPlanChangeModalOpen, setIsPlanChangeModalOpen] = useState(false);
  const [selectedPlanChange, setSelectedPlanChange] = useState<'upgrade' | 'downgrade' | null>(null);

  const aiTokenPercentage = (aiTokenUsage.used / aiTokenUsage.limit) * 100;
  const storagePercentage = (storageUsage.used / storageUsage.limit) * 100;
  const isAiTokenWarning = aiTokenPercentage >= 80;
  const isStorageWarning = storagePercentage >= 80;

  const handlePlanChange = (type: 'upgrade' | 'downgrade') => {
    setSelectedPlanChange(type);
    setIsPlanChangeModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsPlanChangeModalOpen(false);
    setSelectedPlanChange(null);
  };

  const handleConfirmPlanChange = () => {
    handleCloseModal();
  };

  const handleDownloadInvoice = (invoiceUrl: string) => {
    // FUTURE: Invoice download API (GET /billing/invoices/{id}/download)
    window.open(invoiceUrl, '_blank');
  };

  const handleUpdatePaymentMethod = () => {
    // FUTURE: Payment method update modal (requires payment gateway integration)
  };

  return (
    <div className="min-h-screen bg-neutral-50 p-8">
      <nav aria-label="Breadcrumb" className="mb-6">
        <ol className="flex items-center space-x-2 text-sm">
          <li><a href="/settings" className="text-neutral-600 hover:text-secondary">Settings</a></li>
          <ChevronRight className="w-4 h-4 text-gray-400" />
          <li><span className="text-secondary font-semibold">Billing</span></li>
        </ol>
      </nav>

      <div className="mb-8">
        <h1 className="text-3xl font-bold text-secondary">빌링 및 구독 관리</h1>
        <p className="text-neutral-600 mt-2">구독 플랜, 결제 수단, 사용량을 관리합니다</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <section className="bg-neutral-50 border border-gray-200 rounded-lg p-6 shadow-sm" aria-labelledby="current-plan-title">
          <h2 id="current-plan-title" className="text-xl font-semibold text-secondary mb-4">현재 구독 플랜</h2>
          <div className="space-y-4">
            <div>
              <p className="text-sm text-neutral-600">플랜 이름</p>
              <p className="text-2xl font-bold text-secondary mt-1">{currentPlan.name}</p>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-neutral-600">월 요금</p>
                <p className="text-xl font-semibold text-secondary mt-1">₩{currentPlan.price.toLocaleString()}</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-neutral-600">다음 결제일</p>
                <div className="flex items-center mt-1">
                  <Calendar className="w-4 h-4 text-accent mr-1" />
                  <p className="text-sm font-medium text-secondary">{currentPlan.nextBillingDate}</p>
                </div>
              </div>
            </div>
            <div className="flex space-x-3 pt-4 border-t border-gray-200">
              <button onClick={() => handlePlanChange('upgrade')} className="flex-1 px-4 py-2 bg-accent text-white rounded-md hover:bg-accent-dark transition-colors" aria-label="Upgrade plan">업그레이드</button>
              <button onClick={() => handlePlanChange('downgrade')} className="flex-1 px-4 py-2 bg-gray-200 text-neutral-700 rounded-md hover:bg-gray-300 transition-colors" aria-label="Downgrade plan">다운그레이드</button>
            </div>
          </div>
        </section>

        <section className="bg-neutral-50 border border-gray-200 rounded-lg p-6 shadow-sm" aria-labelledby="payment-method-title">
          <h2 id="payment-method-title" className="text-xl font-semibold text-secondary mb-4">결제 수단</h2>
          <div className="space-y-4">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-deep-trust-blue rounded-lg flex items-center justify-center">
                <CreditCard className="w-6 h-6 text-white" />
              </div>
              <div className="flex-1">
                <p className="text-sm text-neutral-600">카드 유형</p>
                <p className="text-lg font-semibold text-secondary">{paymentMethod.type} •••• {paymentMethod.last4}</p>
              </div>
            </div>
            <div>
              <p className="text-sm text-neutral-600">만료일</p>
              <p className="text-sm font-medium text-secondary mt-1">{paymentMethod.expiryDate}</p>
            </div>
            <button onClick={handleUpdatePaymentMethod} className="w-full px-4 py-2 bg-white border border-gray-300 text-secondary rounded-md hover:bg-gray-50 transition-colors mt-4" aria-label="Update payment method">결제 수단 변경</button>
          </div>
        </section>
      </div>

      <section className="bg-neutral-50 border border-gray-200 rounded-lg p-6 shadow-sm mb-8" aria-labelledby="usage-metering-title">
        <h2 id="usage-metering-title" className="text-xl font-semibold text-secondary mb-6">사용량 현황</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div aria-labelledby="ai-token-usage-label">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center">
                <TrendingUp className="w-5 h-5 text-accent mr-2" />
                <h3 id="ai-token-usage-label" className="text-lg font-semibold text-secondary">AI 토큰 사용량</h3>
              </div>
              {isAiTokenWarning && (
                <div className="flex items-center text-semantic-error">
                  <AlertCircle className="w-4 h-4 mr-1" />
                  <span className="text-sm font-medium">한도 임박</span>
                </div>
              )}
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-neutral-600">{aiTokenUsage.used.toLocaleString()} / {aiTokenUsage.limit.toLocaleString()} {aiTokenUsage.unit}</span>
                <span className="font-semibold text-secondary">{aiTokenPercentage.toFixed(1)}%</span>
              </div>
              <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden" role="progressbar" aria-valuenow={aiTokenPercentage} aria-valuemin={0} aria-valuemax={100} aria-label={`AI token usage: ${aiTokenPercentage.toFixed(1)}%`}>
                <div className={`h-full transition-all duration-300 ${isAiTokenWarning ? 'bg-semantic-error' : 'bg-success-green'}`} style={{ width: `${aiTokenPercentage}%` }} />
              </div>
            </div>
          </div>

          <div aria-labelledby="storage-usage-label">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center">
                <Database className="w-5 h-5 text-accent mr-2" />
                <h3 id="storage-usage-label" className="text-lg font-semibold text-secondary">스토리지 사용량</h3>
              </div>
              {isStorageWarning && (
                <div className="flex items-center text-semantic-error">
                  <AlertCircle className="w-4 h-4 mr-1" />
                  <span className="text-sm font-medium">한도 임박</span>
                </div>
              )}
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-neutral-600">{storageUsage.used} / {storageUsage.limit} {storageUsage.unit}</span>
                <span className="font-semibold text-secondary">{storagePercentage.toFixed(1)}%</span>
              </div>
              <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden" role="progressbar" aria-valuenow={storagePercentage} aria-valuemin={0} aria-valuemax={100} aria-label={`Storage usage: ${storagePercentage.toFixed(1)}%`}>
                <div className={`h-full transition-all duration-300 ${isStorageWarning ? 'bg-semantic-error' : 'bg-success-green'}`} style={{ width: `${storagePercentage}%` }} />
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="bg-neutral-50 border border-gray-200 rounded-lg p-6 shadow-sm" aria-labelledby="billing-history-title">
        <h2 id="billing-history-title" className="text-xl font-semibold text-secondary mb-6">청구서 내역</h2>
        <div className="overflow-x-auto">
          <table className="w-full" role="table" aria-label="Billing history table">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 text-sm font-semibold text-secondary">청구서 번호</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-secondary">날짜</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-secondary">금액</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-secondary">상태</th>
                <th className="text-left py-3 px-4 text-sm font-semibold text-secondary">작업</th>
              </tr>
            </thead>
            <tbody>
              {billingHistory.map((invoice) => (
                <tr key={invoice.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-4 text-sm text-neutral-700">{invoice.id}</td>
                  <td className="py-3 px-4 text-sm text-neutral-700">{invoice.date}</td>
                  <td className="py-3 px-4 text-sm font-medium text-secondary">₩{invoice.amount.toLocaleString()}</td>
                  <td className="py-3 px-4">
                    {invoice.status === 'paid' ? (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-success-green">
                        <CheckCircle2 className="w-3 h-3 mr-1" />결제 완료
                      </span>
                    ) : invoice.status === 'pending' ? (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">대기 중</span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-semantic-error">실패</span>
                    )}
                  </td>
                  <td className="py-3 px-4">
                    <button onClick={() => handleDownloadInvoice(invoice.invoiceUrl)} className="inline-flex items-center text-sm text-accent hover:text-accent-dark transition-colors" aria-label={`Download invoice ${invoice.id}`}>
                      <Download className="w-4 h-4 mr-1" />다운로드
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {isPlanChangeModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" role="dialog" aria-modal="true" aria-labelledby="plan-change-modal-title">
          <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4 shadow-xl">
            <div className="flex items-center justify-between mb-6">
              <h3 id="plan-change-modal-title" className="text-2xl font-bold text-secondary">
                {selectedPlanChange === 'upgrade' ? '플랜 업그레이드' : '플랜 다운그레이드'}
              </h3>
              <button onClick={handleCloseModal} className="text-gray-400 hover:text-neutral-600" aria-label="Close modal">
                <X className="w-6 h-6" />
              </button>
            </div>
            <div className="mb-6">
              <p className="text-neutral-600 mb-4">
                {selectedPlanChange === 'upgrade' ? 'Enterprise 플랜으로 업그레이드하시겠습니까?' : 'Basic 플랜으로 다운그레이드하시겠습니까?'}
              </p>
              <div className="bg-neutral-50 p-4 rounded-lg">
                <p className="text-sm text-neutral-600 mb-1">새로운 월 요금</p>
                <p className="text-2xl font-bold text-secondary">₩{selectedPlanChange === 'upgrade' ? '199,000' : '49,000'}</p>
              </div>
            </div>
            <div className="flex space-x-3">
              <button onClick={handleCloseModal} className="flex-1 px-4 py-2 bg-gray-200 text-neutral-700 rounded-md hover:bg-gray-300 transition-colors">취소</button>
              <button onClick={handleConfirmPlanChange} className="flex-1 px-4 py-2 bg-accent text-white rounded-md hover:bg-accent-dark transition-colors" aria-label="Confirm plan change">확인</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
