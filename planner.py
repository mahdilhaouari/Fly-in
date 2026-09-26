from __future__ import annotations

from data_model import Graph, Zone, Movement, NoPathError, SimulationError
from pathfinder import Pathfinder
from scheduler import Scheduler


class Planner:
    def __init__(self, graph: Graph, nb_drones: int) -> None:
        if graph.start is None or graph.end is None:
            raise NoPathError("the map has no start or end")
        self.graph = graph
        self.nb_drones = nb_drones
        self.paths = Pathfinder(graph).find_paths(
            graph.start, graph.end, nb_drones
        )

    @staticmethod
    def path_cost(path: list[Zone]) -> int:
        return sum(zone.cost for zone in path[1:])

    def distribute(self, paths: list[list[Zone]]) -> list[list[Zone]]:
        counts = [0] * len(paths)
        routes: list[list[Zone]] = []
        for _ in range(self.nb_drones):
            best = min(
                range(len(paths)),
                key=lambda i: self.path_cost(paths[i]) + counts[i],
            )
            counts[best] += 1
            routes.append(paths[best])
        return routes

    def plan(self) -> list[list[Movement]]:
        best: list[list[Movement]] | None = None
        for k in range(1, len(self.paths) + 1):
            routes = self.distribute(self.paths[:k])
            try:
                turns = Scheduler(self.graph, routes).run()
            except SimulationError:
                continue
            if best is None or len(turns) < len(best):
                best = turns
        if best is None:
            raise SimulationError("no drone distribution works")
        return best