from enum import EnumMeta, StrEnum
from typing import Any


class MetaEnum(EnumMeta):
    def __contains__(self: type[Any], item: object) -> bool:
        try:
            self(item)
        except ValueError:
            return False
        return True


class NodeDescriptor(StrEnum, metaclass=MetaEnum):
    CHEST = 'chest'
    FLAG = 'flag'
    DOOR = 'door'
    ENTRANCE = 'entrance'
    EXIT = 'exit'
    MAIL = 'mail'
    HINT = 'hint'
    ENEMY = 'enemy'
    LOCK = 'lock'
    GAIN = 'gain'
    LOSE = 'lose'
    SHOP = 'shop'


class EdgeDescriptor(StrEnum, metaclass=MetaEnum):
    ITEM = 'item'
    FLAG = 'flag'
    OPEN = 'open'
    DEFEATED = 'defeated'
    SETTING = 'setting'
    STATE = 'state'
    MACRO = 'macro'
