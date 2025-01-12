from pathlib import Path

from desmume.emulator import SCREEN_WIDTH
from ndspy.rom import NintendoDSRom
import pytest

from ph_rando.common import ShufflerAuxData
from ph_rando.patcher._items import ITEMS_REVERSED
from ph_rando.patcher._util import GD_MODELS, _patch_zmb_map_objects
from ph_rando.shuffler.aux_models import Chest, Item

from .conftest import GOT_ITEM_TEXT, ITEM_MEMORY_OFFSETS
from .emulator_utils import (
    AbstractEmulatorWrapper,
    assert_item_is_picked_up,
    assert_text_displayed,
    start_first_file,
)
from .melonds import MelonDSWrapper


@pytest.fixture
def chest_test_emu(
    rom_path: Path,
    emulator: AbstractEmulatorWrapper,
    request,
    aux_data: ShufflerAuxData,
):
    """Generate and run a rom with a custom chest item set."""
    rom = NintendoDSRom.fromFile(rom_path)
    chests = [
        chest
        for area in aux_data.areas
        for room in area.rooms
        for chest in room.chests
        if type(chest) is Chest
        and chest.zmb_file_path == 'Map/isle_main/map19.bin/zmb/isle_main_19.zmb'
    ]
    for chest in chests:
        chest.contents = Item(name=ITEMS_REVERSED[request.param], states=set())

    _patch_zmb_map_objects(aux_data.areas, rom)

    rom.saveToFile(rom_path)

    emulator.open(str(rom_path))

    return emulator


@pytest.mark.parametrize(
    'chest_test_emu',
    [val for val in ITEM_MEMORY_OFFSETS.keys()],
    ids=[f'{hex(val)}-{GD_MODELS[val]}' for val in ITEM_MEMORY_OFFSETS.keys()],
    indirect=['chest_test_emu'],
)
def test_custom_chest_items(
    chest_test_emu: AbstractEmulatorWrapper, request: pytest.FixtureRequest
):
    item_id: int = request.node.callspec.params['chest_test_emu']

    start_first_file(chest_test_emu)

    with assert_item_is_picked_up(item_id, chest_test_emu):
        # Walk up to chest
        chest_test_emu.touch_set(SCREEN_WIDTH // 2, 0)
        chest_test_emu.wait(320)
        chest_test_emu.touch_release()
        chest_test_emu.wait(10)

        # Open chest
        chest_test_emu.touch_set_and_release((SCREEN_WIDTH // 2, 100), 2)

        # Wait for "Got item" text
        chest_test_emu.wait(800)

        # Check if the "got item" text is correct
        if item_id in GOT_ITEM_TEXT:
            assert_text_displayed(chest_test_emu, GOT_ITEM_TEXT[item_id])

        chest_test_emu.touch_set_and_release((0, 0), 2)
        chest_test_emu.wait(200)
        chest_test_emu.touch_set_and_release((0, 0), 2)
        chest_test_emu.wait(100)

        # Gems require one more text box to be clicked through.
        # Put this behind an if statement so we don't have to
        # wait extra time for every other item.
        if item_id in range(0x2D, 0x30) or item_id == 0x13:
            chest_test_emu.touch_set_and_release((0, 0), 2)
            chest_test_emu.wait(50)

        if isinstance(chest_test_emu, MelonDSWrapper) and item_id in range(0x72, 0x75):
            # TODO: these items cause a crash when the chest is opened, but only in MelonDS,
            # and only in CI (it works fine in my local environment).
            pytest.skip(f'Item {hex(item_id)} crashes MelonDS, temporarily skipping test.')
