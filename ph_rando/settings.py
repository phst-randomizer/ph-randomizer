from pathlib import Path

from pydantic import BaseModel, Field, validator


class Setting(BaseModel):
    name: str
    description: str | None
    flag: bool | None
    options: list[str] | None
    supported: bool = Field(default=True)
    default: bool | str | None

    @validator('default')
    def validate_default_value(cls, v: bool | str | None, values: dict) -> bool | str | None:
        # If default isn't provided, that's fine
        if v is None:
            return v
        # If default is provided and this setting is a flag, ensure the default value is a boolean
        elif isinstance(values['flag'], bool) and not isinstance(v, bool):
            raise ValueError(
                f'Invalid default value "{v}" for setting "{values["name"]}", must be bool.'
            )
        # If default is provided and this setting is a string-based option, ensure the default
        # value is one of the values in self.options
        elif (
            values['options']
            and isinstance(values['options'][0], str)
            and (v not in values['options'])
        ):
            raise ValueError(
                f'Invalid default value "{v}" for setting "{values["name"]}", '
                f'must be one of {values["options"]}.'
            )
        return v

    @validator('options')
    def ensure_values_or_flag(cls, v: list[str] | None, values: dict) -> list[str] | None:
        if not ('options' in values or 'flag' in values):
            raise ValueError(f'Invalid setting {values["name"]} - require "options" or "flag".')
        if 'options' in values and 'flag' in values:
            raise ValueError(
                f'Invalid setting {values["name"]} - has both'
                '"options" or "flag", only one allowed.'
            )
        return v


class Settings(BaseModel):
    settings: list[Setting]


if __name__ == '__main__':
    json_schema = Settings.schema_json(indent=2)
    with open(Path(__file__).parent / 'settings_schema.json', 'w') as fd:
        fd.write(json_schema + '\n')
