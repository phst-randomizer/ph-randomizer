from pathlib import Path

from desmume.emulator import SCREEN_HEIGHT, SCREEN_WIDTH
import pytest

from .conftest import DeSmuMEWrapper
from .desmume_utils import start_first_file


# @pytest.fixture(
#     params=[val for val in ITEM_MEMORY_ADDRESSES.keys()],
#     ids=[f'{hex(val)}-{GD_MODELS[val]}' for val in ITEM_MEMORY_ADDRESSES.keys()],
# )
@pytest.fixture
def minigame_reward_chest_emu(tmp_path: Path, desmume_emulator: DeSmuMEWrapper, request):
    rom_path = str(tmp_path / f'{tmp_path.name}.nds')

    desmume_emulator.open(rom_path)

    return desmume_emulator


def test_minigame_reward_chests(minigame_reward_chest_emu: DeSmuMEWrapper):
    start_first_file(minigame_reward_chest_emu)

    # Skip "arriving in port" cutscene
    minigame_reward_chest_emu.touch_input((SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 1)
    minigame_reward_chest_emu.touch_input((SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 1)

    # Walk left from boat
    minigame_reward_chest_emu.touch_input((0, SCREEN_HEIGHT // 2), 160)

    # Walk up
    minigame_reward_chest_emu.touch_input((SCREEN_WIDTH // 2, 0), 50)

    # Walk to goron
    minigame_reward_chest_emu.touch_input((0, SCREEN_HEIGHT // 2), 150)  # left
    minigame_reward_chest_emu.touch_input((0, SCREEN_HEIGHT), 20)  # left and down
    minigame_reward_chest_emu.touch_input((0, SCREEN_HEIGHT // 2), 20)  # left
    minigame_reward_chest_emu.touch_input((SCREEN_WIDTH // 2, 0), 5)  # up
    minigame_reward_chest_emu.wait(20)

    # Talk to goron
    minigame_reward_chest_emu.touch_input((165, 65), 20)  # touch goron
    minigame_reward_chest_emu.wait(150)
    minigame_reward_chest_emu.touch_input((SCREEN_HEIGHT, SCREEN_WIDTH // 2), 5)  # advance dialog
    minigame_reward_chest_emu.wait(150)
    minigame_reward_chest_emu.touch_input((206, 90), 5)  # click "Yes" to play game

    # advance dialog
    for _ in range(6):
        minigame_reward_chest_emu.wait(150)
        minigame_reward_chest_emu.touch_input((SCREEN_HEIGHT, SCREEN_WIDTH // 2), 5)

    minigame_reward_chest_emu.wait(20)
    minigame_reward_chest_emu.touch_input((206, 90), 5)  # click "Yes" to play game

    # advance dialog
    for _ in range(11):
        minigame_reward_chest_emu.wait(150)
        minigame_reward_chest_emu.touch_input((SCREEN_HEIGHT, SCREEN_WIDTH // 2), 5)

    minigame_reward_chest_emu.wait(300)

    # Start rolling
    for x in range(40):
        minigame_reward_chest_emu.input.touch_set_pos(
            (SCREEN_WIDTH // 2) - x * 2, SCREEN_HEIGHT // 2
        )
        minigame_reward_chest_emu.wait(1)

    minigame_reward_chest_emu.wait(115)
    minigame_reward_chest_emu.input.touch_set_pos(SCREEN_WIDTH // 2, SCREEN_HEIGHT)  # Down
    minigame_reward_chest_emu.wait(80)
    minigame_reward_chest_emu.input.touch_set_pos(SCREEN_WIDTH, SCREEN_HEIGHT // 2)  # Right
    minigame_reward_chest_emu.wait(30)
    minigame_reward_chest_emu.input.touch_set_pos(SCREEN_WIDTH // 2, 0)  # Up
    minigame_reward_chest_emu.wait(40)
    minigame_reward_chest_emu.input.touch_set_pos(SCREEN_WIDTH, SCREEN_HEIGHT // 2)  # Right
    minigame_reward_chest_emu.wait(20)
    minigame_reward_chest_emu.input.touch_set_pos(SCREEN_WIDTH // 2, SCREEN_HEIGHT)  # Down
    minigame_reward_chest_emu.wait(60)
    minigame_reward_chest_emu.input.touch_set_pos(SCREEN_WIDTH, SCREEN_HEIGHT // 2)  # Right
    minigame_reward_chest_emu.wait(30)
    minigame_reward_chest_emu.input.touch_set_pos(SCREEN_WIDTH // 2, SCREEN_HEIGHT)  # Down
    minigame_reward_chest_emu.wait(35)

    minigame_reward_chest_emu.input.touch_set_pos(0, SCREEN_HEIGHT // 2)  # Left
    minigame_reward_chest_emu.wait(30)
    minigame_reward_chest_emu.input.touch_set_pos(SCREEN_WIDTH // 2, SCREEN_HEIGHT)  # Down
    minigame_reward_chest_emu.wait(10)
    minigame_reward_chest_emu.input.touch_set_pos(0, SCREEN_HEIGHT // 2)  # Left
    minigame_reward_chest_emu.wait(50)
    minigame_reward_chest_emu.input.touch_set_pos(SCREEN_WIDTH // 2, SCREEN_HEIGHT)  # Down
    minigame_reward_chest_emu.wait(80)
    minigame_reward_chest_emu.input.touch_set_pos(SCREEN_WIDTH, SCREEN_HEIGHT // 2)  # Right
    minigame_reward_chest_emu.wait(190)
    minigame_reward_chest_emu.input.touch_set_pos(SCREEN_WIDTH // 2, 0)  # Up
    minigame_reward_chest_emu.wait(40)
    minigame_reward_chest_emu.input.touch_set_pos(SCREEN_WIDTH, SCREEN_HEIGHT // 2)  # Right
    minigame_reward_chest_emu.wait(20)
    minigame_reward_chest_emu.input.touch_set_pos(SCREEN_WIDTH // 2, 0)  # Up
    minigame_reward_chest_emu.wait(70)
    minigame_reward_chest_emu.input.touch_set_pos(0, SCREEN_HEIGHT // 2)  # Left
    minigame_reward_chest_emu.wait(75)
    minigame_reward_chest_emu.input.touch_set_pos(SCREEN_WIDTH // 2, SCREEN_HEIGHT)  # Down
    minigame_reward_chest_emu.wait(90)
    minigame_reward_chest_emu.input.touch_set_pos(SCREEN_WIDTH // 2, 0)  # Up
    minigame_reward_chest_emu.wait(55)
    minigame_reward_chest_emu.input.touch_set_pos(0, SCREEN_HEIGHT // 2)  # Left
    minigame_reward_chest_emu.wait(40)

    minigame_reward_chest_emu.input.touch_set_pos(SCREEN_WIDTH // 2, 0)  # Up
    minigame_reward_chest_emu.wait(27)
    minigame_reward_chest_emu.input.touch_set_pos(SCREEN_WIDTH, SCREEN_HEIGHT // 2)  # Right
    minigame_reward_chest_emu.wait(45)
    minigame_reward_chest_emu.input.touch_set_pos(SCREEN_WIDTH // 2, 0)  # Up
    minigame_reward_chest_emu.wait(50)
    minigame_reward_chest_emu.input.touch_set_pos(0, SCREEN_HEIGHT // 2)  # Left
    minigame_reward_chest_emu.wait(35)

    minigame_reward_chest_emu.input.touch_set_pos(SCREEN_WIDTH // 2, SCREEN_HEIGHT)  # Down
    minigame_reward_chest_emu.wait(50)
    minigame_reward_chest_emu.input.touch_set_pos(0, SCREEN_HEIGHT // 2)  # Left
    minigame_reward_chest_emu.wait(40)
    minigame_reward_chest_emu.input.touch_set_pos(SCREEN_WIDTH // 2, SCREEN_HEIGHT)  # Down
    minigame_reward_chest_emu.wait(40)
    minigame_reward_chest_emu.input.touch_set_pos(SCREEN_WIDTH, SCREEN_HEIGHT // 2)  # Right
    minigame_reward_chest_emu.wait(30)
    minigame_reward_chest_emu.input.touch_set_pos(SCREEN_WIDTH // 2, 0)  # Up
    minigame_reward_chest_emu.wait(30)
    minigame_reward_chest_emu.input.touch_set_pos(0, SCREEN_HEIGHT // 2)  # Left
    minigame_reward_chest_emu.wait(30)
    minigame_reward_chest_emu.input.touch_set_pos(SCREEN_WIDTH, SCREEN_HEIGHT // 2)  # Right
    minigame_reward_chest_emu.wait(50)
    minigame_reward_chest_emu.input.touch_set_pos(SCREEN_WIDTH // 2, 0)  # Up
    minigame_reward_chest_emu.wait(40)
    minigame_reward_chest_emu.input.touch_set_pos(0, SCREEN_HEIGHT // 2)  # Left
    minigame_reward_chest_emu.wait(40)
    minigame_reward_chest_emu.input.touch_set_pos(SCREEN_WIDTH // 2, SCREEN_HEIGHT)  # Down

    # Wait for door to open
    minigame_reward_chest_emu.wait(280)

    minigame_reward_chest_emu.input.touch_set_pos(0, SCREEN_HEIGHT // 2)  # Left
    minigame_reward_chest_emu.wait(50)
    minigame_reward_chest_emu.input.touch_set_pos(SCREEN_WIDTH // 2, SCREEN_HEIGHT)  # Down
    minigame_reward_chest_emu.wait(50)
    minigame_reward_chest_emu.input.touch_set_pos(SCREEN_WIDTH, SCREEN_HEIGHT // 2)  # Right
    minigame_reward_chest_emu.wait(60)
    minigame_reward_chest_emu.input.touch_set_pos(SCREEN_WIDTH // 2, 0)  # Up
    minigame_reward_chest_emu.wait(40)
    minigame_reward_chest_emu.input.touch_set_pos(0, SCREEN_HEIGHT // 2)  # Left
    minigame_reward_chest_emu.wait(200)
    minigame_reward_chest_emu.input.touch_release()  # End of race

    minigame_reward_chest_emu.wait(80)
    minigame_reward_chest_emu.touch_input((SCREEN_HEIGHT, SCREEN_WIDTH // 2), 5)  # advance dialog

    minigame_reward_chest_emu.wait(200)
    minigame_reward_chest_emu.touch_input((SCREEN_HEIGHT, SCREEN_WIDTH // 2), 5)  # advance dialog
    minigame_reward_chest_emu.wait(150)
    minigame_reward_chest_emu.touch_input((SCREEN_HEIGHT, SCREEN_WIDTH // 2), 5)  # advance dialog
    minigame_reward_chest_emu.wait(50)

    minigame_reward_chest_emu.touch_input((SCREEN_WIDTH // 2, SCREEN_HEIGHT), 15)  # Down
    minigame_reward_chest_emu.touch_input((SCREEN_WIDTH, SCREEN_HEIGHT // 2), 30)  # Right

    minigame_reward_chest_emu.wait(10)
    minigame_reward_chest_emu.touch_input((107, 67), 2)  # Open chest

    minigame_reward_chest_emu.wait(400)
