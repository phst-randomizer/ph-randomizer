from pathlib import Path

import click
from ndspy import rom

from patcher._util import load_aux_data, load_rom, patch_rom


def patch(
    aux_data_directory: str, input_rom_path: str, output_rom_path: str | None = None
) -> rom.NintendoDSRom:
    input_rom = load_rom(Path(input_rom_path))
    new_aux_data = load_aux_data(Path(aux_data_directory))
    patched_rom = patch_rom(new_aux_data, input_rom)

    if output_rom_path is not None:
        # Save the ROM to disk
        patched_rom.saveToFile(output_rom_path)

    return patched_rom


@click.command()
@click.option(
    "-a",
    "--aux-data-directory",
    required=True,
    type=str,
    help="Path to directory containing the aux data to patch the ROM with.",
)
@click.option(
    "-i",
    "--input-rom-path",
    required=True,
    type=str,
    help="Path to ROM to patch.",
)
@click.option(
    "-o", "--output-rom-path", default=None, type=str, help="Path to save patched ROM to."
)
def patcher_cli(aux_data_directory: str, input_rom_path: str, output_rom_path: str | None):
    return patch(aux_data_directory, input_rom_path, output_rom_path)


if __name__ == "__main__":
    patcher_cli()
