'use client';

/**
 * Panel for viewing Claude's reflections and insights.
 */

import { useState, useEffect } from 'react';
import { useNexusStore } from '@/components/providers/NexusProvider';
import { api } from '@/lib/api';
import type { Reflection, ReflectionType } from '@/types';

// ============================================================================
// Reflection Card
// ============================================================================

interface ReflectionCardProps {
  reflection: Reflection;
}

function ReflectionCard({ reflection }: ReflectionCardProps) {
  const typeColors: Record<ReflectionType, string> = {
    session_end: '#6366f1',
    insight: '#22c55e',
    pattern: '#3b82f6',
    growth: '#10b981',
    curiosity: '#f59e0b',
    mistake: '#ef4444',
    milestone: '#a855f7',
  };

  const typeIcons: Record<ReflectionType, string> = {
    session_end: '🌙',
    insight: '💡',
    pattern: '🔄',
    growth: '📈',
    curiosity: '❓',
    mistake: '⚠️',
    milestone: '🏆',
  };

  const color = typeColors[reflection.reflection_type] || '#6366f1';
  const icon = typeIcons[reflection.reflection_type] || '📝';

  return (
    <div
      className="p-4 bg-nexus-dark/50 rounded-lg border border-nexus-muted/20 hover:border-nexus-muted/40 transition-colors"
      style={{ borderLeftColor: color, borderLeftWidth: '3px' }}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <span>{icon}</span>
          <span
            className="text-xs font-mono uppercase tracking-wide"
            style={{ color }}
          >
            {reflection.reflection_type.replace('_', ' ')}
          </span>
        </div>
        <span className="text-xs text-nexus-muted">
          {new Date(reflection.created_at).toLocaleDateString()}
        </span>
      </div>

      <p className="text-sm text-white/90 whitespace-pre-wrap">
        {reflection.content}
      </p>

      {reflection.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-3">
          {reflection.tags.map((tag, i) => (
            <span
              key={i}
              className="text-xs px-2 py-0.5 rounded bg-nexus-muted/20 text-nexus-muted"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      <div className="flex items-center justify-between mt-3 pt-2 border-t border-nexus-muted/10">
        <span className="text-xs text-nexus-muted">
          Importance: {Math.round(reflection.importance * 100)}%
        </span>
      </div>
    </div>
  );
}

// ============================================================================
// Filter Tabs
// ============================================================================

interface FilterTabsProps {
  activeFilter: ReflectionType | 'all';
  onFilterChange: (filter: ReflectionType | 'all') => void;
}

function FilterTabs({ activeFilter, onFilterChange }: FilterTabsProps) {
  const filters: Array<{ value: ReflectionType | 'all'; label: string }> = [
    { value: 'all', label: 'All' },
    { value: 'insight', label: 'Insights' },
    { value: 'pattern', label: 'Patterns' },
    { value: 'growth', label: 'Growth' },
    { value: 'curiosity', label: 'Curiosities' },
    { value: 'session_end', label: 'Sessions' },
  ];

  return (
    <div className="flex gap-1 overflow-x-auto pb-2">
      {filters.map((filter) => (
        <button
          key={filter.value}
          onClick={() => onFilterChange(filter.value)}
          className={`
            px-3 py-1 rounded-full text-xs font-mono whitespace-nowrap transition-colors
            ${
              activeFilter === filter.value
                ? 'bg-nexus-accent/80 text-white'
                : 'bg-nexus-surface text-nexus-muted hover:bg-nexus-muted/20'
            }
          `}
        >
          {filter.label}
        </button>
      ))}
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export default function ReflectionView() {
  const reflectionsPanelOpen = useNexusStore(
    (state) => state.reflectionsPanelOpen
  );
  const toggleReflections = useNexusStore((state) => state.toggleReflections);
  const isAwake = useNexusStore((state) => state.isAwake);

  const [reflections, setReflections] = useState<Reflection[]>([]);
  const [activeFilter, setActiveFilter] = useState<ReflectionType | 'all'>(
    'all'
  );
  const [isLoading, setIsLoading] = useState(false);

  // Fetch reflections
  useEffect(() => {
    if (reflectionsPanelOpen && isAwake) {
      fetchReflections();
    }
  }, [reflectionsPanelOpen, isAwake, activeFilter]);

  const fetchReflections = async () => {
    setIsLoading(true);
    try {
      const params: { reflection_type?: string; limit?: number } = {
        limit: 20,
      };
      if (activeFilter !== 'all') {
        params.reflection_type = activeFilter;
      }
      const data = await api.getReflections(params);
      setReflections(data);
    } catch (error) {
      console.error('Failed to fetch reflections:', error);
    }
    setIsLoading(false);
  };

  if (!reflectionsPanelOpen) {
    // Floating toggle button
    return (
      <button
        onClick={toggleReflections}
        className="
          absolute top-4 left-4 px-4 py-2
          bg-nexus-surface/90 backdrop-blur-md rounded-lg
          border border-nexus-muted/30 shadow-lg
          flex items-center gap-2
          hover:bg-nexus-surface transition-colors
        "
      >
        <span>📖</span>
        <span className="font-mono text-sm text-white">Reflections</span>
      </button>
    );
  }

  return (
    <div className="absolute top-4 left-4 w-96 h-[calc(100vh-8rem)] bg-nexus-surface/95 backdrop-blur-md rounded-xl border border-nexus-muted/30 shadow-2xl flex flex-col overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-nexus-muted/20">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-mono text-white flex items-center gap-2">
            <span>📖</span>
            Reflections
          </h2>
          <button
            onClick={toggleReflections}
            className="text-nexus-muted hover:text-white transition-colors"
          >
            ✕
          </button>
        </div>

        <FilterTabs
          activeFilter={activeFilter}
          onFilterChange={setActiveFilter}
        />
      </div>

      {/* Reflections list */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <span className="text-nexus-muted animate-pulse">Loading...</span>
          </div>
        ) : reflections.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 text-center">
            <span className="text-4xl mb-2">🌱</span>
            <p className="text-nexus-muted text-sm">
              No reflections yet.
              <br />
              They will appear after sessions.
            </p>
          </div>
        ) : (
          reflections.map((reflection) => (
            <ReflectionCard key={reflection.id} reflection={reflection} />
          ))
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-nexus-muted/20 text-center">
        <span className="text-xs text-nexus-muted">
          {reflections.length} reflection{reflections.length !== 1 ? 's' : ''}
        </span>
      </div>
    </div>
  );
}
