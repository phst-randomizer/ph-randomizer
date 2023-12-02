from pathlib import Path

import pytest

from ph_rando.common import RANDOMIZER_SETTINGS
from ph_rando.shuffler._parser import parse_edge_requirement
from ph_rando.shuffler._shuffler import Edge, Node, Shuffler

TEST_DATA_DIR = Path(__file__).parent / 'test_data'


@pytest.mark.repeat(3)
@pytest.mark.parametrize('seed', ['test', 'another_test', 'another_another_test'])
def test_seeds(seed: str, default_settings):
    """Test that running the shuffler with same seed multiple times produces identical aux data."""
    first = Shuffler(seed=seed, settings=default_settings).generate()
    second = Shuffler(seed=seed, settings=default_settings).generate()
    third = Shuffler(seed=seed, settings=default_settings).generate()
    assert first == second == third


@pytest.mark.parametrize(
    'expression,inventory,flags,states,expected_result',
    [
        # fmt: off
        # Test basic expressions
        ('item Boomerang', ['Boomerang', 'Sword'], {}, {}, True),
        ('item Boomerang', ['Sword'], {}, {}, False),
        # Test expressions with basic logic operators
        ('item Boomerang & item Bombs', ['Boomerang', 'Bombs'], {}, {}, True),
        ('item Boomerang & item Bombs', ['Boomerang', 'Sword'], {}, {}, False),
        ('item Boomerang & item Bombs', ['Bombs'], {}, {}, False),
        ('item Boomerang & item Bombs', [], {}, {}, False),
        ('item Boomerang | item Bombs', ['Boomerang', 'Bombs'], {}, {}, True),
        ('item Boomerang | item Bombs', ['Boomerang', 'Sword'], {}, {}, True),
        ('item Boomerang | item Bombs', ['Bombs'], {}, {}, True),
        ('item Boomerang | item Bombs', ['Sword'], {}, {}, False),
        ('item Boomerang | flag BridgeRepaired', ['Bombs'], {'BridgeRepaired'}, {}, True),
        ('item Boomerang | flag BridgeRepaired', [], {'BridgeRepaired'}, {}, True),
        ('item Boomerang | flag BridgeRepaired', ['Bombs'], {}, {}, False),
        # Test nested expressions
        ('item Boomerang & (item Bombs | item Bombchus)', ['Boomerang', 'Bombs', 'Bombchus'], {}, {}, True),  # noqa: E501
        ('item Boomerang & (item Bombs | item Bombchus | item Hammer)', ['Boomerang', 'Bombchus'], {}, {}, True),  # noqa: E501
        ('item Boomerang & (item Bombs | item Bombchus)', ['Boomerang', 'Bombs'], {}, {}, True),
        ('item Boomerang & (item Bombs | item Bombchus)', ['Bombs', 'Bombchus'], {}, {}, False),
        ('item Boomerang & (item Bombs | item Bombchus)', ['Boomerang', 'Sword'], {}, {}, False),
        ('item Bombchus | item Bombs', ['Bombs', 'Bombchus', 'Cannon'], {}, {}, True),
        ('item Bombchus | item Bombs', ['Bombs', 'Boomerang', 'Cannon'], {}, {}, True),
        ('item Bombchus | item Bombs', ['Bombchus', 'Boomerang', 'Cannon'], {}, {}, True),
        ('item Bombchus | item Bombs', ['Boomerang', 'Cannon', 'Sword'], {}, {}, False),
        ('item Bombchus | item Bombs | item ProgressiveSword', ['Boomerang', 'Cannon', 'ProgressiveSword'], {}, {}, True),  # noqa: E501
        # Test more complex nested expressions
        ('item Boomerang & ((item Bombs | item Bombchus) | (item GrapplingHook & item Bow))', ['Bombs'], {}, {}, False),  # noqa: E501
        ('item Boomerang & ((item Bombs | item Bombchus) | (item GrapplingHook & item Bow))', ['Boomerang', 'Bombs'], {}, {}, True),  # noqa: E501
        ('item Boomerang & ((item Bombs | item Bombchus) | (item GrapplingHook & item Bow))', ['Boomerang', 'Bombchus'], {}, {}, True),  # noqa: E501
        ('item Boomerang & ((item Bombs | item Bombchus) | (item GrapplingHook & item Bow))', ['Boomerang', 'GrapplingHook'], {}, {}, False),  # noqa: E501
        ('item Boomerang & ((item Bombs | item Bombchus) | (item GrapplingHook & item Bow))', ['Boomerang', 'Bow'], {}, {}, False),  # noqa: E501
        ('item Boomerang & ((item Bombs | item Bombchus) | (item GrapplingHook & item Bow))', ['Boomerang', 'GrapplingHook', 'Bow'], {}, {}, True),  # noqa: E501
        # Test expression with a lot of redundant parentheses, which shouldn't affect results
        # other than additional performance overhead.
        ('(((((item ProgressiveSword | ((item Shield)))))))', ['ProgressiveSword'], {}, {}, True),
        # Test state
        ('state Test', [], {}, {'Test'}, True),
        ('state Test', [], {}, {}, False),
        # fmt: on
    ],
)
def test_edge_parser(
    expression: str,
    inventory: list[str],
    flags: set[str],
    states: set[str],
    expected_result: bool,
):
    node1 = Node(
        name='test1',
        area=None,  # type: ignore
        room=None,  # type: ignore
    )
    node2 = Node(
        name='test2',
        area=None,  # type: ignore
        room=None,  # type: ignore
    )
    edge = Edge(src=node1, dest=node2, requirements=parse_edge_requirement(expression))
    node1.edges.append(edge)
    assert (
        edge.is_traversable(
            inventory, flags, states, shuffler_instance=Shuffler(seed='test', settings={})
        )
        == expected_result
    )


