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
