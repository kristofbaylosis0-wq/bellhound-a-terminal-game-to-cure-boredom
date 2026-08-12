"""Authoritative world topology models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


AreaKind = Literal["major", "small"]


@dataclass(frozen=True)
class Location:
    id: str
    name: str
    description: str
    parent_area: str
    kind: AreaKind = "small"
    tags: tuple[str, ...] = ()
    connections: tuple[str, ...] = ()
    discoverable: bool = True
    safe: bool = False


@dataclass(frozen=True)
class AreaConnection:
    from_location: str
    to_location: str
    travel_description: str
    requirements: tuple[dict[str, Any], ...] = ()


@dataclass
class Area:
    id: str
    name: str
    description: str
    theme: str
    atmosphere: str
    parent: str | None = None
    locations: list[Location] = field(default_factory=list)
    connections: list[AreaConnection] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class World:
    areas: dict[str, Area]
    locations: dict[str, Location]
    start_location: str

    def area(self, area_id: str) -> Area:
        return self.areas[area_id]

    def location(self, location_id: str) -> Location:
        return self.locations[location_id]

    def neighbors(self, location_id: str) -> list[Location]:
        location = self.location(location_id)
        return [self.locations[target] for target in location.connections]
