import json
from pathlib import Path
from typing import Any

from ndspy import rom

from patcher._items import ITEMS
from patcher.location_types import EventLocation, IslandShopLocation, Location, MapObjectLocation


def load_rom(file: Path):
    input_rom = rom.NintendoDSRom.fromFile(str(file))
    Location.ROM = input_rom
    return input_rom


def load_aux_data(directory: Path):
    aux_data: list[dict[Any, Any]] = []
    aux_files = list(directory.rglob("*.json"))
    for file in aux_files:
        with open(file, "r") as fd:
            aux_data.append(json.load(fd))
    return aux_data


def patch_chest(chest: dict[str, Any]):
    contents: str = chest["contents"]
    zmb_file_path: str = chest["zmb_file_path"]
    zmb_mapobject_index: int = chest["zmb_mapobject_index"]

    # TODO: remove this when all file paths are set correctly in aux data
    if zmb_file_path == "TODO":
        return

    location = MapObjectLocation(
        child_index=zmb_mapobject_index, file_path=zmb_file_path, is_tree_drop_item=False
    )
    location.set_location(ITEMS[contents])


def patch_tree(chest: dict[str, Any]):
    contents: str = chest["contents"]
    zmb_file_path: str = chest["zmb_file_path"]
    zmb_mapobject_index: int = chest["zmb_mapobject_index"]

    location = MapObjectLocation(
        child_index=zmb_mapobject_index, file_path=zmb_file_path, is_tree_drop_item=True
    )
    location.set_location(ITEMS[contents])


def patch_npc(npc: dict[str, Any]):
    contents: str = npc["contents"]
    bmg_file_path: str = npc["bmg_file_path"]
    bmg_instruction_index: int = npc["bmg_instruction_index"]

    location = EventLocation(instruction_index=bmg_instruction_index, file_path=bmg_file_path)
    location.set_location(ITEMS[contents])


def patch_island_shop(shop_item: dict[str, Any]):
    contents: str = shop_item["contents"]
    overlay: int = shop_item["overlay"]
    # Note, the offset is stored as a string in the aux data so that it can be represented as
    # a hex value for readability. So, we must convert it to an `int` here.
    try:  # TODO: remove this try/catch when all offsets are set correctly in aux data
        overlay_offset: int = int(shop_item["overlay_offset"], base=16)
    except ValueError:
        return

    location = IslandShopLocation(overlay_number=overlay, item_id_index=overlay_offset)
    location.set_location(ITEMS[contents])


def patch_rom(aux_data: dict[Any, Any], input_rom: rom.NintendoDSRom) -> rom.NintendoDSRom:
    """
    Patches a ROM with the given aux data.

    Given aux data, an input rom, and an output path, this function reads the aux data and
    patches the input rom with it accordingly, writing the resulting new rom to the given
    output path.
    """
    for area in aux_data:
        for room in area["rooms"]:
            if "chests" in room:
                for chest in room["chests"]:
                    match chest["type"]:
                        case "chest":
                            patch_chest(chest)
                        case "npc":
                            patch_npc(chest)
                        case "island_shop":
                            patch_island_shop(chest)
                        case "tree":
                            patch_tree(chest)
                        case "dig":
                            pass  # TODO: implement this
                        case "freestanding":
                            pass  # TODO: implement this
                        case "on_enemy":
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
