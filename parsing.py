from data_model import Zone, Graph, ZoneType, HubKind, ParseError
import re

zone_line = re.compile(
    r"(start_hub|end_hub|hub): ([^\s-]+) "
    r"(?P<x>-?\d+) (?P<y>-?\d+)(\s*\[(?P<meta>.*)\])?"
)

connection_line = re.compile(
    r"connection: ([^\s]+)(\s*\[(?P<meta>.*)\])?"
)

drones_line = re.compile(r"nb_drones:\s+(-?\d+)")

meta_pair = re.compile(r"(\w+)=(\S+)")

meta_block = re.compile(r"(\w+)=([^\s=]+)(\s+(\w+)=([^\s=]+))*")


class Parser:
    def __init__(self, path: str) -> None:
        self.path = path
        self.graph = Graph()
        self.nb_drones: int | None = None
        self.line_number = 0

    def clean_line(self, line: str) -> str:
        return line.split("#")[0].strip()

    def parse_drones_line(self, line: str) -> int:
        result = drones_line.fullmatch(line)
        if result is None:
            raise ParseError(
                f"line {self.line_number}: invalid nb_drones line"
            )
        try:
            nbr = int(result.group(1))
        except ValueError as e:
            raise ParseError(
                f"line {self.line_number}: nb_drones must be a number"
            ) from e
        if nbr < 1:
            raise ParseError(
                f"line {self.line_number}: we must have at least 1 drone"
            )
        return nbr

    def parse(self) -> tuple[Graph, int]:
        try:
            with open(self.path) as f:
                lines = f.readlines()
        except FileNotFoundError as e:
            raise ParseError("this file doesnt exist") from e

        for number_of_line, line in enumerate(lines, start=1):
            self.line_number = number_of_line
            check = self.clean_line(line)
            if check == "":
                continue
            if self.nb_drones is None:
                self.nb_drones = self.parse_drones_line(check)
                continue
            if check.startswith("connection:"):
                name_a, name_b, capacity = (
                    self.parse_connection_line(check))
                if name_a not in self.graph.zones:
                    raise ParseError(f"line {self.line_number}:"
                                     f" unknown zone {name_a}")
                if name_b not in self.graph.zones:
                    raise ParseError(f"line {self.line_number}:"
                                     f" unknown zone {name_b}")
                zone_a = self.graph.zones[name_a]
                zone_b = self.graph.zones[name_b]
                try:
                    self.graph.add_connection(zone_a, zone_b, capacity)
                except ParseError as e:
                    raise ParseError(f"line {self.line_number}: {e}") from e
            elif check.startswith(("hub:", "start_hub:", "end_hub:")):
                zone, kind = self.parse_zone_line(check)
                try:
                    self.graph.add_zone(zone, kind)
                except ParseError as e:
                    raise ParseError(f"line {self.line_number}: {e}") from e
            else:
                raise ParseError(f"line {self.line_number}: unknown line type")
        self.graph.start_validate()
        self.graph.end_validate()
        if self.nb_drones is None:
            raise ParseError("no nb_drones line found")
        return self.graph, self.nb_drones

    def parse_metadata(self, raw: str | None) -> dict[str, str]:

        raw = raw or ""   # because raw can be none idan findall radi dkraxi
        if raw and meta_block.fullmatch(raw) is None:
            raise ParseError(f"line {self.line_number}:"
                             f" invalid metadata block")
        pairs = meta_pair.findall(raw)
        dic: dict[str, str] = {}
        for key, value in pairs:
            dic[key] = value
        return dic

    def parse_zone_line(self, line: str) -> tuple[Zone, HubKind]:
        data = zone_line.fullmatch(line)
        if data is None:
            raise ParseError(f"line {self.line_number}: bad line syntax")

        dic = self.parse_metadata(data.group("meta"))

        allowed_metadata = {"zone", "max_drones", "color"}

        # Unknown metadata
        unknown = set(dic) - allowed_metadata

        if unknown:
            raise ParseError(f"line {self.line_number}:"
                             f"metadata not recognized: {unknown}")

        try:
            zone_type = ZoneType(dic.get("zone", "normal"))
        except ValueError as e:
            raise ParseError(f"line {self.line_number}:"
                             f"invalid zone type") from e

        try:
            max_drones = int(dic.get("max_drones", "1"))
        except ValueError as e:
            raise ParseError(f"line {self.line_number}:"
                             f"max_drones must be a number") from e
        if max_drones < 1:
            raise ParseError(f"line {self.line_number}:"
                             f"the minimum possible number of drones is 1")

        color = dic.get("color")
        name = data.group(2)
        x = int(data.group("x"))
        y = int(data.group("y"))
        kind = HubKind(data.group(1))
        zone = Zone(name, color, max_drones, zone_type, x, y)
        return zone, kind

    def parse_connection_line(self, line: str) -> tuple[str, str, int]:
        result = connection_line.fullmatch(line)

        if result is None:
            raise ParseError(f"line {self.line_number}: bad connection line")

        names = result.group(1).split("-")
        if len(names) != 2:
            raise ParseError(f"{self.line_number}:"
                             f" a connection has to be between just two zones")

        if "" in names:
            raise ParseError(f"line {self.line_number}:"
                             f" a connection need to have a name")

        dic = self.parse_metadata(result.group("meta"))
        allowed = {"max_link_capacity"}
        unknown = set(dic) - allowed
        if unknown:
            raise ParseError(f"line {self.line_number}: metadata not allowed")
        try:
            capacity = int(dic.get("max_link_capacity", "1"))
        except ValueError as e:
            raise ParseError(f"line {self.line_number}:"
                             f" max link capacity should be an int") from e
        if capacity < 1:
            raise ParseError(f"line {self.line_number}:"
                             f" the capacity should be a positif number")

        return names[0], names[1], capacity


if __name__ == "__main__":
    try:
        p = Parser("file.txt")
        graph, nb = p.parse()
    except ParseError as e:
        print(f"Error: {e}")
