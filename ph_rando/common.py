from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import click
import inflection
import yaml

from ph_rando.settings import Settings

if TYPE_CHECKING:
    from click.decorators import FC

    from ph_rando.shuffler.aux_models import Area


@dataclass
class ShufflerAuxData:
    areas: dict[str, Area]
    enemy_requirements: dict[str, str]
    requirement_macros: dict[str, str]


RANDOMIZER_SETTINGS = Settings(
    **yaml.safe_load((Path(__file__).parent / 'settings.yaml').read_text())
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
