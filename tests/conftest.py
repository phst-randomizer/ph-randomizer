import os
from pathlib import Path
import shutil
import sys
from typing import Union

from desmume.emulator import DeSmuME, DeSmuME_SDL_Window
import pytest


# TODO: using this temporarily until this is released https://github.com/SkyTemple/py-desmume/pull/19
def keymask(k):
    return 1 << (k - 1) if k > 0 else 0


class DesmumeEmulator:
    def __init__(self, py_desmume_instance: tuple[DeSmuME, DeSmuME_SDL_Window], rom_path: str):
        self.emu = py_desmume_instance[0]
        self.window = py_desmume_instance[1]
        self.frame = 0
        self.emu.open(rom_path)
        self._next_frame()

    def _next_frame(self):
        self.emu.cycle()
        self.frame += 1
        if self.window is not None:
            self.window.draw()
            self.window.process_input()

    def wait(self, frames: int):
        """Idle the emulator for `frames` frames."""
        starting_frame = self.frame
        for _ in range(starting_frame, starting_frame + frames):
            self._next_frame()

    def button_input(self, buttons: Union[int, list[int]], frames: int = 1):
        """
        Press buttons.

        Params:
            buttons: A single button (int) to press, or a list of buttons to simultaneously press.
            frames: Optional number of frames to hold button for.
        """
        if isinstance(buttons, int):
            buttons = [buttons]
        for button in buttons:
            self.emu.input.keypad_add_key(keymask(button))
        self.wait(frames + 1)
        for button in buttons:
            self.emu.input.keypad_rm_key(keymask(button))
        self.wait(2)

    def touch_input(self, position: tuple[int, int], frames: int = 1):
        """
        Touch screen at a given location.

        Params:
            position: tuple in the form of (x, y) representing the location to touch the screen.
            frames: Optional number of frames to hold touch screen for.
        """
        x, y = position
        self._next_frame()
        self.emu.input.touch_set_pos(x, y)
        self.wait(frames + 1)
        self.emu.input.touch_release()


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

    # Path to store rom for the currently running test
    temp_rom_path = tmp_path / f"{test_name_with_params}.nds"

    battery_file_src = Path(__file__).parent / "test_data" / f"{test_name}.dsv"
    battery_file_dest = battery_file_location / f"{test_name_with_params}.dsv"

    # Make a copy of the rom for this test
    shutil.copy(base_rom_path, temp_rom_path)

    if battery_file_src.exists():
        # Create a symlink to the save file for this test if it exists.
        # Note, a symlink is used instead of copying to avoid permission
        # issues with windows.
        battery_file_src.link_to(battery_file_dest)
    else:
        # If a dsv for this test doesn't exist, remove any that exist for this rom.
        battery_file_dest.unlink(missing_ok=True)

    desmume_emulator = DesmumeEmulator(
        py_desmume_instance=py_desmume_instance, rom_path=str(temp_rom_path)
    )

    return desmume_emulator
