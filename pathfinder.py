from __future__ import annotations

import heapq

from data_model import Graph, Zone


class Pathfinder:
    """Distances on the map, ignoring time and other drones."""

    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    def distances_to(self, end: Zone) -> dict[Zone, int]:
        """Cheapest cost from every zone to `end` (Dijkstra, backwards).

        Zones missing from the result cannot reach `end` at all.
        """
        dist = {end: 0}
        counter = 0
        heap = [(0, counter, end)]
        while heap:
            cost, _, zone = heapq.heappop(heap)
            if cost > dist[zone]:
                continue                       # an old, worse copy
            if not zone.is_enterable:
                continue                       # nobody can pass through it
            for conn in zone.connections:
                before = conn.other_side(zone)
                new_cost = cost + zone.cost    # the cost of entering `zone`
                if before not in dist or new_cost < dist[before]:
                    dist[before] = new_cost
                    counter += 1
                    heapq.heappush(heap, (new_cost, counter, before))
        return dist