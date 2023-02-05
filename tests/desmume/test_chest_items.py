import os
from pathlib import Path

from desmume.emulator import SCREEN_WIDTH
from ndspy.rom import NintendoDSRom
import pytest

from ph_rando.patcher.location_types import MapObjectLocation
from ph_rando.patcher.location_types.island_shop import GD_MODELS

from .conftest import ITEM_MEMORY_ADDRESSES, DeSmuMEWrapper
from .desmume_utils import assert_item_is_picked_up, start_first_file


@pytest.fixture(
    params=[val for val in ITEM_MEMORY_ADDRESSES.keys()],
    ids=[f'{hex(val)}-{GD_MODELS[val]}' for val in ITEM_MEMORY_ADDRESSES.keys()],
)
def chest_test_emu(rom_path: Path, desmume_emulator: DeSmuMEWrapper, request):
    """Generate and run a rom with a custom chest item set."""
    MapObjectLocation.ROM = NintendoDSRom.fromFile(rom_path)

    MapObjectLocation(1, 'Map/isle_main/map19.bin/zmb/isle_main_19.zmb').set_location(request.param)
    MapObjectLocation.save_all()

    MapObjectLocation.ROM.saveToFile(rom_path)

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
