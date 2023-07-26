import os
from pathlib import Path

from desmume.emulator import SCREEN_WIDTH
from ndspy.rom import NintendoDSRom
import pytest

from ph_rando.common import ShufflerAuxData
from ph_rando.patcher._items import ITEMS_REVERSED
from ph_rando.patcher.main import GD_MODELS, _patch_zmb_map_objects
from ph_rando.shuffler.aux_models import Chest, Item

from .conftest import ITEM_MEMORY_ADDRESSES, DeSmuMEWrapper
from .desmume_utils import assert_item_is_picked_up, start_first_file


@pytest.fixture(
    params=[val for val in ITEM_MEMORY_ADDRESSES.keys()],
    ids=[f'{hex(val)}-{GD_MODELS[val]}' for val in ITEM_MEMORY_ADDRESSES.keys()],
)
def chest_test_emu(
    rom_path: Path,
    desmume_emulator: DeSmuMEWrapper,
    request,
    aux_data: ShufflerAuxData,
):
    """Generate and run a rom with a custom chest item set."""
    rom = NintendoDSRom.fromFile(rom_path)
    chests = [
        chest
        for area in aux_data.areas.values()
        for room in area.rooms
        for chest in room.chests
        if type(chest) == Chest
        and chest.zmb_file_path == 'Map/isle_main/map19.bin/zmb/isle_main_19.zmb'
    ]
    for chest in chests:
        chest.contents = Item(name=ITEMS_REVERSED[request.param], states=set())

    _patch_zmb_map_objects(aux_data.areas.values(), rom)

    rom.saveToFile(rom_path)

    desmume_emulator.open(str(rom_path))

    return desmume_emulator


def test_custom_chest_items(chest_test_emu: DeSmuMEWrapper):
    item_id = int(os.environ['PYTEST_CURRENT_TEST'].split('[')[1].split('-')[0], 16)

    start_first_file(chest_test_emu)

    with assert_item_is_picked_up(item_id, chest_test_emu):
        # Walk up to chest
        chest_test_emu.input.touch_set_pos(SCREEN_WIDTH // 2, 0)
        chest_test_emu.wait(320)
        chest_test_emu.input.touch_release()
        chest_test_emu.wait(10)

        # Open chest
        chest_test_emu.touch_input((SCREEN_WIDTH // 2, 100), 2)

        # Wait for "Got item" text and skip through it
        chest_test_emu.wait(200)
        chest_test_emu.touch_input((0, 0), 2)
        chest_test_emu.wait(200)
        chest_test_emu.touch_input((0, 0), 2)
        chest_test_emu.wait(100)

        # Gems require one more text box to be clicked through.
        # Put this behind an if statement so we don't have to
        # wait extra time for every other item.
        if item_id in range(0x2D, 0x30):
            chest_test_emu.touch_input((0, 0), 2)
            chest_test_emu.wait(50)
