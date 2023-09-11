from pathlib import Path
import random
import string

import click

from ph_rando.common import click_setting_options
from ph_rando.patcher import apply_base_patch, apply_settings_patches, patch_items
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
@click_setting_options
def randomizer_cli(
    input_rom_path: Path,
    output_rom_path: Path,
    seed: str | None,
    **settings: bool | str | list[str],
) -> None:
    # Generate random seed if one isn't provided
    if seed is None:
        seed = ''.join(random.choices(string.ascii_letters, k=20))

    # Run the shuffler
    shuffled_aux_data = Shuffler(seed, settings).generate()

    # Apply the base ROM patch
    patched_rom = apply_base_patch(input_rom_path.read_bytes())

    # Apply any patches required for randomizer settings selected by user
    patched_rom = apply_settings_patches(patched_rom, settings)

    # Patch the shuffled items into the ROM
    patched_rom = patch_items(shuffled_aux_data, patched_rom)

    if output_rom_path is not None:
        # Save the ROM to disk
        patched_rom.saveToFile(output_rom_path)


if __name__ == '__main__':
    randomizer_cli()
