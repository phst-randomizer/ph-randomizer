import json
from os import path
from pathlib import Path
import sys
from typing import Any

from _parser import clear_nodes, parse_area
import click


def logic_to_aux(logic_directory: str, output: str | None):
    logic_files = list(Path(logic_directory).rglob("*.logic"))

    for file in logic_files:
        file_directory = file.relative_to(logic_directory)

        rooms: dict[str, dict[str, Any]] = {}
        with open(file, "r") as fd:
            lines = [line.strip() for line in fd.readlines() if line and line.strip()]
        clear_nodes()
        nodes = parse_area(lines)

        path_to_schema = "../"
        directories_in_between = str(file_directory.as_posix()).count("/")

        for _ in range(directories_in_between):
            path_to_schema += "../"
        path_to_schema += "aux_schema.json"

        logic: dict[str, Any] = {
            "$schema": str(path_to_schema),
            "name": nodes[0].area,
        }

        for node in nodes:
            room = rooms.get(node.room, {})

            chests = room.get("chests", [])
            doors = room.get("doors", [])
            for content in node.contents:
                match content.type:
                    case "chest":
                        chests.append({"name": content.data, "type": "", "contents": ""})
                    case "door":
                        doors.append({"name": content.data, "link": ""})
            room["chests"] = chests
            room["doors"] = doors
            rooms[node.room] = room

        for room_name, room_content in rooms.items():
            current_rooms = logic.get("rooms", [])

            room_content["name"] = room_name

            current_rooms.append(room_content)

            logic["rooms"] = current_rooms

        if output == "--":
            print(json.dumps(logic, indent=2), file=sys.stdout)
        elif output is not None:
            output_path = Path(output).joinpath(str(file_directory).split(".")[0] + ".wip-json")
            Path(path.dirname(output_path)).mkdir(parents=True, exist_ok=True)

            with open(output_path, "w") as fd:
                fd.write(json.dumps(logic, indent=2))


@click.command()
@click.option("-l", "--logic-directory", required=True, type=click.Path(exists=True))
@click.option(
    "-o",
    "--output",
    default=None,
    type=click.Path(exists=False, dir_okay=True, file_okay=False),
    help="Path to save aux data to. Use -- to output to stdout.",
)
def logic_to_aux_cli(logic_directory: str, output: str | None):
    return logic_to_aux(logic_directory, output)


if __name__ == "__main__":
    logic_to_aux_cli()
