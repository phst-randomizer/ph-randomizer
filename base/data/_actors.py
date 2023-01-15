from ndspy import lz10, narc
from ndspy.rom import NintendoDSRom
from zed import common, zmb


def _patch_mercay_earthquake(rom: NintendoDSRom) -> NintendoDSRom:
    """Disables the earthquake CS on Mercay at beginning of game by removing the `EQAR` actor."""
    narc_file = narc.NARC(lz10.decompress(rom.getFileByName('Map/isle_main/map00.bin')))
    zmb_file = zmb.ZMB(
        common.Game.PhantomHourglass, narc_file.getFileByName('zmb/isle_main_00.zmb')
    )

    earthquake_actors = [actor for actor in zmb_file.actors if actor.type == 'EQAR']
    assert len(earthquake_actors) == 1
    zmb_file.actors.remove(earthquake_actors[0])

    narc_file.setFileByName('zmb/isle_main_00.zmb', zmb_file.save(common.Game.PhantomHourglass))
    rom.setFileByName('Map/isle_main/map00.bin', lz10.compress(narc_file.save()))

    return rom


def patch_actors(rom: NintendoDSRom) -> NintendoDSRom:
    """Applies all patches to NPCA actor section of ZMBs."""
    _patch_mercay_earthquake(rom)
    ...  # Other patches go here

    return rom
