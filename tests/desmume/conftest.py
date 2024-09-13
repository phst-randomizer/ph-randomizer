from enum import Enum
import os
from pathlib import Path
import shutil
import sys
from time import sleep

import cv2
import pytest

from ph_rando.patcher._util import _patch_system_bmg, apply_base_patch

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
def rom_path(tmp_path: Path, request: pytest.FixtureRequest) -> Path:
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

    test_name: str = request.node.originalname

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
    patched_rom = apply_base_patch(temp_rom_path.read_bytes())

    # Patch get item BMGs
    _patch_system_bmg(patched_rom)

    patched_rom.saveToFile(temp_rom_path)

    return temp_rom_path


@pytest.fixture
def base_rom_emu(rom_path: Path, desmume_emulator: DeSmuMEWrapper):
    desmume_emulator.open(str(rom_path))
    return desmume_emulator


class ItemMemoryAddressType(Enum):
    FLAG = 0
    COUNTER_8_BIT = 1
    COUNTER_16_BIT = 2


# Maps item ids to a tuple where first element is the memory offset of the flag indicating the
# player has received the item, and the second element is the bit within that address.
ITEM_MEMORY_OFFSETS: dict[int, tuple[int, int, ItemMemoryAddressType]] = {
    0x02: (0x4FC2, 1, ItemMemoryAddressType.COUNTER_16_BIT),  # small green rupee
    0x03: (0x50C8, 0x01, ItemMemoryAddressType.FLAG),  # oshus sword
    0x04: (0x50C8, 0x02, ItemMemoryAddressType.FLAG),  # shield
    0x07: (0x50C8, 0x10, ItemMemoryAddressType.FLAG),  # bombs
    0x08: (0x50C8, 0x20, ItemMemoryAddressType.FLAG),  # bow
    0x09: (0x4FC2, 100, ItemMemoryAddressType.COUNTER_16_BIT),  # big green rupee
    0x0A: (0x4E0C, 4, ItemMemoryAddressType.COUNTER_8_BIT),  # heart container
    0x0C: (0x50C8, 0x04, ItemMemoryAddressType.FLAG),  # boomerang
    0x0E: (0x50C8, 0x80, ItemMemoryAddressType.FLAG),  # bombchus
    0x13: (0x50CC, 0x02, ItemMemoryAddressType.FLAG),  # southwest sea chart
    0x14: (0x50CC, 0x04, ItemMemoryAddressType.FLAG),  # northwest sea chart
    0x15: (0x50CC, 0x08, ItemMemoryAddressType.FLAG),  # southeast sea chart
    0x16: (0x50CC, 0x10, ItemMemoryAddressType.FLAG),  # northeast sea chart
    0x18: (0x4FC2, 5, ItemMemoryAddressType.COUNTER_16_BIT),  # small blue rupee
    0x19: (0x4FC2, 20, ItemMemoryAddressType.COUNTER_16_BIT),  # small red rupee
    0x1A: (0x4FC2, 200, ItemMemoryAddressType.COUNTER_16_BIT),  # big red rupee
    0x1B: (0x4FC2, 300, ItemMemoryAddressType.COUNTER_16_BIT),  # big gold rupee
    0x1F: (0x50C9, 0x01, ItemMemoryAddressType.FLAG),  # hammer
    0x20: (0x50C8, 0x40, ItemMemoryAddressType.FLAG),  # grapping hook
    0x24: (0x50CD, 0x1, ItemMemoryAddressType.FLAG),  # fishing rod
    0x26: (0x50CC, 0x40, ItemMemoryAddressType.FLAG),  # sun key
    0x2C: (0x50CD, 0x4, ItemMemoryAddressType.FLAG),  # king's key
    0x2D: (0x4FC5, 1, ItemMemoryAddressType.COUNTER_8_BIT),  # power gem
    0x2E: (0x4FC6, 1, ItemMemoryAddressType.COUNTER_8_BIT),  # wisdom gem
    0x2F: (0x4FC4, 1, ItemMemoryAddressType.COUNTER_8_BIT),  # courage gem
    0x38: (0x50CD, 0x8, ItemMemoryAddressType.FLAG),  # ghost key
    # TODO: nothing happens when these three items are collected from a location
    # different from the original game. We may have to set the appropriate flags
    # in memory manually in the base patch code, but more investigation is needed.
    # 0x39: (0xE, 0x40, ItemMemoryAddressType.FLAG),  # freebie card
    # 0x3A: (0xE, 0x80, ItemMemoryAddressType.FLAG),  # compliment card
    # 0x3B: (0xE, 0x20, ItemMemoryAddressType.FLAG),  # complimentary card
    0x72: (0xF, 0x40, ItemMemoryAddressType.FLAG),  # crimsonine
    0x73: (0xF, 0x20, ItemMemoryAddressType.FLAG),  # azurine
    0x74: (0xF, 0x80, ItemMemoryAddressType.FLAG),  # aquanine
    # TODO: Add rest of items
}
BASE_FLAG_ADDRESS = 0x21B67DC  # TODO: dynamically find this address

GOT_ITEM_TEXT: dict[int, str] = {
    0x2: "You got a green Rupee!\nIt's worth 1 Rupee!\n",
    0x3: "You got Oshus's sword!\nTap an enemy or slide the\nstylus on the Touch Screen.\n",
    0x4: 'You got the wooden shield!\nDefend yourself from minor\nattacks just by holding it!\n',
    0x7: 'You got bombs! You can\nhold up to 10 in your\nbomb bag.\n',
    0x8: 'You got the bow and\narrow! Tap the Touch\nScreen and release to fire.\n',
    0x9: "You got a big green Rupee!\nIt's worth 100 Rupees!\n",
    0xA: 'You got a Heart Container!\nYou increased your life by\n1 and refilled your hearts!\n',
    0xC: 'You got the boomerang!\nThis item follows the path\nyou draw on the screen!\n',
    0xE: 'You got a Bombchu! You\ncan carry up to 10\nBombchus in your bag!\n',
    0x13: 'You found a sea chart!\n',
    0x14: 'You got the Northwestern\nSea chart!\n',
    0x15: 'You got the Southeastern\nSea chart!\n',
    0x16: 'You got the Northeastern\nSea chart!\n',
    0x18: "You got a blue Rupee!\nIt's worth 5 Rupees!\n",
    0x19: "You got a red Rupee!\nIt's worth 20 Rupees!\n",
    0x1A: "You got a big red Rupee!\nIt's worth 200 Rupees!\n",
    0x1B: "You got a big gold Rupee!\nIt's worth 300 Rupees!\n",
    0x1F: "You got a hammer! It's\nsmall, but it packs a\npunch!\n",
    0x20: 'You got a grappling hook!\nTap things to grab on to\nthem!\n',
    0x24: 'You got the fishing rod!\nTap Fish from the menu\nwhile sailing to use it.\n',
    0x26: 'You found a sword!\n\n',
    0x2C: "You got the King's Key!\nSome say it holds secrets\nof the Cobble Kingdom.\n",
    0x2D: "You got a Power Gem!\nIt radiates power, but you\ncan't use it like this.\n",
    0x2E: "You got a Wisdom Gem!\nIt radiates wisdom, but it\ncan't be used like this.\n",
    0x2F: "You got a Courage Gem!\nIt radiates courage, but it\ncan't be used like this.\n",
}
