from pydantic import BaseModel

from ph_rando.common import ShufflerAuxData


class SpoilerLog(BaseModel):
    version: str
    seed: str
    settings: list
    items: dict[str, dict[str, dict[str, str]]]


def generate_spoiler_log(randomized_aux_data: ShufflerAuxData) -> SpoilerLog:
    version = '0.0.0-dev'  # TODO: retrieve this from elsewhere

    seed = randomized_aux_data.seed
    assert seed is not None

    items: dict[str, dict[str, dict[str, str]]] = {}
    settings: list = []

    for area in randomized_aux_data.areas.values():
        items[area.name] = {}
        for room in area.rooms:
            if len(room.chests):
                items[area.name][room.name] = {}
            for chest in room.chests:
                items[area.name][room.name][chest.display_name or chest.name] = chest.contents.name

    return SpoilerLog(version=version, seed=seed, items=items, settings=settings)
