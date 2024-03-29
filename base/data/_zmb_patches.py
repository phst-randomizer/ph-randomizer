from collections.abc import Generator
from contextlib import contextmanager

from ndspy import lz10, narc
from ndspy.rom import NintendoDSRom
from zed import common, zmb


@contextmanager
def edit_zmb(rom: NintendoDSRom, narc_path: str, zmb_path: str) -> Generator[zmb.ZMB, None, None]:
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


def _patch_mercay_outside_oshus_house_cutscenes(rom: NintendoDSRom) -> NintendoDSRom:
    """Disables cutscenes on area outside Oshus's house."""
    with edit_zmb(rom, 'Map/isle_main/map00.bin', 'zmb/isle_main_00.zmb') as zmb_file:
        ciela_outside_oshus_house_cs = zmb_file.actors[8]
        assert ciela_outside_oshus_house_cs.type == 'NMSG'
        assert ciela_outside_oshus_house_cs.x == 608
        assert ciela_outside_oshus_house_cs.y == 112
        zmb_file.actors.remove(ciela_outside_oshus_house_cs)
    return rom


def _patch_totok_lobby_cutscenes(rom: NintendoDSRom) -> NintendoDSRom:
    """Disable all cutscenes that play in ToTOK lobby."""
    with edit_zmb(rom, 'Map/dngn_main_f/map00.bin', 'zmb/dngn_main_f_00.zmb') as zmb_file:
        ncma_actors = [actor for actor in zmb_file.actors if actor.type == 'NCMA']
        assert len(ncma_actors) == 4
        for actor in ncma_actors:
            zmb_file.actors.remove(actor)

    return rom


def _add_chest_for_phantom_hourglass(rom: NintendoDSRom) -> NintendoDSRom:
    """
    Add a chest in front of the pedestal that you normally get the phantom hourglass from,
    and removes the phantom hourglass from the pedestal.
    This serves as a replacement for the phantom hourglass pedestal as an item location.
    """
    with edit_zmb(rom, 'Map/dngn_main_f/map00.bin', 'zmb/dngn_main_f_00.zmb') as zmb_file:
        # Remove hourglass from pedestal
        hgoj_actors = [a for a in zmb_file.actors if a.type == 'HGOJ']
        assert len(hgoj_actors) == 1
        zmb_file.actors.remove(hgoj_actors[0])
        # Add new chest containing the phantom hourglass
        chest = zmb.MapObject(game=common.Game.PhantomHourglass)
        chest.x = 33
        chest.y = 12
        chest.rotation = 0
        chest.unk08 = 0x12
        chest.unk0A = 0
        chest.unk0C = 0
        chest.unk10 = 1
        chest.unk11 = 1
        chest.unk12 = 0
        chest.unk13 = 0
        chest.scriptID = 0
        chest.unk1A = 0
        chest.unk1B = 0
        chest.type = 10
        zmb_file.mapObjects.append(chest)
        # NOTE: this should match what's in the aux data.
        assert zmb_file.mapObjects.index(chest) == 8
    return rom


def _patch_mercay_north_cutscenes(rom: NintendoDSRom) -> NintendoDSRom:
    """
    Disable all cutscenes that play in north Mercay area (front of ToTOK + chu area above Oshus)
    """
    with edit_zmb(rom, 'Map/isle_main/map01.bin', 'zmb/isle_main_01.zmb') as zmb_file:
        nmsg_actors = [actor for actor in zmb_file.actors if actor.type == 'NMSG']
        assert len(nmsg_actors) == 4
        for actor in nmsg_actors:
            zmb_file.actors.remove(actor)
    return rom


def _patch_sunkey_first_sight_cutscene(rom: NintendoDSRom) -> NintendoDSRom:
    """
    Disable celia dialog that plays the first time you see the Sun Key door on molida.
    """
    with edit_zmb(rom, 'Map/isle_pluck/map10.bin', 'zmb/isle_pluck_10.zmb') as zmb_file:
        fmsg_actors = [actor for actor in zmb_file.actors if actor.type == 'FMSG']
        assert len(fmsg_actors) == 1
        zmb_file.actors.remove(fmsg_actors[0])
    return rom


def _patch_sw_nw_sea_transition_tornado(rom: NintendoDSRom) -> NintendoDSRom:
    """
    Disable tornados preventing access to NW Sea from SW sea.
    """
    with edit_zmb(rom, 'Map/sea/map00.bin', 'zmb/sea_00.zmb') as zmb_file:
        hrcn_actors = [actor for actor in zmb_file.actors if actor.type == 'HRCN']
        assert len(hrcn_actors) == 1
        zmb_file.actors.remove(hrcn_actors[0])
    return rom


def patch_zmb_files(rom: NintendoDSRom) -> NintendoDSRom:
    """Applies all patches to ZMB files."""
    _patch_mercay_earthquake(rom)
    _patch_mercay_outside_oshus_house_cutscenes(rom)
    _patch_mercay_town_cutscenes(rom)
    _patch_mercay_north_cutscenes(rom)
    _patch_totok_lobby_cutscenes(rom)
    _add_chest_for_phantom_hourglass(rom)
    _patch_sunkey_first_sight_cutscene(rom)
    _patch_sw_nw_sea_transition_tornado(rom)

    return rom
