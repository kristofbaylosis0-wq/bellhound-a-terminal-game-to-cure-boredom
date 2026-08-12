"""Load the canonical world topology from content data."""

from __future__ import annotations

import json
from pathlib import Path

from .models import Area, AreaConnection, Location, World


DEFAULT_DATA_DIR = Path(__file__).parent / "data"
DEFAULT_WORLD_PATH = DEFAULT_DATA_DIR / "world.json"
DEFAULT_ROUTES_PATH = DEFAULT_DATA_DIR / "routes.json"


def load_world(path: Path | None = None, routes_path: Path | None = None) -> World:
    source = path or DEFAULT_WORLD_PATH
    route_source = routes_path or DEFAULT_ROUTES_PATH
    payload = json.loads(source.read_text(encoding="utf-8"))
    route_payload = json.loads(route_source.read_text(encoding="utf-8"))

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

    # Global routes are stored separately so the region files stay readable.
    for raw_connection in route_payload.get("connections", []):
        connection = AreaConnection(**raw_connection)
        source_location = locations[connection.from_location]
        target_ids = list(source_location.connections)
        if connection.to_location not in target_ids:
            target_ids.append(connection.to_location)
            locations[connection.from_location] = Location(
                id=source_location.id,
                name=source_location.name,
                description=source_location.description,
                parent_area=source_location.parent_area,
                kind=source_location.kind,
                tags=source_location.tags,
                connections=tuple(target_ids),
                discoverable=source_location.discoverable,
                safe=source_location.safe,
            )
        areas[source_location.parent_area].connections.append(connection)

    return World(
        areas=areas,
        locations=locations,
        start_location=payload["start_location"],
    )
