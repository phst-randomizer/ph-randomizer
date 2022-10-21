from pathlib import Path

import click
from ndspy import rom

from patcher._util import (
    load_aux_data,
    load_rom,
    patch_chest,
    patch_dig_spot_treasure,
    patch_event,
    patch_island_shop,
    patch_salvage_treasure,
    patch_tree,
)
from patcher.location_types import Location
from shuffler.aux_models import Area, Chest, DigSpot, Event, IslandShop, SalvageTreasure, Tree


def patch(aux_data: list[Area], input_rom: rom.NintendoDSRom) -> rom.NintendoDSRom:
    """
    Patches a ROM with the given aux data.

    Given aux data, an input rom, and an output path, this function reads the aux data and
    patches the input rom with it accordingly, returning the patched rom.
    """
    for area in aux_data:
        for room in area.rooms:
            for chest in room.chests:
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
                    case other:
                        raise NotImplementedError(f'Unknown location type "{other}"')

    # Write changes to the in-memory ROM
    Location.save_all()

    return input_rom


@click.command()
@click.option(
    '-a',
    '--aux-data-directory',
    required=True,
    type=str,
    help='Path to directory containing the aux data to patch the ROM with.',
)
@click.option(
    '-i',
    '--input-rom-path',
    required=True,
    type=str,
    help='Path to ROM to patch.',
)
@click.option(
    '-o', '--output-rom-path', default=None, type=str, help='Path to save patched ROM to.'
)
def patcher_cli(aux_data_directory: str, input_rom_path: str, output_rom_path: str | None):
    input_rom = load_rom(Path(input_rom_path))
    new_aux_data = load_aux_data(Path(aux_data_directory))

    patched_rom = patch(new_aux_data, input_rom)

    if output_rom_path is not None:
        # Save the ROM to disk
        patched_rom.saveToFile(output_rom_path)


if __name__ == '__main__':
    patcher_cli()
