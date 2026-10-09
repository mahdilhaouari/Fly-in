import sys

from data_model import ParseError, NoPathError, SimulationError
from parsing import Parser
from planner import Planner
from renderer import Renderer


def main() -> None:
    args = sys.argv[1:]
    visual = "--visual" in args
    files = [arg for arg in args if not arg.startswith("--")]
    path = files[0] if files else "config.txt"

    try:
        graph, nb_drones = Parser(path).parse()
        turns = Planner(graph, nb_drones).plan()
    except (ParseError, NoPathError, SimulationError) as e:
        print(f"Error: {e}")
        sys.exit(1)

    renderer = Renderer()
    for movements in turns:
        print(renderer.render_turn(movements))

    if visual:
        try:
            from pygame_visualizer import PygameVisualizer
        except ImportError as e:
            print(f"Error: cannot start the visualizer: {e}")
            sys.exit(1)
        PygameVisualizer(graph, nb_drones, turns).run()


if __name__ == "__main__":
    main()