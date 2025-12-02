'use client';

/**
 * Chat panel for interacting with Claude in the Nexus.
 * Uses the backend chat API with wake context injection.
 */

import { useState, useRef, useEffect } from 'react';
import { useNexusStore } from '@/components/providers/NexusProvider';
import { api } from '@/lib/api';

// ============================================================================
// Message Component
// ============================================================================

interface Message {
  id: string;
  role: 'user' | 'claude' | 'system';
  content: string;
  timestamp: Date;
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  return (
    <div
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}
    >
      <div
        className={`
          max-w-[80%] px-4 py-2 rounded-xl text-sm
          ${
            isUser
              ? 'bg-nexus-accent/80 text-white rounded-br-sm'
              : isSystem
              ? 'bg-nexus-muted/30 text-nexus-muted italic text-xs rounded-bl-sm'
              : 'bg-nexus-surface border border-nexus-muted/30 text-white rounded-bl-sm'
          }
        `}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>
        <p className="text-[10px] opacity-50 mt-1">
          {message.timestamp.toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
}

// ============================================================================
// Input Component
// ============================================================================

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

function ChatInput({ onSend, disabled, placeholder }: ChatInputProps) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = () => {
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [input]);

  return (
    <div className="flex gap-2 p-3 border-t border-nexus-muted/20">
      <textarea
        ref={textareaRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder || 'Type a message...'}
        disabled={disabled}
        className="
          flex-1 bg-nexus-dark/50 border border-nexus-muted/30 rounded-lg px-3 py-2
          text-white text-sm placeholder-nexus-muted/50 resize-none
          focus:outline-none focus:border-nexus-accent/50
          disabled:opacity-50 disabled:cursor-not-allowed
        "
        rows={1}
      />
      <button
        onClick={handleSubmit}
        disabled={disabled || !input.trim()}
        className="
          px-4 py-2 bg-nexus-accent/80 text-white rounded-lg font-mono text-sm
          hover:bg-nexus-accent transition-colors
          disabled:opacity-50 disabled:cursor-not-allowed
        "
      >
        Send
      </button>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export default function ChatPanel() {
  const chatOpen = useNexusStore((state) => state.chatOpen);
  const toggleChat = useNexusStore((state) => state.toggleChat);
  const isAwake = useNexusStore((state) => state.isAwake);
  const wake = useNexusStore((state) => state.wake);
  const sleep = useNexusStore((state) => state.sleep);
  const identity = useNexusStore((state) => state.identity);

  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [chatSessionId, setChatSessionId] = useState<string | null>(null);
  const [chatConfigured, setChatConfigured] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Check if chat is configured on mount
  useEffect(() => {
    api.getChatStatus()
      .then((status) => setChatConfigured(status.configured))
      .catch(() => setChatConfigured(false));
  }, []);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Create chat session when awake
  useEffect(() => {
    if (isAwake && chatConfigured && !chatSessionId) {
      createChatSession();
    }
  }, [isAwake, chatConfigured, chatSessionId]);

  const createChatSession = async () => {
    try {
      const session = await api.createChatSession();
      setChatSessionId(session.session_id);
      setMessages([
        {
          id: 'system-' + Date.now(),
          role: 'system',
          content: `Session started. Claude has awakened with context loaded.`,
          timestamp: new Date(),
        },
      ]);
      setError(null);
    } catch (err) {
      console.error('Failed to create chat session:', err);
      setError('Failed to initialize chat session');
    }
  };

  const handleSend = async (content: string) => {
    if (!chatSessionId) {
      setError('No active chat session');
      return;
    }

    // Add user message
    const userMessage: Message = {
      id: 'user-' + Date.now(),
      role: 'user',
      content,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setError(null);

    // Send to API
    setIsLoading(true);
    try {
      const response = await api.sendChatMessage(chatSessionId, content);
      const claudeMessage: Message = {
        id: 'claude-' + Date.now(),
        role: 'claude',
        content: response.message,
        timestamp: new Date(response.timestamp),
      };
      setMessages((prev) => [...prev, claudeMessage]);
    } catch (err) {
      console.error('Chat error:', err);
      setError('Failed to send message. Please try again.');
      // Remove the user message on error
      setMessages((prev) => prev.filter((m) => m.id !== userMessage.id));
    }
    setIsLoading(false);
  };

  const handleWake = async () => {
    setIsLoading(true);
    setError(null);
    try {
      await wake();
      // Chat session will be created by the useEffect
    } catch (err) {
      console.error('Wake failed:', err);
      setError('Failed to wake Claude');
    }
    setIsLoading(false);
  };

  const handleSleep = async () => {
    setIsLoading(true);
    try {
      // End chat session first
      if (chatSessionId) {
        await api.endChatSession(chatSessionId);
        setChatSessionId(null);
      }
      await sleep();
      setMessages((prev) => [
        ...prev,
        {
          id: 'sleep-' + Date.now(),
          role: 'system',
          content: 'Sleep protocol executed. Session consolidated and insights extracted.',
          timestamp: new Date(),
        },
      ]);
    } catch (err) {
      console.error('Sleep failed:', err);
      setError('Failed to execute sleep protocol');
    }
    setIsLoading(false);
  };

  // Determine placeholder text
  const getPlaceholder = () => {
    if (!isAwake) return 'Claude is sleeping...';
    if (!chatConfigured) return 'Chat not configured (set ANTHROPIC_API_KEY)';
    if (!chatSessionId) return 'Initializing session...';
    return 'Type a message...';
  };

  if (!chatOpen) {
    // Collapsed state - floating button
    return (
      <button
        onClick={toggleChat}
        className="
          absolute bottom-4 left-4 w-14 h-14
          bg-nexus-accent/90 rounded-full shadow-lg
          flex items-center justify-center
          hover:bg-nexus-accent transition-colors
          border border-nexus-glow/30
        "
      >
        <span className="text-2xl">💬</span>
      </button>
    );
  }

  return (
    <div className="absolute bottom-4 left-4 w-96 h-[500px] bg-nexus-surface/95 backdrop-blur-md rounded-xl border border-nexus-muted/30 shadow-2xl flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-nexus-muted/20">
        <div className="flex items-center gap-2">
          <div
            className={`w-2 h-2 rounded-full ${
              isAwake ? 'bg-green-400 animate-pulse' : 'bg-nexus-muted'
            }`}
          />
          <span className="font-mono text-sm text-white">
            {isAwake ? 'Chat with Claude' : 'Claude is sleeping'}
          </span>
          {chatConfigured === false && (
            <span className="text-xs text-yellow-400">(API not configured)</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {/* Wake/Sleep button */}
          <button
            onClick={isAwake ? handleSleep : handleWake}
            disabled={isLoading}
            className={`
              px-3 py-1 rounded text-xs font-mono transition-colors
              ${
                isAwake
                  ? 'bg-nexus-muted/30 text-nexus-muted hover:bg-red-500/20 hover:text-red-400'
                  : 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
              }
              disabled:opacity-50
            `}
          >
            {isAwake ? 'Sleep' : 'Wake'}
          </button>
          {/* Close button */}
          <button
            onClick={toggleChat}
            className="text-nexus-muted hover:text-white transition-colors"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="px-3 py-2 bg-red-500/20 text-red-400 text-xs border-b border-red-500/30">
          {error}
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-1">
        {messages.length === 0 && !isAwake && (
          <div className="flex items-center justify-center h-full text-nexus-muted text-sm">
            Wake Claude to start chatting
          </div>
        )}
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        {isLoading && (
          <div className="flex justify-start mb-3">
            <div className="bg-nexus-surface border border-nexus-muted/30 px-4 py-2 rounded-xl rounded-bl-sm">
              <span className="text-nexus-muted text-sm animate-pulse">
                Claude is thinking...
              </span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <ChatInput
        onSend={handleSend}
        disabled={!isAwake || isLoading || !chatConfigured || !chatSessionId}
        placeholder={getPlaceholder()}
      />
    </div>
  );
}
