from pathlib import Path

import pytest

from ph_rando.shuffler._parser import annotate_logic

# from ph_rando.shuffler import shuffle
from ph_rando.shuffler.logic import Edge, Logic, Node, parse_aux_data

TEST_DATA_DIR = Path(__file__).parent / 'test_data'

# TODO: re-enable once shuffler actually works
# @pytest.mark.repeat(3)
# @pytest.mark.parametrize('seed', ['test', 'another_test'])
# def test_seeds(seed: str, settings):
# """Test that running the shuffler with same seed multiple times produces identical aux data."""

#     first = shuffle(seed, settings)
#     second = shuffle(seed, settings)
#     third = shuffle(seed, settings)
#     assert first == second == third


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
        ('item Boomerang | flag BridgeRepaired', ['bombs'], {'BridgeRepaired'}, True),
        ('item Boomerang | flag BridgeRepaired', [], {'BridgeRepaired'}, True),
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
    edge = Edge(src=node1, dest=node2, constraints=expression, areas=[])
    node1.edges.append(edge)
    assert edge.is_traversable(inventory, flags) == expected_result


@pytest.mark.parametrize(
    ('expression', 'result'),
    [
        ('open Door1', True),
        ('item Item1', False),
        ('item Item1 & (open Door1 | item Item2)', True),
        ('open Door1 & (flag Flag1 | item Item1)', True),
    ],
)
def test_edge_contains_open_descriptor(expression: str, result: bool) -> None:
    """Test behavior of Edge.requires_key property."""
    Logic(settings={})
    node1 = Node(name='test1')
    node2 = Node(name='test2')
    edge = Edge(src=node1, dest=node2, constraints=expression, areas=[])
    assert edge.requires_key == result


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
    edge = Edge(src=node1, dest=node2, constraints=expression, areas=[])
    node1.edges.append(edge)
    assert edge.is_traversable([]) == expected_result


@pytest.mark.parametrize(
    'test_data_name,starting_node_name,accessible_nodes_names,non_accessible_nodes_names',
    [
        (
            'basic',
            'TestArea.TestRoom.Node1',
            ['TestArea.TestRoom.Node2'],
            ['TestArea.TestRoom.NotAccessible'],
        ),
        # (
        #     'key_test',
        #     'Test.Test.Start',
        #     ['Test.Test.Start', 'Test.Test.LockedDoor1', 'Test.Test.LockedDoor2'],
        #     ['Test.Test.End'],
        # ),
        (
            'edge_directions_test',
            'EdgeDirectionsTest.Test.Start',
            [
                'EdgeDirectionsTest.Test.Node1',
                'EdgeDirectionsTest.Test.Node2',
                'EdgeDirectionsTest.Test.3',
            ],
            ['EdgeDirectionsTest.Test.Node4'],
        ),
        (
            'flag_test',
            'FlagTest.Test.Start',
            ['FlagTest.Test.Node1', 'FlagTest.Test.Node2', 'FlagTest.Test.Node3'],
            ['FlagTest.Test.Node4'],
        ),
        # (
        #     'state_test',
        #     'StateTest.Test.Start',
        #     ['StateTest.Test.Node1', 'StateTest.Test.Node2', 'StateTest.Test.Node3', 'StateTest.Test.Node4', 'StateTest.Test.Node6', 'StateTest.Test.Node8'],
        #     ['StateTest.Test.Node5', 'StateTest.Test.Node7']
        # ),
    ],
)
def test_graph_traversal(
    test_data_name: str,
    starting_node_name: str,
    accessible_nodes_names: list[str],
    non_accessible_nodes_names: list[str],
) -> None:
    current_test_dir = TEST_DATA_DIR / test_data_name

    areas = parse_aux_data(current_test_dir).values()
    annotate_logic(areas, current_test_dir)

    starting_node = [
        node
        for area in areas
        for room in area.rooms
        for node in room.nodes
        if node.name == starting_node_name
    ][0]
    accessible_nodes = [
        node
        for area in areas
        for room in area.rooms
        for node in room.nodes
        if node.name in accessible_nodes_names
    ]
    non_accessible_nodes = [
        node
        for area in areas
        for room in area.rooms
        for node in room.nodes
        if node.name in non_accessible_nodes_names
    ]

    reachable_nodes = Logic.assumed_search(
        starting_node=starting_node,
        inventory=[],
        keys={area.name: 0 for area in areas},
    )

    assert all(node in reachable_nodes for node in accessible_nodes)
    assert all(node not in reachable_nodes for node in non_accessible_nodes)
