from desmume.controls import Keys
from desmume.emulator import SCREEN_WIDTH

from tests.conftest import DesmumeEmulator
from tests.utils import get_current_rupee_count, start_first_file


def test_boot_new_game(base_rom_emu: DesmumeEmulator):
    """Test bootup from title screen, name entry, and intro CG."""
    start_first_file(base_rom_emu)

    # Press start + touch "Skip" button to skip intro cs
    base_rom_emu.button_input(Keys.KEY_START)
    base_rom_emu.wait(50)
    base_rom_emu.touch_input((SCREEN_WIDTH, 0))
    base_rom_emu.wait(250)

    # Press start + touch "Skip" button to skip Tetra cs
    base_rom_emu.button_input(Keys.KEY_START)
    base_rom_emu.wait(100)
    base_rom_emu.touch_input((SCREEN_WIDTH, 0))
    base_rom_emu.wait(500)

    # Press start + touch "Skip" button to skip ciela/beach cs
    base_rom_emu.button_input(Keys.KEY_START)
    base_rom_emu.wait(15)
    base_rom_emu.touch_input((SCREEN_WIDTH, 0))
    base_rom_emu.wait(200)

    # ensure mercay bridge fixed flag is set
    assert base_rom_emu.emu.memory.unsigned[0x021B553E] & 0x2 == 0x2


def test_custom_shop_items(island_shop_test_emu: DesmumeEmulator):
    start_first_file(island_shop_test_emu)

    island_shop_test_emu.wait(100)
    original_rupee_count = get_current_rupee_count(island_shop_test_emu)

    island_shop_test_emu.touch_input((125, 50))  # Touch the shop keeper
    island_shop_test_emu.wait(200)
    island_shop_test_emu.touch_input((125, 50)) # Advance dialog
    island_shop_test_emu.wait(100)
    island_shop_test_emu.touch_input((190, 50)) # Click item to buy
    island_shop_test_emu.wait(150)
    island_shop_test_emu.touch_input((70, 175)) # Click buy button
    island_shop_test_emu.wait(200)

    # Make sure the item was able to be purchased, which should be reflected by the rupee count
    assert get_current_rupee_count(island_shop_test_emu) < original_rupee_count
