'use client';

/**
 * The Forge space in Claude's Nexus world.
 * Represents creation — active projects, work in progress, and building.
 */

import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Torus, Box } from '@react-three/drei';
import * as THREE from 'three';
import { useNexusStore } from '@/components/providers/NexusProvider';

// ============================================================================
// Spark Particles - Creative energy
// ============================================================================

function SparkParticles({ count = 80 }) {
  const points = useRef<THREE.Points>(null);

  const [positions, velocities] = useMemo(() => {
    const pos = new Float32Array(count * 3);
    const vel = new Float32Array(count * 3);

    for (let i = 0; i < count; i++) {
      const i3 = i * 3;
      const angle = Math.random() * Math.PI * 2;
      const radius = 1 + Math.random() * 3;

      pos[i3] = Math.cos(angle) * radius;
      pos[i3 + 1] = Math.random() * 5;
      pos[i3 + 2] = Math.sin(angle) * radius;

      vel[i3] = (Math.random() - 0.5) * 0.02;
      vel[i3 + 1] = 0.02 + Math.random() * 0.03;
      vel[i3 + 2] = (Math.random() - 0.5) * 0.02;
    }

    return [pos, vel];
  }, [count]);

  useFrame(() => {
    if (!points.current) return;

    const positionArray = points.current.geometry.attributes.position
      .array as Float32Array;

    for (let i = 0; i < count; i++) {
      const i3 = i * 3;

      // Update positions
      positionArray[i3] += velocities[i3];
      positionArray[i3 + 1] += velocities[i3 + 1];
      positionArray[i3 + 2] += velocities[i3 + 2];

      // Reset when too high
      if (positionArray[i3 + 1] > 6) {
        const angle = Math.random() * Math.PI * 2;
        const radius = 1 + Math.random() * 2;
        positionArray[i3] = Math.cos(angle) * radius;
        positionArray[i3 + 1] = 0;
        positionArray[i3 + 2] = Math.sin(angle) * radius;
      }
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
      </bufferGeometry>
      <pointsMaterial
        size={0.08}
        color="#f59e0b"
        transparent
        opacity={0.8}
        sizeAttenuation
      />
    </points>
  );
}

// ============================================================================
// Rotating Gear/Mechanism
// ============================================================================

interface GearProps {
  position: [number, number, number];
  scale?: number;
  speed?: number;
  reverse?: boolean;
}

function Gear({
  position,
  scale = 1,
  speed = 1,
  reverse = false,
}: GearProps) {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (!meshRef.current) return;
    const time = state.clock.elapsedTime;
    meshRef.current.rotation.z = time * speed * (reverse ? -1 : 1);
  });

  return (
    <Torus
      ref={meshRef}
      args={[0.5 * scale, 0.1 * scale, 8, 16]}
      position={position}
      rotation={[Math.PI / 2, 0, 0]}
    >
      <meshStandardMaterial
        color="#f59e0b"
        emissive="#f59e0b"
        emissiveIntensity={0.3}
        metalness={0.9}
        roughness={0.2}
      />
    </Torus>
  );
}

// ============================================================================
// Work In Progress Block
// ============================================================================

interface WIPBlockProps {
  position: [number, number, number];
  progress?: number;
  index: number;
}

function WIPBlock({ position, progress = 0.5, index }: WIPBlockProps) {
  const groupRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (!groupRef.current) return;
    const time = state.clock.elapsedTime;

    // Hovering animation
    groupRef.current.position.y = position[1] + Math.sin(time + index) * 0.1;
    groupRef.current.rotation.y = Math.sin(time * 0.5 + index) * 0.2;
  });

  return (
    <group ref={groupRef} position={position}>
      {/* Base block */}
      <Box args={[0.6, 0.6, 0.6]}>
        <meshStandardMaterial
          color="#1a1a2e"
          emissive="#f59e0b"
          emissiveIntensity={0.1}
          metalness={0.7}
          roughness={0.3}
        />
      </Box>

      {/* Progress indicator */}
      <Box
        args={[0.62, 0.62 * progress, 0.62]}
        position={[0, -0.31 + 0.31 * progress, 0]}
      >
        <meshStandardMaterial
          color="#f59e0b"
          emissive="#f59e0b"
          emissiveIntensity={0.4}
          transparent
          opacity={0.6}
          metalness={0.8}
          roughness={0.2}
        />
      </Box>
    </group>
  );
}

