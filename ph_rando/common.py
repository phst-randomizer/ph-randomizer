from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import json
from pathlib import Path
from typing import TYPE_CHECKING

import click
import inflection

from ph_rando.settings import Settings

if TYPE_CHECKING:
    from click.decorators import FC

    from ph_rando.shuffler.aux_models import Area


@dataclass
class ShufflerAuxData:
    areas: list[Area]
    enemy_requirements: dict[str, str]
    requirement_macros: dict[str, str]
    seed: str | None = None


RANDOMIZER_SETTINGS = {
    setting.name: setting
    for setting in Settings(
        **json.loads((Path(__file__).parent / 'settings.json').read_text())
    ).settings
}


def click_setting_options(function: Callable) -> Callable[[FC], FC]:
    """Generate `click` CLI options for each randomizer setting."""
    for setting in RANDOMIZER_SETTINGS.values():
        cli_arg = f'--{inflection.dasherize(inflection.underscore(setting.name))}'

        click_option_kwargs = {}
        if setting.default is not None:
            click_option_kwargs['default'] = setting.default

        function = click.option(
            cli_arg,
            setting.name,
            type=bool if setting.type == 'flag' else click.Choice(list(setting.choices)),
            help=setting.description,
            show_default=True,
            **click_option_kwargs,
        )(function)

    return function
