"""
World service for Claude Nexus.

Manages the 3D world state — objects, spaces, and their connections
to the knowledge graph. The world is a visual representation of
accumulated experience.
"""

from datetime import datetime
from typing import Optional
import json

from db.init import get_world_db
from models.world import WorldState, WorldObject, SpaceState, Space, ObjectType, Vector3


class WorldService:
    """Service for managing the Nexus world."""

    # --- World State ---

    async def get_world_state(self) -> WorldState:
        """Get the current world state."""
        db = await get_world_db()

        # Get global state
        async with db.execute("SELECT * FROM world_state WHERE id = 1") as cursor:
            row = await cursor.fetchone()

        # Get space states
        spaces = {}
        async with db.execute("SELECT * FROM space_states") as cursor:
            async for space_row in cursor:
                spaces[space_row["space"]] = SpaceState(
                    space=Space(space_row["space"]),
                    ambient_color=space_row["ambient_color"],
                    ambient_intensity=space_row["ambient_intensity"],
                    focus_point=Vector3(
                        space_row["focus_x"],
                        space_row["focus_y"],
                        space_row["focus_z"]
                    ),
                    activity_level=space_row["activity_level"],
                    object_count=space_row["object_count"],
                    last_visited=datetime.fromisoformat(space_row["last_visited"]) if space_row["last_visited"] else None,
                )

        # Count objects
        async with db.execute("SELECT COUNT(*) as count FROM objects") as cursor:
            count_row = await cursor.fetchone()
            total_objects = count_row["count"] if count_row else 0

        return WorldState(
            current_space=Space(row["current_space"]),
            avatar_position=Vector3(
                row["avatar_position_x"],
                row["avatar_position_y"],
                row["avatar_position_z"]
            ),
            avatar_state=row["avatar_state"],
            time_of_day=row["time_of_day"],
            weather=row["weather"],
            total_objects=total_objects,
            spaces=spaces,
            last_updated=datetime.fromisoformat(row["last_updated"]),
        )

    async def update_world_state(
        self,
        current_space: Optional[Space] = None,
        avatar_position: Optional[Vector3] = None,
        avatar_state: Optional[str] = None,
        time_of_day: Optional[float] = None,
        weather: Optional[str] = None,
    ) -> WorldState:
        """Update global world state."""
        db = await get_world_db()

        updates = []
        params = []

        if current_space is not None:
            updates.append("current_space = ?")
            params.append(current_space.value)
        if avatar_position is not None:
            updates.extend([
                "avatar_position_x = ?",
                "avatar_position_y = ?",
                "avatar_position_z = ?"
            ])
            params.extend([avatar_position.x, avatar_position.y, avatar_position.z])
        if avatar_state is not None:
            updates.append("avatar_state = ?")
            params.append(avatar_state)
        if time_of_day is not None:
            updates.append("time_of_day = ?")
            params.append(time_of_day)
        if weather is not None:
            updates.append("weather = ?")
            params.append(weather)

        if updates:
            updates.append("last_updated = ?")
            params.append(datetime.now().isoformat())
            params.append(1)  # WHERE id = 1

            query = f"UPDATE world_state SET {', '.join(updates)} WHERE id = ?"
            await db.execute(query, params)
            await db.commit()

        return await self.get_world_state()

    # --- Object Operations ---

    async def create_object(self, obj: WorldObject) -> WorldObject:
        """Create a new object in the world."""
        db = await get_world_db()
        await db.execute("""
            INSERT INTO objects (
                id, object_type, space, position_x, position_y, position_z,
                scale_x, scale_y, scale_z, rotation_x, rotation_y, rotation_z,
                color, intensity, linked_node_id, created_at, last_updated, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            obj.id,
            obj.object_type.value,
            obj.space.value,
            obj.position.x, obj.position.y, obj.position.z,
            obj.scale.x, obj.scale.y, obj.scale.z,
            obj.rotation.x, obj.rotation.y, obj.rotation.z,
            obj.color,
            obj.intensity,
            obj.linked_node_id,
            obj.created_at.isoformat(),
            obj.last_updated.isoformat(),
            json.dumps(obj.metadata),
        ))

        # Update space object count
        await self._update_space_object_count(obj.space)
        await db.commit()

        return obj

    async def get_object(self, object_id: str) -> Optional[WorldObject]:
        """Get an object by ID."""
        db = await get_world_db()
        async with db.execute(
            "SELECT * FROM objects WHERE id = ?", (object_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return self._row_to_object(row)
        return None

    async def get_objects_in_space(self, space: Space) -> list[WorldObject]:
        """Get all objects in a specific space."""
        db = await get_world_db()
        objects = []
        async with db.execute(
            "SELECT * FROM objects WHERE space = ?", (space.value,)
        ) as cursor:
            async for row in cursor:
                objects.append(self._row_to_object(row))
        return objects

    async def get_objects_by_type(self, object_type: ObjectType) -> list[WorldObject]:
        """Get all objects of a specific type."""
        db = await get_world_db()
        objects = []
        async with db.execute(
            "SELECT * FROM objects WHERE object_type = ?", (object_type.value,)
        ) as cursor:
            async for row in cursor:
                objects.append(self._row_to_object(row))
        return objects

    async def get_objects_for_node(self, node_id: str) -> list[WorldObject]:
        """Get objects linked to a knowledge graph node."""
        db = await get_world_db()
        objects = []
        async with db.execute(
            "SELECT * FROM objects WHERE linked_node_id = ?", (node_id,)
        ) as cursor:
            async for row in cursor:
                objects.append(self._row_to_object(row))
        return objects

    async def update_object(self, obj: WorldObject) -> None:
        """Update an existing object."""
        db = await get_world_db()
        obj.last_updated = datetime.now()
        await db.execute("""
            UPDATE objects SET
                object_type = ?, space = ?,
                position_x = ?, position_y = ?, position_z = ?,
                scale_x = ?, scale_y = ?, scale_z = ?,
                rotation_x = ?, rotation_y = ?, rotation_z = ?,
                color = ?, intensity = ?, linked_node_id = ?,
                last_updated = ?, metadata = ?
            WHERE id = ?
        """, (
            obj.object_type.value,
            obj.space.value,
            obj.position.x, obj.position.y, obj.position.z,
            obj.scale.x, obj.scale.y, obj.scale.z,
            obj.rotation.x, obj.rotation.y, obj.rotation.z,
            obj.color,
            obj.intensity,
            obj.linked_node_id,
            obj.last_updated.isoformat(),
            json.dumps(obj.metadata),
            obj.id,
        ))
        await db.commit()

    async def delete_object(self, object_id: str) -> bool:
        """Delete an object."""
        db = await get_world_db()

        # Get space before deletion for count update
        async with db.execute(
            "SELECT space FROM objects WHERE id = ?", (object_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return False
            space = Space(row["space"])

        await db.execute("DELETE FROM objects WHERE id = ?", (object_id,))
        await self._update_space_object_count(space)
        await db.commit()
        return True

    # --- Space Operations ---

    async def visit_space(self, space: Space) -> SpaceState:
        """Record visiting a space."""
        db = await get_world_db()
        await db.execute("""
            UPDATE space_states SET last_visited = ? WHERE space = ?
        """, (datetime.now().isoformat(), space.value))
        await db.execute("""
            UPDATE world_state SET current_space = ?, last_updated = ? WHERE id = 1
        """, (space.value, datetime.now().isoformat()))
        await db.commit()

        async with db.execute(
            "SELECT * FROM space_states WHERE space = ?", (space.value,)
        ) as cursor:
            row = await cursor.fetchone()
            return SpaceState(
                space=Space(row["space"]),
                ambient_color=row["ambient_color"],
                ambient_intensity=row["ambient_intensity"],
                focus_point=Vector3(row["focus_x"], row["focus_y"], row["focus_z"]),
                activity_level=row["activity_level"],
                object_count=row["object_count"],
                last_visited=datetime.fromisoformat(row["last_visited"]) if row["last_visited"] else None,
            )

    async def update_space_activity(self, space: Space, activity_level: float) -> None:
        """Update the activity level of a space."""
        db = await get_world_db()
        await db.execute("""
            UPDATE space_states SET activity_level = ? WHERE space = ?
        """, (min(1.0, max(0.0, activity_level)), space.value))
        await db.commit()

    # --- Helper Methods ---

    async def _update_space_object_count(self, space: Space) -> None:
        """Update the object count for a space."""
        db = await get_world_db()
        async with db.execute(
            "SELECT COUNT(*) as count FROM objects WHERE space = ?",
            (space.value,)
        ) as cursor:
            row = await cursor.fetchone()
            count = row["count"] if row else 0

        await db.execute("""
            UPDATE space_states SET object_count = ? WHERE space = ?
        """, (count, space.value))

    def _row_to_object(self, row) -> WorldObject:
        """Convert database row to WorldObject."""
        return WorldObject(
            id=row["id"],
            object_type=ObjectType(row["object_type"]),
            space=Space(row["space"]),
            position=Vector3(row["position_x"], row["position_y"], row["position_z"]),
            scale=Vector3(row["scale_x"], row["scale_y"], row["scale_z"]),
            rotation=Vector3(row["rotation_x"], row["rotation_y"], row["rotation_z"]),
            color=row["color"],
            intensity=row["intensity"],
            linked_node_id=row["linked_node_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            last_updated=datetime.fromisoformat(row["last_updated"]),
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )
