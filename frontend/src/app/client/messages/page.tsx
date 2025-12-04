/**
 * Client Messages Page
 * 003-role-based-ui Feature - US6
 *
 * Messaging interface for clients to communicate with their assigned lawyer.
 */

'use client';

import { Suspense } from 'react';
import { MessagesPageContent } from '@/components/messages';
import { useRole } from '@/hooks/useRole';

function ClientMessagesPageContent() {
  const { user, isAuthenticated } = useRole();

  if (!isAuthenticated || !user) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-8rem)]">
        <p className="text-gray-500">로그인이 필요합니다.</p>
      </div>
    );
  }

  return (
    <MessagesPageContent
      portalType="client"
      currentUserId={user.id}
    />
  );
}

export default function ClientMessagesPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center h-[calc(100vh-8rem)]">
          <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
        </div>
      }
    >
      <ClientMessagesPageContent />
    </Suspense>
  );
}
