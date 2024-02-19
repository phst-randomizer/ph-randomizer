from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Literal, TypeAlias, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

if TYPE_CHECKING:
    from ph_rando.shuffler._shuffler import Node


class Item(BaseModel):
    name: str
    states: set[str] = Field(
        set(),
        description='State(s) that should be gained upon obtaining this item.',
    )

    def __repr__(self) -> str:
        s = self.name
        if self.states:
            s += f' ({self.states})'
        return s

    @field_validator('name')
    def check_if_item_is_valid(cls, v: str) -> str:
        """Ensure that this check's `contents` is set to a valid item."""
        from ph_rando.patcher._items import ITEMS

        assert v in ITEMS
        return v


class BaseCheck(BaseModel):
    name: str = Field(..., description='The name of the item check')
    contents: Item = Field(..., description='The item that this check contains')
    # TODO: make this field mandatory when all checks have this
    display_name: str | None = Field(
        None, description='Human-readable name used in spoiler logs, etc.'
    )

    def __hash__(self) -> int:
        return id(self)


class Chest(BaseCheck):
    type: Literal['chest']
    zmb_file_path: str = Field(
        ..., description='File path to the zmb the chest is on', min_length=1
    )
    zmb_mapobject_index: int = Field(..., description='Index of the chest in the defined zmb file')


class Mail(BaseCheck):
    type: Literal['mail']
    # TODO: what info is needed for patcher?


class Tree(BaseCheck):
    type: Literal['tree']
    zmb_file_path: str = Field(..., description='File path to the zmb the tree is on', min_length=1)
    zmb_mapobject_index: int = Field(
        ..., description='Index of the tree object in the defined zmb file'
    )


class Event(BaseCheck):
    type: Literal['event']
    bmg_file_path: str = Field(
        ..., description='File path to the bmg the instruction is on', min_length=1
    )
    bmg_instruction_index: int = Field(
        ..., description='Index of the instruction in the defined bmg file'
    )


class Shop(BaseCheck):
    type: Literal['shop']
    overlay: int = Field(..., description='The code overlay this shop item is on')
    overlay_offset: str = Field(
        ..., description='Hex offset from overlay to the shop item', min_length=1
    )


class Freestanding(BaseCheck):
    type: Literal['freestanding']
    # TODO: add other fields that are needed


class OnEnemy(BaseCheck):
    type: Literal['on_enemy']
    # TODO: what other fields are needed? Can this be replaced by Freestanding?


class SalvageTreasure(BaseCheck):
    type: Literal['salvage_treasure']
    zmb_file_path: str = Field(
        ..., description='File path to the zmb the chest is on', min_length=1
    )
    zmb_actor_index: int = Field(
        ..., description='Index of the chest in the NPCA section of the zmb file'
    )


class DigSpot(BaseCheck):
    type: Literal['dig_spot']
    zmb_file_path: str = Field(
        ..., description='File path to the zmb the chest is on', min_length=1
    )
    zmb_actor_index: int = Field(
        ..., description='Index of the chest in the NPCA section of the zmb file'
    )


class MinigameRewardChest(BaseCheck):
    type: Literal['minigame_reward_chest']
    # TODO: what other fields are needed?


class BossReward(BaseCheck):
    type: Literal['boss_reward']
    # TODO: what other fields are needed? Is this just a special case of "Event"?


class SpiritUpgrade(BaseCheck):
    type: Literal['spirit_upgrade']
    # TODO: what other fields are needed? Is this just a special case of another item type?


Check: TypeAlias = (
    Chest
    | Event
    | Shop
    | Tree
    | Freestanding
    | OnEnemy
    | SalvageTreasure
    | DigSpot
    | MinigameRewardChest
    | Mail
    | BossReward
    | SpiritUpgrade
)


def validate_check_type() -> None:
    """
    Ensure that the `Check` type alias includes all of the subclasses of `BaseCheck`.
    """

    def get_all_subclasses(cls: type[BaseCheck]) -> list[type[BaseCheck]]:
        """Recursively fetch all descendents of a class."""
        all_subclasses: list[type[BaseCheck]] = []
        for subclass in cls.__subclasses__():
            all_subclasses.extend([subclass] + get_all_subclasses(subclass))
        return all_subclasses

    assert Check == Union[*[subclass for subclass in get_all_subclasses(BaseCheck)]]


validate_check_type()


class Exit(BaseModel):
    name: str = Field(..., description='The name of this exit', min_length=1)
    entrance: str = Field(
        ..., description='The `entrance` or `door` where this exit leads.', min_length=1
    )


class Enemy(BaseModel):
    name: str = Field(
        ..., description='The name of the referenced `enemy` in the .logic file.', min_length=1
    )
    type: str = Field(
        ...,
        description='The type of the enemy. Should map to an entry in `shuffler/enemies.json`.',
        min_length=1,
    )

    @field_validator('type')
    def validate_enemy_name(cls, v: str) -> str:
        assert v in json.loads(
            (Path(__file__).parent / 'enemies.json').read_text()
        ), f'{v} is not a valid enemy type'
        return v


class Room(BaseModel):
    model_config = ConfigDict(extra='allow')

    name: str = Field(..., description='The name of the room', min_length=1)
    chests: list[Annotated[Check, Field(discriminator='type')]] = Field(
        [],
        description='Item checks that can be made in this room',
    )
    exits: list[Exit] = Field(
        [],
        description='All `exits` in this room that lead to an `entrance` in another room',
    )
    enemies: list[Enemy] = Field(
        [],
        description='All enemies in this room',
    )

    @field_validator('chests', 'exits', 'enemies')
    def name_uniqueness_check(cls, v: list[Check | Exit | Enemy]) -> list[Check | Exit | Enemy]:
        names_set = {item.name for item in v}
        if len(names_set) != len(v):
            from collections import defaultdict

            name_buckets: defaultdict[str, int] = defaultdict(int)
            for item in v:
                name_buckets[item.name] += 1
                if name_buckets[item.name] > 1:
                    raise ValueError(f'{type(item)} {item.name}: names must be unique!')
        return v

    @field_validator('exits')
    def entrance_uniqueness_check(cls, v: list[Exit]) -> list[Exit]:
        entrances_set = {item.entrance for item in v}
        if len(entrances_set) != len(v):
            from collections import defaultdict

            entrance_buckets: defaultdict[str, int] = defaultdict(int)
            for item in v:
                entrance_buckets[item.entrance] += 1
                if entrance_buckets[item.entrance] > 1:
                    raise ValueError(
                        f'Exit {item.name} contains more than one entrance {item.entrance}'
                    )
        return v

    # Note: pydantic ignores instance variables beginning with an underscore,
    # so we use that here. Nodes are not parsed by pydantic; they are populated
    # when the .logic files are parsed, i.e. after the initial aux data parsing.
    _nodes: list[Node]

    @property
    def nodes(self) -> list[Node]:
        if not hasattr(self, '_nodes'):
            self._nodes = []
        return self._nodes


class Area(BaseModel):
    name: str = Field(..., description='The name of the area', min_length=1)
    rooms: list[Room] = Field(
        ...,
        description='All of the rooms inside this area',
        min_length=1,
    )


if __name__ == '__main__':
    json_schema = json.dumps(Area.model_json_schema(), indent=2)
    with open(Path(__file__).parent / 'aux_schema.json', 'w') as fd:
        fd.write(json_schema + '\n')