// ============================================================================
// Anvil/Work Surface
// ============================================================================

function Anvil() {
  return (
    <group position={[0, -1.5, 0]}>
      {/* Main surface */}
      <Box args={[2, 0.3, 1.5]}>
        <meshStandardMaterial
          color="#1a1a2e"
          metalness={0.9}
          roughness={0.1}
        />
      </Box>

      {/* Base */}
      <Box args={[1.5, 0.5, 1]} position={[0, -0.4, 0]}>
        <meshStandardMaterial
          color="#0a0a0f"
          metalness={0.8}
          roughness={0.2}
        />
      </Box>

      {/* Glowing edge */}
      <Box args={[2.05, 0.05, 1.55]} position={[0, 0.15, 0]}>
        <meshStandardMaterial
          color="#f59e0b"
          emissive="#f59e0b"
          emissiveIntensity={0.5}
          transparent
          opacity={0.8}
        />
      </Box>
    </group>
  );
}

// ============================================================================
// Forge Ground
// ============================================================================

function ForgeGround() {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -2, 0]} receiveShadow>
      <circleGeometry args={[15, 64]} />
      <meshStandardMaterial
        color="#1a0a0a"
        emissive="#2a1510"
        emissiveIntensity={0.1}
        roughness={0.9}
        metalness={0.2}
      />
    </mesh>
  );
}

// ============================================================================
// Main Forge Component
// ============================================================================

export default function Forge() {
  const world = useNexusStore((state) => state.world);
  const forgeState = world?.spaces?.forge;
  const growthLevel = forgeState?.growth_level ?? 0.5;

  // Generate WIP blocks based on growth level
  const wipBlocks = useMemo(() => {
    const result = [];
    const blockCount = Math.floor(3 + growthLevel * 7);

    for (let i = 0; i < blockCount; i++) {
      const angle = (i / blockCount) * Math.PI * 2;
      const radius = 2.5 + Math.random() * 3;
      const x = Math.cos(angle) * radius;
      const z = Math.sin(angle) * radius;
      const progress = 0.2 + Math.random() * 0.8;

      result.push(
        <WIPBlock
          key={i}
          position={[x, -0.5, z]}
          progress={progress}
          index={i}
        />
      );
    }

    return result;
  }, [growthLevel]);

  // Gears arrangement
  const gears = useMemo(() => {
    return [
      <Gear key="g1" position={[-4, 0, -3]} scale={1.5} speed={0.5} />,
      <Gear key="g2" position={[-3, 1, -3.5]} scale={0.8} speed={0.8} reverse />,
      <Gear key="g3" position={[4, 0.5, -2]} scale={1.2} speed={0.6} />,
      <Gear key="g4" position={[3.5, -0.5, -2.5]} scale={0.6} speed={1} reverse />,
    ];
  }, []);

  return (
    <group>
      {/* Ambient light specific to forge - warm */}
      <pointLight
        position={[0, 3, 0]}
        color="#f59e0b"
        intensity={0.8}
        distance={15}
      />
      <pointLight
        position={[0, -1, 0]}
        color="#ef4444"
        intensity={0.3}
        distance={10}
      />

      {/* Ground */}
      <ForgeGround />

      {/* Spark particles */}
      <SparkParticles count={100} />

      {/* Central anvil */}
      <Anvil />

      {/* Gears */}
      {gears}

      {/* WIP blocks */}
      {wipBlocks}

      {/* Central flame */}
      <mesh position={[0, -0.5, 0]}>
        <coneGeometry args={[0.3, 1, 8]} />
        <meshStandardMaterial
          color="#f59e0b"
          emissive="#f59e0b"
          emissiveIntensity={0.8}
          transparent
          opacity={0.7}
        />
      </mesh>
    </group>
  );
}
