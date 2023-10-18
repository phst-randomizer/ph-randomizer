from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from .aux_models import DigSpot, SalvageTreasure, Shop, Tree

if TYPE_CHECKING:
    from ph_rando.shuffler._shuffler import Shuffler


def dig_spot_locations(
    value: Literal['vanilla', 'non_required_items_only', 'fully_randomized'],
    shuffler: Shuffler,
) -> None:
    match value:
        case 'vanilla':
            for area in shuffler.aux_data.areas:
                for room in area.rooms:
                    for chest in filter(
                        lambda chest: isinstance(chest, DigSpot),
                        room.chests,
                    ):
                        shuffler.exclude_check(chest)
        case 'non_required_items_only':
            raise NotImplementedError()
        case 'fully_randomized':
            pass  # do nothing
        case other:
            raise Exception(f'{other}: invalid value for dig_spots setting')


def salvage_arm_treasures(
    value: Literal['vanilla', 'non_required_items_only', 'fully_randomized'],
    shuffler: Shuffler,
) -> None:
    match value:
        case 'vanilla':
            for area in shuffler.aux_data.areas:
                for room in area.rooms:
                    for chest in filter(
                        lambda chest: isinstance(chest, SalvageTreasure),
                        room.chests,
                    ):
                        shuffler.exclude_check(chest)
        case 'non_required_items_only':
            raise NotImplementedError()
        case 'fully_randomized':
            pass  # do nothing
        case other:
            raise Exception(f'{other}: invalid value for salvage_arm_treasures setting')


def shop_items(
    value: Literal['vanilla', 'non_required_items_only', 'fully_randomized'],
    shuffler: Shuffler,
) -> None:
    match value:
        case 'vanilla':
            for area in shuffler.aux_data.areas:
                for room in area.rooms:
                    for chest in filter(
                        lambda chest: isinstance(chest, Shop),
                        room.chests,
                    ):
                        shuffler.exclude_check(chest)
        case 'non_required_items_only':
            raise NotImplementedError()
        case 'fully_randomized':
            pass  # do nothing
        case other:
            raise Exception(f'{other}: invalid value for shop_items setting')


def tree_drops(
    value: Literal['vanilla', 'non_required_items_only', 'fully_randomized'],
    shuffler: Shuffler,
) -> None:
    match value:
        case 'vanilla':
            for area in shuffler.aux_data.areas:
                for room in area.rooms:
                    for chest in filter(
                        lambda chest: isinstance(chest, Tree),
                        room.chests,
                    ):
                        shuffler.exclude_check(chest)
        case 'non_required_items_only':
            raise NotImplementedError()
        case 'fully_randomized':
            pass  # do nothing
        case other:
            raise Exception(f'{other}: invalid value for shop_items setting')


def dungeon_rewards(
    value: Literal['shuffle_amongst_themselves', 'shuffle_with_rest_of_items', 'vanilla'],
    shuffler: Shuffler,
) -> None:
    from ._shuffler import DUNGEON_REWARD_CHECKS

    match value:
        case 'vanilla':
            for area in shuffler.aux_data.areas:
                for room in area.rooms:
                    for chest in filter(
                        lambda chest: '.'.join([area.name, room.name, chest.name])
                        in DUNGEON_REWARD_CHECKS,
                        room.chests,
                    ):
                        shuffler.exclude_check(chest)
        case 'shuffle_amongst_themselves':
            raise NotImplementedError()
        case 'shuffle_with_rest_of_items':
            raise NotImplementedError()
        case other:
            raise Exception(f'{other}: invalid value for shop_items setting')
