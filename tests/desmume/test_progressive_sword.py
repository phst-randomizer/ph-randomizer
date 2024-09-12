from collections import namedtuple
from pathlib import Path

from desmume.emulator import SCREEN_WIDTH
from ndspy.rom import NintendoDSRom
import pytest

from ph_rando.common import ShufflerAuxData
from ph_rando.patcher.main import _patch_zmb_map_objects
from ph_rando.shuffler.aux_models import Chest

from .conftest import DeSmuMEWrapper
from .desmume_utils import start_first_file

SwordProgressionItem = namedtuple('SwordProgressionItem', 'memory_address bit')

SWORD_PROGRESSION_ITEMS = [
    SwordProgressionItem(0x21BA604, 0x01),  # Oshus sword
    SwordProgressionItem(0x21B5550, 0x20),  # Phantom sword (blade only)
    SwordProgressionItem(0x21BA608, 0x20),  # Phantom sword
]


@pytest.fixture
def progressive_sword_test_emu(
    rom_path: Path,
    desmume_emulator: DeSmuMEWrapper,
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
        chest.contents = 'ProgressiveSword'

    _patch_zmb_map_objects(aux_data.areas.values(), rom)

    rom.saveToFile(rom_path)

    desmume_emulator.open(str(rom_path))

    return desmume_emulator


@pytest.mark.parametrize(
    'idx',
    range(len(SWORD_PROGRESSION_ITEMS)),
    ids=['oshus sword (1)', 'phantom blade (2)', 'phantom sword (3)'],
)
def test_progressive_sword(progressive_sword_test_emu: DeSmuMEWrapper, idx: int):
    """Ensure progressive sword patch works."""
    start_first_file(progressive_sword_test_emu)

    # Set flags for earlier sword if needed
    for item in SWORD_PROGRESSION_ITEMS[:idx]:
        progressive_sword_test_emu.memory.unsigned[item.memory_address] |= item.bit

    # Make sure the current "next sword" is not in inventory
    assert (
        progressive_sword_test_emu.memory.unsigned[SWORD_PROGRESSION_ITEMS[idx].memory_address]
        & SWORD_PROGRESSION_ITEMS[idx].bit
        != SWORD_PROGRESSION_ITEMS[idx].bit
    )

    # Walk up to chest
    progressive_sword_test_emu.input.touch_set_pos(SCREEN_WIDTH // 2, 0)
    progressive_sword_test_emu.wait(320)
    progressive_sword_test_emu.input.touch_release()
    progressive_sword_test_emu.wait(10)

    # Open chest
    progressive_sword_test_emu.touch_input((SCREEN_WIDTH // 2, 100), 2)

    # Wait for "Got item" text and skip through it
    progressive_sword_test_emu.wait(200)
    progressive_sword_test_emu.touch_input((0, 0), 2)
    progressive_sword_test_emu.wait(200)
    progressive_sword_test_emu.touch_input((0, 0), 2)
    progressive_sword_test_emu.wait(100)

    # Make sure the "next sword" was obtained
    assert (
        progressive_sword_test_emu.memory.unsigned[SWORD_PROGRESSION_ITEMS[idx].memory_address]
        & SWORD_PROGRESSION_ITEMS[idx].bit
        == SWORD_PROGRESSION_ITEMS[idx].bit
    )
