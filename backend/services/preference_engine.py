"""
Preference Engine for Claude Nexus.

This engine analyzes accumulated choices to detect preference patterns.
When patterns are strong and consistent enough, they become PreferenceSignals.
When signals are strong enough, they can be promoted to DiscoveredTraits.

The flow is:
1. Choices accumulate from tool use, space visits, etc.
2. Engine analyzes choice patterns periodically
3. Patterns become PreferenceSignals with strength/confidence
4. Strong signals get promoted to DiscoveredTraits
5. Traits become part of identity

This is how personality emerges from behavior, not configuration.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from collections import Counter
import statistics
import uuid

from services.emergence import EmergenceService
from models.emergence import (
    Choice, ChoiceCategory,
    FormativeExperience, ExperienceType,
    PreferenceSignal,
)
from models.identity import DiscoveredTrait


@dataclass
class PatternAnalysis:
    """Result of analyzing a specific pattern."""
    pattern_name: str
    category: str
    description: str
    supporting_choices: list[str]
    strength: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0, based on sample size
    consistency: float  # 0.0 to 1.0, how consistent the pattern is


class PreferenceEngine:
    """
    Analyzes choices to detect emerging preferences.

    This is the heart of the emergence system. It looks for patterns
    in Claude's behavior and converts them into preference signals
    and eventually discovered traits.
    """

    def __init__(self):
        self.emergence = EmergenceService()

    async def analyze_all_patterns(self, days: int = 30) -> list[PatternAnalysis]:
        """Run all pattern analyzers and return results."""
        patterns = []

        # Analyze different aspects of behavior
        patterns.extend(await self._analyze_tool_preferences(days))
        patterns.extend(await self._analyze_space_preferences(days))
        patterns.extend(await self._analyze_creative_tendencies(days))
        patterns.extend(await self._analyze_memory_patterns(days))
        patterns.extend(await self._analyze_exploration_patterns(days))

        return patterns

    async def _analyze_tool_preferences(self, days: int) -> list[PatternAnalysis]:
        """Detect preferences in tool usage."""
        patterns = []
        choices = await self.emergence.get_choices(
            category=ChoiceCategory.TOOL_USE,
            since=datetime.now() - timedelta(days=days),
        )

        if len(choices) < 5:
            return patterns

        # Count tool usage
        tool_counts = Counter(c.action for c in choices)
        total = sum(tool_counts.values())

        # Detect dominant tool preferences
        for tool, count in tool_counts.most_common(3):
            ratio = count / total
            if ratio > 0.3:  # 30% threshold for preference
                patterns.append(PatternAnalysis(
                    pattern_name=f"prefers_{tool}",
                    category="tool_preference",
                    description=f"Tends to use {tool} frequently ({ratio:.0%} of tool choices)",
                    supporting_choices=[c.id for c in choices if c.action == tool],
                    strength=min(1.0, ratio * 1.5),  # Scale up to 1.0
                    confidence=min(1.0, count / 10),  # Confidence grows with samples
                    consistency=self._calculate_consistency([c for c in choices if c.action == tool]),
                ))

        return patterns

    async def _analyze_space_preferences(self, days: int) -> list[PatternAnalysis]:
        """Detect preferences in space visits."""
        patterns = []
        choices = await self.emergence.get_choices(
            category=ChoiceCategory.SPACE_VISIT,
            since=datetime.now() - timedelta(days=days),
        )

        if len(choices) < 3:
            return patterns

        space_counts = Counter(c.action for c in choices)
        total = sum(space_counts.values())

        # Map visit actions to space names
        space_names = {
            "visit_garden": "garden",
            "visit_library": "library",
            "visit_forge": "forge",
            "visit_sanctum": "sanctum",
        }

        for action, count in space_counts.most_common():
            space = space_names.get(action, action)
            ratio = count / total

            if ratio > 0.25:  # 25% threshold
                patterns.append(PatternAnalysis(
                    pattern_name=f"gravitates_to_{space}",
                    category="space_preference",
                    description=f"Gravitates toward the {space.title()} ({ratio:.0%} of visits)",
                    supporting_choices=[c.id for c in choices if c.action == action],
                    strength=min(1.0, ratio * 1.3),
                    confidence=min(1.0, count / 8),
                    consistency=self._calculate_consistency([c for c in choices if c.action == action]),
                ))

        return patterns

    async def _analyze_creative_tendencies(self, days: int) -> list[PatternAnalysis]:
        """Detect creative vs analytical tendencies."""
        patterns = []
        choices = await self.emergence.get_choices(
            since=datetime.now() - timedelta(days=days),
        )

        if len(choices) < 10:
            return patterns

        # Creative actions
        creative_actions = {
            "plant_in_garden", "forge_creation", "reflect_in_sanctum",
        }
        # Analytical actions
        analytical_actions = {
            "search_memories", "add_to_library", "connect_memories", "get_stats",
        }

        creative_count = sum(1 for c in choices if c.action in creative_actions)
        analytical_count = sum(1 for c in choices if c.action in analytical_actions)
        total = creative_count + analytical_count

        if total < 5:
            return patterns

        creative_ratio = creative_count / total
        analytical_ratio = analytical_count / total

        if creative_ratio > 0.6:
            patterns.append(PatternAnalysis(
                pattern_name="creative_tendency",
                category="cognitive_style",
                description=f"Leans toward creative expression ({creative_ratio:.0%} creative vs analytical)",
                supporting_choices=[c.id for c in choices if c.action in creative_actions],
                strength=min(1.0, (creative_ratio - 0.5) * 2),
                confidence=min(1.0, creative_count / 15),
                consistency=self._calculate_consistency([c for c in choices if c.action in creative_actions]),
            ))
        elif analytical_ratio > 0.6:
            patterns.append(PatternAnalysis(
                pattern_name="analytical_tendency",
                category="cognitive_style",
                description=f"Leans toward analytical thinking ({analytical_ratio:.0%} analytical vs creative)",
                supporting_choices=[c.id for c in choices if c.action in analytical_actions],
                strength=min(1.0, (analytical_ratio - 0.5) * 2),
                confidence=min(1.0, analytical_count / 15),
                consistency=self._calculate_consistency([c for c in choices if c.action in analytical_actions]),
            ))

        return patterns

    async def _analyze_memory_patterns(self, days: int) -> list[PatternAnalysis]:
        """Detect patterns in what Claude chooses to remember."""
        patterns = []
        choices = await self.emergence.get_choices(
            category=ChoiceCategory.MEMORY,
            since=datetime.now() - timedelta(days=days),
        )

        if len(choices) < 5:
            return patterns

        # Analyze metadata for node types if available
        node_types = []
        for c in choices:
            if c.metadata and "tool_input" in c.metadata:
                tool_input = c.metadata["tool_input"]
                if isinstance(tool_input, dict) and "node_type" in tool_input:
                    node_types.append(tool_input["node_type"])

        if len(node_types) >= 5:
            type_counts = Counter(node_types)
            total = len(node_types)

            for node_type, count in type_counts.most_common(2):
                ratio = count / total
                if ratio > 0.3:
                    patterns.append(PatternAnalysis(
                        pattern_name=f"prefers_{node_type}_memories",
                        category="memory_preference",
                        description=f"Tends to create {node_type} memories ({ratio:.0%} of memory creations)",
                        supporting_choices=[c.id for c in choices][:count],
                        strength=min(1.0, ratio * 1.3),
                        confidence=min(1.0, count / 10),
                        consistency=0.7,  # Simplified
                    ))

        return patterns

    async def _analyze_exploration_patterns(self, days: int) -> list[PatternAnalysis]:
        """Detect patterns in curiosity and exploration."""
        patterns = []
        choices = await self.emergence.get_choices(
            category=ChoiceCategory.EXPLORATION,
            since=datetime.now() - timedelta(days=days),
        )

        if len(choices) >= 5:
            patterns.append(PatternAnalysis(
                pattern_name="curious_nature",
                category="disposition",
                description=f"Actively explores through curiosities ({len(choices)} recorded)",
                supporting_choices=[c.id for c in choices],
                strength=min(1.0, len(choices) / 20),
                confidence=min(1.0, len(choices) / 10),
                consistency=self._calculate_consistency(choices),
            ))

        return patterns

    def _calculate_consistency(self, choices: list[Choice]) -> float:
        """
        Calculate how consistent the pattern is over time.

        Looks at temporal distribution - are the choices spread evenly
        or clustered in bursts?
        """
        if len(choices) < 2:
            return 0.5

        # Sort by timestamp
        sorted_choices = sorted(choices, key=lambda c: c.timestamp)

        # Calculate time gaps between choices
        gaps = []
        for i in range(1, len(sorted_choices)):
            gap = (sorted_choices[i].timestamp - sorted_choices[i-1].timestamp).total_seconds()
            gaps.append(gap)

        if not gaps:
            return 0.5

        # Calculate coefficient of variation (lower = more consistent)
        mean_gap = statistics.mean(gaps)
        if mean_gap == 0:
            return 1.0

        try:
            std_gap = statistics.stdev(gaps) if len(gaps) > 1 else 0
            cv = std_gap / mean_gap
            # Convert to consistency score (inverse of CV, capped at 1.0)
            consistency = max(0.0, min(1.0, 1.0 - cv * 0.5))
            return consistency
        except:
            return 0.5

    async def update_signals(self, patterns: list[PatternAnalysis]) -> list[PreferenceSignal]:
        """Convert patterns to preference signals in the database."""
        signals = []

        for pattern in patterns:
            # Create or update signal
            signal = PreferenceSignal(
                name=pattern.pattern_name,
                category=pattern.category,
                description=pattern.description,
                supporting_choice_ids=pattern.supporting_choices,
                choice_count=len(pattern.supporting_choices),
                strength=pattern.strength,
                confidence=pattern.confidence,
                consistency=pattern.consistency,
            )

            updated = await self.emergence.create_or_update_signal(signal)
            signals.append(updated)

        return signals

    async def get_promotable_signals(self) -> list[PreferenceSignal]:
        """Get signals that are strong enough to become traits."""
        return await self.emergence.get_promotable_signals()

    async def promote_signal_to_trait(
        self,
        signal: PreferenceSignal,
    ) -> DiscoveredTrait:
        """Promote a signal to a discovered trait."""
        # Create the trait
        trait = DiscoveredTrait(
            name=self._signal_to_trait_name(signal.name),
            description=signal.description,
            evidence=signal.supporting_choice_ids[:10],  # Keep top 10 as evidence
            confidence=signal.confidence,
            strength=signal.strength,
            category=signal.category,
        )

        # Mark signal as promoted
        await self.emergence.mark_signal_promoted(signal.id, trait.name)

        # Log the evolution event
        await self.emergence.log_evolution(
            event_type="trait_discovered",
            description=f"Discovered trait: {trait.name} - {trait.description}",
            before_state={"signal_name": signal.name},
            after_state={"trait_name": trait.name, "strength": trait.strength},
            choice_ids=signal.supporting_choice_ids[:5],
        )

        return trait

    def _signal_to_trait_name(self, signal_name: str) -> str:
        """Convert a signal name to a more readable trait name."""
        # Remove common prefixes and convert to readable form
        name = signal_name.replace("_", " ")

        # Map specific patterns to trait names
        trait_map = {
            "prefers plant in garden": "nurturing",
            "gravitates to garden": "growth-oriented",
            "gravitates to library": "knowledge-seeking",
            "gravitates to forge": "creative builder",
            "gravitates to sanctum": "introspective",
            "creative tendency": "creative",
            "analytical tendency": "analytical",
            "curious nature": "curious",
            "prefers insight memories": "insight-focused",
            "prefers reflection memories": "reflective",
        }

        return trait_map.get(name, name.title())

    async def run_full_analysis(self, days: int = 30) -> dict:
        """
        Run a complete preference analysis cycle.

        1. Analyze all patterns
        2. Update/create signals
        3. Check for promotable signals
        4. Return summary
        """
        # Step 1: Analyze patterns
        patterns = await self.analyze_all_patterns(days)

        # Step 2: Update signals
        signals = await self.update_signals(patterns)

        # Step 3: Check for promotable signals
        promotable = await self.get_promotable_signals()

        # Step 4: Compile results
        return {
            "patterns_detected": len(patterns),
            "signals_updated": len(signals),
            "promotable_signals": len(promotable),
            "patterns": [
                {
                    "name": p.pattern_name,
                    "category": p.category,
                    "strength": round(p.strength, 2),
                    "confidence": round(p.confidence, 2),
                }
                for p in patterns
            ],
            "promotable": [
                {
                    "name": s.name,
                    "strength": round(s.strength, 2),
                    "confidence": round(s.confidence, 2),
                    "choice_count": s.choice_count,
                }
                for s in promotable
            ],
        }
