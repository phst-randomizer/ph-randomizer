from collections import defaultdict
import json
from pathlib import Path

from ph_rando.shuffler._shuffler import assumed_search, init_logic_graph
from ph_rando.shuffler.aux_models import Area


def test_graph_connectedness() -> None:
    aux_data = init_logic_graph()

    areas = aux_data.areas

    # Compute list of tuples of each check its area.
    all_checks = [
        (chest, area.name)
        for area in areas.values()
        for room in area.rooms
        for chest in room.chests
    ]

    # Put every item in the game in the current inventory, appending the area name to each
    # small_key so we know which key goes to which area.
    items = [
        chest.contents if chest.contents != 'SmallKey' else f'SmallKey_{area_name}'
        for chest, area_name in all_checks
    ]

    # Populate the `keys` dict for the assumed search function with all of
    # the small keys in the inventory.
    keys: dict[str, int] = defaultdict(int)
    for item in items:
        if item.startswith('SmallKey_'):
            keys[item[len('SmallKey_') :]] += 1

    starting_node = [
        node
        for area in areas.values()
        for room in area.rooms
        for node in room.nodes
        if node.name == 'Mercay.OutsideOshus.Outside'
    ][0]

    assumed_search_nodes = set(
        assumed_search(
            starting_node=starting_node,
            aux_data=aux_data,
            items=items,
        )
    )

    # Create set consisting of all areas reported as reachable by the assumed search
    reachable_areas = {node.area.name for node in assumed_search_nodes}

    # Create set consisting of all areas in the logic
    all_areas = {area.name for area in areas.values()}

    assert reachable_areas == all_areas

    # Create set consisting of all rooms reported as reachable by the assumed search
    reachable_rooms = {f'{node.area.name}.{node.room.name}' for node in assumed_search_nodes}

    # Create set consisting of all rooms in the logic
    all_rooms = {f'{area.name}.{room.name}' for area in areas.values() for room in area.rooms}

    assert reachable_rooms == all_rooms

    # # Create set consisting of all nods reported as reachable by the assumed search
    reachable_nodes = {node.name for node in assumed_search_nodes}

    # Create set consisting of all nodes in the logic
    all_nodes = {node.name for area in areas.values() for room in area.rooms for node in room.nodes}

    print(sorted(all_nodes - reachable_nodes))
    assert reachable_nodes == all_nodes


def test_aux_data_validation():
    """Run every aux data json through validation."""
    aux_data_files = list(
        (Path(__file__).parents[1] / 'ph_rando' / 'shuffler' / 'logic').rglob('*.json')
    )
    assert len(aux_data_files) > 0
    for filename in aux_data_files:
        with open(filename) as fd:
            Area(**json.load(fd))
