import json
import logging
from pathlib import Path

import click

from ph_rando.common import click_setting_options
from ph_rando.patcher._patcher import Patcher
from ph_rando.shuffler._shuffler import Shuffler
from ph_rando.shuffler._spoiler_log import generate_spoiler_log
from ph_rando.shuffler._util import generate_random_seed


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
@click.option(
    '--spoiler-log',
    required=False,
    type=click.Path(exists=False, path_type=Path),
    help='File path to save spoiler log to.',
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
    spoiler_log: Path | None,
    seed: str | None,
    log_level: str,
    **settings: bool | str | set[str],
) -> None:
    logging.basicConfig(level=logging.getLevelNamesMapping()[log_level])

    # Generate random seed if one isn't provided
    if seed is None:
        seed = generate_random_seed()

    # Run the shuffler
    shuffled_aux_data = Shuffler(seed, settings).generate()

    if spoiler_log:
        sl = generate_spoiler_log(shuffled_aux_data).dict()
        Path(spoiler_log).write_text(json.dumps(sl, indent=2))

    patcher = Patcher(rom=input_rom_path, aux_data=shuffled_aux_data, settings=settings)

    patched_rom = patcher.generate()

    if output_rom_path is not None:
        # Save the ROM to disk
        patched_rom.saveToFile(output_rom_path)


if __name__ == '__main__':
    randomizer_cli()
