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
            raise NotImplementedError()
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
            raise NotImplementedError()
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
            raise NotImplementedError()
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
            raise NotImplementedError()
        case other:
            raise Exception(f'{other}: invalid value for shop_items setting')
