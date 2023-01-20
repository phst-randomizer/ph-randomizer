import hashlib
from io import BytesIO
import logging
from pathlib import Path

import click
from ndspy import rom
from vidua import bps

from ph_rando.shuffler.aux_models import (
    Area,
    Chest,
    DigSpot,
    Event,
    IslandShop,
    SalvageTreasure,
    Tree,
)

from ._items import ITEMS
from ._util import (
    load_aux_data,
    patch_chest,
    patch_dig_spot_treasure,
    patch_event,
    patch_island_shop,
    patch_salvage_treasure,
    patch_tree,
)
from .location_types import Location


def apply_base_patch(input_rom_data: bytes) -> rom.NintendoDSRom:
    """Apply the base patch to `input_rom`."""
    # Calculate sha256 of provided ROM
    sha256_calculator = hashlib.sha256()
    sha256_calculator.update(input_rom_data)
    sha256 = sha256_calculator.hexdigest()

    # Get the path to the base patch for the given ROM, erroring out of it doesn't exist
    base_patch_path = Path(__file__).parents[1] / 'base' / 'out' / f'{sha256}.bps'
    if not base_patch_path.exists():
        raise Exception(f'Invalid ROM! No base patch found for a ROM with sha256 of {sha256}.')

    # Apply the base patch to the ROM
    with open(base_patch_path, 'rb') as patch_file:
        patched_rom = bps.patch(source=BytesIO(input_rom_data), bps_patch=patch_file)

    return rom.NintendoDSRom(data=patched_rom.read())


def patch_items(aux_data: list[Area], input_rom: rom.NintendoDSRom) -> rom.NintendoDSRom:
    """
    Patches a ROM with the given aux data.

    Given aux data, an input rom, and an output path, this function reads the aux data and
    patches the input rom with it accordingly, returning the patched rom. Note, the base
    ROM patch is also applied and should be located at the expected location (see apply_base_patch
    function for more details).
    """
    # TODO: maybe eliminate this global variable and directly
    # pass the NDS rom object to patcher functions?
    Location.ROM = input_rom

    for area in aux_data:
        for room in area.rooms:
            for chest in room.chests:
                if chest.contents not in ITEMS:  # TODO: remove
                    logging.warning(f'Item {chest.contents} not defined in patcher/_items.py !')
                    continue
                match chest.type:
                    case 'chest':
                        assert isinstance(chest, Chest)
                        patch_chest(chest)
                    case 'event':
                        assert isinstance(chest, Event)
                        patch_event(chest)
                    case 'island_shop':
                        assert isinstance(chest, IslandShop)
                        patch_island_shop(chest)
                    case 'tree':
                        assert isinstance(chest, Tree)
                        patch_tree(chest)
                    case 'salvage_treasure':
                        assert isinstance(chest, SalvageTreasure)
                        patch_salvage_treasure(chest)
                    case 'dig_spot':
                        assert isinstance(chest, DigSpot)
                        patch_dig_spot_treasure(chest)
                    case 'freestanding':
                        pass  # TODO: implement this
                    case 'on_enemy':
                        # TODO: is this needed? It represents items that are
                        # carried by enemies and dropped, like keys on
                        # phantoms or rats. This *might* be the same as
                        # freestanding; more research is needed
                        pass  # TODO: implement this
                    case 'minigame_reward_chest':
                        pass  # TODO: implement this
                    case other:
                        raise NotImplementedError(f'Unknown location type {other!r}')

    # Write changes to the in-memory ROM
    Location.save_all()

    return Location.ROM


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
def patcher_cli(aux_data_directory: Path, input_rom_path: Path, output_rom_path: str | None):
    new_aux_data = load_aux_data(aux_data_directory)

    patched_rom = apply_base_patch(input_rom_path.read_bytes())

    patched_rom = patch_items(new_aux_data, patched_rom)

    if output_rom_path is not None:
        # Save the ROM to disk
        patched_rom.saveToFile(output_rom_path)


if __name__ == '__main__':
    patcher_cli()
