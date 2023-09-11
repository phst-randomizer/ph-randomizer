from collections import defaultdict
import json
from pathlib import Path
from pprint import pprint

from ph_rando.common import RANDOMIZER_SETTINGS
from ph_rando.shuffler._descriptors import EdgeDescriptor
from ph_rando.shuffler._parser import Edge, parse_edge_requirement
from ph_rando.shuffler._shuffler import Shuffler
from ph_rando.shuffler.aux_models import Area, Item


def test_graph_connectedness() -> None:
    shuffler = Shuffler(
        seed='test',
        settings={
            setting.name: True
            if setting.type == 'flag'
            else list(setting.default)
            if setting.type == 'multiple_choice'
            else setting.default
            for setting in RANDOMIZER_SETTINGS.values()
        },
    )

    areas = shuffler.aux_data.areas

    # Compute list of tuples of each check its area.
    all_checks = [
        (chest, area.name) for area in areas for room in area.rooms for chest in room.chests
    ]

    # Put every item in the game in the current inventory, appending the area name to each
    # small_key so we know which key goes to which area.
    items: list[Item] = []
    for chest, area_name in all_checks:
        if chest.contents.name == 'SmallKey':
            chest.contents.name += f'_{area_name}'
        items.append(chest.contents)

    # Populate the `keys` dict for the assumed search function with all of
    # the small keys in the inventory.
    keys: dict[str, int] = defaultdict(int)
    for item in items:
        if item.name.startswith('SmallKey_'):
            keys[item.name[len('SmallKey_') :]] += 1

    starting_node = [
        node
        for area in areas
        for room in area.rooms
        for node in room.nodes
        if node.name == 'Mercay.OutsideOshus.Outside'
    ][0]

    # Remove all state "lose" descriptors, since they aren't the same per run
    states: set[str] = set()
    for area in areas:
        for room in area.rooms:
            for node in room.nodes:
                node.states_lost = set()
                states.update(node.states_gained)
            for chest in room.chests:
                states.update(chest.contents.states)

    starting_node.states_gained = states

    assumed_search_nodes = set(shuffler.assumed_search(items=items))

    # Create set consisting of all areas reported as reachable by the assumed search
    reachable_areas = {node.area.name for node in assumed_search_nodes}

    # Create set consisting of all areas in the logic
    all_areas = {area.name for area in areas}

    print(sorted(all_areas - reachable_areas))
    assert reachable_areas == all_areas

    # Create set consisting of all rooms reported as reachable by the assumed search
    reachable_rooms = {f'{node.area.name}.{node.room.name}' for node in assumed_search_nodes}

    # Create set consisting of all rooms in the logic
    all_rooms = {f'{area.name}.{room.name}' for area in areas for room in area.rooms}

    print(sorted(all_rooms - reachable_rooms))
    assert reachable_rooms == all_rooms

    # # Create set consisting of all nods reported as reachable by the assumed search
    reachable_nodes = {node.name for node in assumed_search_nodes}

    # Create set consisting of all nodes in the logic
    all_nodes = {node.name for area in areas for room in area.rooms for node in room.nodes}

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


def _get_required_states(edge: Edge, macros: dict[str, str]) -> set[str]:
    """Return the states that an edge requires, if any"""

    def _contains_state(
        constraints: list[str | list[str | list]], states: set[str] | None = None
    ) -> set[str]:
        if states is None:
            states = set()
        for i, elem in enumerate(constraints):
            if isinstance(elem, list):
                states.update(_contains_state(elem, states))
            elif EdgeDescriptor.STATE == elem:
                state_name = constraints[i + 1]
                assert isinstance(state_name, str)
                states.add(state_name)
            elif EdgeDescriptor.MACRO == elem:
                macro_name = constraints[i + 1]
                assert isinstance(macro_name, str)
                states.update(_contains_state(parse_edge_requirement(macros[macro_name]), states))
        return states

    return _contains_state(edge.requirements) if edge.requirements else set()


def test_ensure_states_exist() -> None:
    shuffler = Shuffler(seed='test', settings={})

    aux_data = shuffler.aux_data

    states_required: set[str] = set()
    states_gained: set[str] = set()
    states_lost: set[str] = set()
    for area in aux_data.areas:
        for room in area.rooms:
            for node in room.nodes:
                for edge in node.edges:
                    states_required.update(_get_required_states(edge, aux_data.requirement_macros))
                states_gained.update(node.states_gained)
                states_lost.update(node.states_lost)
            for chest in room.chests:
                states_gained.update(chest.contents.states)

    if states_required != states_gained:
        print('The following states are required by edges but are never gained:')
        pprint(states_required.difference(states_gained))
        print('The following states are gained but are never required by edges:')
        pprint(states_gained.difference(states_required))

    if not states_lost.issubset(states_gained):
        print('The following states are lost but never gained')
        pprint(states_lost.difference(states_gained))

    assert states_required == states_gained
    assert states_lost.issubset(states_gained)
