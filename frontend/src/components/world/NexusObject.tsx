'use client';

/**
 * Dynamic object renderer for items in Claude's Nexus world.
 * Objects can be linked to memories, reflections, or other data.
 */

import { useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html, Box, Sphere, Torus, Cone, Dodecahedron } from '@react-three/drei';
import * as THREE from 'three';
import type { NexusObject as NexusObjectType } from '@/types';

// ============================================================================
// Object Type to Geometry Mapping
// ============================================================================

const geometryComponents: Record<string, React.FC<{ scale: number }>> = {
  cube: ({ scale }) => <Box args={[scale, scale, scale]} />,
  sphere: ({ scale }) => <Sphere args={[scale / 2, 32, 32]} />,
  torus: ({ scale }) => <Torus args={[scale / 2, scale / 6, 16, 32]} />,
  cone: ({ scale }) => <Cone args={[scale / 2, scale, 8]} />,
  crystal: ({ scale }) => <Dodecahedron args={[scale / 2]} />,
  default: ({ scale }) => <Box args={[scale, scale, scale]} />,
};

// ============================================================================
// Space to Default Color Mapping
// ============================================================================

const spaceColors: Record<string, string> = {
  garden: '#22c55e',
  library: '#3b82f6',
  forge: '#f59e0b',
  sanctum: '#a855f7',
};

// ============================================================================
// Main Component
// ============================================================================

interface NexusObjectProps {
  object: NexusObjectType;
  onClick?: () => void;
  showLabel?: boolean;
}

export default function NexusObject({
  object,
  onClick,
  showLabel = false,
}: NexusObjectProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  const [hovered, setHovered] = useState(false);

  // Get geometry component
  const GeometryComponent =
    geometryComponents[object.object_type] || geometryComponents.default;

  // Determine color
  const color = object.color || spaceColors[object.space] || '#6366f1';

  // Animation
  useFrame((state) => {
    if (!meshRef.current) return;
    const time = state.clock.elapsedTime;

    // Subtle floating animation
    meshRef.current.position.y =
      object.position.y + Math.sin(time + object.position.x) * 0.1;

    // Rotation
    meshRef.current.rotation.y = time * 0.2;

    // Glow pulse when hovered
    if (hovered) {
      const material = meshRef.current.material as THREE.MeshStandardMaterial;
      material.emissiveIntensity = object.glow_intensity + Math.sin(time * 4) * 0.2;
    }
  });

  return (
    <group
      position={[object.position.x, object.position.y, object.position.z]}
      onClick={(e) => {
        e.stopPropagation();
        onClick?.();
      }}
      onPointerOver={(e) => {
        e.stopPropagation();
        setHovered(true);
        document.body.style.cursor = 'pointer';
      }}
      onPointerOut={() => {
        setHovered(false);
        document.body.style.cursor = 'auto';
      }}
    >
      <mesh ref={meshRef}>
        <GeometryComponent scale={object.scale} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={hovered ? object.glow_intensity * 1.5 : object.glow_intensity}
          transparent
          opacity={0.9}
          metalness={0.7}
          roughness={0.3}
        />
      </mesh>

      {/* Point light for glow effect */}
      <pointLight
        color={color}
        intensity={object.glow_intensity * (hovered ? 2 : 1)}
        distance={object.scale * 3}
        decay={2}
      />

      {/* Label on hover or always if showLabel */}
      {(hovered || showLabel) && (
        <Html
          position={[0, object.scale + 0.5, 0]}
          center
          distanceFactor={10}
          style={{ pointerEvents: 'none' }}
        >
          <div className="bg-nexus-surface/90 px-3 py-1 rounded-lg border border-nexus-muted/30 backdrop-blur-sm">
            <p className="text-white text-sm font-mono whitespace-nowrap">
              {object.name}
            </p>
            {object.description && (
              <p className="text-nexus-muted text-xs max-w-48 truncate">
                {object.description}
              </p>
            )}
          </div>
        </Html>
      )}
    </group>
  );
}
