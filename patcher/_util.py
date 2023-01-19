import json
import logging
from pathlib import Path

from patcher._items import ITEMS
from patcher.location_types import (
    DigSpotLocation,
    EventLocation,
    IslandShopLocation,
    MapObjectLocation,
    SalvageTreasureLocation,
)
from shuffler.aux_models import Area, Chest, DigSpot, Event, IslandShop, SalvageTreasure, Tree


def load_aux_data(directory: Path) -> list[Area]:
    aux_data: list[Area] = []
    for file in directory.rglob('*.json'):
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
    if event.bmg_file_path.lower() == 'todo':  # TODO: remove
        logging.warning(f'{event.name}: bmg_file_path not set')
        return
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
    if dig_spot.zmb_file_path.lower() == 'todo':  # TODO: remove
        logging.warning(f'{dig_spot.name}: zmb_file_path not set')
        return
    location = DigSpotLocation(
        actor_index=dig_spot.zmb_actor_index, file_path=dig_spot.zmb_file_path
    )
    location.set_location(ITEMS[dig_spot.contents])
