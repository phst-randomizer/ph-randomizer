from pathlib import Path
import re

from conftest import DesmumeEmulator
from desmume.controls import Keys
from desmume.emulator import SCREEN_HEIGHT, SCREEN_WIDTH
import pytest

RANDO_SETTINGS_BITMAP_ADDR = int(
    re.findall(
        r'#define RANDO_SETTINGS_BITMAP_ADDR (.+)',
        (Path(__file__).parent.parent / 'base' / 'src' / 'rando_settings.h').read_text(),
    )[0],
    16,
)


@pytest.mark.parametrize(
    'bridge_repaired', [True, False], ids=['Bridge repaired from start', 'Bridge broken from start']
)
def test_flags_and_settings(base_rom_emu: DesmumeEmulator, bridge_repaired: bool):
    """Ensure all flags are set properly + all rando settings work."""
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

    base_rom_emu.emu.memory.unsigned[RANDO_SETTINGS_BITMAP_ADDR] |= int(bridge_repaired)

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

    ########################################
    # Assert that flags are set correctly: #
    ########################################

    # Mercay bridge repaired
    assert (base_rom_emu.emu.memory.unsigned[0x021B553C + 0x2] & 0x2 == 0x2) is bridge_repaired
    # Talked to Oshus for first time
    assert base_rom_emu.emu.memory.unsigned[0x021B553C + 0x18] & 0x2 == 0x2
    # Saw broken bridge for first time
    assert base_rom_emu.emu.memory.unsigned[0x021B553C + 0x2C] & 0x1 == 0x1
