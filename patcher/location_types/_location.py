from ndspy.rom import NintendoDSRom


class Location:
    """Parent class that all location types inherit from so that they can access the rom."""

    ROM: NintendoDSRom | None = None
