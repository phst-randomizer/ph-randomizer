import os
from pathlib import Path
from typing import TypeAlias, Union

from pydantic import BaseModel, Field, validator

from shuffler._parser import Descriptor, parse

AUX_DATA_DIRECTORY = Path(os.environ.get('AUX_DATA_DIRECTORY', Path(__file__).parent / 'auxiliary'))
LOGIC_DATA_DIRECTORY = Path(os.environ.get('LOGIC_DATA_DIRECTORY', Path(__file__).parent / 'logic'))


class BaseCheck(BaseModel):
    name: str = Field(..., description='The name of the item check')
    contents: str = Field(..., description='The item that this check contains')

    @validator('contents')
    def check_if_item_is_valid(cls, v: str) -> str:
        """
        Ensure that this check's `contents` is set to a valid item.

        It'd be nice to have this be a JSON-Schema level check instead of a pydantic validator,
        but to do that, we need to dynamically generate an `Enum` with all possible item values
        using the ITEMS dict in patcher._items.py. As part of that, we would want to use pydantic's
        `use_enum_values` setting for the model, but mypy doesn't support it currently:
        https://github.com/pydantic/pydantic/issues/3809 and reports type errors all over the
        place if it's used. If this is ever fixed, it should be changed.
        """
        from patcher._items import ITEMS

        # TODO: Use the following assertion instead once all aux data chest contents is complete.
        # assert v in ITEMS
        assert v in ITEMS or not v or v.lower() == 'todo', f'Item "{v}" not valid.'

        return v


class Chest(BaseCheck):
    type = Field('chest', const=True)
    zmb_file_path: str = Field(..., description='File path to the zmb the chest is on')
    zmb_mapobject_index: int = Field(..., description='Index of the chest in the defined zmb file')


class Tree(Chest):
    type = Field('tree', const=True)


class Event(BaseCheck):
    type = Field('event', const=True)
    bmg_file_path: str = Field(..., description='File path to the bmg the instruction is on')
    bmg_instruction_index: int = Field(
        ..., description='Index of the instruction in the defined bmg file'
    )


class IslandShop(BaseCheck):
    type = Field('island_shop', const=True)
    overlay: int = Field(..., description='The code overlay this shop item is on')
    overlay_offset: str = Field(..., description='Hex offset from overlay to the shop item')


class Freestanding(BaseCheck):
    type = Field('freestanding', const=True)
    # TODO: add other fields that are needed


class OnEnemy(BaseCheck):
    type = Field('on_enemy', const=True)
    # TODO: what other fields are needed? Can this be replaced by Freestanding?


class SalvageTreasure(BaseCheck):
    type = Field('salvage_treasure', const=True)
    zmb_file_path: str = Field(..., description='File path to the zmb the chest is on')
    zmb_actor_index: int = Field(
        ..., description='Index of the chest in the NPCA section of the zmb file'
    )


class DigSpot(SalvageTreasure):
    type = Field('dig_spot', const=True)


Check: TypeAlias = (
    Chest | Event | IslandShop | Tree | Freestanding | OnEnemy | SalvageTreasure | DigSpot
)


def validate_check_type():
    """
    Ensure that the `Check` type alias includes all of the subclasses of `BaseCheck`.
    """

    def get_all_subclasses(cls):
        """Recursively fetch all descendents of a class."""
        all_subclasses = []
        for subclass in cls.__subclasses__():
            all_subclasses.extend([subclass] + get_all_subclasses(subclass))
        return all_subclasses

    assert Check == Union[*[subclass for subclass in get_all_subclasses(BaseCheck)]]


validate_check_type()


class Door(BaseModel):
    name: str = Field(..., description='The name of this exit')
    link: str = Field(..., description='The `entrance` or `door` where this exit leads.')


class Room(BaseModel):
    name: str = Field(..., description='The name of the room')
    chests: list[Check] = Field(
        [],
        description='Item checks that can be made in this room',
        unique_items=True,
    )
    doors: list[Door] = Field(
        ...,
        description='All doors in this room that lead to a different room or area',
        min_items=1,
        unique_items=True,
    )


class Area(BaseModel):
    name: str = Field(..., description='The name of the area')
    rooms: list[Room] = Field(
        ..., description='All of the rooms inside this area', min_items=1, unique_items=True
    )

    @validator('rooms')
    def check_if_doors_are_consistent_between_aux_data_and_logic(
        cls, v: list[Room], values
    ) -> list[Room]:  # noqa: N805
        """Check that all doors/exits in the aux data are also in the logic (and vice-versa)."""
        nodes, _ = parse(LOGIC_DATA_DIRECTORY)
        for room in v:
            # Get all doors in the logic
            logic_doors = set()
            for node in nodes:
                if node.area != values['name'] or node.room != room.name:
                    continue
                for contents in node.contents:
                    if contents.type in (Descriptor.DOOR.value, Descriptor.EXIT.value):
                        logic_doors.add(contents.data)

            # Get all doors in the aux data
            aux_data_doors = {door.name for door in room.doors}

            # Make sure they are the same.
            # If not, display the differences.
            assert logic_doors == aux_data_doors, (
                'The following doors were found in the logic but not the aux data: '
                f"{logic_doors - aux_data_doors or '{}'}"
                '\nThe following doors were found in the aux data but not the logic: '
                f"{aux_data_doors - logic_doors or '{}'}"
            )

        return v

    @validator('rooms')
    def check_if_chests_are_consistent_between_aux_data_and_logic(
        cls, v: list[Room], values
    ) -> list[Room]:  # noqa: N805
        """Check that all chests in the aux data are also in the logic (and vice-versa)."""
        nodes, _ = parse(LOGIC_DATA_DIRECTORY)
        for room in v:
            # Get all chests in the logic
            logic_chests = set()
            for node in nodes:
                if node.area != values['name'] or node.room != room.name:
                    continue
                for contents in node.contents:
                    if contents.type == Descriptor.CHEST.value:
                        logic_chests.add(contents.data)

            # Get all chests in the aux data
            aux_data_chests = {chest.name for chest in room.chests or []}

            assert logic_chests == aux_data_chests, (
                'The following chests were found in the logic but not the aux data: '
                f"{logic_chests - aux_data_chests or '{}'}"
                '\nThe following chests were found in the aux data but not the logic: '
                f"{aux_data_chests - logic_chests or '{}'}"
            )

        return v


if __name__ == '__main__':
    json_schema = Area.schema_json(indent=2)
    with open(Path(__file__).parent / 'aux_schema.json', 'w') as fd:
        fd.write(json_schema + '\n')
