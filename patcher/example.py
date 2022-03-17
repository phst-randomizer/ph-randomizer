from typing import Union

from patcher import settings
from patcher.location_types import EventLocation, IslandShopLocation, MapObjectLocation

LOCATIONS: dict[str, Union[EventLocation, IslandShopLocation, MapObjectLocation]] = {
    "ocean_temple_first_chest": MapObjectLocation(
        34, "Map/dngn_main/map00.bin/zmb/dngn_main_00.zmb"
    ),
    "mercay_island_first_npc": EventLocation(135, "English/Message/main_isl.bmg"),
    "mercay_island_chest_on_small_island": MapObjectLocation(
        54, "Map/isle_main/map02.bin/zmb/isle_main_02.zmb"
    ),
    "mercay_island_rollable_tree": MapObjectLocation(
        25, "Map/isle_main/map02.bin/zmb/isle_main_02.zmb"
    ),
    "mercay_island_SE_cliff_chest_left": MapObjectLocation(
        97, "Map/isle_main/map03.bin/zmb/isle_main_03.zmb"
    ),
    "mercay_island_SE_cliff_chest_right": MapObjectLocation(
        98, "Map/isle_main/map03.bin/zmb/isle_main_03.zmb"
    ),
    "mercay_island_SE_cucco_chest": MapObjectLocation(
        113, "Map/isle_main/map03.bin/zmb/isle_main_03.zmb"
    ),
    "mercay_island_shipyard_chest": MapObjectLocation(
        2, "Map/isle_main/map16.bin/zmb/isle_main_16.zmb"
    ),
    "mercay_island_oshus_sword_chest": MapObjectLocation(
        1, "Map/isle_main/map19.bin/zmb/isle_main_19.zmb"
    ),
    "mercay_island_shop_shield": IslandShopLocation(31, 0x217ECB4 - 0x217BCE0),
    "mercay_island_shop_power_gem": IslandShopLocation(31, 0x217EC68 - 0x217BCE0),
    "isle_ember_chest_near_flame_temple": MapObjectLocation(
        74, "Map/isle_flame/map00.bin/zmb/isle_flame_00.zmb"
    ),
    "isle_ember_chest_on_northern_small_island": MapObjectLocation(
        75, "Map/isle_flame/map00.bin/zmb/isle_flame_00.zmb"
    ),
    "flame_temple_first_floor_key_chest": MapObjectLocation(
        26, "Map/dngn_flame/map00.bin/zmb/dngn_flame_00.zmb"
    ),
    "flame_temple_first_floor_red_rupee_chest": MapObjectLocation(
        68, "Map/dngn_flame/map00.bin/zmb/dngn_flame_00.zmb"
    ),
    "flame_temple_second_floor_boomerang_chest": MapObjectLocation(
        7, "Map/dngn_flame/map01.bin/zmb/dngn_flame_01.zmb"
    ),
    "flame_temple_third_floor_big_key_chest": MapObjectLocation(
        15, "Map/dngn_flame/map02.bin/zmb/dngn_flame_02.zmb"
    ),
    "flame_temple_boss_chest": MapObjectLocation(
        2, "Map/boss_flame/map00.bin/zmb/boss_flame_00.zmb"
    ),
}

# Set every location to a gold rupee
for _, location in LOCATIONS.items():
    location.set_location(0x1B)

EventLocation.save_all()
IslandShopLocation.save_all()
MapObjectLocation.save_all()

settings.ROM.saveToFile("out.nds")
