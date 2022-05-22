from pathlib import Path

from shuffler._parser import parse


def test_parse(tmp_path: Path):
    test_logic = """
    area TestArea:
      room TestRoom1:
        node TestNode1:
            chest Chest1
            door Door1
        
        node TestNode2:
            chest Chest2
            door Door2
            door Door3

        node TestNode3:
            door Door4

        TestNode1 <-> TestNode3
        TestNode2 -> TestNode3

      room TestRoom2:
        node TestNode4:
            chest Chest3
    """

    with open(tmp_path / "test.logic", "w") as fd:
        fd.write(test_logic)

    nodes, edges = parse(tmp_path)

    expected = set(
        [
            "TestArea.TestRoom1.TestNode1",
            "TestArea.TestRoom1.TestNode2",
            "TestArea.TestRoom1.TestNode3",
            "TestArea.TestRoom2.TestNode4",
        ]
    )
    assert set([node.name for node in nodes]) == expected
