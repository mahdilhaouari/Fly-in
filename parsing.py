from __future__ import annotations
from enum import Enum


class ZoneType(Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class Zone:
    def __init__(self, name: str, color: str | None, max_drones: int,
                 zone_type: ZoneType, x: int, y: int,
                 connections: list) -> None:
        self.name = name
        self.color = color
        self.max_drones = max_drones
        self.zone_type = zone_type
        self.x = x
        self.y = y
        self.connections: list[Connection] = []


class Connection:
    def __init__(self, zone_a: Zone, zone_b: Zone,
                 max_link_capacity: int) -> None:
        self.max_link_capacity = max_link_capacity
        self.zone_a = zone_a
        self.zone_b = zone_b

    def other_side(self, zone: Zone) -> Zone:
        return self.zone_b if zone is self.zone_a else self.zone_a

class Graph:
    def __init__(self, zones: dict[str, Zone], connections: list[Connection],
                 start: Zone, end: Zone) -> None:
        self.zones = zones
        self.connections = connections
        self.start = start
        self.end = end
