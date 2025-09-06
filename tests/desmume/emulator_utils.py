from abc import ABC, abstractmethod
from collections.abc import Callable, Generator
from contextlib import contextmanager
import logging
from pathlib import Path
import struct

from desmume.emulator import SCREEN_HEIGHT, SCREEN_WIDTH
import pytesseract

from ph_rando.patcher._items import ITEMS
from ph_rando.shuffler.aux_models import Area

logger = logging.getLogger(__name__)


class AbstractEmulatorWrapper(ABC):
    video = None

    @abstractmethod
    def open(self, rom_path: str):
        raise NotImplementedError

    @abstractmethod
    def destroy(self):
        raise NotImplementedError

    @abstractmethod
    def wait(self, frames: int):
        raise NotImplementedError

    @abstractmethod
    def button_input(self, buttons: int | list[int], frames: int = 1):
        raise NotImplementedError

    @abstractmethod
    def touch_set(self, x: int, y: int):
        raise NotImplementedError

    @abstractmethod
    def touch_release(self):
        raise NotImplementedError

    @abstractmethod
    def touch_set_and_release(self, position: tuple[int, int], frames: int = 1):
        raise NotImplementedError

    @abstractmethod
    def read_memory(self, start: int, stop: int | None = None):
        raise NotImplementedError

    @abstractmethod
    def write_memory(self, address: int, data: bytes | int):
        raise NotImplementedError

    @abstractmethod
    def set_read_breakpoint(self, address: int, callback: Callable[[int, int], None] | None):
        raise NotImplementedError

    @abstractmethod
    def set_write_breakpoint(self, address: int, callback: Callable[[int, int], None] | None):
        raise NotImplementedError

    @abstractmethod
    def set_exec_breakpoint(self, address: int, callback: Callable[[int, int], None] | None):
        raise NotImplementedError

    @property
    @abstractmethod
    def r0(self):
        raise NotImplementedError

    @r0.setter
    @abstractmethod
    def r0(self, value: int):
        raise NotImplementedError

    @property
    @abstractmethod
    def r1(self):
        raise NotImplementedError

    @r1.setter
    @abstractmethod
    def r1(self, value: int):
        raise NotImplementedError

    @property
    @abstractmethod
    def r2(self):
        raise NotImplementedError

    @r2.setter
    @abstractmethod
    def r2(self, value: int):
        raise NotImplementedError

    @property
    @abstractmethod
    def r3(self):
        raise NotImplementedError

    @r3.setter
    @abstractmethod
    def r3(self, value: int):
        raise NotImplementedError

    @abstractmethod
    def reset(self):
        raise NotImplementedError

    @abstractmethod
    def load_battery_file(self, test_name: str, rom_path: Path):
        raise NotImplementedError

    @abstractmethod
    def screenshot(self):
        raise NotImplementedError

    @property
    def event_flag_base_addr(self) -> int:
        addr = int.from_bytes(self.read_memory(start=0x27E0F74, stop=0x27E0F78), 'little')
        if addr == 0:
            raise ValueError('Event flag base address not set.')
        return addr

    # Optional methods
    def stop(self):
        return


def start_first_file(emulator: AbstractEmulatorWrapper):
    """From game boot, goes through the title screen and starts the first save."""
    emulator.wait(500)

    # Click title screen
    emulator.touch_set_and_release(
        (
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2,
        )
    )

    emulator.wait(100)

    # Click title screen again
    emulator.touch_set_and_release(
        (
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2,
        )
    )
    emulator.wait(200)

    # Click file
    emulator.touch_set_and_release((130, 70), 0)
    emulator.wait(100)

    # Click it again
    emulator.touch_set_and_release((130, 70), 0)
    emulator.wait(100)

    # Click "Adventure"
    emulator.touch_set_and_release((130, 70), 0)
    emulator.wait(600)


def get_current_rupee_count(emulator: AbstractEmulatorWrapper):
    addr = emulator.event_flag_base_addr + 0x4FC2
    return int.from_bytes(emulator.read_memory(addr, addr + 2), 'little')


# Screen coordinates for each item when the "Items" menu is open
ITEMS_MENU_COORDINATES = {'shovel': (225, 175), 'bombs': (98, 178)}


def open_items_menu(emulator: AbstractEmulatorWrapper):
    emulator.touch_set_and_release((SCREEN_WIDTH - 5, SCREEN_HEIGHT - 5), 5)
    emulator.wait(20)


def select_item_from_items_menu(emulator: AbstractEmulatorWrapper, item: str):
    emulator.touch_set_and_release(ITEMS_MENU_COORDINATES[item], 5)
    emulator.wait(20)


def equip_item(emulator: AbstractEmulatorWrapper, item: str):
    open_items_menu(emulator)
    select_item_from_items_menu(emulator, item)


