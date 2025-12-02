'use client';

/**
 * Main Three.js canvas for the Nexus world.
 * Renders the 3D environment where Claude exists.
 */

import { Suspense, useRef } from 'react';
import { Canvas } from '@react-three/fiber';
import {
  OrbitControls,
  PerspectiveCamera,
  Environment,
  Stars,
  Float,
} from '@react-three/drei';
import { useNexusStore } from '@/components/providers/NexusProvider';
import ClaudeAvatar from './ClaudeAvatar';
import Garden from './Garden';
import Library from './Library';
import Forge from './Forge';
import Sanctum from './Sanctum';
import NexusObject from './NexusObject';
import type { SpaceType, NexusObject as NexusObjectType } from '@/types';

// ============================================================================
// Loading Fallback
// ============================================================================

function LoadingFallback() {
  return (
    <mesh>
      <sphereGeometry args={[0.5, 32, 32]} />
      <meshStandardMaterial color="#6366f1" wireframe />
    </mesh>
  );
}

// ============================================================================
// Space Renderer
// ============================================================================

interface SpaceRendererProps {
  space: SpaceType;
  objects: NexusObjectType[];
  onObjectClick?: (object: NexusObjectType) => void;
}

function SpaceRenderer({ space, objects, onObjectClick }: SpaceRendererProps) {
  const spaceComponents = {
    garden: <Garden />,
    library: <Library />,
    forge: <Forge />,
    sanctum: <Sanctum />,
  };

  return (
    <group>
      {/* Render the space environment */}
      {spaceComponents[space]}

      {/* Render objects in this space */}
      {objects
        .filter((obj) => obj.space === space)
        .map((obj) => (
          <NexusObject
            key={obj.id}
            object={obj}
            onClick={() => onObjectClick?.(obj)}
          />
        ))}
    </group>
  );
}

// ============================================================================
// Ground Plane
// ============================================================================

function GroundPlane() {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -2, 0]} receiveShadow>
      <planeGeometry args={[100, 100]} />
      <meshStandardMaterial
        color="#0a0a0f"
        metalness={0.8}
        roughness={0.4}
        transparent
        opacity={0.8}
      />
    </mesh>
  );
}

// ============================================================================
// Ambient Effects
// ============================================================================

function AmbientEffects() {
  return (
    <>
      <Stars
        radius={100}
        depth={50}
        count={5000}
        factor={4}
        saturation={0}
        fade
        speed={1}
      />
      <fog attach="fog" args={['#0a0a0f', 10, 50]} />
    </>
  );
}

// ============================================================================
// Main Canvas Component
// ============================================================================

interface NexusCanvasProps {
  className?: string;
}

export default function NexusCanvas({ className }: NexusCanvasProps) {
  const currentSpace = useNexusStore((state) => state.currentSpace);
  const world = useNexusStore((state) => state.world);
  const setSelectedObject = useNexusStore((state) => state.setSelectedObject);
  const isAwake = useNexusStore((state) => state.isAwake);

  const controlsRef = useRef(null);

  // Get objects for current space - safely handle missing world/spaces
  const objects = world?.spaces?.[currentSpace]?.objects ?? [];

  return (
    <div className={`w-full h-full ${className ?? ''}`}>
      <Canvas
        shadows
        dpr={[1, 2]}
        gl={{ antialias: true, alpha: false }}
        style={{ background: '#0a0a0f', width: '100%', height: '100%' }}
      >
        <Suspense fallback={<LoadingFallback />}>
          {/* Camera */}
          <PerspectiveCamera makeDefault position={[0, 5, 10]} fov={60} />
          <OrbitControls
            ref={controlsRef}
            enablePan={false}
            enableZoom={true}
            minDistance={5}
            maxDistance={30}
            maxPolarAngle={Math.PI / 2 - 0.1}
          />

          {/* Lighting */}
          <ambientLight intensity={0.3} />
          <pointLight
            position={[10, 10, 10]}
            intensity={1}
            castShadow
            shadow-mapSize-width={2048}
            shadow-mapSize-height={2048}
          />
          <pointLight position={[-10, 5, -10]} intensity={0.5} color="#818cf8" />

          {/* Environment */}
          <Environment preset="night" />
          <AmbientEffects />
          <GroundPlane />

          {/* Claude's Avatar - always present when awake */}
          {isAwake && (
            <Float speed={2} rotationIntensity={0.2} floatIntensity={0.5}>
              <ClaudeAvatar position={[0, 0, 0]} />
            </Float>
          )}

          {/* Current Space */}
          <SpaceRenderer
            space={currentSpace}
            objects={objects}
            onObjectClick={setSelectedObject}
          />
        </Suspense>
      </Canvas>
    </div>
  );
}
