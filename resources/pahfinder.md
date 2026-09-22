# BFS and Dijkstra — for the Fly-in project

Two algorithms that find a path from `start` to `goal`.
Read slowly. Draw the maps on paper while you read — it helps a lot.

---

## Part 0 — What we are looking for

Your graph is zones connected by connections.
A **path** is a list of zones, from `start` to `goal`, where each zone is
connected to the next one.

```
start → junction → path_a → goal
```

Many paths can exist. We want a **good** one. "Good" can mean two things:

- **fewest steps** — the number of moves
- **lowest cost** — the number of turns, where a restricted zone costs 2

BFS finds the first. Dijkstra finds the second.

---

## Part 1 — BFS (Breadth-First Search)

### The idea

BFS explores the graph **in layers**, like a wave spreading from `start`:

- first, every zone 1 step away
- then, every zone 2 steps away
- then 3 steps, and so on

The first time the wave touches `goal`, you have found the path with the
**fewest steps**. Nothing can be shorter, because all shorter distances were
already explored.

### What BFS needs

Three things:

1. **A queue** — the zones waiting to be explored. First in, first out.
   Like a line at a shop: the one who came first is served first.
2. **A visited set** — the zones already seen, so you never add them twice.
3. **A parent record** — for each zone, *which zone we came from*. You need
   this to rebuild the path at the end.

### The steps

```
put start in the queue
mark start as visited

while the queue is not empty:
    take the zone at the FRONT of the queue    ← the oldest one
    if it is goal: stop

    for each neighbour of this zone:
        if the neighbour is not visited and can be entered:
            mark it visited
            parent[neighbour] = this zone
            add it to the BACK of the queue
```

### Example — `02_simple_fork.txt`

The map:

```
                  ┌── path_a ──┐
start ── junction ┤            ├── goal
                  └── path_b ──┘
```

Let's run BFS by hand.

| Step | Take from queue | Neighbours added | Queue after | Parent set |
|---|---|---|---|---|
| 0 | — | start | `[start]` | — |
| 1 | start | junction | `[junction]` | junction ← start |
| 2 | junction | path_a, path_b | `[path_a, path_b]` | path_a ← junction, path_b ← junction |
| 3 | path_a | goal | `[path_b, goal]` | goal ← path_a |
| 4 | path_b | (goal already visited) | `[goal]` | — |
| 5 | goal | **stop** | | |

### Rebuilding the path

Start at `goal`, follow the parents backwards:

```
goal → parent is path_a
path_a → parent is junction
junction → parent is start
start → no parent, stop
```

That gives `goal, path_a, junction, start`. Reverse it:

```
start → junction → path_a → goal
```

### Notice two things

**BFS found only one path.** `path_b` was explored, but `goal` was already
visited, so the second route was ignored. BFS gives you *one* answer. Finding
several paths is a separate problem, for later.

**The visited set saves you from loops.** Look at `02_circular_loop.txt`:
`loop_a → loop_b → loop_c → loop_d → loop_a`. Without the visited set, BFS
would go around forever. With it, each zone enters the queue at most once.

---

## Part 2 — Why BFS is wrong for this project

BFS counts **steps**. But your moves don't all cost the same:

| entering a zone of type | costs |
|---|---|
| normal | 1 turn |
| priority | 1 turn |
| restricted | **2 turns** |
| blocked | impossible |

### Example — `03_priority_puzzle.txt`

```
         slow_path1 ── slow_path2
        /  (restricted)            \
start                                merge_point ── goal
        \                          /
         fast_junction ── fast_path
          (priority)     (priority)
```

Two routes, both **4 steps**:

| Route | Zones entered | Cost |
|---|---|---|
| slow | slow_path1 (2) + slow_path2 (1) + merge_point (1) + goal (1) | **5** |
| fast | fast_junction (1) + fast_path (1) + merge_point (1) + goal (1) | **4** |

Run BFS on this map. In the file, `start-slow_path1` is written **before**
`start-fast_junction`. So `slow_path1` enters the queue first, reaches
`merge_point` first, and BFS returns:

```
start → slow_path1 → slow_path2 → merge_point → goal     (cost 5)
```

**BFS picks the slow route — just because of the order of lines in the file.**
To BFS both routes are equal (4 steps each), so it takes whichever it met
first.

This is the core problem. We need an algorithm that understands cost.

---

## Part 3 — Dijkstra

### The idea

