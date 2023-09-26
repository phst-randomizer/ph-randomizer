import logging
from pathlib import Path
import random
import string

import click

from ph_rando.common import click_setting_options
from ph_rando.patcher._patcher import Patcher
from ph_rando.shuffler._shuffler import Shuffler


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
def randomizer_cli(
    input_rom_path: Path,
    output_rom_path: Path,
    seed: str | None,
    log_level: str,
    **settings: bool | str | list[str],
) -> None:
    logging.basicConfig(level=logging.getLevelNamesMapping()[log_level])

    # Generate random seed if one isn't provided
    if seed is None:
        seed = ''.join(random.choices(string.ascii_letters, k=20))

    # Run the shuffler
    shuffled_aux_data = Shuffler(seed, settings).generate()

    patcher = Patcher(rom=input_rom_path, aux_data=shuffled_aux_data, settings=settings)

    patched_rom = patcher.generate()

    if output_rom_path is not None:
        # Save the ROM to disk
        patched_rom.saveToFile(output_rom_path)


if __name__ == '__main__':
    randomizer_cli()
