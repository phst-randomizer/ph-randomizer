from collections.abc import Callable
import hashlib
import json
import logging
import os
from pathlib import Path
import shutil
import socket
import subprocess
from tempfile import TemporaryDirectory
import time

import birdseyelib as bird
import pytest

from .emulator_utils import AbstractEmulatorWrapper

logger = logging.getLogger(__name__)

EMUHAWK_PATH = Path(
    os.environ.get(
        'EMUHAWK_PATH', 'C:\\Users\\Mike\\Downloads\\BizHawk-2.9.1-win-x64_2\\EmuHawk.exe'
    )
)


class MelonDSWrapper(AbstractEmulatorWrapper):
    def __init__(self):
        self._bizhawk_process = None
        self._client = None
        self._memory = None
        self._emulation = None
        self._external_tool = None
        self._controller = None
        self._host = '127.0.0.1'
        self._bizhawk_directory = None
        self._rom_path: str | None = None
        self.video = None

    def __del__(self):
        self._cleanup_bizhawk_directory()

    def _cleanup_bizhawk_directory(self):
        logger.debug('Cleaning up BizHawk resources')

        # If the BizHawk process is still running, kill it
        if self._bizhawk_process is not None:
            self._bizhawk_process.kill()

        if self._bizhawk_directory is None:
            return

        for file in Path(self._bizhawk_directory.name).rglob('*'):
            if file.is_file():
                try:
                    file.unlink(missing_ok=True)
                except PermissionError:
                    logger.debug(f'Failed to delete {file} due to PermissionError, skipping')

        try:
            self._bizhawk_directory.cleanup()
        except Exception:
            logger.warning(
                f'Failed to cleanup {self._bizhawk_directory.name} due to PermissionError, skipping'
            )

    def open(self, rom_path: str):
        # Create a temporary directory to store BizHawk files
        self._bizhawk_directory = TemporaryDirectory()

        self._rom_path = rom_path

        # Find an open port for BirdsEye tool
        sock = socket.socket()
        sock.bind(('', 0))
        port = sock.getsockname()[1]
        sock.close()
        self._port = port

        logger.debug(f'Copying BizHawk files to {self._bizhawk_directory.name}')
        shutil.copytree(EMUHAWK_PATH.parent, self._bizhawk_directory.name, dirs_exist_ok=True)

        emuhawk_config_file_src = Path(__file__).parent / 'test_data' / 'config.ini'
        emuhawk_config_file_dest = Path(self._bizhawk_directory.name) / 'config.ini'

        # Create a BirdsEye config file
        birds_eye_config = (
            f'host={self._host}\n'
            f'port={self._port}\n'
            'logLevel=4\n'
            'socketTimeout=10000\n'
            'socketBufSize=2048\n'
        )
        birds_eye_config_file = Path(self._bizhawk_directory.name) / 'birdconfig.txt'
        birds_eye_config_file.touch(exist_ok=False)
        birds_eye_config_file.write_text(birds_eye_config, newline='\n')

        # Delete the gamedb file to force BizHawk to use the ROM name as the SaveRAM
        # filename instead of the internal name
        logger.debug('Deleting gamedb file')
        gamedb = Path(self._bizhawk_directory.name) / 'gamedb' / 'gamedb_nds.txt'
        gamedb.unlink(missing_ok=True)

        # Add BirdsEye to the list of trusted external tools
        logger.debug('Adding BirdsEye to the list of trusted external tools')
        birds_eye_external_tool = (
            Path(self._bizhawk_directory.name) / 'ExternalTools' / 'BirdsEye.dll'
        )
        be_tool_sha1 = hashlib.sha1(birds_eye_external_tool.read_bytes()).hexdigest().upper()
        emuhawk_config = json.loads(emuhawk_config_file_src.read_text())
        if 'TrustedExtTools' not in emuhawk_config:
            emuhawk_config['TrustedExtTools'] = {}
        emuhawk_config['TrustedExtTools'][
            str(birds_eye_external_tool.resolve())
        ] = f'SHA1:{be_tool_sha1}'
        emuhawk_config_file_dest.write_text(json.dumps(emuhawk_config))

        # Launch BizHawk with the ROM and BirdsEye
        logger.debug('Launching BizHawk')
        emuhawk_args = [
            str((Path(self._bizhawk_directory.name) / 'EmuHawk.exe').resolve()),
            rom_path,
            '--open-ext-tool-dll=BirdsEye',
            f'--config={str(emuhawk_config_file_dest.resolve())}',
        ]
        self._bizhawk_process = subprocess.Popen(
            emuhawk_args, cwd=Path(self._bizhawk_directory.name)
        )

        # Wait for BirdsEye to connect
        logger.debug(f'Waiting for BirdsEye to connect on port {self._port}')
        start_time = time.time()
        while True:
            if time.time() - start_time > 30:
                raise TimeoutError('BirdsEye did not connect within 30 seconds')
            try:
                with socket.create_connection((self._host, self._port), timeout=5):
                    logger.debug(f"Server {self._host}:{self._port} is available!")
                    break
            except (TimeoutError, ConnectionRefusedError):
                logger.debug(f"Waiting for server {self._host}:{self._port}...")
                time.sleep(1)

        self._client = bird.Client(self._host, self._port)
        self._memory = bird.Memory(self._client)
        self._emulation = bird.Emulation(self._client)
        self._external_tool = bird.ExternalTool(self._client)
        self._controller = bird.ControllerInput(self._client)
        self._joypad = bird.NDSJoypad()
        self._controller.set_joypad(self._joypad)
        self._client.connect()
        self._external_tool.set_commandeer(enabled=True)

    def destroy(self):
        if self._bizhawk_process is not None:
            logger.debug('Terminating BizHawk process')
            self._bizhawk_process.terminate()
        self._cleanup_bizhawk_directory()

    def wait(self, frames: int):
        for _ in range(frames + int(frames * 0.1)):
            self._memory.request_memory()
            self._emulation.request_framecount()
            self._client.advance_frame()

    def button_input(self, buttons: int | list[int], frames: int = 1):
        raise NotImplementedError

    def touch_set(self, x: int, y: int):
        logger.debug(f'touch_set({x}, {y})')

        # MelonDS doesn't like touch coordinates of 0 or 256
        if x == 0:
            x = 1
        elif x == 256:
            x = 255

        self._joypad.analog_controls['Touch X'] = str(x)
        self._joypad.analog_controls['Touch Y'] = str(y)
        self._joypad.controls['Touch'] = True
        self._controller.set_controller_input(joypad=self._joypad)

    def touch_release(self):
        logger.debug('touch_release()')
        self._joypad.controls['Touch'] = False
        self._controller.set_controller_input(joypad=self._joypad)

    def touch_set_and_release(self, position: tuple[int, int], frames: int = 1):
        logger.debug(f'touch_set_and_release({position}, {frames})')
        self.wait(1)
        self.touch_set(position[0], position[1])
        self.wait(frames + 1)
        self.touch_release()

    def read_memory(self, start: int, stop: int | None = None):
        if stop is None:
            self._memory.add_address(start)
        else:
            self._memory.add_address_range(start, stop)
        self._memory.request_memory()
        self._client.advance_frame()

        memory = self._memory.get_memory()

        if stop is None:
            return memory[hex(start)]

        b = bytearray()
        for address in range(start, stop):
            b.append(memory[hex(address)])

        return bytes(b)

    def write_memory(self, address: int, data: bytes | int):
        pytest.skip('MelonDSWrapper does not support memory writing yet')

    def set_read_breakpoint(self, address: int, callback: Callable[[int, int], None]):
        pytest.skip('MelonDSWrapper does not support breakpoints yet')

    def set_write_breakpoint(self, address: int, callback: Callable[[int, int], None]):
        pytest.skip('MelonDSWrapper does not support breakpoints yet')

    def set_exec_breakpoint(self, address: int, callback: Callable[[int, int], None]):
        pytest.skip('MelonDSWrapper does not support breakpoints yet')

    @property
    def r0(self):
        pytest.skip('MelonDSWrapper does not support reading registers yet')

    @r0.setter
    def r0(self, value: int):
        pytest.skip('MelonDSWrapper does not support writing registers yet')

    @property
    def r1(self):
        pytest.skip('MelonDSWrapper does not support reading registers yet')

    @r1.setter
    def r1(self, value: int):
        pytest.skip('MelonDSWrapper does not support writing registers yet')

    @property
    def r2(self):
        pytest.skip('MelonDSWrapper does not support reading registers yet')

    @r2.setter
    def r2(self, value: int):
        pytest.skip('MelonDSWrapper does not support writing registers yet')

    @property
    def r3(self):
        pytest.skip('MelonDSWrapper does not support reading registers yet')

    @r3.setter
    def r3(self, value: int):
        pytest.skip('MelonDSWrapper does not support writing registers yet')

    def load_battery_file(self, test_name: str, rom_path: Path):
        battery_file_location = EMUHAWK_PATH.parent / 'NDS' / 'SaveRAM'

        battery_file_src = Path(__file__).parent / 'test_data' / f'{test_name}.dsv'

        # For some reason, MelonDS strips underscores from the rom name when it saves the battery file.
        battery_file_dest = (
            battery_file_location
            / f'{Path(rom_path.name.replace("_", " ")).with_suffix(".SaveRAM")}'
        )

        logger.debug(f'Copying battery file from {battery_file_src} to {battery_file_dest}')
        battery_file_dest.parent.mkdir(parents=True, exist_ok=True)

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
                    time.sleep(5)

    def reset(self):
        self.destroy()
        self.open(self._rom_path)

    def stop(self):
        logger.debug('Stopping MelonDS')
        self.destroy()
