"""Independent checker for Fly-in simulation output.

This is a testing tool, not part of the graded program (subject, III.3).
It never uses the scheduler's logic: it only reads the map and the printed
lines, replays them, and checks every rule of the subject on its own.

Usage:
    python3 validator.py                  # validate every map under maps/
    python3 validator.py maps/a.txt ...   # validate only these maps
"""
import sys
from pathlib import Path

from data_model import (Graph, Zone, Connection, ZoneType, ParseError,
                        NoPathError, SimulationError)


class ValidationError(Exception):
    pass


class Validator:
    def __init__(self, graph: Graph, nb_drones: int) -> None:
        if graph.start is None or graph.end is None:
            raise ValidationError("the map has no start or end")
        self.graph = graph
        self.start: Zone = graph.start
        self.end: Zone = graph.end
        self.nb_drones = nb_drones

        # Every connection, found by its two zones in either order.
        self.links: dict[frozenset[Zone], Connection] = {
            frozenset((c.zone_a, c.zone_b)): c for c in graph.connections
        }

        # The state of the replay.
        self.position: dict[int, Zone] = {
            i: self.start for i in range(1, nb_drones + 1)
        }
        # drone id -> (connection, destination, turn it entered)
        self.transit: dict[int, tuple[Connection, Zone, int]] = {}
        self.delivered: set[int] = set()
        self.turn = 0

    # ------------------------------------------------------------ helpers

    def fail(self, message: str) -> ValidationError:
        return ValidationError(f"turn {self.turn}: {message}")

    def zone(self, name: str) -> Zone:
        if name not in self.graph.zones:
            raise self.fail(f"unknown zone '{name}'")
        return self.graph.zones[name]

    def link(self, a: Zone, b: Zone) -> Connection:
        conn = self.links.get(frozenset((a, b)))
        if conn is None:
            raise self.fail(f"{a.name} and {b.name} are not connected")
        return conn

    def parse_token(self, token: str) -> tuple[int, list[str]]:
        parts = token.split("-")
        if len(parts) not in (2, 3) or not parts[0].startswith("D"):
            raise self.fail(f"bad token '{token}'")
        try:
            drone_id = int(parts[0][1:])
        except ValueError as e:
            raise self.fail(f"bad drone id in '{token}'") from e
        if not 1 <= drone_id <= self.nb_drones:
            raise self.fail(f"unknown drone D{drone_id}")
        return drone_id, parts[1:]

    # --------------------------------------------------------- main entry

    def validate(self, lines: list[str]) -> None:
        for line in lines:
            self.turn += 1
            self.check_turn(line)

        if self.transit:
            stuck = sorted(self.transit)
            raise ValidationError(f"drones left on a connection: {stuck}")
        missing = set(range(1, self.nb_drones + 1)) - self.delivered
        if missing:
            raise ValidationError(
                f"drones never delivered: {sorted(missing)}"
            )

    # ------------------------------------------------------ one whole turn

    def check_turn(self, line: str) -> None:
        link_usage: dict[Connection, int] = {}
        moved: set[int] = set()

        for token in line.split():
            drone_id, names = self.parse_token(token)

            if drone_id in moved:
                raise self.fail(f"D{drone_id} moves twice")
            moved.add(drone_id)
            if drone_id in self.delivered:
                raise self.fail(f"D{drone_id} moves after delivery")

            if drone_id in self.transit:
                self.check_landing(drone_id, names)
            elif len(names) == 1:
                self.check_zone_move(drone_id, names[0], link_usage)
            else:
                self.check_transit_start(drone_id, names, link_usage)

        # A drone that entered a connection last turn must have landed now.
        for drone_id, (conn, _, entered) in self.transit.items():
            if entered < self.turn:
                raise self.fail(
                    f"D{drone_id} stayed on {conn.name} instead of landing"
                )

        for conn, used in link_usage.items():
            if used > conn.max_link_capacity:
                raise self.fail(
                    f"{used} drones crossed {conn.name} "
                    f"(max {conn.max_link_capacity})"
                )

        # Only the end-of-turn picture counts, so a drone leaving a zone
        # frees its place for another entering in the same turn (VII.3).
        occupancy: dict[Zone, int] = {}
        for drone_id, zone in self.position.items():
            if drone_id in self.transit or drone_id in self.delivered:
                continue
            occupancy[zone] = occupancy.get(zone, 0) + 1
        for zone, count in occupancy.items():
            if zone is self.start or zone is self.end:
                continue
            if count > zone.max_drones:
                raise self.fail(
                    f"{count} drones in {zone.name} (max {zone.max_drones})"
                )

    # ------------------------------------------------- the three move kinds

    def check_zone_move(self, drone_id: int, name: str,
                        link_usage: dict[Connection, int]) -> None:
        here = self.position[drone_id]
        target = self.zone(name)
        conn = self.link(here, target)

        if not target.is_enterable:
            raise self.fail(f"D{drone_id} enters blocked zone {name}")
        if target.zone_type == ZoneType.RESTRICTED:
            raise self.fail(
                f"D{drone_id} enters restricted {name} in one turn"
            )

        link_usage[conn] = link_usage.get(conn, 0) + 1
        self.arrive(drone_id, target)

    def check_transit_start(self, drone_id: int, names: list[str],
                            link_usage: dict[Connection, int]) -> None:
        here = self.position[drone_id]
        a, b = self.zone(names[0]), self.zone(names[1])
        conn = self.link(a, b)

        if here is not a and here is not b:
            raise self.fail(
                f"D{drone_id} is in {here.name}, not on {conn.name}"
            )
        destination = conn.other_side(here)
        if destination.zone_type != ZoneType.RESTRICTED:
            raise self.fail(
                f"D{drone_id} goes through {conn.name}, but "
                f"{destination.name} is not restricted"
            )

        link_usage[conn] = link_usage.get(conn, 0) + 1
        self.transit[drone_id] = (conn, destination, self.turn)

    def check_landing(self, drone_id: int, names: list[str]) -> None:
        conn, destination, _ = self.transit[drone_id]
        if len(names) != 1 or names[0] != destination.name:
            raise self.fail(
                f"D{drone_id} must land in {destination.name}, "
                f"got '{'-'.join(names)}'"
            )
        # Landing does not count against the link: the crossing was
        # counted when the drone entered it.
        del self.transit[drone_id]
        self.arrive(drone_id, destination)

    def arrive(self, drone_id: int, zone: Zone) -> None:
        self.position[drone_id] = zone
        if zone is self.end:
            self.delivered.add(drone_id)


# ---------------------------------------------------------------- runner

def simulate(map_path: str) -> tuple[Graph, int, list[str]]:
    """Run the real program's chain and return its printed lines."""
    from parsing import Parser
    from planner import Planner
    from renderer import Renderer

    graph, nb_drones = Parser(map_path).parse()
    turns = Planner(graph, nb_drones).plan()
    renderer = Renderer()
    return graph, nb_drones, [renderer.render_turn(t) for t in turns]


def main() -> None:
    paths = sys.argv[1:] or sorted(str(p) for p in Path("maps").rglob("*.txt"))
    failures = 0
    for path in paths:
        try:
            graph, nb_drones, lines = simulate(path)
            Validator(graph, nb_drones).validate(lines)
            print(f"OK    {len(lines):>3} turns  {path}")
        except (ParseError, NoPathError, SimulationError,
                ValidationError) as e:
            failures += 1
            print(f"FAIL            {path}\n      {e}")
    print(f"\n{len(paths) - failures}/{len(paths)} maps valid")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()