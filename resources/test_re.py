import re

text = "nb of dranes: "

result = re.fullmatch(r"nb of dranes: \d?", text)
print(result)