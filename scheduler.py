from data_model import Graph, Zone, Drone, Movement, Connection, ZoneType, SimulationError
from renderer import Renderer

class Scheduler:
    def __init__(self, graph: Graph, routes: list[list[Zone]]) -> None:
        self.drones: list[Drone] = []
        self.graph = graph
        for i, route in enumerate(routes, start=1):
            drone = Drone(i, route[0])
            drone.path = route
            self.drones.append(drone)

    def run(self) -> list[list[Movement]]:
        turns: list[list[Movement]] = []

        while any(d.zone is not self.graph.end for d in self.drones):
            movements: list[Movement] = []

            occupancy: dict[Zone, int] = {}
            for d in self.drones:
                zone = d.occupying
                occupancy[zone] = occupancy.get(zone, 0) + 1
            link_usage: dict[Connection, int] = {}        

            by_progress = sorted(self.drones, key=lambda d: d.step,
                                reverse=True)
            for drone in by_progress:
                if drone.zone is self.graph.end:
                    continue
                
                if drone.transit is not None:
                    drone.transit = None
                    drone.step += 1
                    drone.zone = drone.path[drone.step]
                    movements.append(Movement(drone, drone.zone))
                    continue

                next_zone = drone.path[drone.step + 1]
                conn = drone.zone.connection_to(next_zone)

                if not self.has_room(next_zone, occupancy):
                    continue
                if not self.link_has_room(conn, link_usage): 
                    continue

                occupancy[drone.zone] -= 1
                # VII.3 rule: drones moving out of a zone free up capacity for that same turn. so khes nkhwi blasa 9bel
                occupancy[next_zone] = occupancy.get(next_zone, 0) + 1
                link_usage[conn] = link_usage.get(conn, 0) + 1 

                if next_zone.zone_type == ZoneType.RESTRICTED:
                    drone.transit = conn
                    movements.append(Movement(drone, conn))
                else:
                    drone.step += 1
                    drone.zone = drone.path[drone.step]
                    movements.append(Movement(drone, drone.zone))

            if not movements:
                raise SimulationError("no drone can move: simulation stuck")


            turns.append(movements)

        return turns
    
    def has_room(self, zone: Zone, occupancy: dict[Zone, int]) -> bool:  
        # rah start dayman anbdaw fiha so manehtajox nzidoha
        if zone is self.graph.end:
            return True
        return occupancy.get(zone, 0) < zone.max_drones
    
    def link_has_room(self, conn: Connection,
                  link_usage: dict[Connection, int]) -> bool:
        return link_usage.get(conn, 0) < conn.max_link_capacity



if __name__ == "__main__":
    from parsing import Parser
    from pathfinder import Pathfinder

    graph, nb = Parser("file.txt").parse()
    if graph.start is None or graph.end is None:
        raise SystemExit("no start or end")
    path = Pathfinder(graph).dijkstra(graph.start, graph.end)

    s = Scheduler(graph, nb, path)
    turns = s.run()
    r = Renderer()
    for movements in turns:
        print(r.render_turn(movements))
    print(len(turns))