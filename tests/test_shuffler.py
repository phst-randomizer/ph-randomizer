import json
from pathlib import Path

import pytest

from shuffler import shuffle
from shuffler.aux_models import Area
from shuffler.logic import Edge, Node


@pytest.mark.parametrize('seed', ['test', 'another_test', 'ANOTHER_TEST!!', 'this_is_a_real_seed'])
def test_seeds(seed: str):
    """Test that running the shuffler with same seed multiple times produces identical aux data."""

    first = shuffle(seed)
    second = shuffle(seed)
    third = shuffle(seed)
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
        ('item Bombchus | item Bombs | item Sword', ['boomerang', 'cannon', 'sword'], {}, True),
        # Test more complex nested expressions
        ('item Boomerang & ((item Bombs | item Bombchus) | (item GrapplingHook & item Bow))', ['bombs'], {}, False),  # noqa: E501
        ('item Boomerang & ((item Bombs | item Bombchus) | (item GrapplingHook & item Bow))', ['boomerang', 'bombs'], {}, True),  # noqa: E501
        ('item Boomerang & ((item Bombs | item Bombchus) | (item GrapplingHook & item Bow))', ['boomerang', 'bombchus'], {}, True),  # noqa: E501
        ('item Boomerang & ((item Bombs | item Bombchus) | (item GrapplingHook & item Bow))', ['boomerang', 'grappling_hook'], {}, False),  # noqa: E501
        ('item Boomerang & ((item Bombs | item Bombchus) | (item GrapplingHook & item Bow))', ['boomerang', 'bow'], {}, False),  # noqa: E501
        ('item Boomerang & ((item Bombs | item Bombchus) | (item GrapplingHook & item Bow))', ['boomerang', 'grappling_hook', 'bow'], {}, True),  # noqa: E501
        # Test expression with a lot of redundant parentheses, which shouldn't affect results
        # other than additional performance overhead.
        ('(((((item Sword | ((item Shield)))))))', ['sword'], {}, True),
        # fmt: on
    ],
)
def test_edge_parser(expression: str, inventory: list[str], flags: set[str], expected_result: bool):
    assert (
        Edge(Node('test1', [], [], [], set(), set()), expression).is_traversable(inventory, flags)
        == expected_result
    )
