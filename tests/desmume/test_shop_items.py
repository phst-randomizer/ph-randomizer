from pathlib import Path

from ndspy.rom import NintendoDSRom
import pytest

from patcher.location_types import IslandShopLocation
from patcher.location_types.island_shop import GD_MODELS

from .desmume_utils import DesmumeEmulator, get_current_rupee_count, start_first_file


@pytest.fixture(
    params=[val for val in GD_MODELS.keys() if GD_MODELS[val]],
    ids=[f'{hex(key)}-{val}' for key, val in GD_MODELS.items() if val],
)
def island_shop_test_emu(tmp_path: Path, desmume_emulator: DesmumeEmulator, request):
    rom_path = str(tmp_path / f'{tmp_path.name}.nds')

    IslandShopLocation.ROM = NintendoDSRom.fromFile(rom_path)

    locations = [
        IslandShopLocation(31, 0x217ECB4 - 0x217BCE0),  # shield in mercay shop
        IslandShopLocation(31, 0x217EC68 - 0x217BCE0),  # power gem in mercay shop
        IslandShopLocation(31, 0x217EC34 - 0x217BCE0),  # treasure item in mercay shop
    ]

    for location in locations:
        location.set_location(request.param)

    IslandShopLocation.ROM.saveToFile(rom_path)

    desmume_emulator.open_rom(rom_path)

    return desmume_emulator


def test_custom_shop_items(island_shop_test_emu: DesmumeEmulator):
    start_first_file(island_shop_test_emu)

    island_shop_test_emu.wait(100)
    original_rupee_count = get_current_rupee_count(island_shop_test_emu)
    island_shop_test_emu.touch_input((125, 50))  # Touch the shop keeper
    island_shop_test_emu.wait(200)
    island_shop_test_emu.touch_input((125, 50))  # Advance dialog
    island_shop_test_emu.wait(100)
    island_shop_test_emu.touch_input((190, 50))  # Click item to buy
    island_shop_test_emu.wait(150)
    island_shop_test_emu.touch_input((70, 175))  # Click buy button
    island_shop_test_emu.wait(200)

    # Make sure the item was able to be purchased, which should be reflected by the rupee count
    assert get_current_rupee_count(island_shop_test_emu) < original_rupee_count
