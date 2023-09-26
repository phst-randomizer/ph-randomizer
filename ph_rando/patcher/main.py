import logging
from pathlib import Path

import click

from ph_rando.common import click_setting_options

from ._patcher import Patcher

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    '-a',
    '--aux-data-directory',
    required=True,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help='Path to directory containing the aux data to patch the ROM with.',
)
@click.option(
    '-i',
    '--input-rom-path',
    required=True,
    type=click.Path(exists=False, path_type=Path),
    help='Path to ROM to patch.',
)
@click.option(
    '-o', '--output-rom-path', default=None, type=str, help='Path to save patched ROM to.'
)
@click.option(
    '-l',
    '--log-level',
    type=click.Choice(
        list(logging.getLevelNamesMapping().keys()),
        case_sensitive=False,
    ),
    default='INFO',
)
@click_setting_options
def patcher_cli(
    aux_data_directory: Path,
    input_rom_path: Path,
    output_rom_path: str | None,
    log_level: str,
    **settings: bool | str | list[str],
) -> None:
    from ph_rando.shuffler._shuffler import parse_aux_data

    logging.basicConfig(level=logging.getLevelNamesMapping()[log_level])

    new_aux_data = parse_aux_data(
        areas_directory=aux_data_directory,
        enemy_mapping_file=Path(__file__).parents[1] / 'shuffler' / 'enemies.json',
        macros_file=Path(__file__).parents[1] / 'shuffler' / 'macros.json',
    )

    patcher = Patcher(rom=input_rom_path, aux_data=new_aux_data, settings=settings)

    patched_rom = patcher.generate()

    if output_rom_path is not None:
        # Save the ROM to disk
        patched_rom.saveToFile(output_rom_path)


if __name__ == '__main__':
    patcher_cli()
