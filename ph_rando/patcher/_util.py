from collections.abc import Generator, Iterable
from contextlib import contextmanager

from ndspy import bmg, lz10, narc, rom
from zed.common import Game
from zed.zmb import ZMB

GD_MODELS = {
    0x00: None,
    0x01: 'key',
    0x02: 'rupee_g',
    0x03: 'swA',
    0x04: 'shA',
    0x05: '',  # TODO: what is this?
    0x06: 'force_y',  # TODO: find force gem model
    0x07: 'bomb',
    0x08: 'bow',
    0x09: 'rupee_g',
    0x0A: 'heart_utu',
    0x0B: '',  # TODO: what is this?
    0x0C: 'boomerang',
    0x0D: 'scp',
    0x0E: 'bomchu',
    0x0F: 'bosskey',
    0x10: 'rev_bin',
    0x11: '',  # TODO: what is this?
    0x12: '',  # TODO: what is this?
    0x13: 'mapSea',
    0x14: 'mapSea',
    0x15: 'mapSea',
    0x16: 'mapSea',
    0x17: '',  # TODO: what is this?
    0x18: 'rupee_b',
    0x19: 'rupee_r',
    0x1A: 'rupee_r',
    0x1B: 'rupee_go',
    0x1C: 'force_y',  # NOTE: Used in multiplayer mode only
    0x1D: 'force_r',  # NOTE: Used in multiplayer mode only
    0x1E: 'force_b',  # NOTE: Used in multiplayer mode only
    0x1F: 'ham',
    0x20: 'rope',
    0x21: 'cstl_c',
    0x22: 'cstl_s',
    0x23: 'cstl_t',
    0x24: 'fp',
    0x25: 'ship',  # TODO: ship or ship02?
    0x26: 'key_su',
    0x27: '',  # TODO: what is this?
    0x28: 'arrowpodL',  # TODO: arrowpod or arrowpodL?
    0x29: 'bmbagL',  # TODO: bmbag or bmbagL or bmbagM?
    0x2A: 'bcbagL',  # TODO: bcbag or bcbagL or bcbagM?
    0x2B: '',  # TODO: what is this?
    0x2C: 'key_ki',
    0x2D: 'minaP',
    0x2E: 'minaC',
    0x2F: 'minaY',
    0x30: 'sango',
    0x31: 'perlA',
    0x32: 'perlB',
    0x33: 'uroko',
    0x34: 'mineral',
    0x35: 'crown',
    0x36: 'wing',
    0x37: 'ring',
    0x38: 'key_gh',
    0x39: 'tic_tada',
    0x3A: 'tic_ohome',
    0x3B: 'tic_rare',
    0x3C: 'neckl',
    0x3D: 'slvarm',
    0x3E: '',  # TODO: find id for hero"s new clothes
    0x3F: 'telescope',
    0x40: 'notebook',
    0x41: 'letter',
    0x42: 'card',
    0x43: 'marron',
    0x44: '',  # TODO: what is this?
    0x45: '',  # TODO: what is this?
    0x46: '',  # TODO: what is this?
    0x47: '',  # TODO: what is this?
    0x48: '',  # TODO: what is this?
    0x49: '',  # TODO: what is this?
    0x4A: '',  # TODO: what is this?
    0x4B: 'mapTakara',
    0x4C: 'mapTakara',
    0x4D: 'mapTakara',
    0x4E: 'mapTakara',
    0x4F: 'mapTakara',
    0x50: 'mapTakara',
    0x51: 'mapTakara',
    0x52: 'mapTakara',
    0x53: 'mapTakara',
    0x54: 'mapTakara',
    0x55: 'mapTakara',
    0x56: 'mapTakara',
    0x57: 'mapTakara',
    0x58: 'mapTakara',
    0x59: 'mapTakara',
    0x5A: 'mapTakara',
    0x5B: 'mapTakara',
    0x5C: 'mapTakara',
    0x5D: 'mapTakara',
    0x5E: 'mapTakara',
    0x5F: 'mapTakara',
    0x60: 'mapTakara',
    0x61: 'mapTakara',
    0x62: 'mapTakara',
    0x63: 'mapTakara',
    0x64: 'mapTakara',
    0x65: 'mapTakara',
    0x66: 'mapTakara',
    0x67: 'mapTakara',
    0x68: 'mapTakara',
    0x69: 'mapTakara',
    0x6A: 'mapTakara',
    0x6B: '',  # TODO: what is this?
    0x6C: '',  # TODO: what is this?
    0x6D: '',  # TODO: what is this?
    0x6E: '',  # TODO: what is this?
    0x6F: '',  # TODO: what is this?
    0x70: '',  # TODO: what is this?
    0x71: '',
    0x72: 'hagaH',
    0x73: 'hagaK',
    0x74: 'hagaS',
    0x75: 'rev_bin',
    0x76: 'rev_binP',
    0x77: 'rev_binY',
    0x78: 'sand_m',
    0x79: 'ship',  # TODO: ship or ship02?
    0x7A: 'ship',  # TODO: ship or ship02?
    0x7B: 'ship',  # TODO: ship or ship02?
    0x7C: 'ship',  # TODO: ship or ship02?
    0x7D: '',  # TODO: what to do for random treasure?
    0x7E: '',  # TODO: what to do for random ship part?
    0x7F: '',  # TODO: find warp tablet model
    0x80: '',  # TODO: find bait model
    0x81: 'rupee_bb',
    0x82: 'rupee_bb',
    0x83: '',  # TODO: what is this?
    0x84: '',  # TODO: what is this?
    0x85: '',  # TODO: what to do for random ship part?
    0x86: '',  # TODO: what to do for random treasure?
    0x87: '',  # TODO: what to do for random ship part?
    # TODO: are there any more items?
}


@contextmanager
def open_bmg_files(
    bmg_file_paths: Iterable[str],
    input_rom: rom.NintendoDSRom,
) -> Generator[dict[str, bmg.BMG], None, None]:
    bmg_file_map: dict[str, bmg.BMG] = {}

    bmg_file_map = {
        bmg_path: bmg.BMG(input_rom.getFileByName(bmg_path)) for bmg_path in bmg_file_paths
    }

    yield bmg_file_map

    for path, bmg_file in bmg_file_map.items():
        input_rom.setFileByName(path, bmg_file.save())


@contextmanager
def open_zmb_files(
    zmb_file_paths: Iterable[str],
    input_rom: rom.NintendoDSRom,
) -> Generator[dict[str, ZMB], None, None]:
    zmb_file_map: dict[str, ZMB] = {}

    for path in zmb_file_paths:
        narc_path = path[: path.index('.bin/') + 4]
        zmb_path = path[path.index('.bin/') + 5 :]
        narc_file = narc.NARC(lz10.decompress(input_rom.getFileByName(narc_path)))
        zmb_file = ZMB(game=Game.PhantomHourglass, data=narc_file.getFileByName(zmb_path))
        zmb_file_map[path] = zmb_file

    yield zmb_file_map

    for path, zmb_file in zmb_file_map.items():
        narc_path = path[: path.index('.bin/') + 4]
        zmb_path = path[path.index('.bin/') + 5 :]
        narc_file = narc.NARC(lz10.decompress(input_rom.getFileByName(narc_path)))
        narc_file.setFileByName(zmb_path, zmb_file.save(game=Game.PhantomHourglass))
        input_rom.setFileByName(narc_path, lz10.compress(narc_file.save()))
