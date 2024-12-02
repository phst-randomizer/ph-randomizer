from pathlib import Path

from ndspy.rom import NintendoDSRom
import pytest

from ph_rando.common import ShufflerAuxData
from ph_rando.patcher._items import ITEMS_REVERSED
from ph_rando.patcher._util import GD_MODELS, _patch_shop_items
from ph_rando.shuffler.aux_models import Item, Shop

from .desmume_utils import DeSmuMEWrapper, get_current_rupee_count, start_first_file


@pytest.fixture
def island_shop_test_emu(
    rom_path: Path,
    desmume_emulator: DeSmuMEWrapper,
    request,
    aux_data: ShufflerAuxData,
):
    rom = NintendoDSRom.fromFile(rom_path)
    chests = [
        chest
        for area in aux_data.areas
        for room in area.rooms
        for chest in room.chests
        if type(chest) is Shop
    ]
    for chest in chests:
        chest.contents = Item(name=ITEMS_REVERSED[request.param], states=set())

    _patch_shop_items(aux_data.areas, rom)

    rom.saveToFile(rom_path)

    desmume_emulator.open(str(rom_path))

    return desmume_emulator


@pytest.mark.parametrize(
    'island_shop_test_emu',
    [val for val in GD_MODELS.keys() if GD_MODELS[val] and val in ITEMS_REVERSED],
    ids=[f'{hex(key)}-{val}' for key, val in GD_MODELS.items() if val and val in ITEMS_REVERSED],
    indirect=['island_shop_test_emu'],
)
def test_custom_shop_items(island_shop_test_emu: DeSmuMEWrapper):
    start_first_file(island_shop_test_emu)

    island_shop_test_emu.wait(100)
    original_rupee_count = get_current_rupee_count(island_shop_test_emu)
    island_shop_test_emu.touch_set_and_release((125, 50))  # Touch the shop keeper
    island_shop_test_emu.wait(200)
    island_shop_test_emu.touch_set_and_release((125, 50))  # Advance dialog
    island_shop_test_emu.wait(100)
    island_shop_test_emu.touch_set_and_release((190, 50))  # Click item to buy
    island_shop_test_emu.wait(150)
    island_shop_test_emu.touch_set_and_release((70, 175))  # Click buy button
    island_shop_test_emu.wait(200)

    # Make sure the item was able to be purchased, which should be reflected by the rupee count
    assert get_current_rupee_count(island_shop_test_emu) < original_rupee_count
