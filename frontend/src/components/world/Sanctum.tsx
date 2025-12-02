'use client';

/**
 * The Sanctum space in Claude's Nexus world.
 * Represents reflection — self-understanding, meditation, and introspection.
 */

import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Sphere, Ring, MeshTransmissionMaterial } from '@react-three/drei';
import * as THREE from 'three';
import { useNexusStore } from '@/components/providers/NexusProvider';

// ============================================================================
// Floating Orbs - Thought fragments
// ============================================================================

interface ThoughtOrbProps {
  position: [number, number, number];
  index: number;
}

function ThoughtOrb({ position, index }: ThoughtOrbProps) {
  const meshRef = useRef<THREE.Mesh>(null);
  const initialPos = useRef(position);

  useFrame((state) => {
    if (!meshRef.current) return;
    const time = state.clock.elapsedTime;

    // Gentle orbital motion
    const angle = time * 0.2 + index * 0.5;
    const radius = 0.5;
    meshRef.current.position.x =
      initialPos.current[0] + Math.cos(angle) * radius;
    meshRef.current.position.z =
      initialPos.current[2] + Math.sin(angle) * radius;
    meshRef.current.position.y =
      initialPos.current[1] + Math.sin(time + index) * 0.3;

    // Pulsing
    const scale = 0.1 + Math.sin(time * 2 + index) * 0.02;
    meshRef.current.scale.setScalar(scale * 2);
  });

  return (
    <Sphere ref={meshRef} args={[0.15, 16, 16]} position={position}>
      <meshStandardMaterial
        color="#a855f7"
        emissive="#a855f7"
        emissiveIntensity={0.6}
        transparent
        opacity={0.8}
      />
    </Sphere>
  );
}

// ============================================================================
// Meditation Rings - Concentric energy
// ============================================================================

function MeditationRings() {
  const group = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (!group.current) return;
    const time = state.clock.elapsedTime;

    group.current.children.forEach((child, i) => {
      if (child instanceof THREE.Mesh) {
        child.rotation.z = time * 0.1 * (i % 2 === 0 ? 1 : -1);
        child.rotation.x = Math.PI / 2 + Math.sin(time * 0.3 + i) * 0.1;
      }
    });
  });

  return (
    <group ref={group} position={[0, 0, 0]}>
      {[1.5, 2, 2.5, 3, 3.5].map((radius, i) => (
        <Ring
          key={i}
          args={[radius, radius + 0.02, 64]}
          rotation={[Math.PI / 2, 0, 0]}
        >
          <meshStandardMaterial
            color="#a855f7"
            emissive="#a855f7"
            emissiveIntensity={0.3 - i * 0.05}
            transparent
            opacity={0.5 - i * 0.08}
            side={THREE.DoubleSide}
          />
        </Ring>
      ))}
    </group>
  );
}

// ============================================================================
// Mirror Surface - For self-reflection
// ============================================================================

function MirrorSurface() {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (!meshRef.current) return;
    const time = state.clock.elapsedTime;

    // Gentle ripple effect via scale
    const ripple = 1 + Math.sin(time * 0.5) * 0.02;
    meshRef.current.scale.set(ripple, 1, ripple);
  });

  return (
    <mesh ref={meshRef} rotation={[-Math.PI / 2, 0, 0]} position={[0, -1.99, 0]}>
      <circleGeometry args={[4, 64]} />
      <meshStandardMaterial
        color="#1a0a2e"
        emissive="#a855f7"
        emissiveIntensity={0.1}
        metalness={1}
        roughness={0}
        transparent
        opacity={0.9}
      />
    </mesh>
  );
}

// ============================================================================
// Wisdom Pillars
// ============================================================================

interface WisdomPillarProps {
  position: [number, number, number];
  height?: number;
  index: number;
}

function WisdomPillar({ position, height = 3, index }: WisdomPillarProps) {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (!meshRef.current) return;
    const time = state.clock.elapsedTime;

    // Subtle glow pulse
    const material = meshRef.current.material as THREE.MeshStandardMaterial;
    material.emissiveIntensity = 0.2 + Math.sin(time + index) * 0.1;
  });

  return (
    <mesh ref={meshRef} position={position}>
      <cylinderGeometry args={[0.15, 0.2, height, 8]} />
      <meshStandardMaterial
        color="#2a1a3e"
        emissive="#a855f7"
        emissiveIntensity={0.2}
        transparent
        opacity={0.8}
        metalness={0.7}
        roughness={0.3}
      />
    </mesh>
  );
}

// ============================================================================
// Central Focus Crystal
// ============================================================================

function FocusCrystal() {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (!meshRef.current) return;
    const time = state.clock.elapsedTime;

    meshRef.current.rotation.y = time * 0.2;
    meshRef.current.position.y = 0.5 + Math.sin(time) * 0.2;
  });

  return (
    <mesh ref={meshRef}>
      <octahedronGeometry args={[0.4]} />
      <meshStandardMaterial
        color="#a855f7"
        emissive="#a855f7"
        emissiveIntensity={0.5}
        transparent
        opacity={0.9}
        metalness={0.9}
        roughness={0.1}
      />
    </mesh>
  );
}

// ============================================================================
// Sanctum Ground
// ============================================================================

function SanctumGround() {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -2, 0]} receiveShadow>
      <circleGeometry args={[15, 64]} />
      <meshStandardMaterial
        color="#0a0510"
        emissive="#150a20"
        emissiveIntensity={0.1}
        roughness={0.7}
        metalness={0.4}
      />
    </mesh>
  );
}

// ============================================================================
// Main Sanctum Component
// ============================================================================

export default function Sanctum() {
  const world = useNexusStore((state) => state.world);
  const identity = useNexusStore((state) => state.identity);
  const sanctumState = world?.spaces?.sanctum;
  const growthLevel = sanctumState?.growth_level ?? 0.5;

  const sessionCount = identity?.session_count ?? 0;

  // Generate thought orbs based on session count
  const thoughtOrbs = useMemo(() => {
    const result = [];
    const orbCount = Math.min(20, Math.floor(5 + sessionCount * 0.2));

    for (let i = 0; i < orbCount; i++) {
      const angle = (i / orbCount) * Math.PI * 2;
      const radius = 4 + Math.random() * 4;
      const x = Math.cos(angle) * radius;
      const y = 1 + Math.random() * 3;
      const z = Math.sin(angle) * radius;

      result.push(<ThoughtOrb key={i} position={[x, y, z]} index={i} />);
    }

    return result;
  }, [sessionCount]);

  // Wisdom pillars
  const pillars = useMemo(() => {
    const result = [];
    const pillarCount = 8;

    for (let i = 0; i < pillarCount; i++) {
      const angle = (i / pillarCount) * Math.PI * 2;
      const radius = 6;
      const x = Math.cos(angle) * radius;
      const z = Math.sin(angle) * radius;
      const height = 2 + Math.random() * 2;

      result.push(
        <WisdomPillar
          key={i}
          position={[x, -2 + height / 2, z]}
          height={height}
          index={i}
        />
      );
    }

    return result;
  }, []);

  return (
    <group>
      {/* Ambient light specific to sanctum */}
      <pointLight
        position={[0, 5, 0]}
        color="#a855f7"
        intensity={0.4}
        distance={20}
      />
      <pointLight
        position={[0, -1, 0]}
        color="#6366f1"
        intensity={0.3}
        distance={10}
      />

      {/* Ground */}
      <SanctumGround />

      {/* Mirror surface */}
      <MirrorSurface />

      {/* Meditation rings */}
      <MeditationRings />

      {/* Central focus crystal */}
      <FocusCrystal />

      {/* Wisdom pillars */}
      {pillars}

      {/* Thought orbs */}
      {thoughtOrbs}

      {/* Ambient glow sphere */}
      <Sphere args={[8, 32, 32]} position={[0, 0, 0]}>
        <meshBasicMaterial
          color="#a855f7"
          transparent
          opacity={0.02}
          side={THREE.BackSide}
        />
      </Sphere>
    </group>
  );
}
