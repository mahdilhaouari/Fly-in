"""Pygame view of the simulation.

SPACE plays the next turn, R restarts, ESC quits.
Hover a zone with the mouse to see its details.
"""
from __future__ import annotations

import pygame
from pygame.math import Vector2

from data_model import Graph, Zone, Connection, Movement, ZoneType

SIZE = (1100, 680)
MARGIN = 90           # empty border around the map
TOP_BAR = 60          # height of the bar at the top
ZONE = 15             # radius of a zone circle
DRONE = 5             # radius of a drone dot
MOVE_MS = 500         # how long a move takes on screen, in milliseconds

BACKGROUND = pygame.Color(20, 22, 30)
BAR = pygame.Color(30, 33, 44)
LINE = pygame.Color(85, 92, 110)
TEXT = pygame.Color(235, 237, 245)
MUTED = pygame.Color(140, 146, 162)
DRONE_COLOR = pygame.Color("white")
TRANSIT_COLOR = pygame.Color("gold")
FULL_COLOR = pygame.Color(255, 90, 90)
PROGRESS = pygame.Color(90, 200, 130)
RESTRICTED_RING = pygame.Color("red")
PRIORITY_RING = pygame.Color("white")
HOVER_RING = pygame.Color("deepskyblue")


class PygameVisualizer:
    def __init__(self, graph: Graph, nb_drones: int,
                 turns: list[list[Movement]]) -> None:
        if graph.start is None or graph.end is None:
            raise ValueError("the map has no start or end")
        self.graph = graph
        self.start: Zone = graph.start
        self.end: Zone = graph.end
        self.nb_drones = nb_drones
        self.turns = turns

        pygame.init()
        self.screen = pygame.display.set_mode(SIZE)
        pygame.display.set_caption("Fly-in")
        self.font = pygame.font.Font(None, 28)
        self.small = pygame.font.Font(None, 20)
        self.clock = pygame.time.Clock()

        self.points = self.place_zones()
        self.reset()

    # ------------------------------------------------------------ the map

    def place_zones(self) -> dict[Zone, Vector2]:
        """Turn each zone's x, y into a point inside the window."""
        area = pygame.Rect(MARGIN, TOP_BAR + MARGIN // 2,
                           SIZE[0] - 2 * MARGIN,
                           SIZE[1] - TOP_BAR - MARGIN - 40)
        zones = self.graph.zones.values()
        min_x = min(zone.x for zone in zones)
        max_x = max(zone.x for zone in zones)
        min_y = min(zone.y for zone in zones)
        max_y = max(zone.y for zone in zones)

        points: dict[Zone, Vector2] = {}
        for zone in zones:
            fx = 0.5 if max_x == min_x else (zone.x - min_x) / (max_x - min_x)
            fy = 0.5 if max_y == min_y else (max_y - zone.y) / (max_y - min_y)
            points[zone] = Vector2(area.left + fx * area.width,
                                   area.top + fy * area.height)
        return points

    def zone_at(self, mouse: Vector2) -> Zone | None:
        """The zone under the mouse, if any."""
        for zone, point in self.points.items():
            if point.distance_to(mouse) <= ZONE + 4:
                return zone
        return None

    def counts(self) -> dict[Zone, int]:
        """How many drones are inside each zone right now."""
        counts: dict[Zone, int] = {}
        for drone_id, zone in self.position.items():
            if drone_id not in self.transit:
                counts[zone] = counts.get(zone, 0) + 1
        return counts

    # ---------------------------------------------------------- the drones

    def reset(self) -> None:
        self.turn = 0
        self.position = {i: self.start for i in range(1, self.nb_drones + 1)}
        self.transit: dict[int, Connection] = {}
        self.old_spots = self.spots()
        self.new_spots = self.old_spots
        self.move_start = 0

    def next_turn(self) -> None:
        if self.turn == len(self.turns):
            return
        self.old_spots = self.current_spots()
        for m in self.turns[self.turn]:
            if isinstance(m.target, Connection):
                self.transit[m.drone.id] = m.target
            else:
                self.transit.pop(m.drone.id, None)
                self.position[m.drone.id] = m.target
        self.turn += 1
        self.new_spots = self.spots()
        self.move_start = pygame.time.get_ticks()

    def spots(self) -> dict[int, Vector2]:
        """Where each drone belongs on screen after this turn."""
        spots: dict[int, Vector2] = {}
        for drone_id, conn in self.transit.items():
            a, b = self.points[conn.zone_a], self.points[conn.zone_b]
            spots[drone_id] = a.lerp(b, 0.5)       # halfway on the line

        groups: dict[Zone, list[int]] = {}
        for drone_id, zone in self.position.items():
            if drone_id not in self.transit:
                groups.setdefault(zone, []).append(drone_id)
        for zone, drones in groups.items():
            for k, drone_id in enumerate(drones):
                # Spread the drones of one zone around its center.
                offset = Vector2(6 * k ** 0.5, 0).rotate(k * 137.5)
                spots[drone_id] = self.points[zone] + offset
        return spots

    def current_spots(self) -> dict[int, Vector2]:
        """Where each drone is right now, part way through its move."""
        elapsed = pygame.time.get_ticks() - self.move_start
        t = min(1.0, elapsed / MOVE_MS)
        t = t * t * (3 - 2 * t)                    # smooth start and stop
        return {
            drone_id: self.old_spots[drone_id].lerp(new, t)
            for drone_id, new in self.new_spots.items()
        }

    # --------------------------------------------------------- the drawing

    @staticmethod
    def zone_color(zone: Zone) -> pygame.Color:
        try:
            return pygame.Color(zone.color or "gray")
        except ValueError:
            return pygame.Color("gray")

    def text(self, font: pygame.font.Font, message: str,
             color: pygame.Color, **where: tuple[float, float]) -> None:
        """Draw text placed by one anchor, e.g. center=(x, y)."""
        surface = font.render(message, True, color)
        self.screen.blit(surface, surface.get_rect(**where))

    def draw_map(self, hovered: Zone | None) -> None:
        for conn in self.graph.connections:
            pygame.draw.aaline(self.screen, LINE, self.points[conn.zone_a],
                               self.points[conn.zone_b])

        counts = self.counts()
        for zone, point in self.points.items():
            pygame.draw.circle(self.screen, self.zone_color(zone), point, ZONE)
            pygame.draw.circle(self.screen, BACKGROUND, point, ZONE, 1)
            if zone.zone_type == ZoneType.RESTRICTED:
                pygame.draw.circle(self.screen, RESTRICTED_RING, point,
                                   ZONE + 4, 2)
            elif zone.zone_type == ZoneType.PRIORITY:
                pygame.draw.circle(self.screen, PRIORITY_RING, point,
                                   ZONE + 4, 2)
            if zone is hovered:
                pygame.draw.circle(self.screen, HOVER_RING, point,
                                   ZONE + 8, 2)

            # A small "drones / capacity" label under busy zones.
            count = counts.get(zone, 0)
            hub = zone is self.start or zone is self.end
            if count and not hub:
                full = count >= zone.max_drones
                label = f"{count}/{zone.max_drones}"
                self.text(self.small, label, FULL_COLOR if full else TEXT,
                          midtop=(point.x, point.y + ZONE + 6))

    def draw_drones(self) -> None:
        for drone_id, point in self.current_spots().items():
            color = TRANSIT_COLOR if drone_id in self.transit else DRONE_COLOR
            pygame.draw.circle(self.screen, color, point, DRONE)
            pygame.draw.circle(self.screen, BACKGROUND, point, DRONE, 1)

    def draw_bars(self) -> None:
        width, height = SIZE
        pygame.draw.rect(self.screen, BAR, (0, 0, width, TOP_BAR))
        self.text(self.font, "Fly-in", TEXT, midleft=(24, TOP_BAR / 2))
        self.text(self.font, f"Turn {self.turn} / {len(self.turns)}", TEXT,
                  midleft=(130, TOP_BAR / 2))

        # Progress bar of delivered drones.
        delivered = self.counts().get(self.end, 0)
        track = pygame.Rect(0, 0, 260, 10)
        track.midright = (width - 150, TOP_BAR // 2)
        pygame.draw.rect(self.screen, LINE, track, border_radius=5)
        done = track.copy()
        done.width = track.width * delivered // self.nb_drones
        if done.width:
            pygame.draw.rect(self.screen, PROGRESS, done, border_radius=5)
        self.text(self.small, f"delivered {delivered} / {self.nb_drones}",
                  MUTED, midleft=(track.right + 14, TOP_BAR / 2))

        if self.turn == len(self.turns):
            hint = f"All drones delivered in {self.turn} turns  -  R replay"
        else:
            hint = "SPACE next turn    R restart    ESC quit"
        hint += "    |    hover a zone for details"
        self.text(self.small, hint, MUTED, midbottom=(width / 2, height - 14))

    def draw_tooltip(self, zone: Zone, mouse: Vector2) -> None:
        count = self.counts().get(zone, 0)
        if zone is self.start or zone is self.end:
            drones = f"drones: {count}"
        else:
            drones = f"drones: {count} / {zone.max_drones}"
        lines = [zone.name, f"type: {zone.zone_type.value}", drones,
                 f"color: {zone.color or 'none'}"]
        width = max(self.small.size(line)[0] for line in lines) + 24
        box = pygame.Rect(0, 0, width, 18 * len(lines) + 16)
        box.topleft = (int(mouse.x) + 16, int(mouse.y) + 16)
        box.clamp_ip(self.screen.get_rect())       # keep it on screen

        pygame.draw.rect(self.screen, BAR, box, border_radius=8)
        pygame.draw.rect(self.screen, HOVER_RING, box, 1, border_radius=8)
        for i, line in enumerate(lines):
            self.text(self.small, line, TEXT if i == 0 else MUTED,
                      topleft=(box.x + 12, box.y + 10 + 18 * i))

    def draw(self) -> None:
        mouse = Vector2(pygame.mouse.get_pos())
        hovered = self.zone_at(mouse)

        self.screen.fill(BACKGROUND)
        self.draw_map(hovered)
        self.draw_drones()
        self.draw_bars()
        if hovered is not None:
            self.draw_tooltip(hovered, mouse)
        pygame.display.flip()

    # ---------------------------------------------------------- main loop

    def run(self) -> None:
        running = True
        try:
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            self.next_turn()
                        elif event.key == pygame.K_r:
                            self.reset()
                        elif event.key == pygame.K_ESCAPE:
                            running = False
                self.draw()
                self.clock.tick(60)
        finally:
            pygame.quit()