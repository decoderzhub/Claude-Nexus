'use client';

/**
 * The Garden space in Claude's Nexus world.
 * Represents growth — new ideas, curiosities, and emerging concepts.
 */

import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { useNexusStore } from '@/components/providers/NexusProvider';

// ============================================================================
// Particle System - Floating Seeds/Spores
// ============================================================================

function FloatingParticles({ count = 100 }) {
  const points = useRef<THREE.Points>(null);

  const [positions, sizes] = useMemo(() => {
    const pos = new Float32Array(count * 3);
    const size = new Float32Array(count);

    for (let i = 0; i < count; i++) {
      const i3 = i * 3;
      pos[i3] = (Math.random() - 0.5) * 20;
      pos[i3 + 1] = Math.random() * 10;
      pos[i3 + 2] = (Math.random() - 0.5) * 20;
      size[i] = Math.random() * 0.1 + 0.02;
    }

    return [pos, size];
  }, [count]);

  useFrame((state) => {
    if (!points.current) return;
    const time = state.clock.elapsedTime;

    const positionArray = points.current.geometry.attributes.position
      .array as Float32Array;

    for (let i = 0; i < count; i++) {
      const i3 = i * 3;
      positionArray[i3 + 1] += Math.sin(time + i) * 0.002;

      // Gentle drift
      positionArray[i3] += Math.sin(time * 0.1 + i) * 0.001;
      positionArray[i3 + 2] += Math.cos(time * 0.1 + i) * 0.001;
    }

    points.current.geometry.attributes.position.needsUpdate = true;
  });

  return (
    <points ref={points}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={count}
          array={positions}
          itemSize={3}
        />
        <bufferAttribute
          attach="attributes-size"
          count={count}
          array={sizes}
          itemSize={1}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.1}
        color="#22c55e"
        transparent
        opacity={0.6}
        sizeAttenuation
      />
    </points>
  );
}

// ============================================================================
// Growing Crystal/Plant Form
// ============================================================================

interface GrowthFormProps {
  position: [number, number, number];
  scale?: number;
  growthLevel?: number;
}

function GrowthForm({ position, scale = 1, growthLevel = 1 }: GrowthFormProps) {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (!meshRef.current) return;
    const time = state.clock.elapsedTime;

    // Subtle breathing animation
    meshRef.current.scale.y = scale * (1 + Math.sin(time * 2) * 0.05 * growthLevel);
  });

  return (
    <mesh ref={meshRef} position={position}>
      <coneGeometry args={[0.2 * scale, 1 * scale * growthLevel, 6]} />
      <meshStandardMaterial
        color="#22c55e"
        emissive="#22c55e"
        emissiveIntensity={0.3}
        transparent
        opacity={0.8}
        roughness={0.3}
        metalness={0.7}
      />
    </mesh>
  );
}

// ============================================================================
// Ground with Moss/Growth Pattern
// ============================================================================

function GardenGround() {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -2, 0]} receiveShadow>
      <circleGeometry args={[15, 64]} />
      <meshStandardMaterial
        color="#0a1a0f"
        emissive="#0a2010"
        emissiveIntensity={0.1}
        roughness={0.9}
        metalness={0.1}
      />
    </mesh>
  );
}

// ============================================================================
// Main Garden Component
// ============================================================================

export default function Garden() {
  const world = useNexusStore((state) => state.world);
  const gardenState = world?.spaces?.garden;
  const growthLevel = gardenState?.growth_level ?? 0.5;

  // Generate growth forms based on growth level
  const growthForms = useMemo(() => {
    const forms = [];
    const formCount = Math.floor(5 + growthLevel * 15);

    for (let i = 0; i < formCount; i++) {
      const angle = (i / formCount) * Math.PI * 2;
      const radius = 3 + Math.random() * 8;
      const x = Math.cos(angle) * radius;
      const z = Math.sin(angle) * radius;
      const scale = 0.5 + Math.random() * 1.5;

      forms.push(
        <GrowthForm
          key={i}
          position={[x, -2 + scale * 0.5, z]}
          scale={scale}
          growthLevel={growthLevel}
        />
      );
    }

    return forms;
  }, [growthLevel]);

  return (
    <group>
      {/* Ambient light specific to garden */}
      <pointLight
        position={[0, 5, 0]}
        color="#22c55e"
        intensity={0.5}
        distance={20}
      />

      {/* Ground */}
      <GardenGround />

      {/* Floating particles */}
      <FloatingParticles count={150} />

      {/* Growth forms */}
      {growthForms}

      {/* Central focal point */}
      <mesh position={[0, -1, 0]}>
        <dodecahedronGeometry args={[0.5]} />
        <meshStandardMaterial
          color="#22c55e"
          emissive="#22c55e"
          emissiveIntensity={0.5 + growthLevel * 0.3}
          transparent
          opacity={0.9}
          roughness={0.2}
          metalness={0.8}
        />
      </mesh>
    </group>
  );
}
