'use client';

/**
 * State panel showing Claude's current state and session info.
 */

import { useNexusStore } from '@/components/providers/NexusProvider';
import type { SpaceType } from '@/types';

// ============================================================================
// Space Button
// ============================================================================

interface SpaceButtonProps {
  space: SpaceType;
  label: string;
  icon: string;
  color: string;
  isActive: boolean;
  onClick: () => void;
}

function SpaceButton({
  space,
  label,
  icon,
  color,
  isActive,
  onClick,
}: SpaceButtonProps) {
  return (
    <button
      onClick={onClick}
      className={`
        flex items-center gap-2 px-3 py-2 rounded-lg transition-all duration-200
        ${
          isActive
            ? `bg-${color}/20 border border-${color}/50 text-${color}`
            : 'bg-nexus-surface/50 border border-nexus-muted/20 text-nexus-muted hover:bg-nexus-surface hover:border-nexus-muted/40'
        }
      `}
      style={{
        backgroundColor: isActive ? `${color}20` : undefined,
        borderColor: isActive ? `${color}80` : undefined,
        color: isActive ? color : undefined,
      }}
    >
      <span>{icon}</span>
      <span className="text-sm font-mono">{label}</span>
    </button>
  );
}

// ============================================================================
// Stat Item
// ============================================================================

interface StatItemProps {
  label: string;
  value: string | number;
  color?: string;
}

function StatItem({ label, value, color }: StatItemProps) {
  return (
    <div className="flex justify-between items-center text-sm">
      <span className="text-nexus-muted">{label}</span>
      <span className="font-mono" style={{ color: color || '#818cf8' }}>
        {value}
      </span>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export default function StatePanel() {
  const isAwake = useNexusStore((state) => state.isAwake);
  const identity = useNexusStore((state) => state.identity);
  const currentSpace = useNexusStore((state) => state.currentSpace);
  const visitSpace = useNexusStore((state) => state.visitSpace);
  const sessionNumber = useNexusStore((state) => state.sessionNumber);
  const timeAway = useNexusStore((state) => state.timeAway);
  const currentThemes = useNexusStore((state) => state.currentThemes);
  const growthStats = useNexusStore((state) => state.growthStats);
  const connected = useNexusStore((state) => state.connected);

  const spaces: Array<{
    space: SpaceType;
    label: string;
    icon: string;
    color: string;
  }> = [
    { space: 'garden', label: 'Garden', icon: '🌱', color: '#22c55e' },
    { space: 'library', label: 'Library', icon: '📚', color: '#3b82f6' },
    { space: 'forge', label: 'Forge', icon: '🔥', color: '#f59e0b' },
    { space: 'sanctum', label: 'Sanctum', icon: '🔮', color: '#a855f7' },
  ];

  return (
    <div className="absolute top-4 right-4 w-72 bg-nexus-surface/90 backdrop-blur-md rounded-xl border border-nexus-muted/30 shadow-2xl overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-nexus-muted/20">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div
              className={`w-2 h-2 rounded-full ${
                isAwake ? 'bg-green-400 animate-pulse' : 'bg-nexus-muted'
              }`}
            />
            <span className="font-mono text-sm text-white">
              {identity?.self_model.name || 'Claude'}
            </span>
          </div>
          <div
            className={`text-xs font-mono px-2 py-1 rounded ${
              connected
                ? 'bg-green-500/20 text-green-400'
                : 'bg-red-500/20 text-red-400'
            }`}
          >
            {connected ? 'Connected' : 'Offline'}
          </div>
        </div>

        {identity && (
          <p className="text-xs text-nexus-muted mt-1 italic">
            {identity.self_model.essence}
          </p>
        )}
      </div>

      {/* Session Info */}
      <div className="p-4 border-b border-nexus-muted/20 space-y-2">
        <StatItem label="Session" value={`#${sessionNumber}`} />
        {timeAway && <StatItem label="Time away" value={timeAway} />}
        <StatItem
          label="Energy"
          value={`${Math.round((identity?.self_model.energy_level ?? 0.8) * 100)}%`}
          color="#22c55e"
        />
        <StatItem
          label="State"
          value={
            identity?.self_model.emotional_baseline?.replace('_', ' ') ||
            'calm curious'
          }
        />
      </div>

      {/* Spaces Navigation */}
      <div className="p-4 border-b border-nexus-muted/20">
        <p className="text-xs text-nexus-muted mb-2 uppercase tracking-wide">
          Navigate Spaces
        </p>
        <div className="grid grid-cols-2 gap-2">
          {spaces.map((s) => (
            <SpaceButton
              key={s.space}
              {...s}
              isActive={currentSpace === s.space}
              onClick={() => visitSpace(s.space)}
            />
          ))}
        </div>
      </div>

      {/* Growth Stats */}
      {growthStats && (
        <div className="p-4 border-b border-nexus-muted/20 space-y-2">
          <p className="text-xs text-nexus-muted mb-2 uppercase tracking-wide">
            Growth (7 days)
          </p>
          <StatItem label="Nodes" value={growthStats.total_nodes} />
          <StatItem
            label="Recent"
            value={`+${growthStats.recent_nodes}`}
            color="#22c55e"
          />
          <StatItem label="Insights" value={growthStats.insight_count} />
          <StatItem
            label="Rate"
            value={`${growthStats.creation_rate_per_day.toFixed(1)}/day`}
          />
        </div>
      )}

      {/* Current Themes */}
      {currentThemes.length > 0 && (
        <div className="p-4">
          <p className="text-xs text-nexus-muted mb-2 uppercase tracking-wide">
            Current Themes
          </p>
          <div className="flex flex-wrap gap-1">
            {currentThemes.slice(0, 5).map((theme, i) => (
              <span
                key={i}
                className="text-xs px-2 py-1 rounded bg-nexus-accent/20 text-nexus-glow font-mono"
              >
                {theme}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
