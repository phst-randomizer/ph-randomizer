from __future__ import annotations

import importlib
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Literal, Protocol, runtime_checkable

from pydantic import BaseModel, Field, validator

if TYPE_CHECKING:
    from ph_rando.patcher._patcher import Patcher
    from ph_rando.shuffler._shuffler import Shuffler


@runtime_checkable
class PatcherHook(Protocol):
    def __call__(self, value: bool | str | list[str], patcher: Patcher) -> None:
        ...


@runtime_checkable
class ShufflerHook(Protocol):
    def __call__(self, value: bool | str | list[str], shuffler: Shuffler) -> None:
        ...


class BaseSetting(BaseModel):
    name: str
    description: str | None
    supported: bool = Field(default=True)

    patcher_hook: str | None
    shuffler_hook: str | None

    @validator('patcher_hook', pre=True)
    def import_patcher_hook(cls, v: str | None) -> str | None:
        if v is not None:
            assert hasattr(importlib.import_module('ph_rando.patcher._settings'), v)
        return v

    @validator('shuffler_hook', pre=True)
    def import_shuffler_hook(cls, v: str | None) -> str | None:
        if v is not None:
            assert hasattr(importlib.import_module('ph_rando.shuffler._settings'), v)
        return v


class FlagSetting(BaseSetting):
    type: Literal['flag']
    default: bool


class SingleChoiceSetting(BaseSetting):
    type: Literal['single_choice']
    choices: set[str]
    default: str

    @validator('default')
    def ensure_values_or_flag(cls, v: str, values: dict) -> str:
        if v not in values['choices']:
            raise ValueError(f'Invalid default: must be one of "{"|".join(values["choices"])}"')
        return v


class MultipleChoiceSetting(BaseSetting):
    type: Literal['multiple_choice']
    choices: set[str]
    default: set[str]

    @validator('default')
    def ensure_values_or_flag(cls, v: set[str], values: dict) -> set[str]:
        if not v.issubset(values['choices']):
            raise ValueError('Invalid default: "default" must be subset of "choices"')
        return v


class Settings(BaseModel):
    settings: list[
        Annotated[
            FlagSetting | SingleChoiceSetting | MultipleChoiceSetting,
            Field(discriminator='type'),
        ]
    ]


if __name__ == '__main__':
    json_schema = Settings.schema_json(indent=2)
    with open(Path(__file__).parent / 'settings_schema.json', 'w') as fd:
        fd.write(json_schema + '\n')