def use_equipped_item(emulator: AbstractEmulatorWrapper):
    emulator.touch_set_and_release((SCREEN_WIDTH, 0), 5)
    emulator.wait(20)


@contextmanager
def assert_item_is_picked_up(item: int | str, emu_instance: AbstractEmulatorWrapper) -> Generator:
    from .conftest import ITEM_MEMORY_OFFSETS, ItemMemoryAddressType

    if isinstance(item, str):
        item = ITEMS[item]

    base_addr = emu_instance.event_flag_base_addr

    # Get original value (before item is retrieved)
    original_value = emu_instance.read_memory(ITEM_MEMORY_OFFSETS[item][0] + base_addr)
    if ITEM_MEMORY_OFFSETS[item][2] == ItemMemoryAddressType.FLAG:
        assert original_value & ITEM_MEMORY_OFFSETS[item][1] != ITEM_MEMORY_OFFSETS[item][1]
    elif ITEM_MEMORY_OFFSETS[item][2] == ItemMemoryAddressType.COUNTER_8_BIT:
        original_value = emu_instance.read_memory(ITEM_MEMORY_OFFSETS[item][0] + base_addr)
    elif ITEM_MEMORY_OFFSETS[item][2] == ItemMemoryAddressType.COUNTER_16_BIT:
        original_value = int.from_bytes(
            emu_instance.read_memory(
                ITEM_MEMORY_OFFSETS[item][0] + base_addr,
                ITEM_MEMORY_OFFSETS[item][0] + base_addr + 2,
            ),
            'little',
        )
    else:
        raise NotImplementedError(f'{ITEM_MEMORY_OFFSETS[item][2]} not a valid item type.')

    yield

    # Make sure correct item was retrieved.
    if ITEM_MEMORY_OFFSETS[item][2] == ItemMemoryAddressType.FLAG:
        assert (
            emu_instance.read_memory(ITEM_MEMORY_OFFSETS[item][0] + base_addr)
            & ITEM_MEMORY_OFFSETS[item][1]
            == ITEM_MEMORY_OFFSETS[item][1]
        )
    elif ITEM_MEMORY_OFFSETS[item][2] == ItemMemoryAddressType.COUNTER_8_BIT:
        assert (
            emu_instance.read_memory(ITEM_MEMORY_OFFSETS[item][0] + base_addr)
            - ITEM_MEMORY_OFFSETS[item][1]
            == original_value
        )
    elif ITEM_MEMORY_OFFSETS[item][2] == ItemMemoryAddressType.COUNTER_16_BIT:
        assert (
            int.from_bytes(
                emu_instance.read_memory(
                    ITEM_MEMORY_OFFSETS[item][0] + base_addr,
                    ITEM_MEMORY_OFFSETS[item][0] + base_addr + 2,
                ),
                'little',
            )
            - ITEM_MEMORY_OFFSETS[item][1]
            == original_value
        )
    else:
        raise NotImplementedError(f'{ITEM_MEMORY_OFFSETS[item][2]} not a valid item type.')


def get_check_contents(
    aux_data: list[Area],
    area_name: str,
    room_name: str,
    chest_name: str,
) -> str:
    return [
        chest.contents.name
        for area in aux_data
        for room in area.rooms
        for chest in room.chests
        if (area.name, room.name, chest.name) == (area_name, room_name, chest_name)
    ][0]


@contextmanager
def prevent_actor_spawn(
    emu_instance: AbstractEmulatorWrapper,
    actors: list[str] | str,
    replacement: str = 'RUPY',
):
    """
    Prevents one or more actors from spawning while this context manager is active.
    """
    if isinstance(actors, str):
        actors = [actors]

    def cancel_spawn(addr: int, size: int):
        npc_id = emu_instance.r1
        npc = struct.Struct('>I').pack(npc_id).decode()
        if npc in actors:
            emu_instance.r1 = int.from_bytes(replacement.encode(), 'little')

    emu_instance.set_exec_breakpoint(0x20C3FE8, cancel_spawn)

    yield

    # Clear callback on context manager exit
    emu_instance.set_exec_breakpoint(0x20C3FE8, None)


def assert_text_displayed(emu_instance: AbstractEmulatorWrapper, text: str) -> None:
    """
    Asserts that the given text is displayed on the screen.
    """
    from .desmume import DeSmuMEWrapper

    if not isinstance(emu_instance, DeSmuMEWrapper):
        logger.warning('Text assertion only supported for DeSmuME emulator.')
        return

    screenshot = emu_instance.screenshot()

    # Check if the text is correct
    ocr_text: str = pytesseract.image_to_string(screenshot.crop((24, 325, 231, 384))).replace(
        '\u2019', "'"
    )

    assert text in ocr_text
