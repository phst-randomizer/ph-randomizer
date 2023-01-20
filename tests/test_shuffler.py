from collections import defaultdict
import json
from pathlib import Path

import pytest

from ph_rando.shuffler import shuffle
from ph_rando.shuffler.aux_models import Area
from ph_rando.shuffler.logic import Edge, Logic, Node


@pytest.mark.repeat(3)
@pytest.mark.parametrize('seed', ['test', 'another_test'])
def test_seeds(seed: str, settings):
    """Test that running the shuffler with same seed multiple times produces identical aux data."""

    first = shuffle(seed, settings)
    second = shuffle(seed, settings)
    third = shuffle(seed, settings)
    assert first == second == third


@pytest.mark.parametrize(
    'filename',
    [str(file) for file in (Path(__file__).parent.parent / 'shuffler' / 'logic').rglob('*.json')],
)
def test_aux_data_validation(filename: str):
    """Run every aux data json through validation."""
    with open(filename) as fd:
        Area(**json.load(fd))


@pytest.mark.parametrize(
    'expression,inventory,flags,expected_result',
    [
        # fmt: off
        # Test basic expressions
        ('item Boomerang', ['boomerang', 'sword'], {}, True),
        ('item Boomerang', ['sword'], {}, False),
        # Test expressions with basic logic operators
        ('item Boomerang & item Bombs', ['boomerang', 'bombs'], {}, True),
        ('item Boomerang & item Bombs', ['boomerang', 'sword'], {}, False),
        ('item Boomerang & item Bombs', ['bombs'], {}, False),
        ('item Boomerang & item Bombs', [], {}, False),
        ('item Boomerang | item Bombs', ['boomerang', 'bombs'], {}, True),
        ('item Boomerang | item Bombs', ['boomerang', 'sword'], {}, True),
        ('item Boomerang | item Bombs', ['bombs'], {}, True),
        ('item Boomerang | item Bombs', ['sword'], {}, False),
        ('item Boomerang | flag BridgeRepaired', ['bombs'], {'bridge_repaired'}, True),
        ('item Boomerang | flag BridgeRepaired', [], {'bridge_repaired'}, True),
        ('item Boomerang | flag BridgeRepaired', ['bombs'], {}, False),
        # Test nested expressions
        ('item Boomerang & (item Bombs | item Bombchus)', ['boomerang', 'bombs', 'bombchus'], {}, True),  # noqa: E501
        ('item Boomerang & (item Bombs | item Bombchus | item Hammer)', ['boomerang', 'bombchus'], {}, True),  # noqa: E501
        ('item Boomerang & (item Bombs | item Bombchus)', ['boomerang', 'bombs'], {}, True),
        ('item Boomerang & (item Bombs | item Bombchus)', ['bombs', 'bombchus'], {}, False),
        ('item Boomerang & (item Bombs | item Bombchus)', ['boomerang', 'sword'], {}, False),
        ('item Bombchus | item Bombs', ['bombs', 'bombchus', 'cannon'], {}, True),
        ('item Bombchus | item Bombs', ['bombs', 'boomerang', 'cannon'], {}, True),
        ('item Bombchus | item Bombs', ['bombchus', 'boomerang', 'cannon'], {}, True),
        ('item Bombchus | item Bombs', ['boomerang', 'cannon', 'sword'], {}, False),
        ('item Bombchus | item Bombs | item Sword', ['boomerang', 'cannon', 'oshus_sword'], {}, True),  # noqa: E501
        # Test more complex nested expressions
        ('item Boomerang & ((item Bombs | item Bombchus) | (item GrapplingHook & item Bow))', ['bombs'], {}, False),  # noqa: E501
        ('item Boomerang & ((item Bombs | item Bombchus) | (item GrapplingHook & item Bow))', ['boomerang', 'bombs'], {}, True),  # noqa: E501
        ('item Boomerang & ((item Bombs | item Bombchus) | (item GrapplingHook & item Bow))', ['boomerang', 'bombchus'], {}, True),  # noqa: E501
        ('item Boomerang & ((item Bombs | item Bombchus) | (item GrapplingHook & item Bow))', ['boomerang', 'grappling_hook'], {}, False),  # noqa: E501
        ('item Boomerang & ((item Bombs | item Bombchus) | (item GrapplingHook & item Bow))', ['boomerang', 'bow'], {}, False),  # noqa: E501
        ('item Boomerang & ((item Bombs | item Bombchus) | (item GrapplingHook & item Bow))', ['boomerang', 'grappling_hook', 'bow'], {}, True),  # noqa: E501
        # Test expression with a lot of redundant parentheses, which shouldn't affect results
        # other than additional performance overhead.
        ('(((((item Sword | ((item Shield)))))))', ['oshus_sword'], {}, True),
        # fmt: on
    ],
)
def test_edge_parser(expression: str, inventory: list[str], flags: set[str], expected_result: bool):
    node1 = Node(name='test1')
    node2 = Node(name='test2')
    edge = Edge(node1, node2, expression)
    node1.edges.append(edge)
    assert edge.is_traversable(inventory, flags, set()) == expected_result


@pytest.mark.parametrize(
    'expression,settings,expected_result',
    [
        ('setting NoPuzzleSolution', {'NoPuzzleSolution': False}, False),
        ('setting NoPuzzleSolution', {'NoPuzzleSolution': True}, True),
    ],
)
def test_settings(expression: str, settings: dict[str, bool | str], expected_result: bool):
    Logic.settings = settings
    node1 = Node(name='test1')
    node2 = Node(name='test2')
    edge = Edge(node1, node2, expression)
    node1.edges.append(edge)
    assert edge.is_traversable([], set(), set()) == expected_result


def test_graph_connectedness(settings) -> None:
    logic = Logic(settings=settings)
    logic.connect_rooms()

    # Compute list of tuples of each check its area.
    all_checks = [
        (chest, area.name)
        for area in logic.areas.values()
        for room in area.rooms
        for chest in room.chests
    ]

    # Put every item in the game in the current inventory, appending the area name to each
    # small_key so we know which key goes to which area.
    inventory = [
        chest.contents if chest.contents != 'small_key' else f'small_key_{area_name}'
        for chest, area_name in all_checks
    ]

    # Populate the `keys` dict for the assumed search function with all of
    # the small keys in the inventory.
    keys: dict[str, int] = defaultdict(int)
    for item in inventory:
        if item.startswith('small_key_'):
            keys[item[len('small_key_') :]] += 1

    reachable_nodes = logic._assumed_search(
        logic.starting_node,
        inventory,
        keys,
    )

    # Create set consisting of all areas reported as reachable by the assumed search
    reachable_areas = {node.area for node in reachable_nodes}

    # Create set consisting of all areas in the logic
    all_areas = {area.name for area in logic.areas.values()}

    assert reachable_areas == all_areas

    # TODO: assert that rooms + nodes are identical too
