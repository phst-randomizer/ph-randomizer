import os
from typing import Union

from desmume.emulator import SCREEN_HEIGHT, SCREEN_WIDTH, DeSmuME, DeSmuME_SDL_Window
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
        self.emu.input.touch_release()
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

    def button_input(self, buttons: Union[int, list[int]], idle_frames: int = 0):
        """
        Press buttons.

        Params:
            buttons: A single button (int) to press, or a list of buttons to simultaneously press.
            idle_frames: Optional number of frames to wait before touching the screen.
                         Shortcut for calling DesmumeEmulator.wait() before this method.
        """
        self.wait(idle_frames)
        if isinstance(buttons, int):
            buttons = [buttons]
        for button in buttons:
            self.emu.input.keypad_rm_key(keymask(button))
        self.wait(2)
        for button in buttons:
            self.emu.input.keypad_add_key(keymask(button))
        self.wait(2)
        for button in buttons:
            self.emu.input.keypad_rm_key(keymask(button))
        self.wait(2)

    def touch_input(self, position: tuple[int, int], idle_frames: int = 0):
        """
        Touch screen at a given location.

        Params:
            position: tuple in the form of (x, y) representing the location to touch the screen.
            idle_frames: Optional number of frames to wait before touching the screen.
                         Shortcut for calling DesmumeEmulator.wait() before this method.
        """
        self.wait(idle_frames)
        x, y = position
        self.emu.input.touch_release()
        self._next_frame()
        self.emu.input.touch_set_pos(x, y)
        self._next_frame()
        self.emu.input.touch_release()


@pytest.fixture
def desmume_emulator() -> DesmumeEmulator:
    return DesmumeEmulator(
        rom_path=os.environ["PH_ROM_PATH"], enable_sdl=False
    )  # TODO: make enable_sdl configurable


@pytest.fixture
def emulator_at_file_select(desmume_emulator: DesmumeEmulator) -> DesmumeEmulator:
    desmume_emulator.wait(350)
    desmume_emulator.touch_input(
        (
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2,
        )
    )
    desmume_emulator.wait(50)
    desmume_emulator.touch_input(
        (
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2,
        )
    )
    desmume_emulator.wait(200)
    return desmume_emulator
