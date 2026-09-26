import sys
from data_model import ParseError, NoPathError, SimulationError
from parsing import Parser
from pathfinder import Pathfinder
from scheduler import Scheduler
from renderer import Renderer
from planner import Planner


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else "config.txt"

    try:
        graph, nb_drones = Parser(path).parse()
        turns = Planner(graph, nb_drones).plan()

        if graph.start is None or graph.end is None:
            raise NoPathError("the map has no start or end")

        route = Pathfinder(graph).dijkstra(graph.start, graph.end)
        turns = Scheduler(graph, nb_drones, route).run()

    except (ParseError, NoPathError, SimulationError) as e:
        print(f"Error: {e}")
        sys.exit(1)

    renderer = Renderer()
    for movements in turns:
        print(renderer.render_turn(movements))
    print(len(turns))


if __name__ == "__main__":
    main()