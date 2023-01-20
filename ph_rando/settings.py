from pathlib import Path

from pydantic import BaseModel, validator


class Setting(BaseModel):
    name: str
    flag: bool | None
    options: list[str] | None
    default: bool | str

    @validator('options')
    def ensure_values_or_flag(cls, v: list[str] | None, values: dict):
        if not ('options' in values or 'flag' in values):
            raise ValueError(f'Invalid setting {values["name"]} - require "options" or "flag".')
        if 'options' in values and 'flag' in values:
            raise ValueError(
                f'Invalid setting {values["name"]} - has both'
                '"options" or "flag", only one allowed.'
            )
        return v

    @validator('default')
    def validate_default(cls, v: bool | str, values: dict):
        if (isinstance(v, bool) and not values.get('flag')) or (
            isinstance(v, str) and values.get('flag')
        ):
            raise ValueError(f'Invalid default {v!r} for setting.')
        return v


class Settings(BaseModel):
    settings: list[Setting]


if __name__ == '__main__':
    json_schema = Settings.schema_json(indent=2)
    with open(Path(__file__).parent / 'settings_schema.json', 'w') as fd:
        fd.write(json_schema + '\n')
