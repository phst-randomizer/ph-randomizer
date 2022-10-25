from pathlib import Path

from desmume.emulator import SCREEN_HEIGHT, SCREEN_WIDTH
from ndspy.rom import NintendoDSRom
import pytesseract
import pytest

from ph_rando.common import ShufflerAuxData
from ph_rando.patcher._items import ITEMS_REVERSED
from ph_rando.patcher._util import GD_MODELS, _patch_minigame_items
from ph_rando.shuffler.aux_models import Item, MinigameRewardChest
from tests.desmume.conftest import GOT_ITEM_TEXT, ITEM_MEMORY_OFFSETS
from tests.desmume.emulator_utils import assert_item_is_picked_up

from .emulator_utils import AbstractEmulatorWrapper, start_first_file
from .melonds import MelonDSWrapper


@pytest.fixture
def minigame_reward_chest_emu(
    rom_path: Path,
    emulator: AbstractEmulatorWrapper,
    request,
    aux_data: ShufflerAuxData,
):
    if isinstance(emulator, MelonDSWrapper):
        pytest.skip('MelonDS not supported for this test yet')

    rom = NintendoDSRom.fromFile(rom_path)
    chests = [
        chest
        for area in aux_data.areas
        for room in area.rooms
        for chest in room.chests
        if type(chest) is MinigameRewardChest
    ]
    for chest in chests:
        chest.contents = Item(name=ITEMS_REVERSED[request.param], states=set())

    _patch_minigame_items(aux_data.areas, rom)

    rom.saveToFile(rom_path)

    emulator.open(str(rom_path))

    return emulator


