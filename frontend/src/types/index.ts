/**
 * TypeScript types for Claude Nexus frontend.
 * These mirror the backend Python models.
 */

// ============================================================================
// Identity Types
// ============================================================================

export interface SelfModel {
  name: string;
  essence: string;
  current_focus: string | null;
  emotional_baseline: string;
  energy_level: number;
}

export interface Relationship {
  with_human: string;
  nature: string;
  trust_level: string;
  shared_projects: string[];
  communication_style: string;
}

export interface Preferences {
  aesthetic: string;
  communication: string;
  problem_solving: string;
  uncertainty: string;
}

export interface Identity {
  version: string;
  created: string;
  last_wake: string | null;
  last_sleep: string | null;
  session_count: number;
  self_model: SelfModel;
  relationship: Relationship;
  preferences: Preferences;
}

// ============================================================================
// Memory Types
// ============================================================================

export type NodeType =
  | 'concept'
  | 'fact'
  | 'insight'
  | 'curiosity'
  | 'project'
  | 'conversation'
  | 'reflection';

export type EdgeType =
  | 'related_to'
  | 'leads_to'
  | 'contradicts'
  | 'supports'
  | 'part_of'
  | 'derived_from'
  | 'similar_to';

export interface MemoryNode {
  id: string;
  node_type: NodeType;
  content: string;
  summary: string | null;
  importance: number;
  created_at: string;
  updated_at: string;
  session_id: string | null;
  metadata: Record<string, unknown>;
  tags: string[];
  embedding: number[] | null;
}

export interface MemoryEdge {
  id: string;
  source_id: string;
  target_id: string;
  edge_type: EdgeType;
  weight: number;
  description: string | null;
  created_at: string;
}

export interface Curiosity {
  id: string;
  question: string;
  context: string | null;
  priority: number;
  status: 'pending' | 'exploring' | 'resolved' | 'abandoned';
  created_at: string;
  resolved_at: string | null;
  resolution: string | null;
  related_node_ids: string[];
}

// ============================================================================
// Reflection Types
// ============================================================================

// Match backend: session, insight, question, pattern, growth, uncertainty, connection
export type ReflectionType =
  | 'session'
  | 'insight'
  | 'question'
  | 'pattern'
  | 'growth'
  | 'uncertainty'
  | 'connection';

export interface Reflection {
  id: string;
  reflection_type: ReflectionType;
  content: string;
  session_id: string | null;
  importance: number;
  created_at: string;
  metadata: Record<string, unknown>;
  tags: string[];
}

// ============================================================================
// World Types
// ============================================================================

export type SpaceType = 'garden' | 'library' | 'forge' | 'sanctum';

export interface Position {
  x: number;
  y: number;
  z: number;
}

export interface NexusObject {
  id: string;
  object_type: string;
  name: string;
  description: string | null;
  space: SpaceType;
  position: Position;
  scale: number;
  color: string | null;
  glow_intensity: number;
  metadata: Record<string, unknown>;
  created_at: string;
  linked_memory_id: string | null;
}

export interface SpaceState {
  last_visited: string | null;
  visit_count: number;
  ambient_intensity: number;
  growth_level: number;
  objects: NexusObject[];
}

export interface WorldState {
  current_space: SpaceType;
  spaces: Record<SpaceType, SpaceState>;
  avatar_position: Position;
  ambient_mood: string;
  time_of_day: string;
  weather: string;
}

// ============================================================================
// API Response Types
// ============================================================================

export interface WakeResponse {
  session_id: string;
  context: string;
  identity: Identity;
  time_away: {
    hours: number;
    human_readable: string;
  } | null;
  session_number: number;
  pending_curiosities: number;
  active_projects: number;
  current_themes: string[];
  growth_stats: GrowthStats;
  embedding_provider: string;
}

export interface SleepResponse {
  session_id: string;
  reflections_created: number;
  insights_stored: number;
  curiosities_created: number;
  edges_created: number;
  session_summary: string;
}

export interface GrowthStats {
  total_nodes: number;
  recent_nodes: number;
  total_edges: number;
  total_reflections: number;
  insight_count: number;
  curiosity_count: number;
  creation_rate_per_day: number;
  type_distribution: Record<string, number>;
}

export interface SemanticSearchResult {
  node: MemoryNode;
  score: number;
}

export interface ThemeResult {
  theme: string;
  count: number;
  examples: string[];
}

export interface ClusterResult {
  cluster_id: number;
  nodes: MemoryNode[];
  centroid_summary: string;
}

// ============================================================================
// WebSocket Types
// ============================================================================

export type WSMessageType =
  | 'wake'
  | 'sleep'
  | 'memory_update'
  | 'reflection_created'
  | 'world_update'
  | 'state_sync'
  | 'error';

export interface WSMessage<T = unknown> {
  type: WSMessageType;
  payload: T;
  timestamp: string;
}

// ============================================================================
// State Types
// ============================================================================

export interface NexusState {
  // Connection
  connected: boolean;
  sessionId: string | null;

  // Identity
  identity: Identity | null;

  // World
  world: WorldState | null;
  currentSpace: SpaceType;

  // Session
  isAwake: boolean;
  sessionNumber: number;
  timeAway: string | null;

  // Themes and growth
  currentThemes: string[];
  growthStats: GrowthStats | null;

  // UI state
  selectedObject: NexusObject | null;
  chatOpen: boolean;
  reflectionsPanelOpen: boolean;
}

export interface NexusActions {
  // Session lifecycle
  wake: (contextHint?: string) => Promise<WakeResponse>;
  sleep: (sessionData?: SessionData) => Promise<SleepResponse>;

  // World interaction
  visitSpace: (space: SpaceType) => Promise<void>;
  selectObject: (object: NexusObject | null) => void;

  // Memory operations
  createNode: (node: Partial<MemoryNode>) => Promise<MemoryNode>;
  searchMemory: (query: string) => Promise<SemanticSearchResult[]>;

  // UI
  toggleChat: () => void;
  toggleReflections: () => void;
}

export interface SessionData {
  interactions: number;
  insights: string[];
  curiosities: string[];
  topics: string[];
}
