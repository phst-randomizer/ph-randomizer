from .desmume_utils import DesmumeEmulator, get_current_rupee_count, start_first_file


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
