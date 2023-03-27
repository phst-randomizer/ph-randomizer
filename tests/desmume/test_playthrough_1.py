from pathlib import Path

from desmume.emulator import SCREEN_HEIGHT, SCREEN_WIDTH

from ph_rando.common import ShufflerAuxData

from .conftest import DeSmuMEWrapper
from .desmume_utils import (
    assert_item_is_picked_up,
    get_check_contents,
    prevent_actor_spawn,
    start_first_file,
)

save_state = Path(__file__).parent / 'test_state.dsv'


def test_mercay_1(base_rom_emu: DeSmuMEWrapper, aux_data: ShufflerAuxData):
    start_first_file(base_rom_emu)

    # Enter oshus's house
    base_rom_emu.wait(1)
    base_rom_emu.touch_input((int(SCREEN_WIDTH * (3 / 4)), 0), 200)
    base_rom_emu.wait(1)
    base_rom_emu.touch_input((SCREEN_WIDTH, SCREEN_HEIGHT // 2), 50)
    base_rom_emu.wait(1)
    base_rom_emu.touch_input((SCREEN_WIDTH // 2, 0), 60)
    base_rom_emu.touch_input(((SCREEN_WIDTH // 2) - 20, 0), 100)
    base_rom_emu.wait(50)

    # Approach oshus
    base_rom_emu.touch_input((SCREEN_WIDTH // 2, 0), 120)
    base_rom_emu.wait(20)
    base_rom_emu.input.touch_set_pos(125, 80)
    base_rom_emu.wait(1)
    base_rom_emu.input.touch_release()

    # Talk to oshus
    base_rom_emu.wait(150)
    base_rom_emu.touch_input((0, 0), 2)
    base_rom_emu.wait(150)
    base_rom_emu.touch_input((0, 0), 2)
    base_rom_emu.wait(150)
    base_rom_emu.touch_input((0, 0), 2)
    base_rom_emu.wait(150)

    # Leave Oshus's house
    base_rom_emu.touch_input((SCREEN_WIDTH // 2, SCREEN_HEIGHT), 120)
    base_rom_emu.wait(150)

    # Walk over to Mercay NPC with rocks in his yard
    base_rom_emu.touch_input((SCREEN_WIDTH // 2, SCREEN_HEIGHT), 35)
    base_rom_emu.wait(1)
    base_rom_emu.touch_input((0, (SCREEN_HEIGHT // 2) - 20), 250)
    base_rom_emu.wait(20)

    # Pickup and throw each rock in Mercay NPC's yard
    base_rom_emu.touch_input((134, 121), 2)
    base_rom_emu.wait(60)
    base_rom_emu.touch_input((134, 121), 2)
    base_rom_emu.wait(60)
    base_rom_emu.touch_input((53, 87), 2)
    base_rom_emu.wait(60)
    base_rom_emu.touch_input((53, 87), 2)
    base_rom_emu.wait(60)
    base_rom_emu.touch_input((163, 40), 2)
    base_rom_emu.wait(60)
    base_rom_emu.touch_input((163, 40), 2)
    base_rom_emu.wait(60)
    base_rom_emu.touch_input((128, 34), 2)
    base_rom_emu.wait(60)
    base_rom_emu.touch_input((128, 134), 2)
    base_rom_emu.wait(60)

    # Talk to Mercay NPC
    base_rom_emu.touch_input((SCREEN_WIDTH, SCREEN_HEIGHT // 2), 20)
    base_rom_emu.wait(10)

    item = get_check_contents(aux_data.areas.values(), 'Mercay', 'OutsideOshus', 'PickUpRock')
    with assert_item_is_picked_up(item, base_rom_emu):
        # Click through his dialog
        base_rom_emu.touch_input((232, 64), 2)
        base_rom_emu.wait(150)
        base_rom_emu.touch_input((0, 0), 2)
        base_rom_emu.wait(150)
        base_rom_emu.touch_input((0, 0), 2)
        base_rom_emu.wait(150)
        base_rom_emu.touch_input((0, 0), 2)
        base_rom_emu.wait(150)
        base_rom_emu.touch_input((0, 0), 2)
        base_rom_emu.wait(150)
        base_rom_emu.touch_input((0, 0), 2)
        base_rom_emu.wait(250)

        base_rom_emu.touch_input((0, 0), 2)
        base_rom_emu.wait(150)
        base_rom_emu.touch_input((0, 0), 2)
        base_rom_emu.wait(250)
        base_rom_emu.touch_input((0, 0), 2)
        base_rom_emu.wait(150)

    # Click through the rest of his dialogue
    base_rom_emu.touch_input((0, 0), 2)
    base_rom_emu.wait(150)
    base_rom_emu.touch_input((0, 0), 2)
    base_rom_emu.wait(150)
    base_rom_emu.touch_input((0, 0), 2)
    base_rom_emu.wait(200)
    base_rom_emu.touch_input((0, 0), 2)
    base_rom_emu.wait(150)
    base_rom_emu.touch_input((0, 0), 2)
    base_rom_emu.wait(150)
    base_rom_emu.touch_input((0, 0), 2)

    # Walk up to chu chu area
    base_rom_emu.wait(20)
    base_rom_emu.touch_input((SCREEN_WIDTH, SCREEN_HEIGHT // 2), 70)
    base_rom_emu.savestate.save_file(str(save_state))
    base_rom_emu.wait(10)
    with prevent_actor_spawn(base_rom_emu, 'CHUC'):
        base_rom_emu.touch_input((SCREEN_WIDTH // 2, 0), 120)
        base_rom_emu.wait(100)

    base_rom_emu.touch_input((SCREEN_WIDTH // 4, 0), 140)
    base_rom_emu.touch_input((SCREEN_WIDTH, 0), 50)
    base_rom_emu.touch_input((SCREEN_WIDTH, SCREEN_HEIGHT), 50)
    base_rom_emu.wait(40)
