from pathlib import Path
import sys
from tempfile import TemporaryDirectory

import click

from patcher import patch
from patcher._util import is_frozen
from shuffler import shuffle

# TODO: this is an example script for how to call the patcher/shuffler.
# At some point this will be fleshed out into a full CLI (and eventually
# GUI) to run the full randomizer.


@click.command()
@click.option(
    "-i",
    "--input-rom-path",
    required=True,
    type=click.Path(exists=True),
    help="Path to stock ROM to randomize.",
)
@click.option(
    "-o",
    "--output-rom-path",
    type=click.Path(exists=False),
    required=True,
    help="Path to save randomized ROM to.",
)
@click.option("-s", "--seed", type=str, required=False, help="Seed for the randomizer.")
def randomizer(input_rom_path: str, output_rom_path: str, seed: str | None):
    if is_frozen():
        aux_data_directory = str(Path(sys._MEIPASS) / "auxiliary")  # type: ignore
        logic_directory = str(Path(sys._MEIPASS) / "logic")  # type: ignore
    else:
        aux_data_directory = str(Path(__file__).parent / "shuffler" / "auxiliary")
        logic_directory = str(Path(__file__).parent / "shuffler" / "logic")

    with TemporaryDirectory() as tmp_dir:
        # Run the shuffler
        shuffle(seed, aux_data_directory, logic_directory, tmp_dir)
        # Run the patcher
        patch(tmp_dir, input_rom_path, output_rom_path)


if __name__ == "__main__":
    randomizer()
