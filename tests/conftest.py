from pathlib import Path

import pytest

from ph_rando.common import RANDOMIZER_SETTINGS
from ph_rando.patcher._util import load_aux_data


# TODO: overhaul this fixture, maybe parametrize for all possible setting combinations
@pytest.fixture
def settings():
    return {setting.name: True for setting in RANDOMIZER_SETTINGS}


@pytest.fixture
def aux_data():
    return load_aux_data(Path(__file__).parents[1] / 'ph_rando' / 'shuffler' / 'logic')
