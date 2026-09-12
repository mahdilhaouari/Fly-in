from enum import Enum

class ZoneType(Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class zone:
    def __init__(self, name, color, max_drones, zone_type, x, y, neighbours):
        self.name = name
        self.color = color
        self.max_drones = max_drones
        self.zone_type = zone_type
        self.x = x
        self.y = y
        self.neighbours = neighbours


class conections:
    def __init__(self, pairs, max_link_capacity):
        self.max_link_capacity = max_link_capacity
        self.pairs = pairs


class graph:
    def __init__(self, nb_of_drones):
        self.nb_of_drones = nb_of_drones

