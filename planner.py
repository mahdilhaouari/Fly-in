"""Plans every drone's route through space AND time.

This is prioritized planning, a classic multi-agent path finding (MAPF)
method: drones are planned one after another. Each drone searches for its
fastest route through (zone, turn) pairs with A*, avoiding what the drones
before it already booked in the Scheduler, then books its own route.
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

        # The A* compass: cheapest cost from each zone to the end.
        self.dist = Pathfinder(graph).distances_to(self.end)
        if self.start not in self.dist:
            raise NoPathError("no path from start to end")

    def next_states(self, zone: Zone, turn: int) -> list[tuple[State, int]]:
        """Every legal next step from (zone, turn), with a priority bonus."""
        options: list[tuple[State, int]] = []
        if self.schedule.has_room(zone, turn + 1):
            options.append(((zone, turn + 1), 0))          # wait here
        for conn in zone.connections:
            nxt = conn.other_side(zone)
            if not nxt.is_enterable or nxt not in self.dist:
                continue                     # blocked, or a dead end
            if not self.schedule.link_has_room(conn, turn + 1):
                continue
            arrive = turn + nxt.cost          # +1, or +2 for restricted
            if not self.schedule.has_room(nxt, arrive):
                continue
            bonus = 1 if nxt.zone_type == ZoneType.PRIORITY else 0
            options.append(((nxt, arrive), bonus))
        return options

    def plan_drone(self) -> list[State]:
        """A* over (zone, turn): the earliest arrival at the end."""
        horizon = self.schedule.last_turn + 4 * len(self.graph.zones) + 10
        begin: State = (self.start, 0)
        parent: dict[State, State] = {}
        seen = {begin}
        counter = 0
        heap = [(self.dist[self.start], 0, counter, 0, self.start)]
        while heap:
            _, priority, _, turn, zone = heapq.heappop(heap)
            if zone is self.end:
                route = [(zone, turn)]
                while route[-1] != begin:
                    route.append(parent[route[-1]])
                return route[::-1]
            if turn >= horizon:
                continue
            for state, bonus in self.next_states(zone, turn):
                if state in seen:
                    continue
                seen.add(state)
                parent[state] = (zone, turn)
                nxt, arrive = state
                counter += 1
                estimate = arrive + self.dist[nxt]
                heapq.heappush(heap, (estimate, priority - bonus, counter,
                                      arrive, nxt))
        raise SimulationError("a drone could not reach the end")

    def plan(self) -> list[list[Movement]]:
        """Plan and book every drone, then build the output turns."""
        routes: list[tuple[Drone, list[State]]] = []
        for drone_id in range(1, self.nb_drones + 1):
            route = self.plan_drone()
            self.schedule.reserve(route)
            routes.append((Drone(drone_id, self.start), route))
        return self.schedule.build_turns(routes)