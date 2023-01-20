from collections.abc import Callable
import json
from pathlib import Path

import click
import inflection

from ph_rando.settings import Settings


def click_setting_options(function: Callable):
    """Generate `click` CLI options for each randomizer setting."""
    with open(Path(__file__).parent / 'settings.json') as fd:
        settings = Settings(**json.load(fd)).settings

    for setting in settings:
        cli_arg = f'--{inflection.dasherize(inflection.underscore(setting.name))}'
        function = click.option(
            cli_arg,
            is_flag=bool(setting.flag),
            type=click.Choice(setting.options) if setting.options else bool,
            help=setting.description,
        )(function)

    return function
