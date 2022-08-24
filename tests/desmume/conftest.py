from enum import Enum
import os
from pathlib import Path
import shutil
import sys
from time import sleep

from desmume.emulator import DeSmuME, DeSmuME_SDL_Window
import pytest

from .desmume_utils import DesmumeEmulator


@pytest.fixture(scope='session')
def py_desmume_instance():
    desmume_emulator = DeSmuME()
    sdl_window = desmume_emulator.create_sdl_window()

    yield desmume_emulator, sdl_window

    # Cleanup desmume processes
    sdl_window.destroy()
    desmume_emulator.destroy()


@pytest.fixture
def desmume_emulator(py_desmume_instance: tuple[DeSmuME, DeSmuME_SDL_Window], tmp_path: Path):
    base_rom_path = Path(os.environ['PH_ROM_PATH'])
    python_version = sys.version_info

    # The directory where py-desmume keeps its save files. This appears to vary from system
    # to system, so it's configurable via an environment variable. In the absence of an env
    # var, it defaults to the location from my Windows system.
    battery_file_location = Path(
        os.environ.get(
            'PY_DESMUME_BATTERY_DIR',
            f'C:\\Users\\{os.getlogin()}\\AppData\\Local\\Programs\\Python\\'
            f'Python{python_version[0]}{python_version[1]}',
        )
    )

    # The name of the test function that is currently executing.
    # PYTEST_CURRENT_TEST env var is set automatically by pytest at runtime.
    test_name = os.environ['PYTEST_CURRENT_TEST'].split(':')[-1].split(' ')[0].split('[')[0]

    # Path to store rom for the currently running test
    temp_rom_path = tmp_path / f'{tmp_path.name}.nds'

    battery_file_src = Path(__file__).parent / 'test_data' / f'{test_name}.dsv'
    battery_file_dest = battery_file_location / f'{tmp_path.name}.dsv'

    # Make a copy of the rom for this test
    shutil.copy(base_rom_path, temp_rom_path)

    if battery_file_src.exists():
        # Copy save file to py-desmume battery directory
        shutil.copy(battery_file_src, battery_file_dest)
    else:
        while True:
            try:
                # If a dsv for this test doesn't exist, remove any that exist for this rom.
                battery_file_dest.unlink(missing_ok=True)
                break
            except PermissionError:
                # If another test is using this file, wait 10 seconds
                # and try again.
                sleep(10)

    desmume_emulator = DesmumeEmulator(py_desmume_instance=py_desmume_instance)

    return desmume_emulator


@pytest.fixture
def base_rom_emu(tmp_path: Path, desmume_emulator: DesmumeEmulator):
    temp_rom_path = tmp_path / f'{tmp_path.name}.nds'
    desmume_emulator.open_rom(str(temp_rom_path))
    return desmume_emulator


class ItemMemoryAddressType(Enum):
    FLAG = 0
    COUNTER_8_BIT = 1
    COUNTER_16_BIT = 2


# Maps item ids to a tuple where first element is the memory address of the flag indicating the
# player has received the item, and the second element is the bit within that address.
ITEM_MEMORY_ADDRESSES: dict[int, tuple[int, int, ItemMemoryAddressType]] = {
    0x02: (0x21BA4FE, 1, ItemMemoryAddressType.COUNTER_16_BIT),  # small green rupee
    0x03: (0x21BA604, 0x01, ItemMemoryAddressType.FLAG),  # oshus sword
    0x04: (0x21BA604, 0x02, ItemMemoryAddressType.FLAG),  # shield
    0x07: (0x21BA604, 0x10, ItemMemoryAddressType.FLAG),  # bombs
    0x08: (0x21BA604, 0x20, ItemMemoryAddressType.FLAG),  # bow
    0x09: (0x21BA4FE, 100, ItemMemoryAddressType.COUNTER_16_BIT),  # big green rupee
    0x0A: (0x21BA348, 4, ItemMemoryAddressType.COUNTER_8_BIT),  # heart container
    0x0C: (0x21BA604, 0x04, ItemMemoryAddressType.FLAG),  # boomerang
    0x0E: (0x21BA604, 0x80, ItemMemoryAddressType.FLAG),  # bombchus
    0x13: (0x21BA608, 0x02, ItemMemoryAddressType.FLAG),  # southwest sea chart
    0x14: (0x21BA608, 0x04, ItemMemoryAddressType.FLAG),  # northwest sea chart
    0x15: (0x21BA608, 0x08, ItemMemoryAddressType.FLAG),  # southeast sea chart
    0x16: (0x21BA608, 0x10, ItemMemoryAddressType.FLAG),  # northeast sea chart
    0x18: (0x21BA4FE, 5, ItemMemoryAddressType.COUNTER_16_BIT),  # small blue rupee
    0x19: (0x21BA4FE, 20, ItemMemoryAddressType.COUNTER_16_BIT),  # small red rupee
    0x1A: (0x21BA4FE, 200, ItemMemoryAddressType.COUNTER_16_BIT),  # big red rupee
    0x1B: (0x21BA4FE, 300, ItemMemoryAddressType.COUNTER_16_BIT),  # big gold rupee
    0x1F: (0x21BA605, 0x01, ItemMemoryAddressType.FLAG),  # hammer
    0x20: (0x21BA604, 0x40, ItemMemoryAddressType.FLAG),  # grapping hook
    0x24: (0x21BA609, 0x1, ItemMemoryAddressType.FLAG),  # fishing rod
    0x26: (0x21BA608, 0x40, ItemMemoryAddressType.FLAG),  # sun key
    0x2C: (0x21BA609, 0x4, ItemMemoryAddressType.FLAG),  # king's key
    0x2D: (0x21BA501, 1, ItemMemoryAddressType.COUNTER_8_BIT),  # power gem
    0x2E: (0x21BA502, 1, ItemMemoryAddressType.COUNTER_8_BIT),  # wisdom gem
    0x2F: (0x21BA500, 1, ItemMemoryAddressType.COUNTER_8_BIT),  # courage gem
    0x38: (0x21BA609, 0x8, ItemMemoryAddressType.FLAG),  # ghost key
    0x39: (0x21B554A, 0x40, ItemMemoryAddressType.FLAG),  # freebie card
    0x3A: (0x21B554A, 0x80, ItemMemoryAddressType.FLAG),  # compliment card
    0x3B: (0x21B554A, 0x20, ItemMemoryAddressType.FLAG),  # complimentary card
    0x72: (0x21B554B, 0x40, ItemMemoryAddressType.FLAG),  # crimsonine
    # TODO: Add rest of items
}
