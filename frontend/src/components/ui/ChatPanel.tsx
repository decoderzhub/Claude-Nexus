'use client';

/**
 * Chat panel for interacting with Claude in the Nexus.
 * Uses the backend chat API with wake context injection.
 * Shows tool actions when Claude acts in the world.
 */

import { useState, useRef, useEffect } from 'react';
import { useNexusStore } from '@/components/providers/NexusProvider';
import { api, ToolAction } from '@/lib/api';

// ============================================================================
// Tool Action Display
// ============================================================================

const TOOL_ICONS: Record<string, string> = {
  create_memory: '🧠',
  search_memories: '🔍',
  plant_in_garden: '🌱',
  add_to_library: '📚',
  forge_creation: '🔥',
  reflect_in_sanctum: '💜',
  record_curiosity: '❓',
  connect_memories: '🔗',
  visit_space: '🚀',
  get_stats: '📊',
};

const TOOL_LABELS: Record<string, string> = {
  create_memory: 'Created memory',
  search_memories: 'Searched memories',
  plant_in_garden: 'Planted in Garden',
  add_to_library: 'Added to Library',
  forge_creation: 'Forged creation',
  reflect_in_sanctum: 'Reflected in Sanctum',
  record_curiosity: 'Recorded curiosity',
  connect_memories: 'Connected memories',
  visit_space: 'Visited space',
  get_stats: 'Got stats',
};

function ToolActionBadge({ action }: { action: ToolAction }) {
  const icon = TOOL_ICONS[action.tool] || '⚡';
  const label = TOOL_LABELS[action.tool] || action.tool;
  const success = action.result.success;

  return (
    <div
      className={`
        inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs
        ${success
          ? 'bg-green-500/20 text-green-400 border border-green-500/30'
          : 'bg-red-500/20 text-red-400 border border-red-500/30'
        }
      `}
      title={action.result.message || JSON.stringify(action.input)}
    >
      <span>{icon}</span>
      <span>{label}</span>
    </div>
  );
}

// ============================================================================
// Message Component
// ============================================================================

interface Message {
  id: string;
  role: 'user' | 'claude' | 'system';
  content: string;
  timestamp: Date;
  toolActions?: ToolAction[];
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';
  const hasActions = message.toolActions && message.toolActions.length > 0;

  return (
    <div
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}
    >
      <div
        className={`
          max-w-[85%] px-4 py-2 rounded-xl text-sm
          ${
            isUser
              ? 'bg-nexus-accent/80 text-white rounded-br-sm'
              : isSystem
              ? 'bg-nexus-muted/30 text-nexus-muted italic text-xs rounded-bl-sm'
              : 'bg-nexus-surface border border-nexus-muted/30 text-white rounded-bl-sm'
          }
        `}
      >
        {/* Tool actions */}
        {hasActions && (
          <div className="flex flex-wrap gap-1.5 mb-2 pb-2 border-b border-nexus-muted/20">
            {message.toolActions!.map((action, i) => (
              <ToolActionBadge key={i} action={action} />
            ))}
          </div>
        )}
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
  const fetchGrowthStats = useNexusStore((state) => state.fetchGrowthStats);
  const fetchWorld = useNexusStore((state) => state.fetchWorld);

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

    // Clear any previous error
    setError(null);

    // Add user message
    const userMessageId = 'user-' + Date.now();
    const userMessage: Message = {
      id: userMessageId,
      role: 'user',
      content,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // Send to API
    setIsLoading(true);
    try {
      const response = await api.sendChatMessage(chatSessionId, content);
      const claudeMessage: Message = {
        id: 'claude-' + Date.now(),
        role: 'claude',
        content: response.message,
        timestamp: new Date(response.timestamp),
        toolActions: response.tool_actions,
      };
      setMessages((prev) => [...prev, claudeMessage]);

      // If Claude took any actions, refresh the stats and world
      if (response.tool_actions && response.tool_actions.length > 0) {
        // Small delay to let backend commit to DB
        setTimeout(() => {
          fetchGrowthStats();
          fetchWorld();
        }, 500);
      }
    } catch (err: unknown) {
      console.error('Chat error:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      setError(errorMessage);
      // Remove the user message on error
      setMessages((prev) => prev.filter((m) => m.id !== userMessageId));
    } finally {
      setIsLoading(false);
    }
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

      {/* Error banner - click to dismiss */}
      {error && (
        <div
          className="px-3 py-2 bg-red-500/20 text-red-400 text-xs border-b border-red-500/30 cursor-pointer flex justify-between items-center"
          onClick={() => setError(null)}
        >
          <span>{error}</span>
          <span className="opacity-50 hover:opacity-100">✕</span>
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
