import json
from pathlib import Path

import pytest

from ph_rando.settings import Settings


# TODO: overhaul this fixture, maybe parametrize for all possible setting combinations
@pytest.fixture
def settings():
    with open(Path(__file__).parents[1] / 'ph_rando' / 'settings.json') as fd:
        settings = Settings(**json.load(fd)).settings
    return {setting.name: True for setting in settings}
