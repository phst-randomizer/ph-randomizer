from collections.abc import Generator, Iterable
from contextlib import contextmanager
import struct

import cv2
from desmume.controls import keymask
from desmume.emulator import SCREEN_HEIGHT, SCREEN_WIDTH, DeSmuME
import numpy as np

from ph_rando.patcher._items import ITEMS
from ph_rando.shuffler.aux_models import Area


class DeSmuMEWrapper(DeSmuME):
    def __init__(self):
        super().__init__()
        self.window = self.create_sdl_window()
        self.video = None

    def open(self, rom_path: str):
        super().open(rom_path)
        self.frame = 0
        self._next_frame()

    def destroy(self):
        self.window.destroy()
        return super().destroy()

    def _next_frame(self):
        self.cycle()
        self.frame += 1
        if self.window is not None:
            self.window.draw()
            if self.video is not None:
                img = self.screenshot()
                self.video.write(cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))
            self.window.process_input()

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
            self.input.keypad_add_key(keymask(button))
        self.wait(frames + 1)
        for button in buttons:
            self.input.keypad_rm_key(keymask(button))
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
        self.input.touch_set_pos(x, y)
        self.wait(frames + 1)
        self.input.touch_release()


def start_first_file(desmume_emulator: DeSmuMEWrapper):
    """From game boot, goes through the title screen and starts the first save."""
    desmume_emulator.wait(500)

    # Click title screen
    desmume_emulator.touch_input(
        (
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2,
        )
    )

    desmume_emulator.wait(100)

    # Click title screen again
    desmume_emulator.touch_input(
        (
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 2,
        )
    )
    desmume_emulator.wait(200)

    # Click file
    desmume_emulator.touch_input((130, 70), 0)
    desmume_emulator.wait(100)

    # Click it again
    desmume_emulator.touch_input((130, 70), 0)
    desmume_emulator.wait(100)

    # Click "Adventure"
    desmume_emulator.touch_input((130, 70), 0)
    desmume_emulator.wait(200)


def get_current_rupee_count(desmume: DeSmuMEWrapper):
    return int.from_bytes(desmume.memory.unsigned[0x021BA4FE : 0x021BA4FE + 2], 'little')


# Screen coordinates for each item when the "Items" menu is open
ITEMS_MENU_COORDINATES = {'shovel': (225, 175), 'bombs': (98, 178)}


def open_items_menu(desmume: DeSmuMEWrapper):
    desmume.touch_input((SCREEN_WIDTH - 5, SCREEN_HEIGHT - 5), 5)
    desmume.wait(20)


def select_item_from_items_menu(desmume: DeSmuMEWrapper, item: str):
    desmume.touch_input(ITEMS_MENU_COORDINATES[item], 5)
    desmume.wait(20)


def equip_item(desmume: DeSmuMEWrapper, item: str):
    open_items_menu(desmume)
    select_item_from_items_menu(desmume, item)


def use_equipped_item(desmume: DeSmuMEWrapper):
    desmume.touch_input((SCREEN_WIDTH, 0), 5)
    desmume.wait(20)


@contextmanager
def assert_item_is_picked_up(item: int | str, emu_instance: DeSmuMEWrapper) -> Generator:
    from .conftest import ITEM_MEMORY_ADDRESSES, ItemMemoryAddressType

    if isinstance(item, str):
        item = ITEMS[item]

    # Get original value (before item is retrieved)
    original_value = emu_instance.memory.unsigned[ITEM_MEMORY_ADDRESSES[item][0]]
    if ITEM_MEMORY_ADDRESSES[item][2] == ItemMemoryAddressType.FLAG:
        assert original_value & ITEM_MEMORY_ADDRESSES[item][1] != ITEM_MEMORY_ADDRESSES[item][1]
    elif ITEM_MEMORY_ADDRESSES[item][2] == ItemMemoryAddressType.COUNTER_8_BIT:
        original_value = emu_instance.memory.unsigned[ITEM_MEMORY_ADDRESSES[item][0]]
    elif ITEM_MEMORY_ADDRESSES[item][2] == ItemMemoryAddressType.COUNTER_16_BIT:
        original_value = int.from_bytes(
            emu_instance.memory.unsigned[
                ITEM_MEMORY_ADDRESSES[item][0] : ITEM_MEMORY_ADDRESSES[item][0] + 2
            ],
            'little',
        )
    else:
        raise NotImplementedError(f'{ITEM_MEMORY_ADDRESSES[item][2]} not a valid item type.')

    yield

    # Make sure correct item was retrieved.
    if ITEM_MEMORY_ADDRESSES[item][2] == ItemMemoryAddressType.FLAG:
        assert (
            emu_instance.memory.unsigned[ITEM_MEMORY_ADDRESSES[item][0]]
            & ITEM_MEMORY_ADDRESSES[item][1]
            == ITEM_MEMORY_ADDRESSES[item][1]
        )
    elif ITEM_MEMORY_ADDRESSES[item][2] == ItemMemoryAddressType.COUNTER_8_BIT:
        assert (
            emu_instance.memory.unsigned[ITEM_MEMORY_ADDRESSES[item][0]]
            - ITEM_MEMORY_ADDRESSES[item][1]
            == original_value
        )
    elif ITEM_MEMORY_ADDRESSES[item][2] == ItemMemoryAddressType.COUNTER_16_BIT:
        assert (
            int.from_bytes(
                emu_instance.memory.unsigned[
                    ITEM_MEMORY_ADDRESSES[item][0] : ITEM_MEMORY_ADDRESSES[item][0] + 2
                ],
                'little',
            )
            - ITEM_MEMORY_ADDRESSES[item][1]
            == original_value
        )
    else:
        raise NotImplementedError(f'{ITEM_MEMORY_ADDRESSES[item][2]} not a valid item type.')


def get_check_contents(
    aux_data: Iterable[Area],
    area_name: str,
    room_name: str,
    chest_name: str,
) -> str:
    return [
        chest.contents
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
        npc_id = emu_instance.memory.register_arm9.r1
        npc = struct.Struct('>I').pack(npc_id).decode()
        if npc in actors:
            emu_instance.memory.register_arm9.r1 = int.from_bytes(replacement.encode(), 'little')

    emu_instance.memory.register_exec(0x20C3FE8, cancel_spawn)

    yield

    # Clear callback on context manager exit
    emu_instance.memory.register_exec(0x20C3FE8, None)
