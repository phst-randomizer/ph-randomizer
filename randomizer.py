from pathlib import Path
from tempfile import TemporaryDirectory

import click

from patcher import patch
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
def randomizer(input_rom_path: str, output_rom_path: str):
    aux_data_directory = str(Path(__file__).parent / "shuffler" / "auxiliary")
    logic_directory = str(Path(__file__).parent / "shuffler" / "logic")

    with TemporaryDirectory() as tmp_dir:
        # Run the shuffler
        shuffle(aux_data_directory, logic_directory, tmp_dir)
        # Run the patcher
        patch(tmp_dir, input_rom_path, output_rom_path)


if __name__ == "__main__":
    randomizer()
