from contextlib import contextmanager

from ndspy import lz10, narc
from ndspy.rom import NintendoDSRom
from zed import common, zmb


@contextmanager
def edit_zmb(rom: NintendoDSRom, narc_path: str, zmb_path: str):
    narc_file = narc.NARC(lz10.decompress(rom.getFileByName(narc_path)))
    zmb_file = zmb.ZMB(common.Game.PhantomHourglass, narc_file.getFileByName(zmb_path))
    yield zmb_file
    narc_file.setFileByName(zmb_path, zmb_file.save(common.Game.PhantomHourglass))
    rom.setFileByName(narc_path, lz10.compress(narc_file.save()))


def _patch_mercay_earthquake(rom: NintendoDSRom) -> NintendoDSRom:
    """Disables the earthquake CS on Mercay at beginning of game by removing the `EQAR` actor."""
    with edit_zmb(rom, 'Map/isle_main/map00.bin', 'zmb/isle_main_00.zmb') as zmb_file:
        earthquake_actors = [actor for actor in zmb_file.actors if actor.type == 'EQAR']
        assert len(earthquake_actors) == 1
        zmb_file.actors.remove(earthquake_actors[0])

    return rom


def _patch_mercay_town_cutscenes(rom: NintendoDSRom) -> NintendoDSRom:
    """
    Disables all cutscenes on Mercay Town.

    Includes:
        - CS when approaching the SS Linebeck for first time (guy that is admiring the boat)
        - CS when leaving the cave (plays when entering town for first time in vanilla)
        - ??? third CS is unknown
    """
    with edit_zmb(rom, 'Map/isle_main/map03.bin', 'zmb/isle_main_03.zmb') as zmb_file:
        nmsg_actors = [actor for actor in zmb_file.actors if actor.type == 'NMSG']
        assert len(nmsg_actors) == 3
        for actor in nmsg_actors:
            zmb_file.actors.remove(actor)

    return rom


def _patch_totok_lobby_cutscenes(rom: NintendoDSRom) -> NintendoDSRom:
    """Disable all cutscenes that play in ToTOK lobby."""
    with edit_zmb(rom, 'Map/dngn_main_f/map00.bin', 'zmb/dngn_main_f_00.zmb') as zmb_file:
        ncma_actors = [actor for actor in zmb_file.actors if actor.type == 'NCMA']
        assert len(ncma_actors) == 4
        for actor in ncma_actors:
            zmb_file.actors.remove(actor)

    return rom


def patch_actors(rom: NintendoDSRom) -> NintendoDSRom:
    """Applies all patches to NPCA actor section of ZMBs."""
    _patch_mercay_earthquake(rom)
    _patch_mercay_town_cutscenes(rom)
    _patch_totok_lobby_cutscenes(rom)

    return rom
