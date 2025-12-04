'use client';

import { useState, useRef, useEffect, FormEvent, KeyboardEvent } from 'react';
import { useMessages } from '@/hooks/useMessages';
import type { Message } from '@/types/message';

interface MessageThreadProps {
  caseId: string;
  recipientId: string;
  currentUserId: string;
  className?: string;
}

export function MessageThread({
  caseId,
  recipientId,
  currentUserId,
  className = "",
}: MessageThreadProps) {
  const {
    messages,
    isLoading,
    error,
    sendMessage,
    isTyping,
    sendTypingIndicator,
    hasMore,
    loadMore,
    isConnected,
    refetch,
  } = useMessages({ caseId, recipientId });

  const [inputValue, setInputValue] = useState("");
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value);
    sendTypingIndicator(true);
    if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
    typingTimeoutRef.current = setTimeout(() => sendTypingIndicator(false), 2000);
  };

  const handleSend = async (e?: FormEvent) => {
    e?.preventDefault();
    if (!inputValue.trim() || isSending) return;
    setIsSending(true);
    sendTypingIndicator(false);
    try {
      await sendMessage({ case_id: caseId, recipient_id: recipientId, content: inputValue.trim() });
      setInputValue("");
    } catch (err) {
      console.error("Failed to send:", err);
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" });
  };

  const renderMessage = (message: Message) => {
    const isMine = message.is_mine || message.sender.id === currentUserId;
    const alignClass = isMine ? "justify-end" : "justify-start";
    const bgClass = isMine ? "bg-blue-500 text-white" : "bg-gray-100 text-gray-900";
    return (
      <div key={message.id} data-testid="message-item" data-is-mine={isMine ? "true" : "false"} className={"flex " + alignClass + " mb-4"}>
        <div className={"max-w-[70%] " + bgClass + " rounded-lg px-4 py-2"}>
          {!isMine && <div className="text-xs font-medium mb-1 text-gray-600">{message.sender.name}</div>}
          <div className="whitespace-pre-wrap break-words">{message.content}</div>
          {message.attachments && message.attachments.length > 0 && (
            <div data-testid="attachment-preview" className="mt-2">
              {message.attachments.map((url, idx) => (
                <a key={idx} href={url} target="_blank" rel="noopener noreferrer" aria-label="첨부파일" className="text-sm underline">첨부파일</a>
              ))}
            </div>
          )}
          <div className="flex items-center justify-end mt-1 space-x-2 text-xs opacity-70">
            <span>{formatTime(message.created_at)}</span>
            {isMine && message.read_at && <span data-testid={"read-receipt-" + message.id}>읽음</span>}
          </div>
        </div>
      </div>
    );
  };

  const connectedClass = isConnected ? "bg-green-100 text-green-700" : "bg-yellow-100 text-yellow-700";
  return (
    <div data-testid="message-thread" className={"flex flex-col h-full " + className}>
      <div data-testid="connection-status" data-connected={isConnected ? "true" : "false"} className={"px-4 py-1 text-xs text-center " + connectedClass}>{isConnected ? "연결됨" : "연결 중..."}</div>
      <div data-testid="message-list" role="log" aria-live="polite" className="flex-1 overflow-y-auto p-4">
        {isLoading && <div data-testid="loading-spinner" className="flex justify-center py-4"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div></div>}
        {error && <div className="text-center py-8"><p className="text-red-500 mb-4">{error}</p><button onClick={() => refetch()} className="px-4 py-2 bg-blue-500 text-white rounded">다시 시도</button></div>}
        {!isLoading && !error && messages.length === 0 && <div className="text-center py-8 text-gray-500">메시지가 없습니다. 대화를 시작하세요.</div>}
        {hasMore && !isLoading && <div className="text-center mb-4"><button onClick={loadMore} className="text-sm text-blue-500">이전 메시지 보기</button></div>}
        {messages.map(renderMessage)}
        {isTyping && <div data-testid="typing-indicator" className="flex items-center text-gray-500 text-sm mb-4"><div className="flex space-x-1 mr-2"><span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span><span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span><span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span></div>입력 중...</div>}
        <div ref={messagesEndRef} />
      </div>
      <form onSubmit={handleSend} className="border-t p-4">
        <div className="flex items-end space-x-2">
          <textarea value={inputValue} onChange={handleInputChange} onKeyDown={handleKeyDown} placeholder="메시지를 입력하세요..." aria-label="메시지 입력" rows={1} className="flex-1 resize-none border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 max-h-32" style={{ minHeight: "44px" }} />
          <button type="submit" disabled={!inputValue.trim() || isSending} className="px-4 py-2 bg-blue-500 text-white rounded-lg disabled:opacity-50">{isSending ? "전송 중..." : "전송"}</button>
        </div>
      </form>
    </div>
  );
}

export default MessageThread;
