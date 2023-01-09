

from .conftest import DesmumeEmulator
from .desmume_utils import start_first_file


def test_intro(base_rom_emu: DesmumeEmulator):
    start_first_file(base_rom_emu)

    # # Press start + touch "Skip" button to skip intro cs
    # base_rom_emu.button_input(Keys.KEY_START)
    # base_rom_emu.wait(50)
    # base_rom_emu.touch_input((SCREEN_WIDTH, 0))
    # base_rom_emu.wait(450)

    # for _ in range(2):
    #     # Press start + touch "Skip" button to skip Tetra cs
    #     base_rom_emu.button_input(Keys.KEY_START)
    #     base_rom_emu.wait(100)
    #     base_rom_emu.touch_input((SCREEN_WIDTH, 0))
    #     base_rom_emu.wait(100)

    # base_rom_emu.wait(215)
    # # Press start + touch "Skip" button to skip ciela/beach cs
    # base_rom_emu.button_input(Keys.KEY_START)
    # base_rom_emu.wait(15)
    # base_rom_emu.touch_input((SCREEN_WIDTH, 0))
    # base_rom_emu.wait(200)

    while True:
        base_rom_emu.window.process_input()
        base_rom_emu.emu.cycle()
        base_rom_emu.window.draw()
