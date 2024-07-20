from pydantic import BaseModel

from ph_rando import __version__
from ph_rando.common import ShufflerAuxData


class SpoilerLog(BaseModel):
    version: str
    seed: str
    settings: dict
    items: dict[str, dict[str, dict[str, str]]]


def generate_spoiler_log(randomized_aux_data: ShufflerAuxData, settings: dict) -> SpoilerLog:
    seed = randomized_aux_data.seed
    assert seed is not None

    items: dict[str, dict[str, dict[str, str]]] = {}

    for area in randomized_aux_data.areas:
        items[area.name] = {}
        for room in area.rooms:
            if len(room.chests):
                items[area.name][room.name] = {}
            for chest in room.chests:
                items[area.name][room.name][chest.display_name or chest.name] = chest.contents.name

    return SpoilerLog(
        version=__version__,
        seed=seed,
        items=items,
        settings=settings,
    )
