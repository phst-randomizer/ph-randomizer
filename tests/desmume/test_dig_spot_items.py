import os

from conftest import ITEM_MEMORY_ADDRESSES, DesmumeEmulator, ItemMemoryAddressType
from desmume.emulator import SCREEN_HEIGHT, SCREEN_WIDTH

from .desmume_utils import equip_item, start_first_file, use_equipped_item


def test_custom_dig_spot_items(dig_spot_test_emu: DesmumeEmulator):
    item_id = int(os.environ['PYTEST_CURRENT_TEST'].split('[')[1].split('-')[0], 16)

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
                'little',
            )

    # Walk down from Oshus house
    dig_spot_test_emu.touch_input((SCREEN_WIDTH // 2, SCREEN_HEIGHT), 15)

    # Turn right and walk towards sword cave/tree with shovel spot
    dig_spot_test_emu.touch_input((SCREEN_WIDTH, SCREEN_HEIGHT // 2), 100)

    dig_spot_test_emu.wait(30)

    # Take out shovel
    equip_item(dig_spot_test_emu, 'shovel')
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
                    'little',
                )
                - ITEM_MEMORY_ADDRESSES[item_id][1]
                == original_value
            )
