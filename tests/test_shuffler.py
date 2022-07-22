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
                flag Flag1

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
            name="TestArea.TestRoom1.TestNode1",
            contents=[
                NodeContents(type=type, data=str)
                for type, str in [("chest", "Chest1"), ("door", "Door1")]
            ],
        ),
        Node(
            name="TestArea.TestRoom1.TestNode2",
            contents=[
                NodeContents(type=type, data=str)
                for type, str in [("chest", "Chest2"), ("door", "Door2"), ("door", "Door3")]
            ],
        ),
        Node(
            name="TestArea.TestRoom1.TestNode3",
            contents=[
                NodeContents(type=type, data=str)
                for type, str in [("door", "Door4"), ("flag", "Flag1")]
            ],
        ),
        Node(
            name="TestArea.TestRoom2.TestNode4",
            contents=[NodeContents(type=type, data=str) for type, str in [("chest", "Chest3")]],
        ),
    ]

    # Write test logic to a file so the parser can find it
    with open(tmp_path / "test.logic", "w") as fd:
        fd.write(test_logic)

    nodes, edges = parse(tmp_path)

    assert nodes == expected_nodes

    # TODO: test edges once edge parsing is implemented


@pytest.mark.parametrize("seed", ["test", "another_test", "ANOTHER_TEST!!", "this_is_a_real_seed"])
def test_seeds(seed: str, aux_data_directory: str, logic_directory: str):
    """Test that running the shuffler with the same seed multiple times produces identical aux data."""
    first = shuffle(seed, aux_data_directory, logic_directory)
    second = shuffle(seed, aux_data_directory, logic_directory)
    third = shuffle(seed, aux_data_directory, logic_directory)
    assert first == second == third


@pytest.mark.parametrize(
    "filename",
    [
        str(file)
        for file in (Path(__file__).parent.parent / "shuffler" / "auxiliary").rglob("*.json")
    ],
)
def test_aux_data_validation(filename: str):
    """Run every aux data json through validation."""
    with open(filename, "r") as fd:
        Area(**json.load(fd))


@pytest.mark.parametrize(
    "expression,inventory,flags,expected_result",
    [
        # fmt: off
        # Test basic expressions
        ("item Boomerang", ["boomerang", "sword"], set(), True),
        ("item Boomerang", ["sword"], set(), False),
        # Test expressions with basic logic operators
        ("item Boomerang & item Bombs)", ["boomerang", "bombs"], set(), True),
        ("item Boomerang & item Bombs)", ["boomerang", "sword"], set(), False),
        ("item Boomerang & item Bombs)", ["bombs"], set(), False),
        ("item Boomerang & item Bombs)", [], set(), False),
        ("item Boomerang | item Bombs)", ["boomerang", "bombs"], set(), True),
        ("item Boomerang | item Bombs)", ["boomerang", "sword"], set(), True),
        ("item Boomerang | item Bombs)", ["bombs"], set(), True),
        ("item Boomerang | item Bombs)", ["sword"], set(), False),
        # Test nested expressions
        ("item Boomerang & (item Bombs | item Bombchus)", ["boomerang", "bombs", "bombchus"], set(), True),
        ("item Boomerang & (item Bombs | item Bombchus | item Hammer)", ["boomerang", "bombchus"], set(), True),  # noqa: E501
        ("item Boomerang & (item Bombs | item Bombchus)", ["boomerang", "bombs"], set(), True),
        ("item Boomerang & (item Bombs | item Bombchus)", ["bombs", "bombchus"], set(), False),
        ("item Boomerang & (item Bombs | item Bombchus)", ["boomerang", "sword"], set(), False),
        ("item Bombchus | item Bombs", ["bombs", "bombchus", "cannon"], set(), True),
        ("item Bombchus | item Bombs", ["bombs", "boomerang", "cannon"], set(), True),
        ("item Bombchus | item Bombs", ["bombchus", "boomerang", "cannon"], set(), True),
        ("item Bombchus | item Bombs", ["boomerang", "cannon", "sword"], set(), False),
        ("item Bombchus | item Bombs | item Sword", ["boomerang", "cannon", "sword"], set(), True),
        # Test more complex nested expressions
        ("item Boomerang & ((item Bombs | item Bombchus) | (item GrapplingHook & item Bow))", ["bombs"], set(), False),  # noqa: E501
        ("item Boomerang & ((item Bombs | item Bombchus) | (item GrapplingHook & item Bow))", ["boomerang", "bombs"], set(), True),  # noqa: E501
        ("item Boomerang & ((item Bombs | item Bombchus) | (item GrapplingHook & item Bow))", ["boomerang", "bombchus"], set(), True),  # noqa: E501
        ("item Boomerang & ((item Bombs | item Bombchus) | (item GrapplingHook & item Bow))", ["boomerang", "grappling_hook"], set(), False),  # noqa: E501
        ("item Boomerang & ((item Bombs | item Bombchus) | (item GrapplingHook & item Bow))", ["boomerang", "bow"], set(), False),  # noqa: E501
        ("item Boomerang & ((item Bombs | item Bombchus) | (item GrapplingHook & item Bow))", ["boomerang", "grappling_hook", "bow"], set(), True),  # noqa: E501
        # Test expression with a lot of redundant parentheses, which shouldn't affect results
        # other than additional performance overhead.
        ("(((((item Sword | ((item Shield)))))))", ["sword"], set(), True),
        # fmt: on
    ],
)
def test_edge_parser(expression: str, inventory: list[str], flags: set[str], expected_result: bool):
    assert (
        Edge(Node("test1", []), Node("test2", []), expression).is_traversable(inventory, flags)
        == expected_result
    )
