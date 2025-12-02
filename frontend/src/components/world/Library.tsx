'use client';

/**
 * The Library space in Claude's Nexus world.
 * Represents accumulated knowledge — stored memories, concepts, and facts.
 */

import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Box, Text } from '@react-three/drei';
import * as THREE from 'three';
import { useNexusStore } from '@/components/providers/NexusProvider';

// ============================================================================
// Knowledge Crystal - Represents a memory node
// ============================================================================

interface KnowledgeCrystalProps {
  position: [number, number, number];
  scale?: number;
  importance?: number;
  index: number;
}

function KnowledgeCrystal({
  position,
  scale = 1,
  importance = 0.5,
  index,
}: KnowledgeCrystalProps) {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (!meshRef.current) return;
    const time = state.clock.elapsedTime;

    // Subtle rotation
    meshRef.current.rotation.y = time * 0.1 + index;
    meshRef.current.rotation.x = Math.sin(time * 0.2 + index) * 0.1;

    // Pulse based on importance
    const pulse = 1 + Math.sin(time * 2 + index) * 0.05 * importance;
    meshRef.current.scale.setScalar(scale * pulse);
  });

  return (
    <mesh ref={meshRef} position={position}>
      <octahedronGeometry args={[0.3 * scale]} />
      <meshStandardMaterial
        color="#3b82f6"
        emissive="#3b82f6"
        emissiveIntensity={importance * 0.5}
        transparent
        opacity={0.7 + importance * 0.3}
        roughness={0.1}
        metalness={0.9}
      />
    </mesh>
  );
}

// ============================================================================
// Floating Shelves - Ethereal book-like structures
// ============================================================================

interface ShelfProps {
  position: [number, number, number];
  rotation?: [number, number, number];
  width?: number;
}

function Shelf({ position, rotation = [0, 0, 0], width = 4 }: ShelfProps) {
  return (
    <group position={position} rotation={rotation}>
      {/* Shelf platform */}
      <Box args={[width, 0.05, 0.5]} position={[0, 0, 0]}>
        <meshStandardMaterial
          color="#1e3a5f"
          emissive="#1e3a5f"
          emissiveIntensity={0.1}
          transparent
          opacity={0.5}
          metalness={0.8}
          roughness={0.2}
        />
      </Box>

      {/* Books/data blocks on shelf */}
      {Array.from({ length: Math.floor(width * 2) }).map((_, i) => (
        <Box
          key={i}
          args={[0.15, 0.3 + Math.random() * 0.2, 0.3]}
          position={[-width / 2 + 0.2 + i * 0.25, 0.2, 0]}
        >
          <meshStandardMaterial
            color={`hsl(${210 + Math.random() * 30}, 70%, ${40 + Math.random() * 20}%)`}
            emissive="#3b82f6"
            emissiveIntensity={0.1}
            roughness={0.4}
            metalness={0.6}
          />
        </Box>
      ))}
    </group>
  );
}

// ============================================================================
// Data Streams - Flowing information visualization
// ============================================================================

function DataStreams() {
  const linesRef = useRef<THREE.Group>(null);

  const lines = useMemo(() => {
    const result = [];
    for (let i = 0; i < 20; i++) {
      const points = [];
      const startY = -2 + Math.random() * 8;
      const x = (Math.random() - 0.5) * 15;
      const z = (Math.random() - 0.5) * 15;

      for (let j = 0; j < 10; j++) {
        points.push(new THREE.Vector3(x + Math.sin(j * 0.5) * 0.5, startY + j * 0.3, z + Math.cos(j * 0.5) * 0.5));
      }

      result.push({ points, key: i });
    }
    return result;
  }, []);

  useFrame((state) => {
    if (!linesRef.current) return;
    const time = state.clock.elapsedTime;

    linesRef.current.children.forEach((child, i) => {
      if (child instanceof THREE.Line) {
        const material = child.material as THREE.LineBasicMaterial;
        material.opacity = 0.3 + Math.sin(time * 2 + i) * 0.2;
      }
    });
  });

  return (
    <group ref={linesRef}>
      {lines.map(({ points, key }) => (
        <line key={key}>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              count={points.length}
              array={new Float32Array(points.flatMap((p) => [p.x, p.y, p.z]))}
              itemSize={3}
            />
          </bufferGeometry>
          <lineBasicMaterial color="#3b82f6" transparent opacity={0.3} />
        </line>
      ))}
    </group>
  );
}

// ============================================================================
// Library Ground
// ============================================================================

function LibraryGround() {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -2, 0]} receiveShadow>
      <circleGeometry args={[15, 64]} />
      <meshStandardMaterial
        color="#0a0a1f"
        emissive="#0a1020"
        emissiveIntensity={0.1}
        roughness={0.8}
        metalness={0.3}
      />
    </mesh>
  );
}

// ============================================================================
// Main Library Component
// ============================================================================

export default function Library() {
  const world = useNexusStore((state) => state.world);
  const growthStats = useNexusStore((state) => state.growthStats);
  const libraryState = world?.spaces?.library;
  const growthLevel = libraryState?.growth_level ?? 0.5;

  const nodeCount = growthStats?.total_nodes ?? 0;

  // Generate knowledge crystals based on node count
  const crystals = useMemo(() => {
    const result = [];
    const crystalCount = Math.min(30, Math.floor(5 + nodeCount * 0.1));

    for (let i = 0; i < crystalCount; i++) {
      const angle = (i / crystalCount) * Math.PI * 2;
      const radius = 2 + Math.random() * 6;
      const x = Math.cos(angle) * radius;
      const y = -1 + Math.random() * 4;
      const z = Math.sin(angle) * radius;
      const scale = 0.5 + Math.random();
      const importance = Math.random();

      result.push(
        <KnowledgeCrystal
          key={i}
          position={[x, y, z]}
          scale={scale}
          importance={importance}
          index={i}
        />
      );
    }

    return result;
  }, [nodeCount]);

  // Shelves arrangement
  const shelves = useMemo(() => {
    const result = [];
    for (let i = 0; i < 5; i++) {
      const y = -1 + i * 1.5;
      const angle = (i * Math.PI) / 5;

      result.push(
        <Shelf
          key={i}
          position={[Math.cos(angle) * 5, y, Math.sin(angle) * 5]}
          rotation={[0, -angle, 0]}
          width={3 + Math.random() * 2}
        />
      );
    }
    return result;
  }, []);

  return (
    <group>
      {/* Ambient light specific to library */}
      <pointLight
        position={[0, 5, 0]}
        color="#3b82f6"
        intensity={0.5}
        distance={20}
      />

      {/* Ground */}
      <LibraryGround />

      {/* Data streams */}
      <DataStreams />

      {/* Shelves */}
      {shelves}

      {/* Knowledge crystals */}
      {crystals}

      {/* Central archive core */}
      <mesh position={[0, 0, 0]}>
        <icosahedronGeometry args={[0.8]} />
        <meshStandardMaterial
          color="#3b82f6"
          emissive="#3b82f6"
          emissiveIntensity={0.3 + growthLevel * 0.4}
          transparent
          opacity={0.8}
          roughness={0.1}
          metalness={0.9}
          wireframe
        />
      </mesh>
    </group>
  );
}
