from enum import Enum
import os
from pathlib import Path
import shutil
import sys
from time import sleep

import cv2
import pytest

from ph_rando.patcher import apply_base_patch

from .desmume_utils import DeSmuMEWrapper


@pytest.fixture(autouse=True)
def test_teardown(rom_path: Path, request):
    tests_failed_before = request.session.testsfailed
    yield

    video_recording_directory = os.environ.get('PY_DESMUME_VIDEO_RECORDING_DIR')
    if not video_recording_directory:
        return

    video_path = Path(video_recording_directory) / f'{rom_path.name}.mp4'

    # If the test didn't fail, just delete the recording
    if tests_failed_before == request.session.testsfailed:
        video_path.unlink(missing_ok=True)
        return

    for file in video_path.parent.iterdir():
        if file.is_dir() or not file.suffix == '.mp4':
            continue
        if file.resolve() != video_path.resolve():
            file.unlink()


@pytest.fixture(scope='session')
def desmume_instance():
    desmume_emulator = DeSmuMEWrapper()
    yield desmume_emulator
    desmume_emulator.destroy()


@pytest.fixture
def desmume_emulator(desmume_instance: DeSmuMEWrapper, rom_path: Path) -> DeSmuMEWrapper:
    video_recording_directory = os.environ.get('PY_DESMUME_VIDEO_RECORDING_DIR')
    if video_recording_directory:
        video_path = Path(video_recording_directory) / f'{rom_path.name}.mp4'
        video_path.parent.mkdir(parents=True, exist_ok=True)
        desmume_instance.video = cv2.VideoWriter(
            str(video_path), cv2.VideoWriter_fourcc(*'avc1'), 60, (256, 384)
        )
    else:
        desmume_instance.video = None

    return desmume_instance


@pytest.fixture
def rom_path(tmp_path: Path) -> Path:
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

    # Apply base patches to ROM
    apply_base_patch(temp_rom_path.read_bytes()).saveToFile(temp_rom_path)

    return temp_rom_path


@pytest.fixture
def base_rom_emu(rom_path: Path, desmume_emulator: DeSmuMEWrapper):
    desmume_emulator.open(str(rom_path))
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
    # TODO: nothing happens when these three items are collected from a location
    # different from the original game. We may have to set the appropriate flags
    # in memory manually in the base patch code, but more investigation is needed.
    # 0x39: (0x21B554A, 0x40, ItemMemoryAddressType.FLAG),  # freebie card
    # 0x3A: (0x21B554A, 0x80, ItemMemoryAddressType.FLAG),  # compliment card
    # 0x3B: (0x21B554A, 0x20, ItemMemoryAddressType.FLAG),  # complimentary card
    0x72: (0x21B554B, 0x40, ItemMemoryAddressType.FLAG),  # crimsonine
    0x73: (0x21B554B, 0x20, ItemMemoryAddressType.FLAG),  # azurine
    0x74: (0x21B554B, 0x80, ItemMemoryAddressType.FLAG),  # aquanine
    # TODO: Add rest of items
}
