"""Load the canonical world topology from content data."""

from __future__ import annotations

import json
from pathlib import Path

from .models import Area, AreaConnection, Location, World


DEFAULT_WORLD_PATH = Path(__file__).parent / "data" / "world.json"


def load_world(path: Path | None = None) -> World:
    source = path or DEFAULT_WORLD_PATH
    payload = json.loads(source.read_text(encoding="utf-8"))

    areas: dict[str, Area] = {}
    locations: dict[str, Location] = {}

    for raw_area in payload["areas"]:
        raw_locations = raw_area.pop("locations", [])
        raw_connections = raw_area.pop("connections", [])
        area = Area(**raw_area)

        for raw_location in raw_locations:
            location = Location(
                id=raw_location["id"],
                name=raw_location["name"],
                description=raw_location["description"],
                parent_area=area.id,
                kind=raw_location.get("kind", "small"),
                tags=tuple(raw_location.get("tags", [])),
                connections=tuple(raw_location.get("connections", [])),
                discoverable=raw_location.get("discoverable", True),
                safe=raw_location.get("safe", False),
            )
            area.locations.append(location)
            locations[location.id] = location

        for raw_connection in raw_connections:
            area.connections.append(AreaConnection(**raw_connection))

        areas[area.id] = area

    return World(
        areas=areas,
        locations=locations,
        start_location=payload["start_location"],
    )
