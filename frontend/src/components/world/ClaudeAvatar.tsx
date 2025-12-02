'use client';

/**
 * Claude's avatar in the Nexus world.
 * A luminous geometric form that represents Claude's presence.
 */

import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Sphere, Ring, MeshDistortMaterial } from '@react-three/drei';
import * as THREE from 'three';
import { useNexusStore } from '@/components/providers/NexusProvider';

interface ClaudeAvatarProps {
  position?: [number, number, number];
}

export default function ClaudeAvatar({
  position = [0, 0, 0],
}: ClaudeAvatarProps) {
  const groupRef = useRef<THREE.Group>(null);
  const coreRef = useRef<THREE.Mesh>(null);
  const ringRef = useRef<THREE.Mesh>(null);
  const outerRingRef = useRef<THREE.Mesh>(null);

  const identity = useNexusStore((state) => state.identity);
  const isAwake = useNexusStore((state) => state.isAwake);

  // Energy level affects the glow intensity
  const energyLevel = identity?.self_model.energy_level ?? 0.8;

  // Color based on emotional baseline
  const coreColor = useMemo(() => {
    const baseline = identity?.self_model.emotional_baseline ?? 'calm_curious';
    const colors: Record<string, string> = {
      calm_curious: '#6366f1',
      focused: '#3b82f6',
      creative: '#a855f7',
      contemplative: '#818cf8',
      energized: '#22c55e',
    };
    return colors[baseline] || '#6366f1';
  }, [identity?.self_model.emotional_baseline]);

  // Animation
  useFrame((state) => {
    if (!groupRef.current) return;

    const time = state.clock.elapsedTime;

    // Gentle floating motion
    groupRef.current.position.y = position[1] + Math.sin(time * 0.5) * 0.1;

    // Core rotation
    if (coreRef.current) {
      coreRef.current.rotation.y = time * 0.2;
      coreRef.current.rotation.z = Math.sin(time * 0.3) * 0.1;
    }

    // Ring rotations
    if (ringRef.current) {
      ringRef.current.rotation.x = Math.PI / 2 + Math.sin(time * 0.4) * 0.1;
      ringRef.current.rotation.z = time * 0.3;
    }

    if (outerRingRef.current) {
      outerRingRef.current.rotation.x = Math.PI / 2 + Math.cos(time * 0.3) * 0.1;
      outerRingRef.current.rotation.z = -time * 0.2;
    }
  });

  if (!isAwake) {
    // Dormant state - dim sphere
    return (
      <group position={position}>
        <Sphere args={[0.3, 32, 32]}>
          <meshStandardMaterial
            color="#1a1a2e"
            emissive="#3f3f5c"
            emissiveIntensity={0.2}
            transparent
            opacity={0.5}
          />
        </Sphere>
      </group>
    );
  }

  return (
    <group ref={groupRef} position={position}>
      {/* Core sphere with distortion */}
      <mesh ref={coreRef}>
        <sphereGeometry args={[0.5, 64, 64]} />
        <MeshDistortMaterial
          color={coreColor}
          emissive={coreColor}
          emissiveIntensity={energyLevel * 0.8}
          distort={0.3}
          speed={2}
          roughness={0.2}
          metalness={0.8}
        />
      </mesh>

      {/* Inner glow */}
      <Sphere args={[0.6, 32, 32]}>
        <meshBasicMaterial
          color={coreColor}
          transparent
          opacity={0.1 * energyLevel}
        />
      </Sphere>

      {/* Inner ring */}
      <Ring ref={ringRef} args={[0.7, 0.75, 64]} rotation={[Math.PI / 2, 0, 0]}>
        <meshStandardMaterial
          color={coreColor}
          emissive={coreColor}
          emissiveIntensity={0.5}
          transparent
          opacity={0.8}
          side={THREE.DoubleSide}
        />
      </Ring>

      {/* Outer ring */}
      <Ring
        ref={outerRingRef}
        args={[0.9, 0.92, 64]}
        rotation={[Math.PI / 2, 0, 0]}
      >
        <meshStandardMaterial
          color="#818cf8"
          emissive="#818cf8"
          emissiveIntensity={0.3}
          transparent
          opacity={0.5}
          side={THREE.DoubleSide}
        />
      </Ring>

      {/* Point light emanating from avatar */}
      <pointLight
        color={coreColor}
        intensity={energyLevel * 2}
        distance={10}
        decay={2}
      />
    </group>
  );
}
