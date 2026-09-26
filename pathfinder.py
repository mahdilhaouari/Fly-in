from __future__ import annotations
from data_model import Graph, Zone, ZoneType, NoPathError
import heapq


class Pathfinder:
    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    def dijkstra(self, start: Zone, end: Zone, penalty: dict[Zone, int] | None = None) -> list[Zone]:
        best_cost: dict[Zone, tuple[int, int]] = {start: (0, 0)}
        parent: dict[Zone, Zone] = {}
        counter = 0
        heap = [((0, 0), counter, start)]
        penalty = penalty or {}
        while heap:
            cost, _, zone = heapq.heappop(heap)
            if cost > best_cost[zone]:
                continue
            if zone is end:
                break
            for conn in zone.connections:
                neighbour = conn.other_side(zone)
                if not neighbour.is_enterable:
                    continue
                new_total = cost[0] + neighbour.cost + penalty.get(neighbour, 0)
                new_priority = cost[1]
                if neighbour.zone_type == ZoneType.PRIORITY:
                    new_priority -= 1
                new_cost = (new_total, new_priority)
                if (neighbour not in best_cost or
                        new_cost < best_cost[neighbour]):
                    best_cost[neighbour] = new_cost
                    parent[neighbour] = zone
                    counter += 1
                    heapq.heappush(heap, (new_cost, counter, neighbour))

        if end not in best_cost:
            raise NoPathError("no path from start to end")

        path = [end]
        zone = end
        while zone is not start:
            zone = parent[zone]
            path.append(zone)

        return path[::-1]
    
    def find_paths(self, start: Zone, end: Zone,
               limit: int) -> list[list[Zone]]:
        paths: list[list[Zone]] = []
        penalty: dict[Zone, int] = {}
        for _ in range(limit):
            path = self.dijkstra(start, end, penalty)
            if path in paths:
                break
            paths.append(path)
            for zone in path[1:-1]:
                penalty[zone] = penalty.get(zone, 0) + 1
        return paths


if __name__ == "__main__":
    from parsing import Parser

    p = Parser("maps/hard/01_maze_nightmare.txt")
    graph, nb = p.parse()

    pf = Pathfinder(graph)
    if graph.start is None or graph.end is None:
        raise NoPathError("graph has no start or end")

    path = pf.dijkstra(graph.start, graph.end)
    path = pf.dijkstra(graph.start, graph.end)
    for zone in path:
        print(zone.name)
