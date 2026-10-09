from __future__ import annotations
from enum import Enum


class ParseError(Exception):
    """The map file is written wrong."""


class NoPathError(Exception):
    """The map is written right, but the end cannot be reached."""


class SimulationError(Exception):
    """The planner could not finish the simulation."""


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
    """One place on the map."""

    def __init__(self, name: str, color: str | None, max_drones: int,
                 zone_type: ZoneType, x: int, y: int) -> None:
        self.name = name
        self.color = color
        self.max_drones = max_drones
        self.zone_type = zone_type
        self.x = x
        self.y = y
        self.connections: list[Connection] = []

    @property
    def cost(self) -> int:
        """How many turns it takes to enter this zone."""
        if self.zone_type in (ZoneType.NORMAL, ZoneType.PRIORITY):
            return 1
        elif self.zone_type == ZoneType.RESTRICTED:
            return 2
        raise ValueError(f"blocked zone {self.name} has no cost")

    @property
    def is_enterable(self) -> bool:
        return self.zone_type is not ZoneType.BLOCKED

    def connection_to(self, other: Zone) -> Connection:
        for conn in self.connections:
            if conn.other_side(self) is other:
                return conn
        raise ValueError(
            f"no connection between {self.name} and {other.name}"
        )


class Connection:
    """A two-way link between two zones."""

    def __init__(self, zone_a: Zone, zone_b: Zone,
                 max_link_capacity: int) -> None:
        self.max_link_capacity = max_link_capacity
        self.zone_a = zone_a
        self.zone_b = zone_b

    @property
    def name(self) -> str:
        return f"{self.zone_a.name}-{self.zone_b.name}"

    def other_side(self, zone: Zone) -> Zone:
        return self.zone_b if zone is self.zone_a else self.zone_a


class Graph:
    """The whole map: every zone, every connection, the start and the end."""

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
            raise ParseError(f"{first_zone.name} and {second_zone.name} "
                             "are already connected")
        conn = Connection(first_zone, second_zone, capacity)
        first_zone.connections.append(conn)
        second_zone.connections.append(conn)
        self.connections.append(conn)

    def add_zone(self, zone: Zone, kind: HubKind) -> None:
        # First check everything, then change the graph.
        if zone.name in self.zones:
            raise ParseError(f"zone {zone.name} already exists")
        if kind == HubKind.START and self.start is not None:
            raise ParseError("there are two start hubs")
        if kind == HubKind.END and self.end is not None:
            raise ParseError("there are two end hubs")

        self.zones[zone.name] = zone
        if kind == HubKind.START:
            self.start = zone
        elif kind == HubKind.END:
            self.end = zone

    def start_validate(self) -> None:
        if self.start is None:
            raise ParseError("no start hub found")

    def end_validate(self) -> None:
        if self.end is None:
            raise ParseError("no end hub found")


class Drone:
    """One drone. Its route is planned by the Planner, not stored here."""

    def __init__(self, drone_id: int, start: Zone) -> None:
        self.id = drone_id
        self.start = start


class Movement:
    """One line part of the output: drone `drone` goes to `target`."""

    def __init__(self, drone: Drone, target: Zone | Connection) -> None:
        self.drone = drone
        self.target = target