from pathlib import Path

import pytest

from shuffler import shuffle
from shuffler._parser import Node, NodeContents, parse


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
            contents=[NodeContents(type=type, data=str) for type, str in [("door", "Door4")]],
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
