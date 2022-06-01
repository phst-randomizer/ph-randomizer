from pathlib import Path

from pydantic import BaseModel, Field


class Check(BaseModel):
    name: str = Field(..., description="The name of the item check")
    contents: str = Field(..., description="The item that this check contains")


class Chest(Check):
    type = Field("chest", const=True)
    zmb_file_path: str = Field(..., description="File path to the zmb the chest is on")
    zmb_mapobject_index: int = Field(..., description="Index of the chest in the defined zmb file")


class Tree(Chest):
    type = Field("tree", const=True)


class Npc(Check):
    type = Field("npc", const=True)
    bmg_file_path: str = Field(..., description="File path to the bmg the instruction is on")
    bmg_instruction_index: int = Field(
        ..., description="Index of the instruction in the defined bmg file"
    )


class IslandShop(Check):
    type = Field("island_shop", const=True)
    overlay: int = Field(..., description="The code overlay this shop item is on")
    overlay_offset: str = Field(..., description="Hex offset from overlay to the shop item")


class Freestanding(Check):
    type = Field("freestanding", const=True)
    # TODO: add other fields that are needed


class OnEnemy(Check):
    type = Field("on_enemy", const=True)
    # TODO: what other fields are needed? Can this be replaced by Freestanding?


class Door(BaseModel):
    name: str = Field(..., description="The name of this exit")
    link: str = Field(..., description="The `entrance` or `door` where this exit leads.")


class Room(BaseModel):
    name: str = Field(..., description="The name of the room")
    chests: list[Chest | Npc | IslandShop | Tree | Freestanding | OnEnemy] | None = Field(
        None,
        description="Item checks that can be made in this room",
        min_items=1,
        unique_items=True,
    )
    doors: list[Door] = Field(
        ...,
        description="All doors in this room that lead to a different room or area",
        min_items=1,
        unique_items=True,
    )


class Area(BaseModel):
    name: str = Field(..., description="The name of the area")
    rooms: list[Room] = Field(
        ..., description="All of the rooms inside this area", min_items=1, unique_items=True
    )


if __name__ == "__main__":
    json_schema = Area.schema_json(indent=2)
    with open(Path(__file__).parent / "aux_schema.json", "w") as fd:
        fd.write(json_schema)
