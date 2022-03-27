from desmume.emulator import SCREEN_HEIGHT, SCREEN_WIDTH

from tests.conftest import DesmumeEmulator


def start_first_file(desmume_emulator: DesmumeEmulator):
    """
    From game boot, goes through the title screen and starts the first save.

    Creates a new game if one isn't present.
    """
    for i in range(2):
        desmume_emulator.wait(500)
        desmume_emulator.touch_input(
            (
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2,
            )
        )
        desmume_emulator.wait(100)
        desmume_emulator.touch_input(
            (
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2,
            )
        )
        desmume_emulator.wait(200)
        desmume_emulator.touch_input(
            (
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2,
            )
        )

        if i == 0:
            # NOTE: The next two lines may appear to be useless, but they
            # handle waiting and clicking the "Creating save data" text
            # that appears when there is no save data on the card.
            # Do not remove them.
            desmume_emulator.wait(400)
            desmume_emulator.emu.reset()

    # Touch file
    desmume_emulator.touch_input((130, 70), 0)
    desmume_emulator.wait(500)

    # Confirm name
    desmume_emulator.touch_input((190, 180), 0)
    desmume_emulator.wait(100)

    # Click yes
    desmume_emulator.touch_input((210, 110), 0)
    desmume_emulator.wait(100)

    # Click right hand
    desmume_emulator.touch_input((210, 110), 0)
    desmume_emulator.wait(100)

    # Click yes
    desmume_emulator.touch_input((210, 110), 0)
    desmume_emulator.wait(100)

    # Click newly created file
    desmume_emulator.touch_input((130, 70), 0)
    desmume_emulator.wait(100)

    # Click it again
    desmume_emulator.touch_input((130, 70), 0)
    desmume_emulator.wait(100)

    # Click "Adventure"
    desmume_emulator.touch_input((130, 70), 0)
    desmume_emulator.wait(500)
