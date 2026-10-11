from data_model import Movement


class Renderer:
    def render_turn(self, movements: list[Movement]) -> str:
        return " ".join(
            f"D{m.drone.id}-{m.target.name}" for m in movements)