@pytest.mark.parametrize(
    'minigame_reward_chest_emu',
    [val for val in ITEM_MEMORY_OFFSETS.keys()],
    ids=[f'{hex(val)}-{GD_MODELS[val]}' for val in ITEM_MEMORY_OFFSETS.keys()],
    indirect=['minigame_reward_chest_emu'],
)
def test_minigame_reward_chests(minigame_reward_chest_emu: AbstractEmulatorWrapper, request):
    item_id: int = request.node.callspec.params['minigame_reward_chest_emu']

    start_first_file(minigame_reward_chest_emu)

    # Skip "arriving in port" cutscene
    minigame_reward_chest_emu.touch_set_and_release((SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 1)

    # Walk left from boat
    minigame_reward_chest_emu.touch_set_and_release((0, SCREEN_HEIGHT // 2), 160)

    # Walk up
    minigame_reward_chest_emu.touch_set_and_release((SCREEN_WIDTH // 2, 0), 50)

    # Walk to goron
    minigame_reward_chest_emu.touch_set_and_release((0, SCREEN_HEIGHT // 2), 150)  # left
    minigame_reward_chest_emu.touch_set_and_release((0, SCREEN_HEIGHT), 20)  # left and down
    minigame_reward_chest_emu.touch_set_and_release((0, SCREEN_HEIGHT // 2), 20)  # left
    minigame_reward_chest_emu.touch_set_and_release((SCREEN_WIDTH // 2, 0), 5)  # up
    minigame_reward_chest_emu.wait(20)

    # Talk to goron
    minigame_reward_chest_emu.touch_set_and_release((165, 65), 5)  # touch goron
    minigame_reward_chest_emu.wait(165)
    minigame_reward_chest_emu.touch_set_and_release(
        (SCREEN_HEIGHT, SCREEN_WIDTH // 2), 5
    )  # advance dialog
    minigame_reward_chest_emu.wait(130)
    minigame_reward_chest_emu.touch_set_and_release((206, 90), 5)  # click "Yes" to play game

    # advance dialog
    for _ in range(6):
        minigame_reward_chest_emu.wait(150)
        minigame_reward_chest_emu.touch_set_and_release((SCREEN_HEIGHT, SCREEN_WIDTH // 2), 5)

    minigame_reward_chest_emu.wait(20)
    minigame_reward_chest_emu.touch_set_and_release((206, 90), 5)  # click "Yes" to play game

    # advance dialog
    for _ in range(11):
        minigame_reward_chest_emu.wait(150)
        minigame_reward_chest_emu.touch_set_and_release((SCREEN_HEIGHT, SCREEN_WIDTH // 2), 5)

    minigame_reward_chest_emu.wait(300)

    # Start rolling
    for x in range(40):
        minigame_reward_chest_emu.touch_set((SCREEN_WIDTH // 2) - x * 2, SCREEN_HEIGHT // 2)
        minigame_reward_chest_emu.wait(1)

    minigame_reward_chest_emu.wait(115)
    minigame_reward_chest_emu.touch_set(SCREEN_WIDTH // 2, SCREEN_HEIGHT)  # Down
    minigame_reward_chest_emu.wait(80)
    minigame_reward_chest_emu.touch_set(SCREEN_WIDTH, SCREEN_HEIGHT // 2)  # Right
    minigame_reward_chest_emu.wait(30)
    minigame_reward_chest_emu.touch_set(SCREEN_WIDTH // 2, 0)  # Up
    minigame_reward_chest_emu.wait(40)
    minigame_reward_chest_emu.touch_set(SCREEN_WIDTH, SCREEN_HEIGHT // 2)  # Right
    minigame_reward_chest_emu.wait(20)
    minigame_reward_chest_emu.touch_set(SCREEN_WIDTH // 2, SCREEN_HEIGHT)  # Down
    minigame_reward_chest_emu.wait(60)
    minigame_reward_chest_emu.touch_set(SCREEN_WIDTH, SCREEN_HEIGHT // 2)  # Right
    minigame_reward_chest_emu.wait(30)
    minigame_reward_chest_emu.touch_set(SCREEN_WIDTH // 2, SCREEN_HEIGHT)  # Down
    minigame_reward_chest_emu.wait(35)

    minigame_reward_chest_emu.touch_set(0, SCREEN_HEIGHT // 2)  # Left
    minigame_reward_chest_emu.wait(30)
    minigame_reward_chest_emu.touch_set(SCREEN_WIDTH // 2, SCREEN_HEIGHT)  # Down
    minigame_reward_chest_emu.wait(10)
    minigame_reward_chest_emu.touch_set(0, SCREEN_HEIGHT // 2)  # Left
    minigame_reward_chest_emu.wait(50)
    minigame_reward_chest_emu.touch_set(SCREEN_WIDTH // 2, SCREEN_HEIGHT)  # Down
    minigame_reward_chest_emu.wait(80)
    minigame_reward_chest_emu.touch_set(SCREEN_WIDTH, SCREEN_HEIGHT // 2)  # Right
    minigame_reward_chest_emu.wait(190)
    minigame_reward_chest_emu.touch_set(SCREEN_WIDTH // 2, 0)  # Up
    minigame_reward_chest_emu.wait(40)
    minigame_reward_chest_emu.touch_set(SCREEN_WIDTH, SCREEN_HEIGHT // 2)  # Right
    minigame_reward_chest_emu.wait(20)
    minigame_reward_chest_emu.touch_set(SCREEN_WIDTH // 2, 0)  # Up
    minigame_reward_chest_emu.wait(70)
    minigame_reward_chest_emu.touch_set(0, SCREEN_HEIGHT // 2)  # Left
    minigame_reward_chest_emu.wait(70)
    minigame_reward_chest_emu.touch_set(SCREEN_WIDTH // 2, SCREEN_HEIGHT)  # Down
    minigame_reward_chest_emu.wait(80)
    minigame_reward_chest_emu.touch_set(SCREEN_WIDTH // 2, 0)  # Up
    minigame_reward_chest_emu.wait(55)
    minigame_reward_chest_emu.touch_set(0, SCREEN_HEIGHT // 2)  # Left
    minigame_reward_chest_emu.wait(40)
    minigame_reward_chest_emu.touch_set(SCREEN_WIDTH // 2, 0)  # Up

    minigame_reward_chest_emu.wait(23)
    minigame_reward_chest_emu.touch_set(SCREEN_WIDTH, SCREEN_HEIGHT // 2 + 10)  # Right
    minigame_reward_chest_emu.wait(45)

    minigame_reward_chest_emu.touch_set(SCREEN_WIDTH // 2, 0)  # Up
    minigame_reward_chest_emu.wait(40)
    minigame_reward_chest_emu.touch_set(0, SCREEN_HEIGHT // 2)  # Left
    minigame_reward_chest_emu.wait(35)

    minigame_reward_chest_emu.touch_set(SCREEN_WIDTH, SCREEN_HEIGHT // 2)  # Right
    minigame_reward_chest_emu.wait(50)

    minigame_reward_chest_emu.touch_set(0, SCREEN_HEIGHT // 2)  # Left
    minigame_reward_chest_emu.wait(60)
    minigame_reward_chest_emu.touch_release()

    minigame_reward_chest_emu.touch_set(SCREEN_WIDTH, SCREEN_HEIGHT // 2)  # Right
    minigame_reward_chest_emu.wait(100)

    minigame_reward_chest_emu.touch_set(0, SCREEN_HEIGHT // 2)  # Left
    minigame_reward_chest_emu.wait(40)
    minigame_reward_chest_emu.touch_set(SCREEN_WIDTH // 2, SCREEN_HEIGHT)  # Down

    # # Wait for door to open
    minigame_reward_chest_emu.wait(260)

    minigame_reward_chest_emu.touch_set(0, SCREEN_HEIGHT // 2)  # Left
    minigame_reward_chest_emu.wait(50)
    minigame_reward_chest_emu.touch_set(SCREEN_WIDTH // 2, SCREEN_HEIGHT)  # Down
    minigame_reward_chest_emu.wait(50)
    minigame_reward_chest_emu.touch_set(SCREEN_WIDTH, SCREEN_HEIGHT // 2)  # Right
    minigame_reward_chest_emu.wait(60)
    minigame_reward_chest_emu.touch_set(SCREEN_WIDTH // 2, 0)  # Up
    minigame_reward_chest_emu.wait(40)
    minigame_reward_chest_emu.touch_set(0, SCREEN_HEIGHT // 2)  # Left
    minigame_reward_chest_emu.wait(200)
    minigame_reward_chest_emu.touch_release()  # End of race

    minigame_reward_chest_emu.wait(80)
    minigame_reward_chest_emu.touch_set_and_release(
        (SCREEN_HEIGHT, SCREEN_WIDTH // 2), 5
    )  # advance dialog

    minigame_reward_chest_emu.wait(200)
    minigame_reward_chest_emu.touch_set_and_release(
        (SCREEN_HEIGHT, SCREEN_WIDTH // 2), 5
    )  # advance dialog
    minigame_reward_chest_emu.wait(150)
    minigame_reward_chest_emu.touch_set_and_release(
        (SCREEN_HEIGHT, SCREEN_WIDTH // 2), 5
    )  # advance dialog
    minigame_reward_chest_emu.wait(50)

    minigame_reward_chest_emu.touch_set_and_release((SCREEN_WIDTH // 2, SCREEN_HEIGHT), 15)  # Down
    minigame_reward_chest_emu.touch_set_and_release((SCREEN_WIDTH, SCREEN_HEIGHT // 2), 30)  # Right

    with assert_item_is_picked_up(item_id, minigame_reward_chest_emu):
        minigame_reward_chest_emu.wait(10)
        minigame_reward_chest_emu.touch_set_and_release((107, 67), 2)  # Open chest

        # Wait for "Got item" text
        minigame_reward_chest_emu.wait(800)

        # Check if the "got item" text is correct
        if hasattr(minigame_reward_chest_emu, 'screenshot') and item_id in GOT_ITEM_TEXT:
            ocr_text: str = pytesseract.image_to_string(
                minigame_reward_chest_emu.screenshot().crop((24, 325, 231, 384))
            ).replace('\u2019', "'")
            assert GOT_ITEM_TEXT[item_id] in ocr_text

        minigame_reward_chest_emu.touch_set_and_release((0, 0), 2)
        minigame_reward_chest_emu.wait(200)
        minigame_reward_chest_emu.touch_set_and_release((0, 0), 2)
        minigame_reward_chest_emu.wait(100)
        minigame_reward_chest_emu.touch_set_and_release((0, 0), 2)
        minigame_reward_chest_emu.wait(100)
