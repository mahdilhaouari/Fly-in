from parsing import ParseError
import re
# text = "nb of dranes: --32"

# result = re.fullmatch(r"nb of dranes: (--?\d+)", text)
# print(result.group(1))


# result2 = re.findall(r"[^a-b]+", "dwdazwwdwdazwd")
# print(result2(1))






# if result.group(2) in [z.value for z in ZoneType]:
#     print("done")


from enum import Enum

class ZoneType(Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"

line = "hub: priority_hub 5 0 [zone=priority color=cyan max_drones=4]"

result = re.fullmatch(r"(start_hub|end_hub|hub): ([^\s-]+) (?P<x>-?\d+) (?P<y>-?\d+)(\s*\[(?P<meta>.*)\])?", line)
if result is None:
    raise ParseError ("bad zone line")

raw = result.group("meta") or ""
result2 = re.findall(r"(\w+)=(\S+)",raw)
print(result2)

dic = {}
for x, y in result2:
    dic[x] = y

allowed_metadata = {"zone", "max_drones", "color"}

# Unknown metadata
unknown = set(dic) - allowed_metadata

if unknown:
    print(f"metadata not recognized: {unknown}")


try:
    zone_type = ZoneType(dic.get("zone", "normal"))
except ValueError:
    raise ParseError("invalid zone type")

try:
    max_drones = int(dic.get("max_drones", "1"))
except ValueError:
    raise ParseError("max_drones must be a number")
if max_drones < 1:
    raise ParseError ("the minimum possible number of drones is 1")

print(max_drones)

color = dic.get("color") 
print(color)








text1 = "connection: start-waypoint1fdfdf"
text2 = "connection: corridorA-tunnelB [max_link_capacity=2]"

result3 = re.fullmatch(r"connection: ([^\s]+)(\s*\[(?P<meta2>.*)\])?", text1)

if result3 is None:
    raise ParseError ("bad connection line")

print(result3.group(0))

names = result3.group(1).split("-")
if len(names) != 2:
    raise ParseError("a connection has to be between just two zones")
print(names)

if "" in names:
    raise ParseError("a connection need to have a name")








text3 = "nb_drones: 25"
result4 = re.fullmatch(r"nb_drones:\s+(-?\d+)", text3)

if result4 is None:
    raise ParseError ("bad number of zone linee")
try:
    nbr = int(result4.group(1))
except ValueError:
    raise ParseError ("the number of drones must be a number")
if nbr < 1:
    raise ParseError ("we must have atlist 1 drone")

# lines = [
#     "hub: end 1 0 []",
# ]

# for line in lines:
#     print(re.fullmatch(r"(start_hub|end_hub|hub): ([^\s-]+) (?P<x>-?\d+) (?P<y>-?\d+)(\s*\[(?P<meta>.*)\])?", line) is not None, "|", line)