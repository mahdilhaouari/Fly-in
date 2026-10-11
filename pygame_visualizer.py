"""A simple pygame window that shows every drone, turn by turn.

SPACE: next turn    R: back to the start    ESC: quit
"""
from __future__ import annotations

import pygame

from data_model import Graph, Zone, Connection, Movement

WIDTH, HEIGHT = 1200, 700
MARGIN = 100


class PygameVisualizer:
    """Draws the map, and each drone with its number."""

    def __init__(self, graph: Graph, nb_drones: int,
                 turns: list[list[Movement]]) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Fly-in")
        self.font = pygame.font.Font(None, 20)
        if graph.start is None or graph.end is None:
            raise ValueError("the map has no start or end")
        self.start: Zone = graph.start
        self.end: Zone = graph.end
        self.graph = graph
        self.nb_drones = nb_drones
        self.turns = turns
        self.turn = 0

        xs = [zone.x for zone in graph.zones.values()]
        ys = [zone.y for zone in graph.zones.values()]
        mid_x, mid_y = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        scale_x = (WIDTH - 2 * MARGIN) / max(max(xs) - min(xs), 1)
        scale_y = (HEIGHT - 2 * MARGIN) / max(max(ys) - min(ys), 1)
        self.points = {
            zone: (WIDTH / 2 + (zone.x - mid_x) * scale_x,
                   HEIGHT / 2 + (zone.y - mid_y) * scale_y)
            for zone in graph.zones.values()
        }

    def draw(self) -> None:
        """Draw the map and the drones as they are after `self.turn`."""
        where: dict[int, Zone | Connection] = {
            drone_id: self.start for drone_id in range(1, self.nb_drones + 1)
        }
        for movements in self.turns[:self.turn]:
            for move in movements:
                where[move.drone.id] = move.target

        self.screen.fill((25, 25, 35))

        for conn in self.graph.connections:
            pygame.draw.line(self.screen, (90, 90, 110),
                             self.points[conn.zone_a],
                             self.points[conn.zone_b], 2)
        names: list[pygame.Rect] = []
        for zone, (x, y) in self.points.items():
            try:
                color = pygame.Color(zone.color or "gray")
            except ValueError:
                color = pygame.Color("gray")
            pygame.draw.circle(self.screen, color, (x, y), 16)
            text = self.font.render(zone.name, True, (200, 200, 210))
            box = text.get_rect(midtop=(x, y + 20))
            if box.collidelist(names) == -1:
                self.screen.blit(text, box)
                names.append(box)

        groups: dict[Zone | Connection, list[int]] = {}
        for drone_id, place in where.items():
            if place is not self.start and place is not self.end:
                groups.setdefault(place, []).append(drone_id)
        for place, drones in groups.items():
            if isinstance(place, Zone):
                x, y = self.points[place]
                bubble = "white"
            else:
                (ax, ay), (bx, by) = (self.points[place.zone_a],
                                      self.points[place.zone_b])
                x, y = (ax + bx) / 2, (ay + by) / 2
                bubble = "yellow"
            for i, drone_id in enumerate(drones):
                spot = (x + (i - (len(drones) - 1) / 2) * 24, y)
                pygame.draw.circle(self.screen, bubble, spot, 11)
                number = self.font.render(str(drone_id), True, "black")
                self.screen.blit(number, number.get_rect(center=spot))

        places = list(where.values())
        waiting = places.count(self.start)
        arrived = places.count(self.end)
        info = (f"Turn {self.turn} / {len(self.turns)}     "
                f"waiting at start: {waiting}     arrived: {arrived}     "
                "SPACE: next turn   R: restart   ESC: quit")
        self.screen.blit(self.font.render(info, True, "white"), (20, 20))
        pygame.display.flip()

    def run(self) -> None:
        """Redraw after every key, until the window is closed."""
        try:
            while True:
                self.draw()
                event = pygame.event.wait(200)
                if event.type == pygame.QUIT:
                    break
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        break
                    if event.key == pygame.K_SPACE:
                        self.turn = min(self.turn + 1, len(self.turns))
                    if event.key == pygame.K_r:
                        self.turn = 0
        finally:
            pygame.quit()
