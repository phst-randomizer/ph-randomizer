from desmume.controls import keymask
from desmume.emulator import SCREEN_HEIGHT, SCREEN_WIDTH, DeSmuME, DeSmuME_SDL_Window


class DesmumeEmulator:
    def __init__(self, py_desmume_instance: tuple[DeSmuME, DeSmuME_SDL_Window]):
        self.emu = py_desmume_instance[0]
        self.window = py_desmume_instance[1]

    def open_rom(self, rom_path: str):
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


def start_first_file(desmume_emulator: DesmumeEmulator):
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


def get_current_rupee_count(desmume: DesmumeEmulator):
    return int.from_bytes(desmume.emu.memory.unsigned[0x021BA4FE : 0x021BA4FE + 2], "little")


# Screen coordinates for each item when the "Items" menu is open
ITEMS_MENU_COORDINATES = {"shovel": (225, 175)}


def open_items_menu(desmume: DesmumeEmulator):
    desmume.touch_input((SCREEN_WIDTH - 5, SCREEN_HEIGHT - 5), 5)
    desmume.wait(20)


def select_item_from_items_menu(desmume: DesmumeEmulator, item: str):
    desmume.touch_input(ITEMS_MENU_COORDINATES[item], 5)
    desmume.wait(20)


def equip_item(desmume: DesmumeEmulator, item: str):
    open_items_menu(desmume)
    select_item_from_items_menu(desmume, item)


def use_equipped_item(desmume: DesmumeEmulator):
    desmume.touch_input((SCREEN_WIDTH, 0), 5)
    desmume.wait(20)
