"""Proves the validator catches mistakes, by feeding it broken output.

Usage:
    python3 test_validator.py
"""
from __future__ import annotations

import sys

from parsing import Parser
from validator import Validator, ValidationError

LINEAR = "maps/easy/01_linear_path.txt"        # waypoints hold 1
LOOP = "maps/medium/02_circular_loop.txt"      # exit_point is restricted
LINK = "maps/test/link_capacity.txt"           # start-wide carries 1

# (description, map, lines, expected: None = must pass, else a word
#  that must appear in the error message)
CASES: list[tuple[str, str, list[str], str | None]] = [
    ("correct output passes", LINEAR,
     ["D1-waypoint1", "D1-waypoint2 D2-waypoint1",
      "D1-goal D2-waypoint2", "D2-goal"], None),
    ("two drones in a capacity-1 zone", LINEAR,
     ["D1-waypoint1 D2-waypoint1"], "max 1"),
    ("move between unconnected zones", LINEAR,
     ["D1-waypoint2"], "not connected"),
    ("same drone moves twice in one turn", LINEAR,
     ["D1-waypoint1 D1-waypoint2"], "twice"),
    ("a drone is never delivered", LINEAR,
     ["D1-waypoint1", "D1-waypoint2", "D1-goal"], "never delivered"),
    ("a drone moves after delivery", LINEAR,
     ["D1-waypoint1", "D1-waypoint2", "D1-goal", "D1-waypoint2"],
     "after delivery"),
    ("bad token", LINEAR, ["X1-waypoint1"], "bad token"),
    ("unknown drone", LINEAR, ["D9-waypoint1"], "unknown drone"),
    ("unknown zone", LINEAR, ["D1-nowhere"], "unknown zone"),
    ("link over capacity", LINK,
     ["D1-wide D2-wide"], "crossed"),
    ("restricted zone entered in one turn", LOOP,
     ["D1-loop_a", "D1-loop_b", "D1-exit_point"], "one turn"),
    ("drone waits on a connection", LOOP,
     ["D1-loop_a", "D1-loop_b", "D1-loop_b-exit_point", "D2-loop_a"],
     "instead of landing"),
    ("drone lands in the wrong zone", LOOP,
     ["D1-loop_a", "D1-loop_b", "D1-loop_b-exit_point", "D1-goal"],
     "must land"),
    ("transit toward a normal zone", LINEAR,
     ["D1-start-waypoint1"], "not restricted"),
    ("transit on a connection the drone is not at", LOOP,
     ["D1-loop_b-exit_point"], "not on"),
    ("simulation ends with a drone in transit", LOOP,
     ["D1-loop_a", "D1-loop_b", "D1-loop_b-exit_point"], "left on"),
]


def main() -> None:
    failures = 0
    for description, map_path, lines, expected in CASES:
        graph, nb_drones = Parser(map_path).parse()
        try:
            Validator(graph, nb_drones).validate(lines)
            error = None
        except ValidationError as e:
            error = str(e)

        if expected is None:
            ok = error is None
        else:
            ok = error is not None and expected in error
        failures += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {description}")
        if not ok:
            print(f"      expected: {expected!r}  got: {error!r}")

    print(f"\n{len(CASES) - failures}/{len(CASES)} checks passed")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()