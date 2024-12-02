from pathlib import Path

from desmume.emulator import SCREEN_HEIGHT
from ndspy.rom import NintendoDSRom
import pytest

from ph_rando.common import ShufflerAuxData
from ph_rando.patcher._items import ITEMS_REVERSED
from ph_rando.patcher._util import GD_MODELS, _patch_zmb_actors
from ph_rando.shuffler.aux_models import Item, SalvageTreasure
from tests.desmume.desmume_utils import DeSmuMEWrapper, assert_item_is_picked_up, start_first_file

from .conftest import ITEM_MEMORY_OFFSETS


@pytest.fixture
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
        if type(chest) is SalvageTreasure
        and chest.zmb_file_path == 'Map/sea/map00.bin/zmb/sea_00.zmb'
    ]
    for chest in chests:
        chest.contents = Item(name=ITEMS_REVERSED[request.param], states=set())

    _patch_zmb_actors(aux_data.areas, rom)

    rom.saveToFile(rom_path)

    desmume_emulator.open(str(rom_path))

    return desmume_emulator


@pytest.mark.parametrize(
    'salvage_item_test_emu',
    [val for val in ITEM_MEMORY_OFFSETS.keys()],
    ids=[f'{hex(val)}-{GD_MODELS[val]}' for val in ITEM_MEMORY_OFFSETS.keys()],
    indirect=['salvage_item_test_emu'],
)
def test_custom_salvage_items(
    salvage_item_test_emu: DeSmuMEWrapper, request: pytest.FixtureRequest
):
    item_id: int = request.node.callspec.params['salvage_item_test_emu']

    start_first_file(salvage_item_test_emu)

    # Drag navigation pen to "X" on map
    salvage_item_test_emu.touch_set(207, 90)
    salvage_item_test_emu.wait(2)
    salvage_item_test_emu.touch_set(220, 90)
    salvage_item_test_emu.wait(2)
    salvage_item_test_emu.touch_release()
    salvage_item_test_emu.wait(2)

    # Click "Go!" button
    salvage_item_test_emu.touch_set(90, 130)
    salvage_item_test_emu.wait(2)
    salvage_item_test_emu.touch_release()

    # Wait for the boat to reach the "X"
    salvage_item_test_emu.wait(500)

    # Take out salvage arm
    salvage_item_test_emu.touch_set(0, SCREEN_HEIGHT)
    salvage_item_test_emu.wait(10)
    salvage_item_test_emu.touch_release()
    salvage_item_test_emu.wait(10)
    salvage_item_test_emu.touch_set(195, 175)
    salvage_item_test_emu.wait(10)
    salvage_item_test_emu.touch_release()

    # Wait for salvage arm to come out
    salvage_item_test_emu.wait(200)

    # Set salvage arm health to 255 so we don't have to worry about running out of health
    salvage_item_test_emu.write_memory(salvage_item_test_emu.event_flag_base_addr + 0x401A4, 0xFF)

    # Pull salvage icon down until we get to the chest
    salvage_item_test_emu.touch_set(125, 170)
    salvage_item_test_emu.wait(10)
    salvage_item_test_emu.touch_set(125, 190)
    salvage_item_test_emu.wait(2500)

    # Release the touch screen, and then pull the salvage icon up to bring the treasure up.
    salvage_item_test_emu.touch_release()
    salvage_item_test_emu.wait(10)
    salvage_item_test_emu.touch_set(125, 170)
    salvage_item_test_emu.wait(10)
    salvage_item_test_emu.touch_set(125, 130)

    # Wait until the chest *just* about to exit the water
    salvage_item_test_emu.wait(2300)

    with assert_item_is_picked_up(item_id, salvage_item_test_emu):
        # Wait for the chest to be pulled out of the water and opened by Link
        salvage_item_test_emu.wait(1050)

        salvage_item_test_emu.touch_release()

        # Click through the "Got new item" text.
        salvage_item_test_emu.wait(200)
        salvage_item_test_emu.touch_set(0, 0)
        salvage_item_test_emu.wait(2)
        salvage_item_test_emu.touch_release()
        salvage_item_test_emu.wait(200)
        salvage_item_test_emu.touch_set(0, 0)
        salvage_item_test_emu.wait(2)
        salvage_item_test_emu.touch_release()
        salvage_item_test_emu.wait(200)
