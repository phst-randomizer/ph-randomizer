# This file contains example code for how to set item locations.

from locations import LOCATIONS

from patcher import settings
from patcher.location_types import (
    DigSpotLocation,
    EventLocation,
    IslandShopLocation,
    MapObjectLocation,
)

# Set every location to a gold rupee
for _, location in LOCATIONS.items():
    location.set_location(0x1B)

DigSpotLocation.save_all()
EventLocation.save_all()
IslandShopLocation.save_all()
MapObjectLocation.save_all()

settings.ROM.saveToFile("out.nds")
