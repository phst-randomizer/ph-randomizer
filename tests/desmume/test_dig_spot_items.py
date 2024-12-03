from pathlib import Path

from desmume.emulator import SCREEN_HEIGHT, SCREEN_WIDTH
from ndspy.rom import NintendoDSRom
import pytest

from ph_rando.common import ShufflerAuxData
from ph_rando.patcher._items import ITEMS_REVERSED
from ph_rando.patcher._util import GD_MODELS, _patch_zmb_actors
from ph_rando.shuffler.aux_models import DigSpot, Item

from .conftest import ITEM_MEMORY_OFFSETS
from .emulator_utils import (
    AbstractEmulatorWrapper,
    assert_item_is_picked_up,
    equip_item,
    start_first_file,
    use_equipped_item,
)
from .melonds import MelonDSWrapper


@pytest.fixture
def dig_spot_test_emu(
    rom_path: Path,
    desmume_emulator: AbstractEmulatorWrapper,
    request,
    aux_data: ShufflerAuxData,
):
    """Generate and run a rom with a custom dig/shovel spot item set."""
    if isinstance(desmume_emulator, MelonDSWrapper):
        pytest.skip('This test is broken on melonDS. TODO: Fix it and remove this skip')
    rom = NintendoDSRom.fromFile(rom_path)
    chests = [
        chest
        for area in aux_data.areas
        for room in area.rooms
        for chest in room.chests
        if type(chest) is DigSpot
        and chest.zmb_file_path == 'Map/isle_main/map00.bin/zmb/isle_main_00.zmb'
    ]
    for chest in chests:
        chest.contents = Item(name=ITEMS_REVERSED[request.param], states=set())

    _patch_zmb_actors(aux_data.areas, rom)

    rom.saveToFile(rom_path)

    desmume_emulator.open(str(rom_path))

    return desmume_emulator


@pytest.mark.parametrize(
    'dig_spot_test_emu',
    [val for val in ITEM_MEMORY_OFFSETS.keys()],
    ids=[f'{hex(val)}-{GD_MODELS[val]}' for val in ITEM_MEMORY_OFFSETS.keys()],
    indirect=['dig_spot_test_emu'],
)
def test_custom_dig_spot_items(
    dig_spot_test_emu: AbstractEmulatorWrapper, request: pytest.FixtureRequest
):
    item_id: int = request.node.callspec.params['dig_spot_test_emu']

    start_first_file(dig_spot_test_emu)

    with assert_item_is_picked_up(item_id, dig_spot_test_emu):
        # Walk down from Oshus house
        dig_spot_test_emu.touch_set_and_release((SCREEN_WIDTH // 2, SCREEN_HEIGHT), 15)

        # Turn right and walk towards sword cave/tree with shovel spot
        dig_spot_test_emu.touch_set_and_release((SCREEN_WIDTH, SCREEN_HEIGHT // 2), 100)

        dig_spot_test_emu.wait(30)

        # Take out shovel
        equip_item(dig_spot_test_emu, 'shovel')
        use_equipped_item(dig_spot_test_emu)

        # Tap ground where item is buried to dig it up
        dig_spot_test_emu.touch_set_and_release((206, 74), 2)

        # Wait for Link to run over and use the shovel
        dig_spot_test_emu.wait(100)

        # Grab the item that appeared
        dig_spot_test_emu.touch_set_and_release((int(SCREEN_WIDTH * (2 / 3)), 0), 40)

        dig_spot_test_emu.wait(200)
        dig_spot_test_emu.touch_set_and_release((0, 0), 2)
        dig_spot_test_emu.wait(200)
        dig_spot_test_emu.touch_set_and_release((0, 0), 2)

        dig_spot_test_emu.wait(200)

        dig_spot_test_emu.touch_set_and_release((0, 0), 2)
        dig_spot_test_emu.wait(200)
        dig_spot_test_emu.touch_set_and_release((0, 0), 2)
        dig_spot_test_emu.wait(200)
        dig_spot_test_emu.touch_set_and_release((0, 0), 2)
        dig_spot_test_emu.wait(200)
