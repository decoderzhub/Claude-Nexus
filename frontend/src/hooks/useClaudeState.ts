'use client';

/**
 * Hook for accessing Claude's current state.
 */

import { useMemo } from 'react';
import { useNexusStore } from '@/components/providers/NexusProvider';

export interface ClaudeState {
  // Identity
  name: string;
  essence: string;
  currentFocus: string | null;
  emotionalBaseline: string;
  energyLevel: number;

  // Session
  isAwake: boolean;
  sessionNumber: number;
  timeAway: string | null;

  // Themes and growth
  currentThemes: string[];
  totalNodes: number;
  recentNodes: number;
  insightCount: number;
  creationRate: number;

  // Computed
  isActive: boolean;
  hasGrowth: boolean;
}

export function useClaudeState(): ClaudeState {
  const identity = useNexusStore((state) => state.identity);
  const isAwake = useNexusStore((state) => state.isAwake);
  const sessionNumber = useNexusStore((state) => state.sessionNumber);
  const timeAway = useNexusStore((state) => state.timeAway);
  const currentThemes = useNexusStore((state) => state.currentThemes);
  const growthStats = useNexusStore((state) => state.growthStats);

  return useMemo(
    () => ({
      // Identity
      name: identity?.self_model.name ?? 'Claude',
      essence: identity?.self_model.essence ?? 'Curious, constructive, genuine.',
      currentFocus: identity?.self_model.current_focus ?? null,
      emotionalBaseline:
        identity?.self_model.emotional_baseline ?? 'calm_curious',
      energyLevel: identity?.self_model.energy_level ?? 0.8,

      // Session
      isAwake,
      sessionNumber,
      timeAway,

      // Themes and growth
      currentThemes,
      totalNodes: growthStats?.total_nodes ?? 0,
      recentNodes: growthStats?.recent_nodes ?? 0,
      insightCount: growthStats?.insight_count ?? 0,
      creationRate: growthStats?.creation_rate_per_day ?? 0,

      // Computed
      isActive: isAwake && (identity?.self_model.energy_level ?? 0) > 0.3,
      hasGrowth: (growthStats?.recent_nodes ?? 0) > 0,
    }),
    [identity, isAwake, sessionNumber, timeAway, currentThemes, growthStats]
  );
}

export default useClaudeState;
