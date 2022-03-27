from desmume.controls import Keys
from desmume.emulator import SCREEN_WIDTH

from tests.conftest import DesmumeEmulator
from tests.helpers import start_first_file


def test_boot_new_game(desmume_emulator: DesmumeEmulator):
    """Test bootup from title screen, name entry, and intro CG."""
    start_first_file(desmume_emulator)

    # Press start + touch "Skip" button to skip intro cs
    desmume_emulator.button_input(Keys.KEY_START)
    desmume_emulator.wait(50)
    desmume_emulator.touch_input((SCREEN_WIDTH, 0))
    desmume_emulator.wait(250)

    # Press start + touch "Skip" button to skip Tetra cs
    desmume_emulator.button_input(Keys.KEY_START)
    desmume_emulator.wait(100)
    desmume_emulator.touch_input((SCREEN_WIDTH, 0))
    desmume_emulator.wait(500)

    # Press start + touch "Skip" button to skip ciela/beach cs
    desmume_emulator.button_input(Keys.KEY_START)
    desmume_emulator.wait(15)
    desmume_emulator.touch_input((SCREEN_WIDTH, 0))
    desmume_emulator.wait(200)

    # ensure mercay bridge fixed flag is set
    assert desmume_emulator.emu.memory.unsigned[0x021B553E] & 0x2 == 0x2
