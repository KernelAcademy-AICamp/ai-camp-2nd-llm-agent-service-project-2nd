/**
 * Messages Page Content Component
 * 003-role-based-ui Feature - US6
 *
 * Shared messaging UI for all portals (lawyer, client, detective).
 * Provides conversation list and message thread views.
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { ConversationList } from './ConversationList';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { useConversations, useMessages, type ConversationSummary } from '@/hooks/useMessages';

interface MessagesPageContentProps {
  portalType: 'lawyer' | 'client' | 'detective';
  currentUserId: string;
}

export function MessagesPageContent({
  portalType,
  currentUserId,
}: MessagesPageContentProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Selected conversation state
  const [selectedConversation, setSelectedConversation] = useState<ConversationSummary | null>(null);
  const [isMobileListView, setIsMobileListView] = useState(true);

  // Fetch conversations
  const {
    conversations,
    totalUnread,
    isLoading: isLoadingConversations,
    error: conversationsError,
    refresh: refreshConversations,
  } = useConversations();

  // Get caseId and recipientId from URL or selected conversation
  const caseId = searchParams?.get('case') || selectedConversation?.case_id || '';
  const recipientId = searchParams?.get('user') || selectedConversation?.other_user.id || '';

  // Fetch messages for selected conversation
  const {
    messages,
    isLoading: isLoadingMessages,
    error: messagesError,
    hasMore,
    isConnected,
    isTyping,
    sendMessage: sendMessageApi,
    loadMore,
    markAsRead,
    sendTypingIndicator,
  } = useMessages({
    caseId,
    recipientId,
  });

  // Computed values for UI compatibility
  const wsStatus = isConnected ? 'connected' : 'disconnected';
  const typingUsers = isTyping ? [recipientId] : [];
  const sendTyping = sendTypingIndicator;

  // Handle conversation selection
  const handleSelectConversation = useCallback(
    (conversation: ConversationSummary) => {
      setSelectedConversation(conversation);
      setIsMobileListView(false);

      // Update URL
      const params = new URLSearchParams();
      params.set('case', conversation.case_id);
      params.set('user', conversation.other_user.id);
      router.replace(`/${portalType}/messages?${params.toString()}`);
    },
    [portalType, router]
  );

  // Handle back button on mobile
  const handleBack = useCallback(() => {
    setIsMobileListView(true);
    setSelectedConversation(null);
    router.replace(`/${portalType}/messages`);
  }, [portalType, router]);

  // Handle send message
  const handleSendMessage = useCallback(
    async (content: string, attachments?: string[]) => {
      if (!selectedConversation) return;
      await sendMessage(content, attachments);
    },
    [selectedConversation, sendMessage]
  );

  // Initialize from URL params
  useEffect(() => {
    const caseParam = searchParams?.get('case');
    const userParam = searchParams?.get('user');

    if (caseParam && userParam && conversations.length > 0) {
      const conversation = conversations.find(
        (c) => c.case_id === caseParam && c.other_user.id === userParam
      );
      if (conversation) {
        setSelectedConversation(conversation);
        setIsMobileListView(false);
      }
    }
  }, [searchParams, conversations]);

  // Auto-mark messages as read
  useEffect(() => {
    if (selectedConversation && messages.length > 0) {
      const unreadMessageIds = messages
        .filter((m) => !m.read_at && !m.is_mine)
        .map((m) => m.id);

      if (unreadMessageIds.length > 0) {
        markAsRead(unreadMessageIds);
      }
    }
  }, [selectedConversation, messages, markAsRead]);

  // Refresh conversations periodically
  useEffect(() => {
    const interval = setInterval(() => {
      refreshConversations();
    }, 30000); // Every 30 seconds

    return () => clearInterval(interval);
  }, [refreshConversations]);

  // Portal-specific titles
  const titles: Record<string, string> = {
    lawyer: '메시지',
    client: '변호사와의 대화',
    detective: '메시지',
  };

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col">
      {/* Page Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">
            {titles[portalType]}
          </h1>
          {totalUnread > 0 && (
            <p className="text-sm text-gray-500 mt-1">
              읽지 않은 메시지 {totalUnread}건
            </p>
          )}
        </div>

        {/* WebSocket Status (for debugging) */}
        {wsStatus !== 'disconnected' && (
          <div className="flex items-center gap-2 text-xs">
            <span
              className={`w-2 h-2 rounded-full ${
                wsStatus === 'connected'
                  ? 'bg-green-500'
                  : wsStatus === 'connecting'
                  ? 'bg-yellow-500 animate-pulse'
                  : 'bg-red-500'
              }`}
            />
            <span className="text-gray-500">
              {wsStatus === 'connected'
                ? '실시간 연결됨'
                : wsStatus === 'connecting'
                ? '연결 중...'
                : '연결 끊김'}
            </span>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 flex bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {/* Conversation List (Left Panel) */}
        <div
          className={`w-full md:w-80 lg:w-96 border-r border-gray-200 flex-shrink-0 ${
            !isMobileListView ? 'hidden md:block' : ''
          }`}
        >
          {isLoadingConversations ? (
            <div className="flex items-center justify-center h-full">
              <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : conversationsError ? (
            <div className="flex items-center justify-center h-full p-4">
              <p className="text-red-500 text-sm">{conversationsError}</p>
            </div>
          ) : (
            <ConversationList
              conversations={conversations}
              selectedId={
                selectedConversation
                  ? `${selectedConversation.case_id}-${selectedConversation.other_user.id}`
                  : undefined
              }
              onSelect={handleSelectConversation}
            />
          )}
        </div>

        {/* Message Thread (Right Panel) */}
        <div
          className={`flex-1 flex flex-col ${
            isMobileListView ? 'hidden md:flex' : ''
          }`}
        >
          {selectedConversation ? (
            <>
              {/* Conversation Header */}
              <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-200 bg-gray-50">
                {/* Back button (mobile only) */}
                <button
                  type="button"
                  onClick={handleBack}
                  className="md:hidden p-1 -ml-1 hover:bg-gray-200 rounded-lg"
                >
                  <svg
                    className="w-5 h-5 text-gray-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15 19l-7-7 7-7"
                    />
                  </svg>
                </button>

                {/* Avatar */}
                <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-medium">
                  {selectedConversation.other_user.name.slice(0, 1)}
                </div>

                {/* User Info */}
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 truncate">
                    {selectedConversation.other_user.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {selectedConversation.case_title}
                  </p>
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-hidden">
                {isLoadingMessages && messages.length === 0 ? (
                  <div className="flex items-center justify-center h-full">
                    <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                  </div>
                ) : messagesError ? (
                  <div className="flex items-center justify-center h-full p-4">
                    <p className="text-red-500 text-sm">{messagesError}</p>
                  </div>
                ) : (
                  <MessageList
                    messages={messages}
                    isLoading={isLoadingMessages}
                    hasMore={hasMore}
                    onLoadMore={loadMore}
                    typingUsers={typingUsers}
                  />
                )}
              </div>

              {/* Input */}
              <MessageInput
                onSend={handleSendMessage}
                onTyping={sendTyping}
                disabled={!selectedConversation}
                placeholder="메시지를 입력하세요..."
              />
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-500">
              <div className="text-center">
                <svg
                  className="w-16 h-16 mx-auto text-gray-300 mb-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1}
                    d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                  />
                </svg>
                <p className="text-lg font-medium text-gray-900">대화를 선택하세요</p>
                <p className="text-sm text-gray-500 mt-1">
                  왼쪽 목록에서 대화를 선택하여 메시지를 확인하세요.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default MessagesPageContent;
