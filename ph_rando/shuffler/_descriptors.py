from enum import Enum, EnumMeta


class MetaEnum(EnumMeta):
    def __contains__(cls, item):
        try:
            cls(item)
        except ValueError:
            return False
        return True


class NodeDescriptor(Enum, metaclass=MetaEnum):
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
    SHOP = 'shop'


class EdgeDescriptor(Enum, metaclass=MetaEnum):
    ITEM = 'item'
    FLAG = 'flag'
    OPEN = 'open'
    DEFEATED = 'defeated'
    SETTING = 'setting'
    STATE = 'state'
    LOSE = 'lose'
