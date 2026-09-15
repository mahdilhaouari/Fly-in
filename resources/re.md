# Regex for the Fly-in parser

A short course. Only what you need for this project.
Read one part, try the code, then go to the next.

---

## Part 0 — What is a regex?

A regex is a small pattern that describes the **shape** of a text.

You do not say "this is the word gate1".
You say "a word, then a space, then a number".

Then you ask Python: does this line have that shape? And if yes, give me
the pieces.

Your map file has four line shapes:

```
nb_drones: 5
start_hub: hub 0 0 [color=green]
hub: roof1 3 4 [zone=restricted color=red]
connection: corridorA-tunnelB [max_link_capacity=2]
```

A regex lets you check the shape and pull out the pieces in one step.

---

## Part 1 — The first pattern

```python
import re

line = "nb_drones: 5"
result = re.fullmatch(r"nb_drones: 5", line)
print(result)
```

Run it. You get a `Match` object. Now change the line to `"nb_drones: 7"`
and run again. You get `None`.

So far the pattern is just fixed text. Useless. But two things to learn:

**`re.fullmatch`** means: the whole line must match, from start to end.
Nothing left over.

**The `r` before the string** — `r"..."` — is a *raw string*. In a raw
string, `\` stays as `\`. Regex uses `\` a lot, so always write `r"..."`
for patterns. Always. If you forget, you get strange bugs.

---

## Part 2 — Matching digits: `\d`

`\d` means "one digit" (0 to 9).

```python
re.fullmatch(r"nb_drones: \d", "nb_drones: 5")    # matches
re.fullmatch(r"nb_drones: \d", "nb_drones: 25")   # None
```

`\d` is exactly one digit. `25` is two digits, so it fails.

### Repeating: `+`

`+` means "one or more of the thing before it".

```python
re.fullmatch(r"nb_drones: \d+", "nb_drones: 25")   # matches
re.fullmatch(r"nb_drones: \d+", "nb_drones: 7")    # matches
re.fullmatch(r"nb_drones: \d+", "nb_drones: ")     # None
```

`\d+` = one digit, two digits, fifty digits. But at least one.

### Other repeat signs

| Sign | Meaning |
|---|---|
| `+` | one or more |
| `*` | zero or more |
| `?` | zero or one (optional) |
| `{2}` | exactly 2 |
| `{1,3}` | between 1 and 3 |

You will mostly use `+`, `*`, and `?`.

**Try it:** what does `r"a+"` match? What about `r"a*"`? Test both on
`"aaa"` and on `""`.

---

## Part 3 — Getting the value out: groups

Matching is not enough. You need the number `25`, not just "yes it matched".

Put round brackets `( )` around the part you want. That is a **group**.

```python
m = re.fullmatch(r"nb_drones: (\d+)", "nb_drones: 25")
print(m.group(1))     # "25"
```

`group(1)` is the first bracket. `group(2)` would be the second, and so on.
`group(0)` is the whole match.

Important: **the result is always a string.** `"25"`, not `25`. You convert
it yourself with `int()`. And you do that inside a `try`, because the
subject wants a clear error on bad input.

### Named groups

With many groups, numbers get confusing. You can name them:

```python
m = re.fullmatch(r"nb_drones: (?P<count>\d+)", "nb_drones: 25")
print(m.group("count"))     # "25"
```

`(?P<name>...)` looks ugly but it is worth it. When your zone pattern has
four groups, `m.group("x")` is much clearer than `m.group(3)`.

---

## Part 4 — Negative numbers

Your map `02_simple_fork.txt` has this line:

```
hub: path_b 2 -1 [color=blue]
```

`-1`. So `\d+` is not enough — there may be a minus sign in front.

The minus is optional, so use `?`:

```python
r"-?\d+"
```

Read it as: maybe a minus, then one or more digits.

**Try it:** test `r"-?\d+"` with `re.fullmatch` on `"5"`, `"-5"`, `"--5"`,
and `"-"`. Make sure you understand each result.

---

## Part 5 — Character classes: `[ ]`

`[ ]` means "one character from this set".

```python
r"[abc]"        # one char: a, b, or c
r"[0-9]"        # one digit (same as \d)
r"[a-z]"        # one lowercase letter
r"[a-zA-Z0-9_]" # letter, digit, or underscore
```

Inside `[ ]`, the `-` makes a range. `a-z` means a to z.

### The `^` inside brackets means NOT

```python
r"[^abc]"       # one char that is NOT a, b, or c
```

This is useful for you. The subject says:

> Zone names can use any valid characters except dashes and spaces.

That is a "not" rule. So:

```python
r"[^\s-]+"
```

`\s` means whitespace (space, tab). So `[^\s-]` is "any char that is not
a space and not a dash". With `+`, that is one or more such characters.

Look at your real names: `gate1`, `path_a`, `restricted_tunnel1`,
`maze_trap_a1`. All of them fit.

**Careful:** the `-` must go at the end inside the brackets (or be escaped),
or Python thinks you want a range.

---

## Part 6 — Anchors: `^` and `$`

- `^` means "start of the text"
- `$` means "end of the text"

These matter with `re.match` and `re.search`. With `re.fullmatch` you do
not need them, because fullmatch already requires the whole text to match.

### The three functions

| Function | Meaning |
|---|---|
| `re.fullmatch` | the whole text must match |
| `re.match` | the text must match from the start, extra at the end is OK |
| `re.search` | find the pattern anywhere in the text |

For checking a line shape, **use `fullmatch`**. It is the strict one, and
strict is what you want — if a line has extra junk at the end, that is an
error, and `fullmatch` catches it while `match` does not.

Use `search` or `findall` when you are looking for pieces *inside* a line
(you will need this for the metadata).

---

## Part 7 — Spaces

`\s` = one whitespace character.
`\s+` = one or more.

In your file, is the space after `nb_drones:` always exactly one? Look at
the subject's example — it shows `nb_drones:   5` with several spaces in
one place. So be safe and use `\s+`.

Also lines may have spaces at the end. You can strip the line before
matching (`line.strip()`), which is simpler than putting `\s*` everywhere.

---

## Part 8 — Building the zone line pattern

Now put it together. A zone line:

```
hub: roof1 3 4 [zone=restricted color=red]
```

The pieces are:

1. a prefix: `hub:` or `start_hub:` or `end_hub:`
2. a name
3. an x number
4. a y number
5. an optional `[...]` block

You know all the tools now:

- prefix — you could match it with a group of alternatives (see below)
- name — `[^\s-]+`
- numbers — `-?\d+`
- the bracket block — optional, so `?`

### Alternatives: `|`

`|` means OR.

```python
r"(start_hub|end_hub|hub)"
```

**Order matters here.** Regex tries left to right and takes the first thing
that works. If you write `(hub|start_hub|end_hub)`, then on the line
`start_hub: ...` it will... actually think about this. Does `hub` match at
the start of `start_hub`? Try it and see what happens. This is a real trap.

### Escaping special characters

Some characters mean something special in regex: `[ ] ( ) . + * ? | ^ $ \`

To match them as normal text, put `\` in front:

```python
r"\["      # a real [ character
r"\]"      # a real ] character
```

Your metadata block is inside `[ ]`, so you will need this.

### The optional block

To make a whole part optional, put it in a group and add `?`:

```python
r"(\[.*\])?"
```

That means: maybe a `[`, then anything, then a `]`.

`.` means "any character". `.*` means "any number of any characters".

**Warning about `.*`:** it is greedy — it takes as much as it can. Usually
fine here, but remember it.

### Your turn

Write a `fullmatch` pattern for a zone line. Use named groups for the
prefix, the name, x, y, and the metadata block. Test it on these real lines:

```
start_hub: start 0 0 [color=green]
hub: path_b 2 -1 [color=blue]
hub: waypoint1 1 0
end_hub: impossible_goal 23 0 [color=rainbow]
hub: priority_hub 5 0 [zone=priority color=cyan max_drones=4]
```

And make sure these **fail**:

```
hub: bad-name 1 2
hub: name 1
hub: name 1 2 extra
```

---

## Part 9 — The metadata block

This is where regex really helps.

```
[zone=restricted color=red max_drones=2]
```

Facts about it:
- the tags can be in any order
- any tag can be missing
- the whole block can be missing

So you cannot write one fixed pattern for the whole block. Instead, find
**all the key=value pairs** inside it.

### `re.findall`

`findall` returns a list of everything that matches.

```python
text = "zone=restricted color=red max_drones=2"
pairs = re.findall(r"(\w+)=(\S+)", text)
print(pairs)
# [('zone', 'restricted'), ('color', 'red'), ('max_drones', '2')]
```

Two new things:
- `\w` = a letter, digit, or underscore (same as `[a-zA-Z0-9_]`)
- `\S` = any character that is NOT whitespace (capital S = the opposite of `\s`)

When your pattern has two groups, `findall` gives you a list of pairs. Very
handy — you can turn it straight into a dict.

### Your turn

Take the inside of the bracket block and turn it into a dict of
key → value. Then:

- for `zone`, convert the value with `ZoneType(value)` inside a `try`
- for `max_drones`, convert with `int(value)` inside a `try`, and check it
  is at least 1 (the subject says capacities must be positive integers)
- for `color`, keep the string
- for anything else — what should happen? An unknown key like
  `[speed=fast]`. Decide: error, or ignore? The subject is not clear.
  Write down your choice.

---

## Part 10 — The connection line

```
connection: corridorA-tunnelB [max_link_capacity=2]
```

Here is the interesting question: **do you need regex for the two names?**

You could match the whole shape with regex. Or you could match the general
shape with regex and then use `.split("-")` on the middle part.

Think about it: the names cannot contain dashes. So the part between
`connection:` and the space has exactly one dash. `split("-")` gives you a
list — and if that list does not have exactly 2 items, that is an error you
must report.

Both ways work. `split` is easier to read. Part of using regex well is
knowing when **not** to use it.

---

## Part 11 — Compiling patterns

If you use a pattern many times, compile it once:

```python
ZONE_LINE = re.compile(r"...")

