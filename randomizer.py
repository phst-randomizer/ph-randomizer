from pathlib import Path
import sys

import click

from patcher import patch
from patcher._util import is_frozen, load_rom
from shuffler import shuffle
from shuffler._parser import parse
from shuffler.main import load_aux_data

# TODO: this is an example script for how to call the patcher/shuffler.
# At some point this will be fleshed out into a full CLI (and eventually
# GUI) to run the full randomizer.


@click.command()
@click.option(
    '-i',
    '--input-rom-path',
    required=True,
    type=click.Path(exists=True),
    help='Path to stock ROM to randomize.',
)
@click.option(
    '-o',
    '--output-rom-path',
    type=click.Path(exists=False),
    required=True,
    help='Path to save randomized ROM to.',
)
@click.option('-s', '--seed', type=str, required=False, help='Seed for the randomizer.')
@click.option('--dpad-patch', is_flag=True, default=False)
def randomizer(input_rom_path: str, output_rom_path: str, seed: str | None, dpad_patch: bool):
    if is_frozen():
        aux_data_directory = str(Path(sys._MEIPASS) / 'auxiliary')  # type: ignore
        logic_directory = str(Path(sys._MEIPASS) / 'logic')  # type: ignore
    else:
        aux_data_directory = str(Path(__file__).parent / 'shuffler' / 'auxiliary')
        logic_directory = str(Path(__file__).parent / 'shuffler' / 'logic')

    # Parse logic files
    nodes, edges = parse(Path(logic_directory))

    # Parse aux data files
    aux_data = load_aux_data(Path(aux_data_directory))

    # Run the shuffler
    shuffled_aux_data = shuffle(seed, nodes, edges, aux_data)

    # Run the patcher
    patch(shuffled_aux_data, load_rom(Path(input_rom_path), dpad_patch), output_rom_path)


if __name__ == '__main__':
    randomizer()
