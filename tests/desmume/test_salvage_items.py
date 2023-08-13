import os
from pathlib import Path

from desmume.emulator import SCREEN_HEIGHT
from ndspy.rom import NintendoDSRom
import pytest

from ph_rando.common import ShufflerAuxData
from ph_rando.patcher._items import ITEMS_REVERSED
from ph_rando.patcher._util import GD_MODELS
from ph_rando.patcher.main import _patch_zmb_actors
from ph_rando.shuffler.aux_models import Item, SalvageTreasure
from tests.desmume.desmume_utils import DeSmuMEWrapper, assert_item_is_picked_up, start_first_file

from .conftest import ITEM_MEMORY_ADDRESSES


@pytest.fixture(
    params=[val for val in ITEM_MEMORY_ADDRESSES.keys()],
    ids=[f'{hex(val)}-{GD_MODELS[val]}' for val in ITEM_MEMORY_ADDRESSES.keys()],
)
def salvage_item_test_emu(
    rom_path: Path,
    desmume_emulator: DeSmuMEWrapper,
    request,
    aux_data: ShufflerAuxData,
):
    """Generate and run a rom with a custom salvage item set."""
    rom = NintendoDSRom.fromFile(rom_path)
    chests = [
        chest
        for area in aux_data.areas
        for room in area.rooms
        for chest in room.chests
        if type(chest) == SalvageTreasure
        and chest.zmb_file_path == 'Map/sea/map00.bin/zmb/sea_00.zmb'
    ]
    for chest in chests:
        chest.contents = Item(name=ITEMS_REVERSED[request.param], states=set())

    _patch_zmb_actors(aux_data.areas, rom)

    rom.saveToFile(rom_path)

    desmume_emulator.open(str(rom_path))

    return desmume_emulator


def test_custom_salvage_items(salvage_item_test_emu: DeSmuMEWrapper):
    item_id = int(os.environ['PYTEST_CURRENT_TEST'].split('[')[1].split('-')[0], 16)

    start_first_file(salvage_item_test_emu)

    # Drag navigation pen to "X" on map
    salvage_item_test_emu.input.touch_set_pos(207, 90)
    salvage_item_test_emu.wait(2)
    salvage_item_test_emu.input.touch_set_pos(220, 90)
    salvage_item_test_emu.wait(2)
    salvage_item_test_emu.input.touch_release()
    salvage_item_test_emu.wait(2)

    # Click "Go!" button
    salvage_item_test_emu.input.touch_set_pos(90, 130)
    salvage_item_test_emu.wait(2)
    salvage_item_test_emu.input.touch_release()

    # Wait for the boat to reach the "X"
    salvage_item_test_emu.wait(500)

    # Take out salvage arm
    salvage_item_test_emu.input.touch_set_pos(0, SCREEN_HEIGHT)
    salvage_item_test_emu.wait(10)
    salvage_item_test_emu.input.touch_release()
    salvage_item_test_emu.wait(10)
    salvage_item_test_emu.input.touch_set_pos(195, 175)
    salvage_item_test_emu.wait(10)
    salvage_item_test_emu.input.touch_release()

    # Wait for salvage arm to come out
    salvage_item_test_emu.wait(200)

    # Set salvage arm health to 255 so we don't have to worry about running out of health
    salvage_item_test_emu.memory.unsigned[0x021F56E0] = 0xFF

    # Pull salvage icon down until we get to the chest
    salvage_item_test_emu.input.touch_set_pos(125, 170)
    salvage_item_test_emu.wait(10)
    salvage_item_test_emu.input.touch_set_pos(125, 190)
    salvage_item_test_emu.wait(2500)

    # Release the touch screen, and then pull the salvage icon up to bring the treasure up.
    salvage_item_test_emu.input.touch_release()
    salvage_item_test_emu.wait(10)
    salvage_item_test_emu.input.touch_set_pos(125, 170)
    salvage_item_test_emu.wait(10)
    salvage_item_test_emu.input.touch_set_pos(125, 130)

    # Wait until the chest *just* about to exit the water
    salvage_item_test_emu.wait(2300)

    with assert_item_is_picked_up(item_id, salvage_item_test_emu):
        # Wait for the chest to be pulled out of the water and opened by Link
        salvage_item_test_emu.wait(1050)

        salvage_item_test_emu.input.touch_release()

        # Click through the "Got new item" text.
        salvage_item_test_emu.wait(200)
        salvage_item_test_emu.input.touch_set_pos(0, 0)
        salvage_item_test_emu.wait(2)
        salvage_item_test_emu.input.touch_release()
        salvage_item_test_emu.wait(200)
        salvage_item_test_emu.input.touch_set_pos(0, 0)
        salvage_item_test_emu.wait(2)
        salvage_item_test_emu.input.touch_release()
        salvage_item_test_emu.wait(200)
