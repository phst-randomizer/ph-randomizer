from __future__ import annotations

from collections.abc import Callable
import json
from pathlib import Path
from typing import TYPE_CHECKING

import click
import inflection

from ph_rando.settings import Settings

if TYPE_CHECKING:
    from click.decorators import FC

RANDOMIZER_SETTINGS = Settings(
    **json.loads((Path(__file__).parent / 'settings.json').read_text())
).settings


def click_setting_options(function: Callable) -> Callable[[FC], FC]:
    """Generate `click` CLI options for each randomizer setting."""
    for setting in RANDOMIZER_SETTINGS:
        cli_arg = f'--{inflection.dasherize(inflection.underscore(setting.name))}'

        click_option_kwargs = {}
        if setting.default is not None:
            click_option_kwargs['default'] = setting.default

        function = click.option(
            cli_arg,
            is_flag=bool(setting.flag),
            type=click.Choice(setting.options) if setting.options else bool,
            help=setting.description,
            show_default=True,
            **click_option_kwargs,
        )(function)

    return function
