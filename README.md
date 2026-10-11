*This project has been created as part of the 42 curriculum by mal-haou.*

# Fly-in

## Description

Fly-in moves a fleet of drones from a **start zone** to an **end zone** on a
map of zones and connections, in as **few turns** as possible.

The program:

1. **reads** a map file (zones, connections, number of drones),
2. **plans** a route for every drone, following all the rules of the subject
   (zone capacity, connection capacity, restricted / priority / blocked
   zones),
3. **prints** the simulation, one line per turn,
4. optionally **shows it in a window** (`--visual`).

It reaches the **optimum number of turns on every map** of the subject,
including the challenger map (bonus):

| Map | Drones | Turns | Optimum |
|---|---|---|---|
| easy / linear path | 2 | 4 | 4 |
| easy / simple fork | 4 | 4 | 4 |
| easy / basic capacity | 4 | 4 | 4 |
| medium / dead end trap | 5 | 8 | 8 |
| medium / circular loop | 6 | 10 | 10 |
| medium / priority puzzle | 5 | 6 | 6 |
| hard / maze nightmare | 8 | 13 | 13 |
| hard / capacity hell | 12 | 16 | 16 |
| hard / ultimate challenge | 15 | 26 | 26 |
| challenger / the impossible dream | 25 | **43** | 43 |

## Instructions

**Requirements:** Python 3.10 or later, and [uv](https://docs.astral.sh/uv/).

```bash
make install                          # install pygame, flake8 and mypy
make run                              # run the challenger map
make run MAP=maps/easy/01_linear_path.txt   # run another map
make visual MAP=maps/easy/01_linear_path.txt
```

Without `make`:

```bash
uv run python main.py <map_file>            # text output only
uv run python main.py <map_file> --visual   # text output + window
```

If no map is given, the program reads `config.txt`.

All the Makefile rules:

| Rule | What it does |
|---|---|
| `make install` | installs the dependencies with `uv sync` |
| `make run` | runs the program on `MAP` (default: the challenger map) |
| `make visual` | same, and opens the pygame window |
| `make debug` | runs the program inside Python's debugger (`pdb`) |
| `make clean` | deletes `__pycache__` and `.mypy_cache` |
| `make lint` | runs `flake8` and `mypy` with the flags of the subject |

**Errors:** a bad map file, a missing file or a map with no route prints
one line starting with `Error:` (with the line number for file errors) and
exits with code 1. The program never crashes with a traceback.

## Example input and output

`example.txt`:

```
nb_drones: 2
start_hub: origin 0 0
hub: restrictedZone 1 0 [zone=restricted]
end_hub: goal 2 0
connection: origin-restrictedZone
connection: restrictedZone-goal
```

```bash
$ uv run python main.py example.txt
D1-origin-restrictedZone
D1-restrictedZone D2-origin-restrictedZone
D1-goal D2-restrictedZone
D2-goal
```

How to read it: one line per turn. `D1-restrictedZone` means drone 1 is in
the zone `restrictedZone` at the end of the turn. `D1-origin-restrictedZone`
means drone 1 is flying on that connection: entering a restricted zone
takes 2 turns. Waiting drones are not printed.

Here D2 must wait at turn 1: the connection and `restrictedZone` (capacity
1) are used by D1. 4 turns is the optimum for this map.

## Algorithm and implementation

### The idea in one sentence

Drones are planned **one after another**. Each drone finds its **fastest
route through space and time**, using only the places that the drones
before it left free, then **books** that route.

This is **prioritized planning**, a classic method for *multi-agent path
finding* (many agents moving on one map without collisions).

### The steps

**1. Parsing** (`parsing.py`) — reads the file line by line with regular
expressions (`re.fullmatch`) and builds a `Graph` of `Zone` and
`Connection` objects. Every rule of the subject is checked: first line,
one start and one end, unique names, valid metadata, positive capacities,
duplicate connections, unknown zones...

**2. Distances to the end** (`pathfinder.py`) — one **Dijkstra, run
backwards from the end zone**, gives every zone its cost to the end
(entering a zone costs 1 turn, 2 for a restricted zone; blocked zones are
never crossed). It's computed **once** and used to:
- stop at once with `Error: no path from start to end` if the start can't
  reach the end,
- never send a drone into a zone that can't reach the end (dead ends).

**3. The reservation table** (`scheduler.py`) — a "booking notebook" with
two counters:
- `zone_use[(zone, turn)]`: drones in a zone at the end of a turn
  (≤ `max_drones`; start and end have no limit),
- `link_use[(connection, turn)]`: drones leaving through a connection
  during a turn (≤ `max_link_capacity`).

A connection is booked only on the turn the drone **leaves**, so a
restricted connection is free again on the landing turn. Waiting also
books a seat.

**4. Planning each drone** (`planner.py`) — a **Dijkstra over states
`(zone, turn)`**. From each state, a drone can **wait** or **move** to a
neighbour, only if the table has room. The search always continues the
route that is **earliest in time**, so the first route that reaches the
end is the fastest one for this drone.
- **Priority zones:** between two routes that arrive at the same turn,
  the one that entered more priority zones wins. It never makes a drone
  slower.
- **The search always ends:** a state is never visited twice, and no
  route goes past `last booked turn + distance from start`, the arrival
  time of a route that always works (wait at the start until the map is
  free, then take the shortest path).

**5. Output** (`scheduler.py` + `renderer.py`) — every drone's route is
turned into one list of moves per turn, then printed as
`D<id>-<zone>` or `D<id>-<zone>-<zone>` (in transit).

### Why these choices

- **Time matters**: the same zone can be full at turn 2 and free at turn
  3, so we search over `(zone, turn)` and not only over zones.
- **Dijkstra, not BFS**: moves don't all cost the same (restricted = 2
  turns).
