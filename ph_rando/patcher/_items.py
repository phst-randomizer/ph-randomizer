ITEMS: dict[str, int] = {
    'SmallKey': 0x1,
    'SmallGreenRupee': 0x2,
    'OshusSword': 0x3,
    'Shield': 0x4,
    'ForceGem': 0x6,  # TODO: difference between this and 0x1C?
    'Bombs': 0x7,
    'Bow': 0x8,
    'BigGreenRupee': 0x9,
    'HeartContainer': 0xA,
    'Boomerang': 0xC,
    'Shovel': 0xD,
    'Bombchus': 0xE,
    'BossKeyFireTemple': 0xF,
    'BossKeyWindTemple': 0xF,
    'BossKeyCourageTemple': 0xF,
    'BossKeyGoronTemple': 0xF,
    'BossKeyIceTemple': 0xF,
    'BossKeyMutohTemple': 0xF,
    'SWSeaChart': 0x13,
    'NWSeaChart': 0x14,
    'SESeaChart': 0x15,
    'NESeaChart': 0x16,
    'SmallBlueRupee': 0x18,
    'SmallRedRupee': 0x19,
    'BigRedRupee': 0x1A,
    'BigGoldRupee': 0x1B,
    'Hammer': 0x1F,
    'GrapplingHook': 0x20,
    'SquareCrystal': 0x21,
    'RoundCrystal': 0x22,
    'TriangleCrystal': 0x23,
    'FishingRod': 0x24,
    'Cannon': 0x25,
    'SunKey': 0x26,
    'QuiverUpgrade': 0x28,
    'BombBagUpgrade': 0x29,
    'BombchuBagUpgrade': 0x2A,
    'ShipPart': 0x2B,
    'KingKey': 0x2C,
    'PowerGem': 0x2D,
    'WisdomGem': 0x2E,
    'CourageGem': 0x2F,
    'CommonTreasure': 0x30,  # TODO: randomize this at run-time
    'GoronAmber': 0x34,
    'GhostKey': 0x38,
    'FreebieCard': 0x39,
    'ComplimentCard': 0x3A,
    'ComplimentaryCard': 0x3B,
    'RegalNecklace': 0x3C,
    'SalvageArm': 0x3D,
    'HeroNewClothes': 0x3E,
    'Kaleidoscope': 0x3F,
    'GuardNotebook': 0x40,
    'JolenesLetter': 0x41,
    'PrizePostcard': 0x42,
    'WoodHeart': 0x43,
    # 'TreasureMapSW1': 0x4B, # TODO: clarify how SW treasure map ids work considering Sun Key
    'TreasureMapSW1': 0x4C,
    'TreasureMapSW2': 0x4D,
    'TreasureMapSW3': 0x4E,
    'TreasureMapSW4': 0x4F,
    'TreasureMapSW5': 0x50,
    'TreasureMapSW6': 0x51,
    'TreasureMapSW7': 0x52,
    'TreasureMapNW1': 0x53,
    'TreasureMapNW2': 0x54,
    'TreasureMapNW3': 0x55,
    'TreasureMapNW4': 0x56,
    'TreasureMapNW5': 0x57,
    'TreasureMapNW6': 0x58,
    'TreasureMapNW7': 0x59,
    'TreasureMapNW8': 0x5A,
    'TreasureMapSE1': 0x5B,
    'TreasureMapSE2': 0x5C,
    'TreasureMapSE3': 0x5D,
    'TreasureMapSE4': 0x5E,
    'TreasureMapSE5': 0x5F,
    'TreasureMapSE6': 0x60,
    'TreasureMapSE7': 0x61,
    'TreasureMapSE8': 0x62,
    'TreasureMapNE1': 0x63,
    'TreasureMapNE2': 0x64,
    'TreasureMapNE3': 0x65,
    'TreasureMapNE4': 0x66,
    'TreasureMapNE5': 0x67,
    'TreasureMapNE6': 0x68,
    'TreasureMapNE7': 0x69,
    'TreasureMapNE8': 0x6A,
    'SwordsmansScroll': 0x71,
    'Crimsonine': 0x72,
    'Azurine': 0x73,
    'Aquanine': 0x74,
    'RedPotion': 0x75,
    'PurplePotion': 0x76,
    'YellowPotion': 0x77,
    'SandOfHours': 0x78,
    'RandomTreasure': 0x7D,
    'RandomShipPart': 0x7E,
    'CycloneSlate': 0x7F,
    'SmallRupoor': 0x81,
    'BigRupoor': 0x82,
    'RandomShipPart2': 0x85,  # TODO: what is this, and how does it relate to other ship parts?
    'RandomTreasure2': 0x86,  # TODO: what is this, and how does it relate to other treasures?
    # TODO: update these when their ids are known
    'PhantomHourglass': -1,
    'PhantomSword': -1,
    'PhantomSwordBlade': -1,
    'Sand2M': -1,
    'PowerSpirit': -1,
    'WisdomSpirit': -1,
    'CourageSpirit': -1,
    'PowerSpiritLv1': -1,
    'WisdomSpiritLv1': -1,
    'CourageSpiritLv1': -1,
    'PowerSpiritLv2': -1,
    'WisdomSpiritLv2': -1,
    'CourageSpiritLv2': -1,
}

ITEMS_REVERSED = {v: k for k, v in ITEMS.items()}
