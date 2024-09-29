from collections.abc import Callable
import os
from pathlib import Path
import shutil
import sys
from time import sleep

import cv2
from desmume.controls import keymask
from desmume.emulator import DeSmuME
import numpy as np

from .emulator_utils import AbstractEmulatorWrapper


class DeSmuMEWrapper(AbstractEmulatorWrapper):
    def __init__(self):
        super().__init__()
        self._emulator = DeSmuME()
        self._window = self._emulator.create_sdl_window()
        self.video = None

    def open(self, rom_path: str):
        self._emulator.open(rom_path)
        self.frame = 0
        self._next_frame()

    def destroy(self):
        self._window.destroy()
        return self._emulator.destroy()

    def _next_frame(self):
        self._emulator.cycle()
        self.frame += 1
        if self._window is not None:
            self._window.draw()
            if self.video is not None:
                img = self.screenshot()
                self.video.write(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))
            self._window.process_input()

    def wait(self, frames: int):
        """Idle the emulator for `frames` frames."""
        starting_frame = self.frame
        for _ in range(starting_frame, starting_frame + frames):
            self._next_frame()

    def button_input(self, buttons: int | list[int], frames: int = 1):
        """
        Press buttons.

        Params:
            buttons: A single button (int) to press, or a list of buttons to simultaneously press.
            frames: Optional number of frames to hold button for.
        """
        if isinstance(buttons, int):
            buttons = [buttons]
        for button in buttons:
            self._emulator.input.keypad_add_key(keymask(button))
        self.wait(frames + 1)
        for button in buttons:
            self._emulator.input.keypad_rm_key(keymask(button))
        self.wait(2)

    def touch_set_and_release(self, position: tuple[int, int], frames: int = 1):
        """
        Touch screen at a given location.

        Params:
            position: tuple in the form of (x, y) representing the location to touch the screen.
            frames: Optional number of frames to hold touch screen for.
        """
        x, y = position
        self._next_frame()
        self.touch_set(x, y)
        self.wait(frames + 1)
        self.touch_release()

    def touch_set(self, x: int, y: int):
        self._emulator.input.touch_set_pos(x, y)

    def touch_release(self):
        return self._emulator.input.touch_release()

    def read_memory(self, start: int, stop: int | None = None):
        self._next_frame()
        if stop is None:
            stop = start
        return self._emulator.memory.read(start, stop, 1, False)

    def write_memory(self, start: int, data: bytes | int):
        if isinstance(data, int):
            return self._emulator.memory.write(start, start, 1, bytes([data]))
        return self._emulator.memory.write(start, start + len(data), 1, data)

    def set_read_breakpoint(self, address: int, callback: Callable[[int, int], None]):
        return self._emulator.memory.register_read(address=address, callback=callback)

    def set_write_breakpoint(self, address: int, callback: Callable[[int, int], None]):
        return self._emulator.memory.register_write(address=address, callback=callback)

    def set_exec_breakpoint(self, address: int, callback: Callable[[int, int], None]):
        return self._emulator.memory.register_exec(address=address, callback=callback)

    @property
    def r0(self):
        return self._emulator.memory.register_arm9.r0

    @r0.setter
    def r0(self, value: int):
        self._emulator.memory.register_arm9.r0 = value

    @property
    def r1(self):
        return self._emulator.memory.register_arm9.r1

    @r1.setter
    def r1(self, value: int):
        self._emulator.memory.register_arm9.r1 = value

    @property
    def r2(self):
        return self._emulator.memory.register_arm9.r2

    @r2.setter
    def r2(self, value: int):
        self._emulator.memory.register_arm9.r2 = value

    @property
    def r3(self):
        return self._emulator.memory.register_arm9.r3

    @r3.setter
    def r3(self, value: int):
        self._emulator.memory.register_arm9.r3 = value

    def load_battery_file(self, test_name: str, rom_path: Path):
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

        battery_file_src = Path(__file__).parent / 'test_data' / f'{test_name}.dsv'
        battery_file_dest = battery_file_location / f'{rom_path.stem}.dsv'

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
                    # If another test is using this file, wait 5 seconds
                    # and try again.
                    sleep(5)

    def reset(self):
        self._emulator.reset()

    def screenshot(self):
        return self._emulator.screenshot()
