from __future__ import annotations

import re

from data_model import Zone, Graph, ZoneType, HubKind, ParseError

# One pattern per kind of line. We always use fullmatch(), so the WHOLE
# line must fit the pattern, not only its beginning.
ZONE_LINE = re.compile(
    r"(?P<kind>start_hub|end_hub|hub):\s+(?P<name>[^\s-]+)"
    r"\s+(?P<x>-?\d+)\s+(?P<y>-?\d+)(\s*\[(?P<meta>.*)\])?"
)
CONNECTION_LINE = re.compile(
    r"connection:\s+(?P<names>\S+)(\s*\[(?P<meta>.*)\])?"
)
DRONES_LINE = re.compile(r"nb_drones:\s+(?P<count>\S+)")
# What is inside [ ]: one or more key=value, separated by spaces.
META_BLOCK = re.compile(r"\w+=[^\s=\]]+(\s+\w+=[^\s=\]]+)*")

ZONE_META = {"zone", "color", "max_drones"}
CONNECTION_META = {"max_link_capacity"}


class Parser:
    """Reads a map file and builds the Graph, line by line."""

    def __init__(self, path: str) -> None:
        self.path = path
        self.graph = Graph()
        self.nb_drones: int | None = None

    def parse(self) -> tuple[Graph, int]:
        try:
            with open(self.path) as f:
                lines = f.readlines()
        except OSError as e:
            raise ParseError(f"cannot read {self.path}: {e.strerror}") from e
        except UnicodeDecodeError as e:
            raise ParseError(f"{self.path} is not a text file") from e

        for number, line in enumerate(lines, start=1):
            text = self.clean_line(line)
            if text == "":
                continue
            try:
                self.parse_line(text)
            except ParseError as e:
                # The only place that adds the line number.
                raise ParseError(f"line {number}: {e}") from e

        if self.nb_drones is None:
            raise ParseError("the file has no nb_drones line")
        self.graph.start_validate()
        self.graph.end_validate()
        return self.graph, self.nb_drones

    @staticmethod
    def clean_line(line: str) -> str:
        """Remove the comment and the spaces around the line."""
        return line.split("#")[0].strip()

    def parse_line(self, text: str) -> None:
        """Send one line to the right method."""
        if self.nb_drones is None:
            self.nb_drones = self.parse_drones_line(text)
        elif text.startswith("connection:"):
            self.parse_connection_line(text)
        elif text.startswith(("hub:", "start_hub:", "end_hub:")):
            self.parse_zone_line(text)
        else:
            raise ParseError(f"unknown line: {text}")

    def parse_drones_line(self, text: str) -> int:
        match = DRONES_LINE.fullmatch(text)
        if match is None:
            raise ParseError("the first line must be 'nb_drones: <number>'")
        return self.positive_int(match.group("count"), "nb_drones")

    def parse_zone_line(self, text: str) -> None:
        match = ZONE_LINE.fullmatch(text)
        if match is None:
            raise ParseError(f"bad zone line: {text}")
        meta = self.parse_metadata(match.group("meta"), ZONE_META)

        try:
            zone_type = ZoneType(meta.get("zone", "normal"))
        except ValueError as e:
            raise ParseError(f"unknown zone type {meta['zone']}") from e
        max_drones = self.positive_int(meta.get("max_drones", "1"),
                                       "max_drones")

        zone = Zone(match.group("name"), meta.get("color"), max_drones,
                    zone_type, int(match.group("x")), int(match.group("y")))
        self.graph.add_zone(zone, HubKind(match.group("kind")))

    def parse_connection_line(self, text: str) -> None:
        match = CONNECTION_LINE.fullmatch(text)
        if match is None:
            raise ParseError(f"bad connection line: {text}")

        names = match.group("names").split("-")
        if len(names) != 2 or "" in names:
            raise ParseError("a connection needs exactly two zone names: "
                             f"{match.group('names')}")
        if names[0] == names[1]:
            raise ParseError(f"zone {names[0]} cannot connect to itself")

        meta = self.parse_metadata(match.group("meta"), CONNECTION_META)
        capacity = self.positive_int(meta.get("max_link_capacity", "1"),
                                     "max_link_capacity")
        zone_a = self.get_zone(names[0])
        zone_b = self.get_zone(names[1])
        self.graph.add_connection(zone_a, zone_b, capacity)

    def parse_metadata(self, raw: str | None,
                       allowed: set[str]) -> dict[str, str]:
        """Turn 'zone=restricted max_drones=2' into a dict."""
        if raw is None:                       # the line has no [ ]
            return {}
        raw = raw.strip()
        if META_BLOCK.fullmatch(raw) is None:
            raise ParseError(f"bad metadata: [{raw}]")

        meta: dict[str, str] = {}
        for pair in raw.split():
            key, value = pair.split("=")
            if key not in allowed:
                raise ParseError(f"metadata {key} is not allowed here")
            if key in meta:
                raise ParseError(f"metadata {key} is given twice")
            meta[key] = value
        return meta

    def get_zone(self, name: str) -> Zone:
        if name not in self.graph.zones:
            raise ParseError(f"unknown zone {name}")
        return self.graph.zones[name]

    @staticmethod
    def positive_int(text: str, what: str) -> int:
        try:
            value = int(text)
        except ValueError as e:
            raise ParseError(f"{what} must be a number, not {text}") from e
        if value < 1:
            raise ParseError(f"{what} must be at least 1, not {value}")
        return value