from pathlib import Path

import click
from ndspy import rom

from patcher import patch
from shuffler import shuffle

# TODO: this is an example script for how to call the patcher/shuffler.
# At some point this will be fleshed out into a full CLI (and eventually
# GUI) to run the full randomizer.


@click.command()
@click.option(
    '-i',
    '--input-rom-path',
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help='Path to stock ROM to randomize.',
)
@click.option(
    '-o',
    '--output-rom-path',
    type=click.Path(exists=False, path_type=Path),
    required=True,
    help='Path to save randomized ROM to.',
)
@click.option('-s', '--seed', type=str, required=False, help='Seed for the randomizer.')
def randomizer(input_rom_path: Path, output_rom_path: Path, seed: str | None):
    # Run the shuffler
    shuffled_aux_data = shuffle(seed)

    # Load the ROM
    input_rom = rom.NintendoDSRom.fromFile(input_rom_path)

    # Run the patcher
    patched_rom = patch(shuffled_aux_data, input_rom)

    if output_rom_path is not None:
        # Save the ROM to disk
        patched_rom.saveToFile(output_rom_path)


if __name__ == '__main__':
    randomizer()