Dijkstra is BFS with one change:

> BFS takes the **oldest** waiting zone.
> Dijkstra takes the **cheapest** waiting zone.

"Cheapest" means: the lowest total cost to reach it from `start`, as far as
we know right now.

Because it always expands the cheapest zone next, the first time it takes
`goal` out of the waiting list, no cheaper route can exist.

### What Dijkstra needs

1. **A waiting list sorted by cost** — called a *priority queue*. Always gives
   you the cheapest item first.
2. **A best-cost record** — for each zone, the cheapest known cost to reach it.
3. **A parent record** — same as BFS.

### The steps

```
best_cost[start] = 0
put (0, start) in the waiting list

while the waiting list is not empty:
    take the CHEAPEST (cost, zone) out
    if cost is worse than best_cost[zone]: skip it      ← see Part 5
    if zone is goal: stop

    for each neighbour of zone:
        if the neighbour cannot be entered: skip it
        new_cost = cost + neighbour.cost          ← cost of ENTERING it
        if new_cost is better than best_cost[neighbour]:
            best_cost[neighbour] = new_cost
            parent[neighbour] = zone
            put (new_cost, neighbour) in the waiting list
```

Look at `new_cost = cost + neighbour.cost`. The cost comes from the zone you
**enter**, not the one you leave. That matches VII.3 of the subject:
*"Each movement between zones has a cost in turns, based on the zone=type of
the destination."*

### Example — `03_priority_puzzle.txt` again

Costs to enter: `slow_path1` = 2, everything else = 1.

| Step | Take out | Update neighbours | Waiting list after |
|---|---|---|---|
| 0 | — | start = 0 | `(0, start)` |
| 1 | (0, start) | slow_path1 = 0+2 = **2**, fast_junction = 0+1 = **1** | `(1, fast_junction)`, `(2, slow_path1)` |
| 2 | (1, fast_junction) | fast_path = 1+1 = **2** | `(2, slow_path1)`, `(2, fast_path)` |
| 3 | (2, slow_path1) | slow_path2 = 2+1 = **3** | `(2, fast_path)`, `(3, slow_path2)` |
| 4 | (2, fast_path) | merge_point = 2+1 = **3** (parent: fast_path) | `(3, slow_path2)`, `(3, merge_point)` |
| 5 | (3, slow_path2) | merge_point = 3+1 = 4 — **not better than 3, ignore** | `(3, merge_point)` |
| 6 | (3, merge_point) | goal = 3+1 = **4** | `(4, goal)` |
| 7 | (4, goal) | **stop** | |

Follow the parents back from `goal`:

```
goal ← merge_point ← fast_path ← fast_junction ← start
```

Reverse:

```
start → fast_junction → fast_path → merge_point → goal     (cost 4)
```

**The fast route.** Dijkstra got it right, whatever the line order in the file.

### The key moment is step 5

The slow route *also* reached `merge_point`, with cost 4. But the fast route
had already reached it with cost 3. So Dijkstra kept 3 and ignored 4.
That comparison — *"is this better than what I knew?"* — is the whole
algorithm.

### Notice step 3

At step 3, two zones were waiting at cost 2: `slow_path1` and `fast_path`.
Which one comes out first doesn't change the final answer here. But ties
matter — see Part 5 and Part 6.

---

## Part 4 — `heapq`, the priority queue

Finding "the cheapest waiting item" by scanning a whole list every time is
slow. Python gives you `heapq` in the standard library. It is not a graph
library, so the subject allows it.

A heap is a normal Python list, but you only touch it with two functions:

```python
import heapq

waiting = []
heapq.heappush(waiting, (5, "c"))
heapq.heappush(waiting, (1, "a"))
heapq.heappush(waiting, (3, "b"))

print(heapq.heappop(waiting))   # (1, 'a')   — smallest first
print(heapq.heappop(waiting))   # (3, 'b')
```

`heappush` adds an item. `heappop` removes and returns the **smallest**.

### How tuples are compared

Python compares tuples item by item, left to right:

```python
(1, "z") < (2, "a")     # True  — 1 < 2, decided on the first item
(2, "a") < (2, "b")     # True  — first items equal, so compare the second
```

So with `(cost, zone)` in the heap, the lowest cost comes out first.

### The trap — ties with objects

When two costs are **equal**, Python moves on to compare the second item.
In your project that is a `Zone` object:

