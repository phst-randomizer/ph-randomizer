import pytest

from ph_rando.common import RANDOMIZER_SETTINGS


# TODO: overhaul this fixture, maybe parametrize for all possible setting combinations
@pytest.fixture
def settings():
    return {setting.name: True for setting in RANDOMIZER_SETTINGS}
