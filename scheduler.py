"""The timetable: which zone and connection is used at which turn."""
from __future__ import annotations

from collections import Counter

from data_model import Graph, Zone, Connection, Drone, Movement, NoPathError

State = tuple[Zone, int]


class Scheduler:
    def __init__(self, graph: Graph) -> None:
        if graph.start is None or graph.end is None:
            raise NoPathError("the map has no start or end")
        self.start: Zone = graph.start
        self.end: Zone = graph.end
        
        self.zone_use: Counter[tuple[Zone, int]] = Counter()
        self.link_use: Counter[tuple[Connection, int]] = Counter()
        self.last_turn = 0

    def has_room(self, zone: Zone, turn: int) -> bool:
        """Can one more drone be in `zone` at the end of `turn`?"""
        if zone is self.start or zone is self.end:
            return True
        return self.zone_use[(zone, turn)] < zone.max_drones

    def link_has_room(self, conn: Connection, turn: int) -> bool:
        """Can one more drone start crossing `conn` during `turn`?"""
        return self.link_use[(conn, turn)] < conn.max_link_capacity

    def reserve(self, route: list[State]) -> None:
        """Book every seat and every connection the route uses."""
        for i in range(len(route) - 1):
            zone, turn = route[i]
            nxt, arrive = route[i + 1]

            if nxt is not zone:
                conn = zone.connection_to(nxt)
                self.link_use[(conn, turn + 1)] += 1

            if nxt is not self.start and nxt is not self.end:
                self.zone_use[(nxt, arrive)] += 1

        final_turn = route[-1][1]
        self.last_turn = max(self.last_turn, final_turn)

    def build_turns(self, routes: list[tuple[Drone, list[State]]]
                    ) -> list[list[Movement]]:
        """Turn every drone's route into the output, one list per turn."""
        turns: list[list[Movement]] = [[] for _ in range(self.last_turn + 1)]
        for drone, route in routes:
            for i in range(len(route) - 1):
                zone, turn = route[i]
                nxt, arrive = route[i + 1]

                if nxt is zone:
                    continue

                if arrive == turn + 2:
                    conn = zone.connection_to(nxt)
                    turns[turn + 1].append(Movement(drone, conn))
                turns[arrive].append(Movement(drone, nxt))
        return turns[1:]