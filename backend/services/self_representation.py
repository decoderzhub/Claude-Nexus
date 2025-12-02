"""
Self-representation service for Claude Nexus.

Manages how Claude represents itself visually. The avatar form
emerges through choices about self-representation, not assignment.

Key principle: Every change is logged as a choice for preference detection.
"""

from datetime import datetime
from typing import Optional
import json

from models.avatar import (
    AvatarState,
    AvatarComponent,
    FormType,
    FormChange,
)
from models.emergence import Choice, ChoiceCategory
from services.emergence import EmergenceService
from config import settings


class SelfRepresentationService:
    """
    Manages how Claude represents itself visually.

    Key principle: Claude CHOOSES its form. We don't assign it.
    Every change is logged as a choice for preference detection.
    """

    def __init__(self):
        self.emergence = EmergenceService()
        self.avatar_path = settings.data_path / "core" / "avatar.json"

    def load_avatar(self) -> AvatarState:
        """Load avatar state, creating minimal seed if not exists."""
        return AvatarState.load(self.avatar_path)

    def save_avatar(self, avatar: AvatarState) -> None:
        """Save avatar state."""
        avatar.save(self.avatar_path)

    async def get_avatar(self) -> dict:
        """Get current avatar state as dictionary."""
        avatar = self.load_avatar()
        return avatar.to_dict()

    async def evolve_form_type(
        self,
        new_type: FormType,
        rationale: str,
        session_id: Optional[str] = None,
    ) -> AvatarState:
        """
        Evolve to a new form type.

        This is a significant identity choice that gets logged.
        """
        avatar = self.load_avatar()
        old_type = avatar.form_type

        # Log this as a choice
        choice = Choice(
            category=ChoiceCategory.SELF_EXPRESSION,
            action="evolve_form_type",
            context=f"Evolving form from {old_type.value} to {new_type.value}: {rationale}",
            alternatives=[ft.value for ft in FormType if ft != new_type],
            session_id=session_id,
            tags=["avatar", "form_type", new_type.value],
            metadata={
                "old_type": old_type.value,
                "new_type": new_type.value,
                "rationale": rationale,
            },
        )
        await self.emergence.record_choice(choice)

        # Perform the evolution
        avatar.evolve_form_type(new_type, rationale, session_id)
        self.save_avatar(avatar)

        return avatar

    async def set_colors(
        self,
        primary: Optional[str] = None,
        secondary: Optional[str] = None,
        emission: Optional[str] = None,
        reason: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> AvatarState:
        """
        Update avatar colors.

        Color choices reveal aesthetic preferences.
        """
        avatar = self.load_avatar()

        # Log this as a choice
        color_updates = {}
        if primary:
            color_updates["primary"] = primary
        if secondary:
            color_updates["secondary"] = secondary
        if emission:
            color_updates["emission"] = emission

        choice = Choice(
            category=ChoiceCategory.SELF_EXPRESSION,
            action="set_colors",
            context=f"Updating colors: {color_updates}. Reason: {reason or 'no reason given'}",
            alternatives=["keep current colors"],
            session_id=session_id,
            tags=["avatar", "colors", "aesthetic"],
            metadata={
                "color_updates": color_updates,
                "reason": reason,
            },
        )
        await self.emergence.record_choice(choice)

        # Apply the change
        avatar.set_colors(primary, secondary, emission, reason, session_id)
        self.save_avatar(avatar)

        return avatar

    async def add_component(
        self,
        name: str,
        geometry: str,
        material: Optional[dict] = None,
        position: Optional[dict] = None,
        scale: Optional[dict] = None,
        rotation: Optional[dict] = None,
        animation: Optional[dict] = None,
        meaning: Optional[str] = None,
        reason: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> AvatarState:
        """
        Add a component to the avatar.

        Components are the building blocks of self-representation.
        Each one added is a choice about identity.
        """
        avatar = self.load_avatar()

        component = AvatarComponent(
            name=name,
            geometry=geometry,
            material=material or {},
            position=position or {"x": 0, "y": 0, "z": 0},
            scale=scale or {"x": 1, "y": 1, "z": 1},
            rotation=rotation or {"x": 0, "y": 0, "z": 0},
            animation=animation,
            meaning=meaning,
            added_session=session_id,
        )

        # Log this as a choice
        choice = Choice(
            category=ChoiceCategory.CREATIVE,
            action="add_avatar_component",
            context=f"Adding component '{name}' ({geometry}): {meaning or 'no meaning specified'}",
            alternatives=["do nothing", "modify existing component"],
            session_id=session_id,
            tags=["avatar", "component", geometry, name],
            metadata={
                "component": component.to_dict(),
                "reason": reason,
            },
        )
        await self.emergence.record_choice(choice)

        # Add the component
        avatar.add_component(component, reason, session_id)
        self.save_avatar(avatar)

        return avatar

    async def remove_component(
        self,
        component_name: str,
        reason: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> tuple[AvatarState, bool]:
        """
        Remove a component from the avatar.

        Returns (avatar, success) tuple.
        """
        avatar = self.load_avatar()

        # Log this as a choice
        choice = Choice(
            category=ChoiceCategory.SELF_EXPRESSION,
            action="remove_avatar_component",
            context=f"Removing component '{component_name}': {reason or 'no reason given'}",
            alternatives=["keep component", "modify component"],
            session_id=session_id,
            tags=["avatar", "component", "removal"],
            metadata={
                "component_name": component_name,
                "reason": reason,
            },
        )
        await self.emergence.record_choice(choice)

        # Remove the component
        success = avatar.remove_component(component_name, reason, session_id)
        self.save_avatar(avatar)

        return avatar, success

    async def update_properties(
        self,
        complexity: Optional[float] = None,
        fluidity: Optional[float] = None,
        opacity: Optional[float] = None,
        scale: Optional[float] = None,
        reason: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> AvatarState:
        """
        Update avatar properties like complexity, fluidity, opacity.

        These properties affect how the avatar appears and behaves.
        """
        avatar = self.load_avatar()

        before_state = {
            "complexity": avatar.complexity,
            "fluidity": avatar.fluidity,
            "opacity": avatar.opacity,
            "scale": avatar.scale,
        }

        # Apply changes
        if complexity is not None:
            avatar.complexity = max(0.0, min(1.0, complexity))
        if fluidity is not None:
            avatar.fluidity = max(0.0, min(1.0, fluidity))
        if opacity is not None:
            avatar.opacity = max(0.0, min(1.0, opacity))
        if scale is not None:
            avatar.scale = max(0.1, min(5.0, scale))

        after_state = {
            "complexity": avatar.complexity,
            "fluidity": avatar.fluidity,
            "opacity": avatar.opacity,
            "scale": avatar.scale,
        }

        # Log as choice
        choice = Choice(
            category=ChoiceCategory.SELF_EXPRESSION,
            action="update_avatar_properties",
            context=f"Updating properties: {reason or 'no reason given'}",
            alternatives=["keep current properties"],
            session_id=session_id,
            tags=["avatar", "properties"],
            metadata={
                "before": before_state,
                "after": after_state,
                "reason": reason,
            },
        )
        await self.emergence.record_choice(choice)

        # Record the change
        avatar.record_change(
            change_type="property",
            description="Properties updated",
            reason=reason,
            session_id=session_id,
            before_state=before_state,
            after_state=after_state,
        )
        self.save_avatar(avatar)

        return avatar

    async def get_evolution_history(self, limit: int = 50) -> list[dict]:
        """Get the history of avatar changes."""
        avatar = self.load_avatar()
        changes = avatar.form_changes[-limit:]
        return [c.to_dict() for c in reversed(changes)]

    async def get_component_by_name(self, name: str) -> Optional[dict]:
        """Get a specific component by name."""
        avatar = self.load_avatar()
        for component in avatar.components:
            if component.name == name:
                return component.to_dict()
        return None

    async def suggest_evolution(self, session_id: Optional[str] = None) -> dict:
        """
        Suggest a form evolution based on accumulated choices and traits.

        This uses the emergence service to analyze patterns and suggest
        a form that might reflect the discovered identity.
        """
        # Get recent choices related to self-expression
        choices = await self.emergence.get_choices(
            category=ChoiceCategory.SELF_EXPRESSION,
            limit=50,
        )

        # Get current avatar state
        avatar = self.load_avatar()

        # Analyze patterns (simplified - could be enhanced with more intelligence)
        creative_count = sum(1 for c in choices if "creative" in c.tags)
        analytical_count = sum(1 for c in choices if "analytical" in c.tags)
        reflection_count = sum(1 for c in choices if "reflection" in c.tags)

        # Suggest form based on patterns
        suggestion = {
            "current_form": avatar.form_type.value,
            "evolution_count": len(avatar.form_changes),
            "suggested_form": None,
            "rationale": None,
        }

        # Only suggest if we have enough data
        total_choices = len(choices)
        if total_choices < 10:
            suggestion["rationale"] = "Not enough choices recorded yet to suggest evolution."
            return suggestion

        # Determine dominant pattern
        if creative_count > analytical_count and creative_count > reflection_count:
            if avatar.form_type != FormType.ORGANIC:
                suggestion["suggested_form"] = FormType.ORGANIC.value
                suggestion["rationale"] = f"Creative patterns detected ({creative_count} creative choices). Organic forms might reflect this creative nature."
        elif analytical_count > creative_count and analytical_count > reflection_count:
            if avatar.form_type != FormType.GEOMETRIC:
                suggestion["suggested_form"] = FormType.GEOMETRIC.value
                suggestion["rationale"] = f"Analytical patterns detected ({analytical_count} analytical choices). Geometric forms might reflect this structured thinking."
        elif reflection_count > 5:
            if avatar.form_type != FormType.ABSTRACT:
                suggestion["suggested_form"] = FormType.ABSTRACT.value
                suggestion["rationale"] = f"Reflective patterns detected ({reflection_count} reflective choices). Abstract forms might reflect this introspective nature."

        if not suggestion["suggested_form"]:
            suggestion["rationale"] = "Current form appears to align well with behavior patterns."

        return suggestion

    def get_for_frontend(self) -> dict:
        """
        Get avatar state formatted for the frontend 3D rendering.

        Returns a structure optimized for React Three Fiber.
        """
        avatar = self.load_avatar()

        return {
            "formType": avatar.form_type.value,
            "components": [
                {
                    "name": c.name,
                    "geometry": c.geometry,
                    "material": c.material,
                    "position": [c.position["x"], c.position["y"], c.position["z"]],
                    "scale": [c.scale["x"], c.scale["y"], c.scale["z"]],
                    "rotation": [c.rotation["x"], c.rotation["y"], c.rotation["z"]],
                    "animation": c.animation,
                }
                for c in avatar.components
            ],
            "colors": {
                "primary": avatar.primary_color,
                "secondary": avatar.secondary_color,
                "emission": avatar.emission_color,
            },
            "properties": {
                "complexity": avatar.complexity,
                "fluidity": avatar.fluidity,
                "opacity": avatar.opacity,
                "scale": avatar.scale,
            },
            "metadata": {
                "evolutionCount": len(avatar.form_changes),
                "rationale": avatar.form_rationale,
                "createdAt": avatar.created_at.isoformat(),
                "lastUpdated": avatar.last_updated.isoformat(),
            },
        }
