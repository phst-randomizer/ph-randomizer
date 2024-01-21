from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Literal, Protocol, Self, runtime_checkable

from pydantic import BaseModel, Field, field_validator, model_validator

if TYPE_CHECKING:
    from ph_rando.patcher._patcher import Patcher
    from ph_rando.shuffler._shuffler import Shuffler


@runtime_checkable
class PatcherHook(Protocol):
    def __call__(self, value: bool | str | set[str], patcher: Patcher) -> None:
        ...


@runtime_checkable
class ShufflerHook(Protocol):
    def __call__(self, value: bool | str | set[str], shuffler: Shuffler) -> None:
        ...


class BaseSetting(BaseModel):
    name: str
    description: str | None = None
    supported: bool = Field(default=True)

    patcher_hook: str | None = None
    shuffler_hook: str | None = None

    @field_validator('patcher_hook', mode='before')
    def import_patcher_hook(cls, v: str | None) -> str | None:
        if v is not None:
            assert hasattr(importlib.import_module('ph_rando.patcher._settings'), v)
        return v

    @field_validator('shuffler_hook', mode='before')
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

    @model_validator(mode='after')
    def ensure_values_or_flag(self) -> Self:
        if self.default not in self.choices:
            raise ValueError(f'Invalid default: must be one of "{"|".join(self.choices)}"')
        return self


class MultipleChoiceSetting(BaseSetting):
    type: Literal['multiple_choice']
    choices: set[str]
    default: set[str]

    @model_validator(mode='after')
    def ensure_values_or_flag(self) -> Self:
        if not self.default.issubset(self.choices):
            raise ValueError('Invalid default: "default" must be subset of "choices"')
        return self


class Settings(BaseModel):
    settings: list[
        Annotated[
            FlagSetting | SingleChoiceSetting | MultipleChoiceSetting,
            Field(discriminator='type'),
        ]
    ]


if __name__ == '__main__':
    json_schema = json.dumps(Settings.model_json_schema(), indent=2)
    with open(Path(__file__).parent / 'settings_schema.json', 'w') as fd:
        fd.write(json_schema + '\n')
