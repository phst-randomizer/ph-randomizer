import os

from desmume.controls import Keys
from desmume.emulator import SCREEN_HEIGHT, SCREEN_WIDTH

from tests.conftest import ITEM_MEMORY_ADDRESSES, DesmumeEmulator, ItemMemoryAddressType
from tests.utils import equip_item, get_current_rupee_count, start_first_file, use_equipped_item


def test_boot_new_game(base_rom_emu: DesmumeEmulator):
    """Test bootup from title screen, name entry, and intro CG."""
    for i in range(2):
        base_rom_emu.wait(500)
        base_rom_emu.touch_input(
            (
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2,
            )
        )
        base_rom_emu.wait(100)
        base_rom_emu.touch_input(
            (
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2,
            )
        )
        base_rom_emu.wait(200)
        base_rom_emu.touch_input(
            (
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2,
            )
        )

        # Wait for the game to initialize the save data and repeat this loop once more
        if i == 0:
            # NOTE: The next two lines may appear to be useless, but they
            # handle waiting and clicking the "Creating save data" text
            # that appears when there is no save data on the card.
            # Do not remove them.
            base_rom_emu.wait(400)
            base_rom_emu.emu.reset()

    # Touch file
    base_rom_emu.touch_input((130, 70), 0)
    base_rom_emu.wait(500)

    # Confirm name
    base_rom_emu.touch_input((190, 180), 0)
    base_rom_emu.wait(100)

    # Click yes
    base_rom_emu.touch_input((210, 110), 0)
    base_rom_emu.wait(100)

    # Click right hand
    base_rom_emu.touch_input((210, 110), 0)
    base_rom_emu.wait(100)

    # Click yes
    base_rom_emu.touch_input((210, 110), 0)
    base_rom_emu.wait(100)

    # Click newly created file
    base_rom_emu.touch_input((130, 70), 0)
    base_rom_emu.wait(100)

    # Click it again
    base_rom_emu.touch_input((130, 70), 0)
    base_rom_emu.wait(100)

    # Click "Adventure"
    base_rom_emu.touch_input((130, 70), 0)
    base_rom_emu.wait(500)

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
    island_shop_test_emu.touch_input((125, 50))  # Advance dialog
    island_shop_test_emu.wait(100)
    island_shop_test_emu.touch_input((190, 50))  # Click item to buy
    island_shop_test_emu.wait(150)
    island_shop_test_emu.touch_input((70, 175))  # Click buy button
    island_shop_test_emu.wait(200)

    # Make sure the item was able to be purchased, which should be reflected by the rupee count
    assert get_current_rupee_count(island_shop_test_emu) < original_rupee_count


def test_custom_dig_spot_items(dig_spot_test_emu: DesmumeEmulator):
    item_id = int(os.environ["PYTEST_CURRENT_TEST"].split("[")[1].split("-")[0], 16)

    start_first_file(dig_spot_test_emu)

    original_value = dig_spot_test_emu.emu.memory.unsigned[ITEM_MEMORY_ADDRESSES[item_id][0]]

    match ITEM_MEMORY_ADDRESSES[item_id][2]:
        case ItemMemoryAddressType.FLAG:
            assert (
                original_value & ITEM_MEMORY_ADDRESSES[item_id][1]
                != ITEM_MEMORY_ADDRESSES[item_id][1]
            )
        case ItemMemoryAddressType.COUNTER_8_BIT:
            original_value = dig_spot_test_emu.emu.memory.unsigned[
                ITEM_MEMORY_ADDRESSES[item_id][0]
            ]
        case ItemMemoryAddressType.COUNTER_16_BIT:
            original_value = int.from_bytes(
                dig_spot_test_emu.emu.memory.unsigned[
                    ITEM_MEMORY_ADDRESSES[item_id][0] : ITEM_MEMORY_ADDRESSES[item_id][0] + 2
                ],
                "little",
            )

    # Walk down from Oshus house
    dig_spot_test_emu.touch_input((SCREEN_WIDTH // 2, SCREEN_HEIGHT), 15)

    # Turn right and walk towards sword cave/tree with shovel spot
    dig_spot_test_emu.touch_input((SCREEN_WIDTH, SCREEN_HEIGHT // 2), 100)

    dig_spot_test_emu.wait(30)

    # Take out shovel
    equip_item(dig_spot_test_emu, "shovel")
    use_equipped_item(dig_spot_test_emu)

    # Tap ground where item is buried to dig it up
    dig_spot_test_emu.touch_input((206, 74), 2)

    # Wait for Link to run over and use the shovel
    dig_spot_test_emu.wait(100)

    # Grab the item that appeared
    dig_spot_test_emu.touch_input((int(SCREEN_WIDTH * (2 / 3)), 0), 40)

    dig_spot_test_emu.wait(200)
    dig_spot_test_emu.touch_input((0, 0), 2)
    dig_spot_test_emu.wait(200)
    dig_spot_test_emu.touch_input((0, 0), 2)

    dig_spot_test_emu.wait(100)

    match ITEM_MEMORY_ADDRESSES[item_id][2]:
        case ItemMemoryAddressType.FLAG:
            assert (
                dig_spot_test_emu.emu.memory.unsigned[ITEM_MEMORY_ADDRESSES[item_id][0]]
                & ITEM_MEMORY_ADDRESSES[item_id][1]
                == ITEM_MEMORY_ADDRESSES[item_id][1]
            )
        case ItemMemoryAddressType.COUNTER_8_BIT:
            assert (
                dig_spot_test_emu.emu.memory.unsigned[ITEM_MEMORY_ADDRESSES[item_id][0]]
                - ITEM_MEMORY_ADDRESSES[item_id][1]
                == original_value
            )
        case ItemMemoryAddressType.COUNTER_16_BIT:
            assert (
                int.from_bytes(
                    dig_spot_test_emu.emu.memory.unsigned[
                        ITEM_MEMORY_ADDRESSES[item_id][0] : ITEM_MEMORY_ADDRESSES[item_id][0] + 2
                    ],
                    "little",
                )
                - ITEM_MEMORY_ADDRESSES[item_id][1]
                == original_value
            )