```python
heapq.heappush(waiting, (2, zone_a))
heapq.heappush(waiting, (2, zone_b))
# TypeError: '<' not supported between instances of 'Zone' and 'Zone'
```

Python doesn't know how to compare two zones, so it crashes. And this *will*
happen — look at step 3 in the table above, where two zones sat at cost 2.

The usual fix: put a counter in the middle, so the comparison never reaches
the object.

```python
counter = 0
heapq.heappush(waiting, (cost, counter, zone))
counter += 1
```

The counter is always different, so ties in cost are broken by the counter,
and the zone is never compared.

---

## Part 5 — Old entries in the heap

Look at the Dijkstra steps again. When a zone's cost improves, you push a
**new** entry. The old one stays in the heap — `heapq` has no way to remove
or update an item in the middle.

So one zone can be in the heap twice, with two costs. The cheap one comes out
first and is processed. Later the expensive one comes out too.

That's why the algorithm has this line:

```
if cost is worse than best_cost[zone]: skip it
```

When an old, outdated entry comes out, you notice it's worse than the best
known cost, and throw it away. This is called **lazy deletion**. It's the
normal way to write Dijkstra in Python.

Without this check, the algorithm still gives the right answer, but it does
the same work several times.

---

## Part 6 — Your priority tie-break

You decided: **cost decides; when two routes cost the same, prefer the one
with more priority zones.**

Example where it matters:

```
         normal_zone
        /           \
start                 goal
        \           /
        priority_zone
```

Both routes cost 2. Plain Dijkstra picks whichever it meets first — the line
order of the file again. Your rule says: take the priority route.

So your comparison is no longer just "is the cost lower?" It is:

- is the cost lower? → better
- is the cost equal, **and** does it pass through more priority zones? → better
- otherwise → not better

A hint about how to write this: in Part 4 you saw that Python compares tuples
item by item. Think about what you could put in the heap, and in the
best-cost record, so that a single `<` does both comparisons at once. And
think about the direction — lower is better for cost, but *more* is better
for priority zones. How do you make "more" come out first in a structure
that always returns the smallest?

That's for you to design.

---

## Part 7 — Other things Dijkstra handles for free

**Blocked zones.** You never push them into the heap — check `is_enterable`
before computing `new_cost`. So no path can ever pass through one.

**Dead ends.** Dijkstra explores them — `dead_end` in
`01_dead_end_trap.txt` will get a cost. But it never lies on the way to
`goal`, so it never appears in the rebuilt path. No special code needed.

**Loops.** A zone's cost only goes down, never up. Going around a loop only
makes the cost higher, so it's never "better", so the loop is never followed
forever. No visited set needed — `best_cost` does that job.

**The start zone.** It has cost 0 and nobody ever "enters" it. Coming back to
it would cost more than 0, so it's never updated.

---

## Part 8 — Complexity

The subject asks you (VII.1): *"What is the complexity?"*

Call **Z** the number of zones and **C** the number of connections.

| Algorithm | Complexity | Why |
|---|---|---|
| BFS | O(Z + C) | each zone enters the queue once, each connection is looked at a constant number of times |
| Dijkstra with heapq | O((Z + C) log Z) | same, but every push and pop on the heap costs log Z |

For the challenger map, Z = 54 and C = 70. Both are instant. Speed is not
your problem in this project — **correctness and turn count** are.

---

## Part 9 — What neither of them does

Both algorithms return **one** path.

The subject wants *"distribution of drones across multiple paths"* (VII.1).
Finding several useful paths is the next step, and it uses Dijkstra as a
building block — but it's a separate question. We'll do it after you have
one working shortest path.

---

## Summary

| | BFS | Dijkstra |
|---|---|---|
| Takes next | the oldest waiting zone | the cheapest waiting zone |
| Waiting list | queue (first in, first out) | heap (smallest first) |
| Finds | fewest steps | lowest cost |
| Handles restricted = 2? | no | yes |
| Remembers | visited set + parents | best cost + parents |
| In this project | not enough | the one you need |

---

## Before you write code — answer these

1. What will you store in `best_cost` and `parent`? Keyed by what?
   (Hint: think about whether to key by `Zone` object or by name.)
2. Where exactly do you check `is_enterable`?
3. What goes in the heap? Remember the tie trap.
4. How does your priority tie-break change what's stored and compared?
5. What should the function return if `goal` is never reached?
   (Remember your decision: "no path exists" should give a clear message.)

Write your answers in words first. Then the code.