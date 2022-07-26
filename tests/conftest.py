from __future__ import annotations

from enum import Enum
import json
import os
from pathlib import Path
import shutil
import sys

from ndspy.rom import NintendoDSRom
import pytest

from patcher.location_types import DigSpotLocation, IslandShopLocation
from patcher.location_types.island_shop import GD_MODELS

# Not all tests require py-desmume, so if it's not installed we
# just silently suppress the error:
try:
    from desmume.emulator import DeSmuME, DeSmuME_SDL_Window

    from tests.desmume_utils import DesmumeEmulator
except ModuleNotFoundError:
    pass


@pytest.fixture(scope="session")
def py_desmume_instance():
    desmume_emulator = DeSmuME()
    sdl_window = desmume_emulator.create_sdl_window()

    yield desmume_emulator, sdl_window

    # Cleanup desmume processes
    sdl_window.destroy()
    desmume_emulator.destroy()


@pytest.fixture
def desmume_emulator(py_desmume_instance: tuple[DeSmuME, DeSmuME_SDL_Window], tmp_path: Path):
    base_rom_path = Path(os.environ["PH_ROM_PATH"])
    python_version = sys.version_info

    # The directory where py-desmume keeps its save files. This appears to vary from system
    # to system, so it's configurable via an environment variable. In the absence of an env
    # var, it defaults to the location from my Windows system.
    battery_file_location = Path(
        os.environ.get(
            "PY_DESMUME_BATTERY_DIR",
            f"C:\\Users\\{os.getlogin()}\\AppData\\Local\\Programs\\Python\\"
            f"Python{python_version[0]}{python_version[1]}",
        )
    )

    # The name of the test function that is currently executing. Set automatically
    # by pytest at runtime.
    test_name: str = os.environ["PYTEST_CURRENT_TEST"].split(":")[-1].split(" ")[0]

    # If using parametrized tests (i.e. via `pytest.mark.parametrize`), `PYTEST_CURRENT_TEST` will
    # have the parameters of the current test appended to it. We want the same .dsv save file to
    # be used for each parameter, but a different rom for each, so save this as a seperate variable.
    test_name_with_params: str = test_name.replace("[", "_").replace("]", "_")

    # Remove parameters
    test_name = test_name.split("[")[0]

    # Path to store rom for the currently running test
    temp_rom_path = tmp_path / f"{test_name_with_params}.nds"

    battery_file_src = Path(__file__).parent / "test_data" / f"{test_name}.dsv"
    battery_file_dest = battery_file_location / f"{test_name_with_params}.dsv"

    # Make a copy of the rom for this test
    shutil.copy(base_rom_path, temp_rom_path)

    if battery_file_src.exists():
        # Copy save file to py-desmume battery directory
        shutil.copy(battery_file_src, battery_file_dest)
    else:
        # If a dsv for this test doesn't exist, remove any that exist for this rom.
        battery_file_dest.unlink(missing_ok=True)

    desmume_emulator = DesmumeEmulator(py_desmume_instance=py_desmume_instance)

    return desmume_emulator


@pytest.fixture
def base_rom_emu(tmp_path: Path, desmume_emulator: DesmumeEmulator):
    test_name: str = os.environ["PYTEST_CURRENT_TEST"].split(":")[-1].split(" ")[0]
    test_name_with_params: str = test_name.replace("[", "_").replace("]", "_")

    temp_rom_path = tmp_path / f"{test_name_with_params}.nds"
    desmume_emulator.open_rom(str(temp_rom_path))
    return desmume_emulator


@pytest.fixture(
    params=[val for val in GD_MODELS.keys() if GD_MODELS[val]],
    ids=[f"{hex(key)}-{val}" for key, val in GD_MODELS.items() if val],
)
def island_shop_test_emu(tmp_path: Path, desmume_emulator: DesmumeEmulator, request):
    test_name = (
        os.environ["PYTEST_CURRENT_TEST"]
        .split(":")[-1]
        .split(" ")[0]
        .replace("[", "_")
        .replace("]", "_")
    )
    rom_path = str(tmp_path / f"{test_name}.nds")

    IslandShopLocation.ROM = NintendoDSRom.fromFile(rom_path)

    locations = [
        IslandShopLocation(31, 0x217ECB4 - 0x217BCE0),  # shield in mercay shop
        IslandShopLocation(31, 0x217EC68 - 0x217BCE0),  # power gem in mercay shop
        IslandShopLocation(31, 0x217EC34 - 0x217BCE0),  # treasure item in mercay shop
    ]

    for location in locations:
        location.set_location(request.param)

    IslandShopLocation.ROM.saveToFile(rom_path)

    desmume_emulator.open_rom(rom_path)

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
    # TODO: Add rest of items
}


@pytest.fixture(
    params=[val for val in ITEM_MEMORY_ADDRESSES.keys()],
    ids=[f"{hex(val)}-{GD_MODELS[val]}" for val in ITEM_MEMORY_ADDRESSES.keys()],
)
def dig_spot_test_emu(tmp_path: Path, desmume_emulator: DesmumeEmulator, request):
    """Generate and run a rom with a custom dig/shovel spot item set."""
    test_name = (
        os.environ["PYTEST_CURRENT_TEST"]
        .split(":")[-1]
        .split(" ")[0]
        .replace("[", "_")
        .replace("]", "_")
    )
    rom_path = str(tmp_path / f"{test_name}.nds")

    DigSpotLocation.ROM = NintendoDSRom.fromFile(rom_path)

    DigSpotLocation(5, "Map/isle_main/map00.bin/zmb/isle_main_00.zmb").set_location(request.param)
    DigSpotLocation.save_all()

    DigSpotLocation.ROM.saveToFile(rom_path)

    desmume_emulator.open_rom(rom_path)

    return desmume_emulator


@pytest.fixture
def aux_data_directory(tmp_path: Path):
    dest = tmp_path / "auxiliary"
    shutil.copytree(Path(__file__).parent.parent / "shuffler" / "auxiliary", dest)

    # Add a new chest to Mercay aux data containing bombs, so that a beatable seed can actually
    # be generated.
    # TODO: Remove this once there's enough aux data completed to generate a beatable seed.
    with open(dest / "SW Sea" / "Mercay Island" / "Mercay.json") as fd:
        mercay_json = json.load(fd)
    mercay_json["rooms"][0]["chests"].append(
        {
            "name": "test",
            "type": "npc",
            "contents": "bombs",
            "bmg_file_path": "TODO",
            "bmg_instruction_index": -1,
        }
    )
    with open(dest / "SW Sea" / "Mercay Island" / "Mercay.json", "w") as fd:
        fd.write(json.dumps(mercay_json))

    return str(dest)


@pytest.fixture
def logic_directory(tmp_path: Path):
    dest = tmp_path / "logic"
    shutil.copytree(Path(__file__).parent.parent / "shuffler" / "logic", dest)
    return str(dest)
