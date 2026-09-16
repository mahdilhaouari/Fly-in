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

line = "start_hub: normal 0 0 [color=green zone=restricted max_drones=2 ]"

try:
    result = re.fullmatch(r"(start_hub|end_hub|hub): ([^\s-]+) (?P<x>-?\d+) (?P<y>-?\d+) (\[.*\])?", line)
    print(result.group(0))
except (AttributeError, IndexError) as e:
    print( f"wa {e}")


# hub type

# name

# x

# y

# metadata

result2 = re.findall(r"(\w+)=(\S+)", result.group(5))
print(result2)

dic = {}
for x, y in result2:
    dic[x] = y

allowed_metadata = {"zone", "max_drones", "color"}

# Unknown metadata
unknown = set(dic) - allowed_metadata

if unknown:
    print(f"metadata not recognized: {unknown}")


if dic["zone"] in [z.value for z in ZoneType]:
    value = dic["zone"]
print(value)

nb_drones = int(dic["max_drones"])
print(nb_drones)

color = dic["color"]

print(color)

