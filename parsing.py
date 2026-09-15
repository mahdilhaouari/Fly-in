from __future__ import annotations
from enum import Enum


class ParseError(Exception):
    pass


class ZoneType(Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class HubKind(Enum):
    START = "start_hub"
    END = "end_hub"
    NORMAL = "hub"


class Zone:
    def __init__(self, name: str, color: str | None, max_drones: int,
                 zone_type: ZoneType, x: int, y: int) -> None:
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
    def __init__(self) -> None:
        self.zones: dict[str, Zone] = {}
        self.connections: list[Connection] = []
        self.start: Zone | None = None
        self.end: Zone | None = None

    def has_connection(self, first_zone: Zone, second_zone: Zone) -> bool:
        for con in self.connections:
            if (
                con.zone_a is first_zone and con.zone_b is second_zone
            ) or (
                con.zone_b is first_zone and con.zone_a is second_zone
            ):
                return True
        return False

    def add_connection(self, first_zone: Zone,
                       second_zone: Zone, capacity: int) -> None:
        if self.has_connection(first_zone, second_zone):
            raise ParseError("the 2 zones already connected")
        conn = Connection(first_zone, second_zone, capacity)
        first_zone.connections.append(conn)
        second_zone.connections.append(conn)
        self.connections.append(conn)

    def add_zone(self, zone: Zone, kind: HubKind) -> None:
        if zone.name in self.zones:
            raise ParseError("this zone already exist")
        self.zones[zone.name] = zone

        if kind == HubKind.START:
            if self.start is not None:
                raise ParseError("there is two start hubs")
            self.start = zone

        if kind == HubKind.END:
            if self.end is not None:
                raise ParseError("there is two end hubs")
            self.end = zone

    def start_validate(self) -> None:
        if self.start is None:
            raise ParseError("no start hub found")

    def end_validate(self) -> None:
        if self.end is None:
            raise ParseError("no end hub found")


if __name__ == "__main__":
    zone1 = Zone("zone1", "red", 3, ZoneType.RESTRICTED, 3, 3)
    zone3 = Zone("zone1", "red", 3, ZoneType.RESTRICTED, 3, 3)
    zone2 = Zone("zone1", "red", 3, ZoneType.RESTRICTED, 3, 3)
    graph = Graph(
    zones={
        zone1.name: zone1,
        zone2.name: zone2,
    },
    connections=[],
    start=zone1,
    end=zone2,
)
    graph.add_connection(zone1, zone2, 2)
    print(graph.has_connection(zone1, zone3))
