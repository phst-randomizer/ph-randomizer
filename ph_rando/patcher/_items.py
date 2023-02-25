ITEMS: dict[str, int] = {
    'small_key': 0x1,
    'small_green_rupee': 0x2,
    'oshus_sword': 0x3,
    'wooden_shield': 0x4,
    'force_gem': 0x6,  # TODO: difference between this and 0x1C?
    'bombs': 0x7,
    'bow': 0x8,
    'big_green_rupee': 0x9,
    'heart_container': 0xA,
    'boomerang': 0xC,
    'shovel': 0xD,
    'bombchus': 0xE,
    'boss_key': 0xF,
    'sw_sea_chart': 0x13,
    'nw_sea_chart': 0x14,
    'se_sea_chart': 0x15,
    'ne_sea_chart': 0x16,
    'small_blue_rupee': 0x18,
    'small_red_rupee': 0x19,
    'big_red_rupee': 0x1A,
    'big_gold_rupee': 0x1B,
    'hammer': 0x1F,
    'grappling_hook': 0x20,
    'square_crystal': 0x21,
    'round_crystal': 0x22,
    'triangle_crystal': 0x23,
    'fishing_rod': 0x24,
    'cannon': 0x25,
    'sun_key': 0x26,
    'quiver_upgrade': 0x28,
    'bomb_bag_upgrade': 0x29,
    'bombchu_bag_upgrade': 0x2A,
    'ship_part': 0x2B,
    'king_key': 0x2C,
    'power_gem': 0x2D,
    'wisdom_gem': 0x2E,
    'courage_gem': 0x2F,
    'common_treasure': 0x30,  # TODO: randomize this at run-time
    'regal_necklace': 0x3C,
    'salvage_arm': 0x3D,
    # 'treasure_map_sw1': 0x4B, # TODO: clarify how SW treasure map ids work considering Sun Key
    'treasure_map_sw1': 0x4C,
    'treasure_map_sw2': 0x4D,
    'treasure_map_sw3': 0x4E,
    'treasure_map_sw4': 0x4F,
    'treasure_map_sw5': 0x50,
    'treasure_map_sw6': 0x51,
    'treasure_map_sw7': 0x52,
    'treasure_map_nw1': 0x53,
    'treasure_map_nw2': 0x54,
    'treasure_map_nw3': 0x55,
    'treasure_map_nw4': 0x56,
    'treasure_map_nw5': 0x57,
    'treasure_map_nw6': 0x58,
    'treasure_map_nw7': 0x59,
    'treasure_map_nw8': 0x5A,
    'treasure_map_se1': 0x5B,
    'treasure_map_se2': 0x5C,
    'treasure_map_se3': 0x5D,
    'treasure_map_se4': 0x5E,
    'treasure_map_se5': 0x5F,
    'treasure_map_se6': 0x60,
    'treasure_map_se7': 0x61,
    'treasure_map_se8': 0x62,
    'treasure_map_ne1': 0x63,
    'treasure_map_ne2': 0x64,
    'treasure_map_ne3': 0x65,
    'treasure_map_ne4': 0x66,
    'treasure_map_ne5': 0x67,
    'treasure_map_ne6': 0x68,
    'treasure_map_ne7': 0x69,
    'treasure_map_ne8': 0x6A,
    'crimsonine': 0x72,
    'azurine': 0x73,
    'aquanine': 0x74,
    'red_potion': 0x75,
    'purple_potion': 0x76,
    'yellow_potion': 0x77,
    'sand_of_hours': 0x78,
    'random_treasure': 0x7D,
    'random_ship_part': 0x7E,
    'cyclone_slate': 0x7F,
    'random_ship_part2': 0x85,  # TODO: what is this, and how does it relate to other ship parts?
    # TODO: update these when their ids are known
    'phantom_hourglass': -1,
    'phantom_sword': -1,
    'sand_2m': -1,
    'power_spirit': -1,
    'wisdom_spirit': -1,
    'courage_spirit': -1,
    'spirit_power_lv1': -1,
    'spirit_wisdom_lv1': -1,
    'spirit_courage_lv1': -1,
    'spirit_power_lv2': -1,
    'spirit_wisdom_lv2': -1,
    'spirit_courage_lv2': -1,
}

ITEMS_REVERSED = {v: k for k, v in ITEMS.items()}
