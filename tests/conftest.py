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
    def __init__(self, rom_path: str, enable_sdl=False):
        self.emu: DeSmuME = DeSmuME()
        self.window: DeSmuME_SDL_Window
        if enable_sdl:
            self.window = self.emu.create_sdl_window()
        else:
            self.window = None
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


@pytest.fixture
def desmume_emulator() -> DesmumeEmulator:
    rom_path = os.environ["PH_ROM_PATH"]
    test_function_name = os.environ["PYTEST_CURRENT_TEST"].split(":")[-1].split(" ")[0]
    battery_file_src = Path(__file__) / "test_data" / f"{test_function_name}.dsv"
    battery_file_dest = Path(sys.executable).parent / f"{rom_path}.dsv"

    # Remove any existing save file
    battery_file_dest.unlink(missing_ok=True)

    # Copy save file to directory where py-desmume will find it
    if battery_file_src.exists():
        shutil.copy(battery_file_src, battery_file_dest)

    return DesmumeEmulator(rom_path=rom_path, enable_sdl=True)  # TODO: make enable_sdl configurable