# @pytest.mark.parametrize(
#     ('expression', 'result'),
#     [
#         ('open Door1', True),
#         ('item Item1', False),
#         ('item Item1 & (open Door1 | item Item2)', True),
#         ('open Door1 & (flag Flag1 | item Item1)', True),
#     ],
# )
# def test_edge_contains_open_descriptor(expression: str, result: bool) -> None:
#     """Test behavior of Edge.requires_key property."""
#     node1 = Node(name='test1')
#     node2 = Node(name='test2')
#     edge = Edge(src=node1, dest=node2, constraints=expression, areas=[])
#     assert edge.requires_key == result


# @pytest.mark.parametrize(
#     'expression,settings,expected_result',
#     [
#         ('setting NoPuzzleSolution', {'NoPuzzleSolution': False}, False),
#         ('setting NoPuzzleSolution', {'NoPuzzleSolution': True}, True),
#     ],
# )
# def test_settings(expression: str, settings: dict[str, bool | str], expected_result: bool):
#     Logic.settings = settings
#     node1 = Node(name='test1')
#     node2 = Node(name='test2')
#     edge = Edge(src=node1, dest=node2, constraints=expression, areas=[])
#     node1.edges.append(edge)
#     assert edge.is_traversable([]) == expected_result


@pytest.mark.parametrize(
    'test_data_name,starting_node_name,accessible_nodes_names,non_accessible_nodes_names',
    [
        (
            'chest_content',
            'ChestContentTest.Test.Node1',
            ['ChestContentTest.Test.Node2'],
            ['ChestContentTest.Test.NotAccessible'],
        ),
        (
            'key_test',
            'FireTemple.Test.Start',
            ['FireTemple.Test.Start', 'FireTemple.Test.LockedDoor1', 'FireTemple.Test.LockedDoor2'],
            ['FireTemple.Test.End'],
        ),
        (
            'edge_directions_test',
            'EdgeDirectionsTest.Test.Start',
            [
                'EdgeDirectionsTest.Test.Node1',
                'EdgeDirectionsTest.Test.Node2',
                'EdgeDirectionsTest.Test.Node3',
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
        #     [
        #         'StateTest.Test.Node1',
        #         'StateTest.Test.Node2',
        #         'StateTest.Test.Node3',
        #         'StateTest.Test.Node4',
        #         'StateTest.Test.Node6',
        #         'StateTest.Test.Node8',
        #     ],
        #     ['StateTest.Test.Node5', 'StateTest.Test.Node7'],
        # ),
    ],
)
def test_assumed_search(
    test_data_name: str,
    starting_node_name: str,
    accessible_nodes_names: list[str],
    non_accessible_nodes_names: list[str],
) -> None:
    current_test_dir = TEST_DATA_DIR / test_data_name

    # Patch out check for mailbox node
    Shuffler._connect_mail_nodes = lambda _: None  # type: ignore

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
        starting_node_name=starting_node_name,
        areas_directory=current_test_dir,
    )

    reachable_nodes = shuffler.assumed_search(items=[])

    reachable_nodes_names = [node.name for node in reachable_nodes]

    assert all(node in reachable_nodes_names for node in accessible_nodes_names)
    assert all(node not in reachable_nodes_names for node in non_accessible_nodes_names)
