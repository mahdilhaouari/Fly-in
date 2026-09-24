from data_model import Zone, ZoneType, Drone, Movement, Connection


class Renderer:
    def render_turn(self, movements: list[Movement]) -> str:
        return " ".join(
            f"D{m.drone.id}-{m.target.name}" for m in movements)


if __name__ == "__main__":
    start = Zone("start", None, 1, ZoneType.NORMAL, 0, 0)
    roof1 = Zone("roof1", None, 1, ZoneType.NORMAL, 1, 0)
    corridor = Zone("corridorA", None, 1, ZoneType.NORMAL, 2, 0)

    d1 = Drone(1, start)
    d2 = Drone(2, start)

    movements = [Movement(d1, roof1), Movement(d2, corridor)]
    print(Renderer().render_turn(movements))

    conn = Connection(start, roof1, 1)
    print(Renderer().render_turn([Movement(d1, conn)]))
