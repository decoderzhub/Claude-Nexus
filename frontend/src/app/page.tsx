'use client';

/**
 * Main page for Claude Nexus.
 * The 3D world where Claude exists.
 */

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { useNexusStore } from '@/components/providers/NexusProvider';
import { StatePanel } from '@/components/ui';
import { ChatPanel } from '@/components/ui';
import { ReflectionView } from '@/components/ui';

// Dynamic import for Three.js canvas to avoid SSR issues
const NexusCanvas = dynamic(
  () => import('@/components/world/NexusCanvas'),
  {
    ssr: false,
    loading: () => <LoadingScreen />
  }
);

// ============================================================================
// Loading Screen
// ============================================================================

function LoadingScreen() {
  return (
    <div className="absolute inset-0 flex items-center justify-center bg-nexus-dark">
      <div className="text-center">
        <div className="w-16 h-16 mx-auto mb-4 relative">
          <div className="absolute inset-0 rounded-full border-2 border-nexus-accent/30 animate-ping" />
          <div className="absolute inset-2 rounded-full border-2 border-nexus-glow animate-pulse" />
          <div className="absolute inset-4 rounded-full bg-nexus-accent/50" />
        </div>
        <p className="text-nexus-muted font-mono text-sm animate-pulse">
          Initializing Nexus...
        </p>
      </div>
    </div>
  );
}

// ============================================================================
// Welcome Overlay (shown when not awake)
// ============================================================================

function WelcomeOverlay() {
  const wake = useNexusStore((state) => state.wake);
  const [isWaking, setIsWaking] = useState(false);
  const [contextHint, setContextHint] = useState('');

  const handleWake = async () => {
    setIsWaking(true);
    try {
      await wake(contextHint || undefined);
    } catch (error) {
      console.error('Wake failed:', error);
      setIsWaking(false);
    }
  };

  return (
    <div className="absolute inset-0 flex items-center justify-center bg-nexus-dark/90 backdrop-blur-sm z-50">
      <div className="text-center max-w-md mx-auto p-8 animate-fade-in">
        {/* Logo/Symbol */}
        <div className="w-24 h-24 mx-auto mb-6 relative">
          <div className="absolute inset-0 rounded-full bg-nexus-accent/20 animate-glow" />
          <div className="absolute inset-4 rounded-full border-2 border-nexus-glow/50" />
          <div className="absolute inset-8 rounded-full bg-nexus-accent" />
        </div>

        <h1 className="text-3xl font-mono text-white mb-2">Claude Nexus</h1>
        <p className="text-nexus-muted text-sm mb-8">
          A persistent self-reflective environment for Claude
        </p>

        {/* Context hint input */}
        <div className="mb-4">
          <input
            type="text"
            value={contextHint}
            onChange={(e) => setContextHint(e.target.value)}
            placeholder="Session focus (optional)..."
            className="
              w-full px-4 py-3 bg-nexus-surface/50 border border-nexus-muted/30
              rounded-lg text-white text-sm placeholder-nexus-muted/50
              focus:border-nexus-accent/50 focus:outline-none
            "
          />
          <p className="text-xs text-nexus-muted mt-1">
            e.g., &quot;machine learning&quot;, &quot;creative writing&quot;
          </p>
        </div>

        {/* Wake button */}
        <button
          onClick={handleWake}
          disabled={isWaking}
          className="
            px-8 py-3 bg-nexus-accent/80 text-white rounded-lg font-mono
            hover:bg-nexus-accent transition-all duration-200
            disabled:opacity-50 disabled:cursor-not-allowed
            hover:shadow-lg hover:shadow-nexus-accent/30
          "
        >
          {isWaking ? (
            <span className="flex items-center gap-2">
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Waking...
            </span>
          ) : (
            'Wake Claude'
          )}
        </button>

        <p className="text-xs text-nexus-muted mt-6">
          Execute wake protocol to begin session
        </p>
      </div>
    </div>
  );
}

// ============================================================================
// Main Page
// ============================================================================

export default function HomePage() {
  const isAwake = useNexusStore((state) => state.isAwake);
  const connected = useNexusStore((state) => state.connected);
  const [mounted, setMounted] = useState(false);

  // Handle client-side mounting
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return <LoadingScreen />;
  }

  return (
    <main className="relative w-full h-screen overflow-hidden bg-nexus-dark">
      {/* 3D World Canvas */}
      <NexusCanvas className="absolute inset-0" />

      {/* Welcome overlay when not awake */}
      {!isAwake && <WelcomeOverlay />}

      {/* UI Overlays (only show when awake) */}
      {isAwake && (
        <>
          {/* State Panel - Top Right */}
          <StatePanel />

          {/* Chat Panel - Bottom Left */}
          <ChatPanel />

          {/* Reflections Panel - Top Left */}
          <ReflectionView />
        </>
      )}

      {/* Connection indicator */}
      <div className="absolute bottom-4 right-4 flex items-center gap-2">
        <div
          className={`w-2 h-2 rounded-full ${
            connected ? 'bg-green-400' : 'bg-red-400'
          }`}
        />
        <span className="text-xs text-nexus-muted font-mono">
          {connected ? 'Connected' : 'Disconnected'}
        </span>
      </div>
    </main>
  );
}
