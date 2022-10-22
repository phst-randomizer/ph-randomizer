from collections import OrderedDict
import json
from os.path import relpath
from pathlib import Path
import sys
from typing import Any

import click

from shuffler._parser import parse_area

AUX_DATA_SCHEMA_FILE = (Path(__file__).parent / 'aux_schema.json').resolve()


def logic_to_aux(logic_directory: str, output: str | None):
    logic_files = list(Path(logic_directory).rglob('*.logic'))

    for file in logic_files:
        file_directory = file.relative_to(logic_directory)

        rooms: dict[str, dict[str, Any]] = {}
        with open(file) as fd:
            lines: list[str] = []
            for line in fd.readlines():
                line = line.strip()  # strip off leading and trailing whitespace
                if '#' in line:
                    line = line[: line.index('#')]  # remove any comments
                if line:
                    lines.append(line)

        nodes, _ = parse_area(lines, [], {})

        path_to_schema = Path(relpath(AUX_DATA_SCHEMA_FILE, file.parent.resolve())).as_posix()

        logic: OrderedDict[str, Any] = OrderedDict(
            {
                '$schema': str(path_to_schema),
                'name': nodes[0].area,
            }
        )

        for node in nodes:
            room = rooms.get(node.room, {})

            chests = room.get('chests', [])
            doors = room.get('doors', [])
            for content in node.contents:
                match content.type:
                    case 'chest':
                        chests.append({'name': content.data, 'type': '', 'contents': ''})
                    case 'door':
                        doors.append({'name': content.data, 'link': ''})
            room['chests'] = chests
            room['doors'] = doors
            rooms[node.room] = room

        for room_name, room_content in rooms.items():
            current_rooms = logic.get('rooms', [])

            room_content['name'] = room_name

            room_content = OrderedDict(
                sorted(room_content.items(), key=lambda i: 0 if i[0] == 'name' else ord(i[0][0]))
            )

            current_rooms.append(room_content)

            logic['rooms'] = current_rooms

        if output == '--':
            print(json.dumps(logic, indent=2), file=sys.stdout)
        elif output is not None:
            output_path = (Path(output) / file_directory).with_suffix('.wip-json')
            output_path.parent.mkdir(parents=True, exist_ok=True)

            existing_filename = output_path.with_suffix('.json')

            if existing_filename.exists():
                print(f'Skipping {output_path.name}, {existing_filename.name} already exists...')
                continue

            with open(output_path, 'w') as fd:
                fd.write(json.dumps(logic, indent=2))
                fd.write('\n')


@click.command()
@click.option('-l', '--logic-directory', required=True, type=click.Path(exists=True))
@click.option(
    '-o',
    '--output',
    default=None,
    type=click.Path(exists=False, dir_okay=True, file_okay=False),
    help='Path to save aux data to. Use -- to output to stdout.',
)
def logic_to_aux_cli(logic_directory: str, output: str | None):
    return logic_to_aux(logic_directory, output)


if __name__ == '__main__':
    logic_to_aux_cli()
