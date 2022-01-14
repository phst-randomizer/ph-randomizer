from test.conftest import DesmumeEmulator

from desmume.controls import Keys
from desmume.emulator import SCREEN_WIDTH


def test_boot_new_game(emulator_at_file_select: DesmumeEmulator):
    """Test bootup from title screen, name entry, and intro CG."""
    # Touch file
    emulator_at_file_select.touch_input((130, 70), 0)
    emulator_at_file_select.wait(100)

    # Confirm name
    emulator_at_file_select.touch_input((190, 180), 0)
    emulator_at_file_select.wait(100)

    # Click yes
    emulator_at_file_select.touch_input((210, 110), 0)
    emulator_at_file_select.wait(100)

    # Click right hand
    emulator_at_file_select.touch_input((210, 110), 0)
    emulator_at_file_select.wait(100)

    # Click yes
    emulator_at_file_select.touch_input((210, 110), 0)
    emulator_at_file_select.wait(100)

    # Click newly created file
    emulator_at_file_select.touch_input((130, 70), 0)
    emulator_at_file_select.wait(100)

    # Click it again
    emulator_at_file_select.touch_input((130, 70), 0)
    emulator_at_file_select.wait(100)

    # Click "Adventure"
    emulator_at_file_select.touch_input((130, 70), 0)
    emulator_at_file_select.wait(250)

    # Press start + touch "Skip" button to skip intro cs
    emulator_at_file_select.button_input(Keys.KEY_START)
    emulator_at_file_select.wait(10)
    emulator_at_file_select.touch_input((SCREEN_WIDTH, 0))
    emulator_at_file_select.wait(250)

    # Press start + touch "Skip" button to skip Tetra cs
    emulator_at_file_select.button_input(Keys.KEY_START)
    emulator_at_file_select.wait(100)
    emulator_at_file_select.touch_input((SCREEN_WIDTH, 0))
    emulator_at_file_select.wait(500)

    # Press start + touch "Skip" button to skip ciela/beach cs
    emulator_at_file_select.button_input(Keys.KEY_START)
    emulator_at_file_select.wait(15)
    emulator_at_file_select.touch_input((SCREEN_WIDTH, 0))
    emulator_at_file_select.wait(200)

    # TODO: make assertions about memory state of new game
