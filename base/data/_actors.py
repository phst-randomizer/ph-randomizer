from ndspy import lz10, narc
from ndspy.rom import NintendoDSRom
from zed import common, zmb


def _load_zmb(rom: NintendoDSRom, narc_path: str, zmb_path: str) -> zmb.ZMB:
    narc_file = narc.NARC(lz10.decompress(rom.getFileByName(narc_path)))
    return zmb.ZMB(common.Game.PhantomHourglass, narc_file.getFileByName(zmb_path))


def _save_zmb(rom: NintendoDSRom, zmb: zmb.ZMB, narc_path: str, zmb_path: str) -> None:
    narc_file = narc.NARC(lz10.decompress(rom.getFileByName(narc_path)))
    narc_file.setFileByName(zmb_path, zmb.save(common.Game.PhantomHourglass))
    rom.setFileByName(narc_path, lz10.compress(narc_file.save()))


def _patch_mercay_earthquake(rom: NintendoDSRom) -> NintendoDSRom:
    """Disables the earthquake CS on Mercay at beginning of game by removing the `EQAR` actor."""
    narc_path = 'Map/isle_main/map00.bin'
    zmb_path = 'zmb/isle_main_00.zmb'

    zmb_file = _load_zmb(rom, narc_path, zmb_path)

    earthquake_actors = [actor for actor in zmb_file.actors if actor.type == 'EQAR']
    assert len(earthquake_actors) == 1
    zmb_file.actors.remove(earthquake_actors[0])

    _save_zmb(rom, zmb_file, narc_path, zmb_path)

    return rom


def _patch_mercay_town_cutscenes(rom: NintendoDSRom) -> NintendoDSRom:
    """
    Disables all cutscenes on Mercay Town.

    Includes:
        - CS when approaching the SS Linebeck for first time (guy that is admiring the boat)
        - CS when leaving the cave (plays when entering town for first time in vanilla)
        - ??? third CS is unknown
    """
    narc_path = 'Map/isle_main/map03.bin'
    zmb_path = 'zmb/isle_main_03.zmb'

    zmb_file = _load_zmb(rom, narc_path, zmb_path)

    nmsg_actors = [actor for actor in zmb_file.actors if actor.type == 'NMSG']
    assert len(nmsg_actors) == 3
    for actor in nmsg_actors:
        zmb_file.actors.remove(actor)

    _save_zmb(rom, zmb_file, narc_path, zmb_path)

    return rom


def patch_actors(rom: NintendoDSRom) -> NintendoDSRom:
    """Applies all patches to NPCA actor section of ZMBs."""
    _patch_mercay_earthquake(rom)
    _patch_mercay_town_cutscenes(rom)
    ...  # Other patches go here

    return rom
