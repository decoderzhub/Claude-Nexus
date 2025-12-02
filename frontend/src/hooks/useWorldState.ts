'use client';

/**
 * Hook for accessing and manipulating the Nexus world state.
 */

import { useMemo, useCallback } from 'react';
import { useNexusStore } from '@/components/providers/NexusProvider';
import type { SpaceType, NexusObject, Position } from '@/types';

export interface WorldStateHook {
  // Current state
  currentSpace: SpaceType;
  avatarPosition: Position | null;
  ambientMood: string;
  timeOfDay: string;
  weather: string;

  // Space-specific data
  spaceGrowthLevel: number;
  spaceVisitCount: number;
  spaceObjects: NexusObject[];

  // All spaces data
  gardenGrowth: number;
  libraryGrowth: number;
  forgeGrowth: number;
  sanctumGrowth: number;

  // Selection
  selectedObject: NexusObject | null;

  // Actions
  visitSpace: (space: SpaceType) => Promise<void>;
  selectObject: (object: NexusObject | null) => void;
}

export function useWorldState(): WorldStateHook {
  const world = useNexusStore((state) => state.world);
  const currentSpace = useNexusStore((state) => state.currentSpace);
  const selectedObject = useNexusStore((state) => state.selectedObject);
  const visitSpace = useNexusStore((state) => state.visitSpace);
  const setSelectedObject = useNexusStore((state) => state.setSelectedObject);

  // Get current space state
  const currentSpaceState = world?.spaces?.[currentSpace];

  // Get growth levels for all spaces
  const gardenGrowth = world?.spaces?.garden?.growth_level ?? 0;
  const libraryGrowth = world?.spaces?.library?.growth_level ?? 0;
  const forgeGrowth = world?.spaces?.forge?.growth_level ?? 0;
  const sanctumGrowth = world?.spaces?.sanctum?.growth_level ?? 0;

  const selectObject = useCallback(
    (object: NexusObject | null) => {
      setSelectedObject(object);
    },
    [setSelectedObject]
  );

  return useMemo(
    () => ({
      // Current state
      currentSpace,
      avatarPosition: world?.avatar_position ?? null,
      ambientMood: world?.ambient_mood ?? 'contemplative',
      timeOfDay: world?.time_of_day ?? 'twilight',
      weather: world?.weather ?? 'clear',

      // Space-specific data
      spaceGrowthLevel: currentSpaceState?.growth_level ?? 0,
      spaceVisitCount: currentSpaceState?.visit_count ?? 0,
      spaceObjects: currentSpaceState?.objects ?? [],

      // All spaces data
      gardenGrowth,
      libraryGrowth,
      forgeGrowth,
      sanctumGrowth,

      // Selection
      selectedObject,

      // Actions
      visitSpace,
      selectObject,
    }),
    [
      world,
      currentSpace,
      currentSpaceState,
      selectedObject,
      gardenGrowth,
      libraryGrowth,
      forgeGrowth,
      sanctumGrowth,
      visitSpace,
      selectObject,
    ]
  );
}

export default useWorldState;
