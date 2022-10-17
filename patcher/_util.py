from io import BytesIO
import json
import os
from pathlib import Path
import sys

from ndspy import rom
from vidua import bps

from patcher._items import ITEMS
from patcher.location_types import (
    DigSpotLocation,
    EventLocation,
    IslandShopLocation,
    Location,
    MapObjectLocation,
    SalvageTreasureLocation,
)
from shuffler.aux_models import Area, Chest, DigSpot, Event, IslandShop, SalvageTreasure, Tree

CHECKSUMS: dict[str, str] = {
    'US': '2dd43288c1b7b428cbd09d9a74464b9a46fe0239eaed82849369f261678011f7',
    'US_DPAD': '7f0caa9d4a071584057ef5c3609d0ed2dfa760fbadd94e1aa431fbdd6dd741fb',
}


def is_frozen():
    """
    Whether or not the app is being executed as part of a script or a frozen executable.

    This can be used to determine if the app is running as a regular python script,
    or if it's a bundled PyInstaller executable.
    """
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def load_rom(file: Path, dpad_patch: bool):
    """
    Load a ROM into memory, patch it, and return it as an ndspy NintendoDSRom object.

    Note that the original file is not modified; the contents of the given ROM are copied into
    memory, and the BPS patch is applied to that in-memory copy.
    """
    base_patch_path = Path(
        Path(sys._MEIPASS) / f'{CHECKSUMS[f"US_DPAD" if dpad_patch else "US"]}.bps'  # type: ignore
        if is_frozen()
        else os.environ.get(
            'BASE_PATCH_PATH',
            Path(__file__).parent.parent
            / 'base'
            / 'out'
            / f'{CHECKSUMS[f"US_DPAD" if dpad_patch else "US"]}.bps',
        )
    )
    with open(base_patch_path, 'rb') as patch_file:
        patched_rom = bps.patch(source=BytesIO(file.read_bytes()), bps_patch=patch_file)
    input_rom = rom.NintendoDSRom(data=patched_rom.read())
    Location.ROM = input_rom
    return input_rom


def load_aux_data(directory: Path):
    aux_data: list[Area] = []
    aux_files = list(directory.rglob('*.json'))
    for file in aux_files:
        with open(file) as fd:
            aux_data.append(Area(**json.load(fd)))
    return aux_data


def patch_chest(chest: Chest):
    # TODO: remove this when all file paths are set correctly in aux data
    if chest.zmb_file_path == 'TODO':
        return

    location = MapObjectLocation(
        child_index=chest.zmb_mapobject_index,
        file_path=chest.zmb_file_path,
        is_tree_drop_item=False,
    )
    location.set_location(ITEMS[chest.contents])


def patch_tree(tree: Tree):
    location = MapObjectLocation(
        child_index=tree.zmb_mapobject_index, file_path=tree.zmb_file_path, is_tree_drop_item=True
    )
    location.set_location(ITEMS[tree.contents])


def patch_event(event: Event):
    location = EventLocation(
        instruction_index=event.bmg_instruction_index, file_path=event.bmg_file_path
    )
    location.set_location(ITEMS[event.contents])


def patch_island_shop(shop_item: IslandShop):
    # Note, the offset is stored as a string in the aux data so that it can be represented as
    # a hex value for readability. So, we must convert it to an `int` here.
    try:  # TODO: remove this try/catch when all offsets are set correctly in aux data
        overlay_offset: int = int(shop_item.overlay_offset, base=16)
    except ValueError:
        return

    location = IslandShopLocation(overlay_number=shop_item.overlay, item_id_index=overlay_offset)
    location.set_location(ITEMS[shop_item.contents])


def patch_salvage_treasure(salvage_treasure: SalvageTreasure):
    location = SalvageTreasureLocation(
        actor_index=salvage_treasure.zmb_actor_index,
        file_path=salvage_treasure.zmb_file_path,
    )
    location.set_location(ITEMS[salvage_treasure.contents])


def patch_dig_spot_treasure(dig_spot: DigSpot):
    location = DigSpotLocation(
        actor_index=dig_spot.zmb_actor_index, file_path=dig_spot.zmb_file_path
    )
    location.set_location(ITEMS[dig_spot.contents])


def patch_rom(aux_data: list[Area], input_rom: rom.NintendoDSRom) -> rom.NintendoDSRom:
    """
    Patches a ROM with the given aux data.

    Given aux data, an input rom, and an output path, this function reads the aux data and
    patches the input rom with it accordingly, writing the resulting new rom to the given
    output path.
    """
    for area in aux_data:
        for room in area.rooms:
            for chest in room.chests or []:
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
