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


def is_frozen():
    """
    Whether or not the app is being executed as part of a script or a frozen executable.

    This can be used to determine if the app is running as a regular python script,
    or if it's a bundled PyInstaller executable.
    """
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def load_rom(file: Path):
    """
    Load a ROM into memory, patch it, and return it as an ndspy NintendoDSRom object.

    Note that the original file is not modified; the contents of the given ROM are copied into
    memory, and the BPS patch is applied to that in-memory copy.
    """
    base_patch_path = Path(
        Path(sys._MEIPASS) / 'patch.bps'  # type: ignore
        if is_frozen()
        else os.environ.get(
            'BASE_PATCH_PATH', Path(__file__).parent.parent / 'base' / 'out' / 'patch.bps'
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
