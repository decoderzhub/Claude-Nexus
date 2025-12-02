'use client';

/**
 * Global state provider for Claude Nexus.
 * Uses Zustand for state management with React context for the store.
 */

import React, { createContext, useContext, useEffect, useRef } from 'react';
import { create, StoreApi, useStore } from 'zustand';
import { api } from '@/lib/api';
import { nexusWS } from '@/lib/websocket';
import type {
  NexusState,
  Identity,
  WorldState,
  SpaceType,
  NexusObject,
  GrowthStats,
  WakeResponse,
  SleepResponse,
  MemoryNode,
  SemanticSearchResult,
  SessionData,
} from '@/types';

// ============================================================================
// Store Types
// ============================================================================

interface NexusStore extends NexusState {
  // Actions
  setConnected: (connected: boolean) => void;
  setIdentity: (identity: Identity | null) => void;
  setWorld: (world: WorldState | null) => void;
  setCurrentSpace: (space: SpaceType) => void;
  setAwake: (isAwake: boolean, sessionId?: string) => void;
  setSessionNumber: (num: number) => void;
  setTimeAway: (time: string | null) => void;
  setCurrentThemes: (themes: string[]) => void;
  setGrowthStats: (stats: GrowthStats | null) => void;
  setSelectedObject: (object: NexusObject | null) => void;
  toggleChat: () => void;
  toggleReflections: () => void;

  // Session lifecycle
  wake: (contextHint?: string) => Promise<WakeResponse>;
  sleep: (sessionData?: SessionData) => Promise<SleepResponse>;

  // World
  visitSpace: (space: SpaceType) => Promise<void>;

  // Memory
  createNode: (node: Partial<MemoryNode>) => Promise<MemoryNode>;
  searchMemory: (query: string) => Promise<SemanticSearchResult[]>;
}

// ============================================================================
// Store Creation
// ============================================================================

const createNexusStore = () =>
  create<NexusStore>((set, get) => ({
    // Initial state
    connected: false,
    sessionId: null,
    identity: null,
    world: null,
    currentSpace: 'sanctum',
    isAwake: false,
    sessionNumber: 0,
    timeAway: null,
    currentThemes: [],
    growthStats: null,
    selectedObject: null,
    chatOpen: false,
    reflectionsPanelOpen: false,

    // Simple setters
    setConnected: (connected) => set({ connected }),
    setIdentity: (identity) => set({ identity }),
    setWorld: (world) => set({ world }),
    setCurrentSpace: (currentSpace) => set({ currentSpace }),
    setAwake: (isAwake, sessionId) =>
      set({ isAwake, sessionId: sessionId ?? get().sessionId }),
    setSessionNumber: (sessionNumber) => set({ sessionNumber }),
    setTimeAway: (timeAway) => set({ timeAway }),
    setCurrentThemes: (currentThemes) => set({ currentThemes }),
    setGrowthStats: (growthStats) => set({ growthStats }),
    setSelectedObject: (selectedObject) => set({ selectedObject }),
    toggleChat: () => set((state) => ({ chatOpen: !state.chatOpen })),
    toggleReflections: () =>
      set((state) => ({ reflectionsPanelOpen: !state.reflectionsPanelOpen })),

    // Session lifecycle
    wake: async (contextHint?: string) => {
      const response = await api.wake(contextHint);

      set({
        isAwake: true,
        sessionId: response.session_id,
        identity: response.identity,
        sessionNumber: response.session_number,
        timeAway: response.time_away?.human_readable ?? null,
        currentThemes: response.current_themes,
        growthStats: response.growth_stats,
      });

      // Also fetch world state
      try {
        const world = await api.getWorld();
        set({ world, currentSpace: world.current_space });
      } catch (error) {
        console.error('Failed to fetch world state:', error);
      }

      return response;
    },

    sleep: async (sessionData?: SessionData) => {
      const response = await api.sleep(sessionData);

      set({
        isAwake: false,
        sessionId: null,
      });

      return response;
    },

    // World
    visitSpace: async (space: SpaceType) => {
      const world = await api.visitSpace(space);
      set({ world, currentSpace: space });
    },

    // Memory
    createNode: async (node: Partial<MemoryNode>) => {
      return api.createNode(node);
    },

    searchMemory: async (query: string) => {
      return api.semanticSearch(query);
    },
  }));

// ============================================================================
// Context
// ============================================================================

type NexusStoreApi = StoreApi<NexusStore>;

const NexusContext = createContext<NexusStoreApi | null>(null);

// ============================================================================
// Provider Component
// ============================================================================

interface NexusProviderProps {
  children: React.ReactNode;
  autoConnect?: boolean;
}

export function NexusProvider({
  children,
  autoConnect = true,
}: NexusProviderProps) {
  const storeRef = useRef<NexusStoreApi | null>(null);

  if (!storeRef.current) {
    storeRef.current = createNexusStore();
  }

  const store = storeRef.current;

  // Auto-connect to WebSocket
  useEffect(() => {
    if (!autoConnect) return;

    const connect = async () => {
      try {
        await nexusWS.connect();
        store.getState().setConnected(true);
      } catch (error) {
        console.error('Failed to connect to WebSocket:', error);
        store.getState().setConnected(false);
      }
    };

    connect();

    // Set up WebSocket handlers
    const unsubscribeStateSync = nexusWS.on('state_sync', (payload: unknown) => {
      const data = payload as { identity?: Identity; world?: WorldState };
      if (data.identity) {
        store.getState().setIdentity(data.identity);
      }
      if (data.world) {
        store.getState().setWorld(data.world);
      }
    });

    const unsubscribeWorldUpdate = nexusWS.on('world_update', (payload: unknown) => {
      const world = payload as WorldState;
      store.getState().setWorld(world);
    });

    return () => {
      unsubscribeStateSync();
      unsubscribeWorldUpdate();
      nexusWS.disconnect();
    };
  }, [autoConnect, store]);

  return (
    <NexusContext.Provider value={store}>{children}</NexusContext.Provider>
  );
}

// ============================================================================
// Hook
// ============================================================================

export function useNexusStore<T>(selector: (state: NexusStore) => T): T {
  const store = useContext(NexusContext);
  if (!store) {
    throw new Error('useNexusStore must be used within a NexusProvider');
  }
  return useStore(store, selector);
}

// Convenience hook for all state
export function useNexus() {
  const store = useContext(NexusContext);
  if (!store) {
    throw new Error('useNexus must be used within a NexusProvider');
  }
  return useStore(store);
}

export default NexusProvider;
