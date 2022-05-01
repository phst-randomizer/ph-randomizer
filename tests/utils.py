from desmume.emulator import SCREEN_HEIGHT, SCREEN_WIDTH

from tests.conftest import DesmumeEmulator


def start_first_file(desmume_emulator: DesmumeEmulator):
    """From game boot, goes through the title screen and starts the first save."""
    desmume_emulator.wait(500)

    # Click title screen
    desmume_emulator.touch_input(
        (
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2,
        )
    )

    desmume_emulator.wait(100)

    # Click title screen again
    desmume_emulator.touch_input(
        (
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2,
        )
    )
    desmume_emulator.wait(200)

    # Click file
    desmume_emulator.touch_input((130, 70), 0)
    desmume_emulator.wait(100)

    # Click it again
    desmume_emulator.touch_input((130, 70), 0)
    desmume_emulator.wait(100)

    # Click "Adventure"
    desmume_emulator.touch_input((130, 70), 0)
    desmume_emulator.wait(200)


def get_current_rupee_count(desmume: DesmumeEmulator):
    return int.from_bytes(desmume.emu.memory.unsigned[0x021BA4FE : 0x021BA4FE + 2], "little")


# Screen coordinates for each item when the "Items" menu is open
ITEMS_MENU_COORDINATES = {"shovel": (225, 175)}


def open_items_menu(desmume: DesmumeEmulator):
    desmume.touch_input((SCREEN_WIDTH - 5, SCREEN_HEIGHT - 5), 5)
    desmume.wait(20)


def select_item_from_items_menu(desmume: DesmumeEmulator, item: str):
    desmume.touch_input(ITEMS_MENU_COORDINATES[item], 5)
    desmume.wait(20)


def equip_item(desmume: DesmumeEmulator, item: str):
    open_items_menu(desmume)
    select_item_from_items_menu(desmume, item)


def use_equipped_item(desmume: DesmumeEmulator):
    desmume.touch_input((SCREEN_WIDTH, 0), 5)
    desmume.wait(20)
