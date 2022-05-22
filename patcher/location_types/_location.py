from ndspy.rom import NintendoDSRom


class Location:
    """Parent class that all location types inherit from so that they can access the rom."""

    ROM: NintendoDSRom

    @classmethod
    def save_all(cls):
        for subclass in cls.__subclasses__():
            subclass.save_all()
