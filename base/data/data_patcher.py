import os
from pathlib import Path

from _title_screen import insert_title_screen
from _zmb_patches import patch_zmb_files
import click
from ndspy.rom import NintendoDSRom


@click.command()
@click.option(
    '-i',
    '--input-rom',
    type=click.Path(exists=False, path_type=Path),
    required=True,
    help='Source ROM',
)
@click.option(
    '-o',
    '--output-rom',
    type=click.Path(path_type=Path),
    required=True,
    help='Dest ROM',
)
def patcher(input_rom: Path, output_rom: Path) -> None:
    rom = NintendoDSRom.fromFile(str(input_rom))

    insert_title_screen(rom, os.environ.get('VERSION_STRING'))
    patch_zmb_files(rom)

    rom.saveToFile(str(output_rom))


if __name__ == '__main__':
    patcher()
