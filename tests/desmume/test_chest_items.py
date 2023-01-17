import os
from pathlib import Path

from desmume.emulator import SCREEN_WIDTH
from ndspy.rom import NintendoDSRom
import pytest

from patcher.location_types import MapObjectLocation
from patcher.location_types.island_shop import GD_MODELS

from .conftest import ITEM_MEMORY_ADDRESSES, DeSmuMEWrapper, ItemMemoryAddressType
from .desmume_utils import start_first_file


@pytest.fixture(
    params=[val for val in ITEM_MEMORY_ADDRESSES.keys()],
    ids=[f'{hex(val)}-{GD_MODELS[val]}' for val in ITEM_MEMORY_ADDRESSES.keys()],
)
def chest_test_emu(tmp_path: Path, desmume_emulator: DeSmuMEWrapper, request):
    """Generate and run a rom with a custom chest item set."""
    rom_path = str(tmp_path / f'{tmp_path.name}.nds')

    MapObjectLocation.ROM = NintendoDSRom.fromFile(rom_path)

    MapObjectLocation(1, 'Map/isle_main/map19.bin/zmb/isle_main_19.zmb').set_location(request.param)
    MapObjectLocation.save_all()

    MapObjectLocation.ROM.saveToFile(rom_path)

    desmume_emulator.open(rom_path)

    return desmume_emulator


def test_custom_chest_items(chest_test_emu: DeSmuMEWrapper):
    item_id = int(os.environ['PYTEST_CURRENT_TEST'].split('[')[1].split('-')[0], 16)

    start_first_file(chest_test_emu)

    original_value = chest_test_emu.memory.unsigned[ITEM_MEMORY_ADDRESSES[item_id][0]]
    if ITEM_MEMORY_ADDRESSES[item_id][2] == ItemMemoryAddressType.FLAG:
        assert (
            original_value & ITEM_MEMORY_ADDRESSES[item_id][1] != ITEM_MEMORY_ADDRESSES[item_id][1]
        )
    elif ITEM_MEMORY_ADDRESSES[item_id][2] == ItemMemoryAddressType.COUNTER_8_BIT:
        original_value = chest_test_emu.memory.unsigned[ITEM_MEMORY_ADDRESSES[item_id][0]]
    elif ITEM_MEMORY_ADDRESSES[item_id][2] == ItemMemoryAddressType.COUNTER_16_BIT:
        original_value = int.from_bytes(
            chest_test_emu.memory.unsigned[
                ITEM_MEMORY_ADDRESSES[item_id][0] : ITEM_MEMORY_ADDRESSES[item_id][0] + 2
            ],
            'little',
        )
    else:
        raise NotImplementedError(f'{ITEM_MEMORY_ADDRESSES[item_id][2]} not a valid item type.')

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

    # Make sure correct item was retrieved.
    if ITEM_MEMORY_ADDRESSES[item_id][2] == ItemMemoryAddressType.FLAG:
        assert (
            chest_test_emu.memory.unsigned[ITEM_MEMORY_ADDRESSES[item_id][0]]
            & ITEM_MEMORY_ADDRESSES[item_id][1]
            == ITEM_MEMORY_ADDRESSES[item_id][1]
        )
    elif ITEM_MEMORY_ADDRESSES[item_id][2] == ItemMemoryAddressType.COUNTER_8_BIT:
        assert (
            chest_test_emu.memory.unsigned[ITEM_MEMORY_ADDRESSES[item_id][0]]
            - ITEM_MEMORY_ADDRESSES[item_id][1]
            == original_value
        )
    elif ITEM_MEMORY_ADDRESSES[item_id][2] == ItemMemoryAddressType.COUNTER_16_BIT:
        assert (
            int.from_bytes(
                chest_test_emu.memory.unsigned[
                    ITEM_MEMORY_ADDRESSES[item_id][0] : ITEM_MEMORY_ADDRESSES[item_id][0] + 2
                ],
                'little',
            )
            - ITEM_MEMORY_ADDRESSES[item_id][1]
            == original_value
        )
    else:
        raise NotImplementedError(f'{ITEM_MEMORY_ADDRESSES[item_id][2]} not a valid item type.')