- **One drone at a time**: simple, easy to check, and each drone gets the
  earliest arrival possible given the drones before it. It is not
  guaranteed optimal in theory, but it reaches the optimum on every map
  of the subject.

### Performance

- **Speed:** the challenger map takes about 0.1 s; all 10 maps take less
  than 1 s together. 500 drones on the linear map: about 0.3 s. 200 drones
  on the challenger map: about 0.7 s.
- **Complexity:** the distances cost `O((Z + C) log Z)` once (Z zones, C
  connections). Each drone explores at most `Z × T` states (T = the
  turn limit), each with a heap push in `O(log)`. So the total grows with
  `drones × zones × turns`.
- **Caching:** the distances are computed once and reused for every
  drone. Each route is computed once and never recalculated.
- **Memory:** the reservation table grows with the total length of all
  routes; the search keeps only the states of one drone at a time.

### Object-oriented design

| File | Class | Job |
|---|---|---|
| `data_model.py` | `Zone`, `Connection`, `Graph`, `Drone`, `Movement`, errors | the data (imports nothing of the project) |
| `parsing.py` | `Parser` | file → `Graph` |
| `pathfinder.py` | `Pathfinder` | distances to the end |
| `scheduler.py` | `Scheduler` | reservation table + output turns |
| `planner.py` | `Planner` | chooses every drone's route |
| `renderer.py` | `Renderer` | turns → text lines |
| `pygame_visualizer.py` | `PygameVisualizer` | the window |
| `main.py` | — | connects everything, handles errors |

No graph library is used (only Python's standard library, and pygame for
the window).

## Visual representation

Run with `--visual` (or `make visual`) to open a pygame window, after the
text output is printed.

**Controls:**

| Key | Action |
|---|---|
| `SPACE` | show the next turn |
| `R` | go back to the start |
| `N` | show / hide the zone names (useful on big maps) |
| `ESC` | quit (closing the window works too) |

**What you see:**

- **The map**: every zone is a circle at its coordinates, in the **color
  given in the map file** (gray if there is none). Lines are the
  connections. The zone names are written under the zones.
- **The drones**: a **bubble with a number** shows how many drones are in
  a place. A **white** bubble is on a zone. A **yellow** bubble is in the
  middle of a connection: those drones are flying to a restricted zone
  (a 2-turn move).
- **The top line**: the current turn (`Turn 2 / 4`) and the keys.

**How it helps:** you can follow the simulation **one turn at a time**, at
your own speed, and check it against the text output. You see where every
drone is, how many drones share a zone, which drones are in the middle of
a 2-turn restricted move, and how the drones arrive at the end zone.

## Resources

- [Dijkstra's algorithm — Wikipedia](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)
- [Multi-agent pathfinding — Wikipedia](https://en.wikipedia.org/wiki/Multi-agent_pathfinding)
- D. Silver, *Cooperative Pathfinding*, AIIDE 2005 (reservation tables and
  space-time search)
- R. Stern et al., *Multi-Agent Pathfinding: Definitions, Variants, and
  Benchmarks*, SoCS 2019
- Python docs: [`heapq`](https://docs.python.org/3/library/heapq.html),
  [`re`](https://docs.python.org/3/library/re.html),
  [`collections.Counter`](https://docs.python.org/3/library/collections.html#collections.Counter),
  [`enum`](https://docs.python.org/3/library/enum.html)
- [pygame documentation](https://www.pygame.org/docs/)
- [flake8](https://flake8.pycqa.org/), [mypy](https://mypy.readthedocs.io/),
  [PEP 8](https://peps.python.org/pep-0008/),
  [PEP 257](https://peps.python.org/pep-0257/)

### How AI was used

I used Claude (Anthropic) as a tutor and reviewer during the whole project:

- **Learning:** explanations and small courses on regular expressions,
  BFS / Dijkstra, `heapq`, multi-agent path finding and space-time
  planning.
- **Review:** correcting my mistakes in the data model and the parser,
  and suggesting cleaner, object-oriented code.
- **Design:** proposing the planner / reservation table design, then
  simplifying it (A* replaced by plain Dijkstra) so it is easy to explain.
- **Code:** writing the pygame visualizer and a test tool (an independent
  output validator, not submitted for grading), and helping with the
  Makefile and this README.
- **Setup:** fixing environment problems (uv, pygame, WSL).

Every file was then reviewed with me step by step, line by line, so that I
can explain all of it during the evaluation.