import json
from pathlib import Path

import pytest

from shuffler import shuffle
from shuffler._parser import Edge, Node, NodeContents, parse
from shuffler.aux_models import Area


def test_parser(tmp_path: Path):
    test_logic = """
    # A comment at the top of the file!
    area TestArea:
        room TestRoom1:
        # Another comment!
            node TestNode1:
                chest Chest1
                door Door1

#A line that only contains a comment, nothing else
            node TestNode2:
                chest Chest2
                door Door2
                door Door3

            node TestNode3:
                door Door4

            TestNode1 <-> TestNode3
            TestNode2 -> TestNode3

            # TestNode3 -> TestNode2
  #
        room TestRoom2:
            node TestNode4:
                chest Chest3
    """

    expected_nodes = [
        Node(
            name='TestArea.TestRoom1.TestNode1',
            contents=[
                NodeContents(type=type, data=str)
                for type, str in [('chest', 'Chest1'), ('door', 'Door1')]
            ],
        ),
        Node(
            name='TestArea.TestRoom1.TestNode2',
            contents=[
                NodeContents(type=type, data=str)
                for type, str in [('chest', 'Chest2'), ('door', 'Door2'), ('door', 'Door3')]
            ],
        ),
        Node(
            name='TestArea.TestRoom1.TestNode3',
            contents=[NodeContents(type=type, data=str) for type, str in [('door', 'Door4')]],
        ),
        Node(
            name='TestArea.TestRoom2.TestNode4',
            contents=[NodeContents(type=type, data=str) for type, str in [('chest', 'Chest3')]],
        ),
    ]

    # Write test logic to a file so the parser can find it
    with open(tmp_path / 'test.logic', 'w') as fd:
        fd.write(test_logic)

    nodes, edges = parse(tmp_path)

    assert nodes == expected_nodes

    # TODO: test edges once edge parsing is implemented


@pytest.mark.parametrize('seed', ['test', 'another_test', 'ANOTHER_TEST!!', 'this_is_a_real_seed'])
def test_seeds(seed: str, aux_data: list[Area], logic: tuple[list[Node], dict[str, list[Edge]]]):
    """Test that running the shuffler with the same seed multiple times produces identical aux data."""
    nodes, edges = logic

    first = shuffle(seed, nodes, edges, aux_data)
    second = shuffle(seed, nodes, edges, aux_data)
    third = shuffle(seed, nodes, edges, aux_data)
    assert first == second == third


@pytest.mark.parametrize(
    'filename',
    [
        str(file)
        for file in (Path(__file__).parent.parent / 'shuffler' / 'auxiliary').rglob('*.json')
    ],
)
def test_aux_data_validation(filename: str):
    """Run every aux data json through validation."""
    with open(filename) as fd:
        Area(**json.load(fd))


@pytest.mark.parametrize(
    'expression,inventory,expected_result',
    [
        # fmt: off
        # Test basic expressions
        ('item Boomerang', ['boomerang', 'sword'], True),
        ('item Boomerang', ['sword'], False),
        # Test expressions with basic logic operators
        ('item Boomerang & item Bombs)', ['boomerang', 'bombs'], True),
        ('item Boomerang & item Bombs)', ['boomerang', 'sword'], False),
        ('item Boomerang & item Bombs)', ['bombs'], False),
        ('item Boomerang & item Bombs)', [], False),
        ('item Boomerang | item Bombs)', ['boomerang', 'bombs'], True),
        ('item Boomerang | item Bombs)', ['boomerang', 'sword'], True),
        ('item Boomerang | item Bombs)', ['bombs'], True),
        ('item Boomerang | item Bombs)', ['sword'], False),
        # Test nested expressions
        ('item Boomerang & (item Bombs | item Bombchus)', ['boomerang', 'bombs', 'bombchus'], True),
        ('item Boomerang & (item Bombs | item Bombchus | item Hammer)', ['boomerang', 'bombchus'], True),  # noqa: E501
        ('item Boomerang & (item Bombs | item Bombchus)', ['boomerang', 'bombs'], True),
        ('item Boomerang & (item Bombs | item Bombchus)', ['bombs', 'bombchus'], False),
        ('item Boomerang & (item Bombs | item Bombchus)', ['boomerang', 'sword'], False),
        ('item Bombchus | item Bombs', ['bombs', 'bombchus', 'cannon'], True),
        ('item Bombchus | item Bombs', ['bombs', 'boomerang', 'cannon'], True),
        ('item Bombchus | item Bombs', ['bombchus', 'boomerang', 'cannon'], True),
        ('item Bombchus | item Bombs', ['boomerang', 'cannon', 'sword'], False),
        ('item Bombchus | item Bombs | item Sword', ['boomerang', 'cannon', 'sword'], True),
        # Test more complex nested expressions
        ('item Boomerang & ((item Bombs | item Bombchus) | (item GrapplingHook & item Bow))', ['bombs'], False),  # noqa: E501
        ('item Boomerang & ((item Bombs | item Bombchus) | (item GrapplingHook & item Bow))', ['boomerang', 'bombs'], True),  # noqa: E501
        ('item Boomerang & ((item Bombs | item Bombchus) | (item GrapplingHook & item Bow))', ['boomerang', 'bombchus'], True),  # noqa: E501
        ('item Boomerang & ((item Bombs | item Bombchus) | (item GrapplingHook & item Bow))', ['boomerang', 'grappling_hook'], False),  # noqa: E501
        ('item Boomerang & ((item Bombs | item Bombchus) | (item GrapplingHook & item Bow))', ['boomerang', 'bow'], False),  # noqa: E501
        ('item Boomerang & ((item Bombs | item Bombchus) | (item GrapplingHook & item Bow))', ['boomerang', 'grappling_hook', 'bow'], True),  # noqa: E501
        # Test expression with a lot of redundant parentheses, which shouldn't affect results
        # other than additional performance overhead.
        ('(((((item Sword | ((item Shield)))))))', ['sword'], True),
        # fmt: on
    ],
)
def test_edge_parser(expression: str, inventory: list[str], expected_result: bool):
    assert (
        Edge(Node('test1', []), Node('test2', []), expression).is_traversable(inventory)
        == expected_result
    )
