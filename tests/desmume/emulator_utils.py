from abc import ABC
from collections.abc import Callable, Generator
from contextlib import contextmanager
from pathlib import Path
import struct

from desmume.emulator import SCREEN_HEIGHT, SCREEN_WIDTH

from ph_rando.patcher._items import ITEMS
from ph_rando.shuffler.aux_models import Area

from .desmume import DeSmuMEWrapper


class AbstractEmulatorWrapper(ABC):
    def open(self, rom_path: str):
        raise NotImplementedError

    def destroy(self):
        raise NotImplementedError

    def wait(self, frames: int):
        raise NotImplementedError

    def button_input(self, buttons: int | list[int], frames: int = 1):
        raise NotImplementedError

    def touch_set(self, x: int, y: int):
        raise NotImplementedError

    def touch_release(self):
        raise NotImplementedError

    def touch_set_and_release(self, position: tuple[int, int], frames: int = 1):
        raise NotImplementedError

    def read_memory(self, start: int, stop: int | None = None):
        raise NotImplementedError

    def write_memory(self, address: int, data: bytes | int):
        raise NotImplementedError

    def set_read_breakpoint(self, address: int, callback: Callable[[int, int], None]):
        raise NotImplementedError

    def set_write_breakpoint(self, address: int, callback: Callable[[int, int], None]):
        raise NotImplementedError

    def set_exec_breakpoint(self, address: int, callback: Callable[[int, int], None]):
        raise NotImplementedError

    @property
    def r0(self):
        raise NotImplementedError

    @r0.setter
    def r0(self, value: int):
        raise NotImplementedError

    @property
    def r1(self):
        raise NotImplementedError

    @r1.setter
    def r1(self, value: int):
        raise NotImplementedError

    @property
    def r2(self):
        raise NotImplementedError

    @r2.setter
    def r2(self, value: int):
        raise NotImplementedError

    @property
    def r3(self):
        raise NotImplementedError

    @r3.setter
    def r3(self, value: int):
        raise NotImplementedError

    @property
    def event_flag_base_addr(self) -> int:
        addr = int.from_bytes(self.read_memory(start=0x27E0F74, stop=0x27E0F78), 'little')
        if addr == 0:
            raise ValueError('Event flag base address not set.')
        return addr

    def reset(self):
        raise NotImplementedError

    def load_battery_file(self, test_name: str, rom_path: Path):
        raise NotImplementedError

    # Optional methods
    def stop(self):
        pass


def start_first_file(desmume_emulator: DeSmuMEWrapper):
    """From game boot, goes through the title screen and starts the first save."""
    desmume_emulator.wait(500)

    # Click title screen
    desmume_emulator.touch_set_and_release(
        (
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2,
        )
    )

    desmume_emulator.wait(100)

    # Click title screen again
    desmume_emulator.touch_set_and_release(
        (
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2,
        )
    )
    desmume_emulator.wait(200)

    # Click file
    desmume_emulator.touch_set_and_release((130, 70), 0)
    desmume_emulator.wait(100)

    # Click it again
    desmume_emulator.touch_set_and_release((130, 70), 0)
    desmume_emulator.wait(100)

    # Click "Adventure"
    desmume_emulator.touch_set_and_release((130, 70), 0)
    desmume_emulator.wait(600)


def get_current_rupee_count(desmume: DeSmuMEWrapper):
    addr = desmume.event_flag_base_addr + 0x4FC2
    return int.from_bytes(desmume.read_memory(addr, addr + 2), 'little')


# Screen coordinates for each item when the "Items" menu is open
ITEMS_MENU_COORDINATES = {'shovel': (225, 175), 'bombs': (98, 178)}


def open_items_menu(desmume: DeSmuMEWrapper):
    desmume.touch_set_and_release((SCREEN_WIDTH - 5, SCREEN_HEIGHT - 5), 5)
    desmume.wait(20)


def select_item_from_items_menu(desmume: DeSmuMEWrapper, item: str):
    desmume.touch_set_and_release(ITEMS_MENU_COORDINATES[item], 5)
    desmume.wait(20)


def equip_item(desmume: DeSmuMEWrapper, item: str):
    open_items_menu(desmume)
    select_item_from_items_menu(desmume, item)


def use_equipped_item(desmume: DeSmuMEWrapper):
    desmume.touch_set_and_release((SCREEN_WIDTH, 0), 5)
    desmume.wait(20)


@contextmanager
def assert_item_is_picked_up(item: int | str, emu_instance: DeSmuMEWrapper) -> Generator:
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
    emu_instance: DeSmuMEWrapper,
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
