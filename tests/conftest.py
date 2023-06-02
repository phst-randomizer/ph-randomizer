from pathlib import Path

import pytest

from ph_rando.common import RANDOMIZER_SETTINGS, ShufflerAuxData
from ph_rando.shuffler._parser import parse_aux_data


# TODO: overhaul this fixture, maybe parametrize for all possible setting combinations
@pytest.fixture
def settings():
    return {setting.name: True for setting in RANDOMIZER_SETTINGS}


@pytest.fixture
def aux_data() -> ShufflerAuxData:
    shuffler_dir = Path(__file__).parents[1] / 'ph_rando' / 'shuffler'
    return parse_aux_data(
        areas_directory=shuffler_dir / 'logic',
        enemy_mapping_file=shuffler_dir / 'enemies.json',
        macros_file=shuffler_dir / 'macros.json',
    )
