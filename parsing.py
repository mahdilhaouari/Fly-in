from data_model import ParseError, Zone



class parser_methodes():
    def clean_line(line: str) -> str:
        return line.strip(" #")

    def parse_drones_line(line) → int
        result4 = re.fullmatch(r"nb_drones:\s+(-?\d+)", text3)

        if result4 is None:
            raise ParseError ("bad number of zone linee")
        try:
            nbr = int(result4.group(1))
        except ValueError:
            raise ParseError ("the number of drones must be a number")
        if nbr < 1:
            raise ParseError ("we must have atlist 1 drone")


class parser(parser_methodes):
    def main_parser_loop(self):
        try:
            with open("file.txt") as f:
                lines = f.readlines()
        except FileNotFoundError:
            print("this file doesnt exist")

        for line_number, line in enumerate(lines, start=1):
            
            line = parser_methodes.clean_line(line)
            print(f"{line_number} and {line}")
            



a = parser()
print(a.main_parser_loop())