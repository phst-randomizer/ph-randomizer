import os
from pathlib import Path

from desmume.emulator import SCREEN_HEIGHT
from ndspy.rom import NintendoDSRom
import pytest

from ph_rando.patcher.location_types import SalvageTreasureLocation
from ph_rando.patcher.location_types.island_shop import GD_MODELS
from tests.desmume.desmume_utils import DeSmuMEWrapper, start_first_file

from .conftest import ITEM_MEMORY_ADDRESSES, ItemMemoryAddressType


@pytest.fixture(
    params=[val for val in ITEM_MEMORY_ADDRESSES.keys()],
    ids=[f'{hex(val)}-{GD_MODELS[val]}' for val in ITEM_MEMORY_ADDRESSES.keys()],
)
def salvage_item_test_emu(tmp_path: Path, desmume_emulator: DeSmuMEWrapper, request):
    """Generate and run a rom with a custom salvage item set."""
    rom_path = str(tmp_path / f'{tmp_path.name}.nds')

    SalvageTreasureLocation.ROM = NintendoDSRom.fromFile(rom_path)

    # Set all SW sea salvage items to the current item parameter
    SalvageTreasureLocation(17, 'Map/sea/map00.bin/zmb/sea_00.zmb').set_location(request.param)
    SalvageTreasureLocation(18, 'Map/sea/map00.bin/zmb/sea_00.zmb').set_location(request.param)
    SalvageTreasureLocation(23, 'Map/sea/map00.bin/zmb/sea_00.zmb').set_location(request.param)
    SalvageTreasureLocation(24, 'Map/sea/map00.bin/zmb/sea_00.zmb').set_location(request.param)
    SalvageTreasureLocation(25, 'Map/sea/map00.bin/zmb/sea_00.zmb').set_location(request.param)
    SalvageTreasureLocation(26, 'Map/sea/map00.bin/zmb/sea_00.zmb').set_location(request.param)
    SalvageTreasureLocation(27, 'Map/sea/map00.bin/zmb/sea_00.zmb').set_location(request.param)
    SalvageTreasureLocation(28, 'Map/sea/map00.bin/zmb/sea_00.zmb').set_location(request.param)

    SalvageTreasureLocation.save_all()
    SalvageTreasureLocation.ROM.saveToFile(rom_path)

    desmume_emulator.open(rom_path)

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

    # Calculate the current "value" of the item we're expecting, so that it can be compared
    # later after we open the chest. Note that this is postponed until now to deal with the
    # salvage arm potentially picking up rupees and messing with the count.
    original_value = salvage_item_test_emu.memory.unsigned[ITEM_MEMORY_ADDRESSES[item_id][0]]
    if ITEM_MEMORY_ADDRESSES[item_id][2] == ItemMemoryAddressType.FLAG:
        assert (
            original_value & ITEM_MEMORY_ADDRESSES[item_id][1] != ITEM_MEMORY_ADDRESSES[item_id][1]
        )
    elif ITEM_MEMORY_ADDRESSES[item_id][2] == ItemMemoryAddressType.COUNTER_8_BIT:
        original_value = salvage_item_test_emu.memory.unsigned[ITEM_MEMORY_ADDRESSES[item_id][0]]
    elif ITEM_MEMORY_ADDRESSES[item_id][2] == ItemMemoryAddressType.COUNTER_16_BIT:
        original_value = int.from_bytes(
            salvage_item_test_emu.memory.unsigned[
                ITEM_MEMORY_ADDRESSES[item_id][0] : ITEM_MEMORY_ADDRESSES[item_id][0] + 2
            ],
            'little',
        )
    else:
        raise NotImplementedError(f'{ITEM_MEMORY_ADDRESSES[item_id][2]} not a valid item type.')

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

    # Make sure correct item was retrieved.
    if ITEM_MEMORY_ADDRESSES[item_id][2] == ItemMemoryAddressType.FLAG:
        assert (
            salvage_item_test_emu.memory.unsigned[ITEM_MEMORY_ADDRESSES[item_id][0]]
            & ITEM_MEMORY_ADDRESSES[item_id][1]
            == ITEM_MEMORY_ADDRESSES[item_id][1]
        )
    elif ITEM_MEMORY_ADDRESSES[item_id][2] == ItemMemoryAddressType.COUNTER_8_BIT:
        assert (
            salvage_item_test_emu.memory.unsigned[ITEM_MEMORY_ADDRESSES[item_id][0]]
            - ITEM_MEMORY_ADDRESSES[item_id][1]
            == original_value
        )
    elif ITEM_MEMORY_ADDRESSES[item_id][2] == ItemMemoryAddressType.COUNTER_16_BIT:
        assert (
            int.from_bytes(
                salvage_item_test_emu.memory.unsigned[
                    ITEM_MEMORY_ADDRESSES[item_id][0] : ITEM_MEMORY_ADDRESSES[item_id][0] + 2
                ],
                'little',
            )
            - ITEM_MEMORY_ADDRESSES[item_id][1]
            == original_value
        )
    else:
        raise NotImplementedError(f'{ITEM_MEMORY_ADDRESSES[item_id][2]} not a valid item type.')