m = ZONE_LINE.fullmatch(line)
```

Why: Python does not re-build the pattern on every line. On the challenger
map with ~100 lines it does not matter much, but it is the normal way to
write it, and it puts all your patterns together at the top of the file
where they are easy to find and easy to fix.

---

## Part 12 — Where NOT to use regex

Important for your peer review. Regex is not always the answer.

**Do not use regex for:**

- Converting `"4"` to a number → use `int()` in a `try`
- Checking a zone type is legal → use `ZoneType(value)` in a `try`
- Removing comments → `line.split("#")[0]` is clearer
- Checking a value is positive → a plain `if`

**Do use regex for:**

- Checking the shape of a whole line
- Pulling out several pieces at once
- Finding all key=value pairs in the metadata
- Checking a name has no forbidden characters

A good rule: regex answers "what shape is this text". Everything after
that is normal Python.

---

## Quick reference

| Pattern | Meaning |
|---|---|
| `\d` | one digit |
| `\w` | letter, digit, or underscore |
| `\s` | one whitespace |
| `\S` | one NON-whitespace |
| `.` | any character |
| `+` | one or more |
| `*` | zero or more |
| `?` | zero or one |
| `[abc]` | one of a, b, c |
| `[^abc]` | one char that is not a, b, c |
| `(...)` | group — pulls the value out |
| `(?P<name>...)` | named group |
| `\|` | or |
| `\[` | a real `[` character |
| `^` `$` | start / end of text |

| Function | Use |
|---|---|
| `re.fullmatch` | whole text must match — use for line shapes |
| `re.search` | find anywhere |
| `re.findall` | get all matches as a list |
| `re.compile` | build the pattern once |

---

## What to do now

1. Open a scratch file and try every example above. Change things, break
   them, see what happens. This is the fastest way to learn regex.
2. Write the zone line pattern from Part 8 and test it on the real lines.
3. Write the metadata reader from Part 9.
4. Send both to me and we will check them together.

One tip: <https://regex101.com> lets you type a pattern and a test line and
shows you exactly what matched. Choose "Python" on the left side. Very
useful while learning.