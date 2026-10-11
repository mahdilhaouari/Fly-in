"""Chooses a route for every drone, one drone after another.

Each drone looks for its fastest route through (zone, turn) states,
using only the seats and connections still free in the Scheduler.
Then it books its route, and the next drone plans around it.
"""
from __future__ import annotations

import heapq

from data_model import (Graph, Zone, Drone, Movement, ZoneType,
                        NoPathError, SimulationError)
from pathfinder import Pathfinder
from scheduler import Scheduler, State


class Planner:
    def __init__(self, graph: Graph, nb_drones: int) -> None:
        if graph.start is None or graph.end is None:
            raise NoPathError("the map has no start or end")
        self.graph = graph
        self.start: Zone = graph.start
        self.end: Zone = graph.end
        self.nb_drones = nb_drones
        self.schedule = Scheduler(graph)
        self.dist = Pathfinder(graph).distances_to(self.end)
        if self.start not in self.dist:
            raise NoPathError("no path from start to end")

    def plan(self) -> list[list[Movement]]:
        """Find and book a route for each drone, then build the output."""
        routes: list[tuple[Drone, list[State]]] = []
        for drone_id in range(1, self.nb_drones + 1):
            route = self.find_route()
            self.schedule.reserve(route)
            routes.append((Drone(drone_id, self.start), route))
        return self.schedule.build_turns(routes)

    def moves_from(self, zone: Zone, turn: int) -> list[State]:
        """Every state a drone in `zone` at `turn` can legally go to next."""
        moves: list[State] = []

        if self.schedule.has_room(zone, turn + 1):
            moves.append((zone, turn + 1))

        for conn in zone.connections:
            nxt = conn.other_side(zone)
            if not nxt.is_enterable or nxt not in self.dist:
                continue
            arrive = turn + nxt.cost
            if (self.schedule.link_has_room(conn, turn + 1)
                    and self.schedule.has_room(nxt, arrive)):
                moves.append((nxt, arrive))
        return moves

    def find_route(self) -> list[State]:
        """The route that reaches the end first (Dijkstra over turns)."""
        max_turn = self.schedule.last_turn + self.dist[self.start]
        first: State = (self.start, 0)
        seen = {first}
        counter = 0
        heap = [(0, 0, counter, [first])]

        while heap:
            turn, priority_score, _, route = heapq.heappop(heap)
            zone = route[-1][0]
            if zone is self.end:
                return route
            if turn >= max_turn:
                continue

            for nxt, arrive in self.moves_from(zone, turn):
                if (nxt, arrive) in seen:
                    continue
                seen.add((nxt, arrive))

                new_score = priority_score
                if nxt is not zone and nxt.zone_type == ZoneType.PRIORITY:
                    new_score -= 1
                counter += 1
                heapq.heappush(heap, (arrive, new_score, counter,
                                      route + [(nxt, arrive)]))

        raise SimulationError("a drone could not reach the end")
