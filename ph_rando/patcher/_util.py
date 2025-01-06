from collections.abc import Generator, Iterable
from contextlib import contextmanager
from copy import copy
import hashlib
from io import BytesIO
import logging
from pathlib import Path
import struct

from ndspy import bmg, code, lz10, narc, rom
from vidua import bps
from zed.common import Game
from zed.zmb import ZMB

from ph_rando.common import ShufflerAuxData
from ph_rando.patcher._bmgs import BMGS
from ph_rando.patcher._items import ITEMS
from ph_rando.shuffler.aux_models import (
    Area,
    Chest,
    DigSpot,
    Event,
    MinigameRewardChest,
    SalvageTreasure,
    Shop,
    Tree,
)

logger = logging.getLogger(__name__)

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
    0x28: 'arrowpod',
    0x29: 'bmbagM',  # bmbagL doesn't seem to render anything
    0x2A: 'bcbagM',
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
    0x71: 'makimono',
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
    0x7D: 'ship',  # TODO: what to do for random treasure?
    0x7E: 'ship',  # TODO: what to do for random ship part?
    0x7F: '',  # TODO: find warp tablet model
    0x80: '',  # TODO: find bait model
    0x81: 'rupee_bb',
    0x82: 'rupee_bb',
    0x83: '',  # TODO: what is this?
    0x84: '',  # TODO: what is this?
    0x85: 'ship',  # TODO: what to do for random ship part?
    0x86: 'ship',  # TODO: what to do for random treasure?
    0x87: 'ship',  # TODO: what to do for random ship part?
    # TODO: are there any more items?
}


def apply_base_patch(rom_data: bytes) -> rom.NintendoDSRom:
    """Apply the base patch to `input_rom`."""
    # Calculate sha256 of provided ROM
    sha256_calculator = hashlib.sha256()
    sha256_calculator.update(rom_data)
    sha256 = sha256_calculator.hexdigest()

    # Get the path to the base patch for the given ROM, erroring out of it doesn't exist
    base_patch_path = Path(__file__).parents[2] / 'base' / 'out' / f'{sha256}.bps'
    if not base_patch_path.exists():
        raise Exception(f'Invalid ROM! No base patch found for a ROM with sha256 of {sha256}.')

    logger.info(f'Applying base patch for ROM with hash of "{sha256}"...')

    # Apply the base patch to the ROM
    with open(base_patch_path, 'rb') as patch_file:
        patched_rom = bps.patch(source=BytesIO(rom_data), bps_patch=patch_file)

    logger.info('Base patch applied successfully.')

    return rom.NintendoDSRom(data=patched_rom.read())


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


def _patch_zmb_map_objects(aux_data: list[Area], input_rom: rom.NintendoDSRom) -> None:
    logging.info('Patching ZMB map objects...')

    chests: dict[str, Chest | Tree] = {
        '.'.join([area.name, room.name, chest.name]): chest
        for area in aux_data
        for room in area.rooms
        for chest in room.chests
        if isinstance(chest, Chest | Tree)
    }

    zmb_file_paths = {chest.zmb_file_path for chest in chests.values()}

    with open_zmb_files(zmb_file_paths, input_rom) as zmb_files:
        for name, chest in chests.items():
            item_id = ITEMS[chest.contents.name]

            logger.info(f'Patching check "{name}" with item {chest.contents.name}')
            zmb_files[chest.zmb_file_path].mapObjects[chest.zmb_mapobject_index].unk08 = item_id


def _patch_zmb_actors(areas: list[Area], input_rom: rom.NintendoDSRom) -> None:
    logging.info('Patching ZMB actors...')

    salvage_treasures: dict[str, SalvageTreasure] = {
        '.'.join([area.name, room.name, chest.name]): chest
        for area in areas
        for room in area.rooms
        for chest in room.chests
        if type(chest) is SalvageTreasure
    }

    dig_spots: dict[str, DigSpot] = {
        '.'.join([area.name, room.name, chest.name]): chest
        for area in areas
        for room in area.rooms
        for chest in room.chests
        if type(chest) is DigSpot
    }

    all_chests = salvage_treasures | dig_spots

    zmb_file_paths = {
        chest.zmb_file_path
        for chest in all_chests.values()
        if chest.zmb_file_path.lower() != 'todo'
    }

    with open_zmb_files(zmb_file_paths, input_rom) as zmb_files:
        for name, chest in all_chests.items():
            if chest.zmb_file_path.lower() == 'todo':
                logger.warning(f'Skipping {chest.name}, zmb_file_path is "TODO"')
                continue

            item_id = ITEMS[chest.contents.name]
            if item_id == -1:
                logger.warning(f'Skipping {chest.name}, item {chest.contents.name} ID is unknown.')
                continue

            logger.info(f'Patching check "{name}" with item {chest.contents.name}')
            zmb_files[chest.zmb_file_path].actors[chest.zmb_actor_index].unk0C = item_id
            if type(chest) is SalvageTreasure:
                zmb_files[chest.zmb_file_path].actors[chest.zmb_actor_index].unk0C |= 0x8000


def _patch_shop_items(areas: list[Area], input_rom: rom.NintendoDSRom) -> None:
    logging.info('Patching shop items...')

    items: dict[str, Shop] = {
        '.'.join([area.name, room.name, chest.name]): chest
        for area in areas
        for room in area.rooms
        for chest in room.chests
        if type(chest) is Shop
    }

    # Load arm9.bin and overlay table
    arm9_executable = bytearray(code.MainCodeFile(input_rom.arm9, 0x02000000).save(compress=False))
    arm9_executable_o = copy(arm9_executable)
    overlay_table: dict[int, code.Overlay] = input_rom.loadArm9Overlays()

    for name, shop_item in items.items():
        item_id = ITEMS[shop_item.contents.name]
        if item_id == -1:
            logger.warning(
                f'Skipping {shop_item.name}, item {shop_item.contents.name} ID is unknown.'
            )
            continue

        logger.info(f'Patching check "{name}" with item {shop_item.contents.name}')
        assert isinstance(shop_item, Shop)

        # Note, the offset is stored as a string in the aux data so that it can be represented as
        # a hex value for readability. So, we must convert it to an `int` here.
        try:  # TODO: remove this try/catch when all offsets are set correctly in aux data
            overlay_offset = int(shop_item.overlay_offset, base=16)
        except ValueError:
            logger.warning(
                f'Invalid overlay offset "{shop_item.overlay_offset}" for {shop_item.name}.'
            )
            continue

        # Get current values of the items we're about to change
        original_item_id: int = overlay_table[shop_item.overlay].data[overlay_offset]
        original_model_name = f'gd_{GD_MODELS[original_item_id]}'

        # Set the item id to the new one. This changes the "internal" item representation,
        # but not the 3D model that is displayed prior to purchasing the item
        overlay_table[shop_item.overlay].data[overlay_offset] = item_id

        # Set new name of NSBMD/NSBTX 3D model
        new_model_name = f'gd_{GD_MODELS[item_id]}'

        # Use the "untouched" copy of arm9.bin to avoid altering names of models that have
        # already been changed.
        offset = arm9_executable_o.index(f'Player/get/{original_model_name}.nsbmd'.encode('ascii'))
        new_data = bytearray(f'Player/get/{new_model_name}.nsbmd'.encode('ascii') + b'\x00')
        arm9_executable = (
            arm9_executable[:offset] + new_data + arm9_executable[offset + len(new_data) :]
        )
        arm9_executable_o = (
            arm9_executable_o[:offset]
            + b' ' * len(new_data)
            + arm9_executable_o[offset + len(new_data) :]
        )

        offset = arm9_executable_o.index(f'Player/get/{original_model_name}.nsbtx'.encode('ascii'))
        new_data = bytearray(f'Player/get/{new_model_name}.nsbtx'.encode('ascii') + b'\x00')
        arm9_executable = (
            arm9_executable[:offset] + new_data + arm9_executable[offset + len(new_data) :]
        )
        arm9_executable_o = (
            arm9_executable_o[:offset]
            + b' ' * len(new_data)
            + arm9_executable_o[offset + len(new_data) :]
        )

        try:
            offset = overlay_table[shop_item.overlay].data.index(
                original_model_name.encode('ascii')
            )
            new_data = bytearray(new_model_name.encode('ascii') + b'\x00')
            overlay_table[shop_item.overlay].data = (
                overlay_table[shop_item.overlay].data[:offset]
                + new_data
                + overlay_table[shop_item.overlay].data[offset + len(new_data) :]
            )
            # Pad remaining non-NULL chars to 0. If this isn't done and there are characters
            # left from the previous item, the game will crash.
            for i in range(offset + len(new_data), offset + 16):
                overlay_table[shop_item.overlay].data[i] = 0x0
        except ValueError:
            # Random treasure items (which should be fixed to Pink Coral in our hacked base rom)
            # are an exception and do not require this step.
            assert original_item_id == 0x30

        input_rom.files[overlay_table[shop_item.overlay].fileID] = overlay_table[
            shop_item.overlay
        ].save(compress=False)
        input_rom.arm9OverlayTable = code.saveOverlayTable(overlay_table)
        input_rom.arm9 = arm9_executable


def _patch_minigame_items(areas: list[Area], input_rom: rom.NintendoDSRom) -> None:
    logging.info('Patching minigame items...')

    items: dict[str, MinigameRewardChest] = {
        '.'.join([area.name, room.name, chest.name]): chest
        for area in areas
        for room in area.rooms
        for chest in room.chests
        if type(chest) is MinigameRewardChest
    }

    # Load overlay table
    overlay_table: dict[int, code.Overlay] = input_rom.loadArm9Overlays()

    for name, item in items.items():
        item_id = ITEMS[item.contents.name]
        if item_id == -1:
            logger.warning(f'Skipping {item.name}, item {item.contents.name} ID is unknown.')
            continue
        elif item.overlay == -1:
            logger.warning(f'Skipping {item.name}, overlay is unknown.')
            continue

        logger.info(f'Patching check "{name}" with item {item.contents.name}')
        assert isinstance(item, MinigameRewardChest)

        # Note, the offset is stored as a string in the aux data so that it can be represented as
        # a hex value for readability. So, we must convert it to an `int` here.
        try:  # TODO: remove this try/catch when all offsets are set correctly in aux data
            overlay_offset = int(item.overlay_offset, base=16)
        except ValueError:
            logger.warning(f'Invalid overlay offset "{item.overlay_offset}" for {item.name}.')
            continue

        # Set the item id to the new one.
        overlay_table[item.overlay].data[overlay_offset] = item_id

        input_rom.files[overlay_table[item.overlay].fileID] = overlay_table[item.overlay].save(
            compress=False
        )


def _patch_bmg_events(areas: list[Area], input_rom: rom.NintendoDSRom) -> None:
    chests = [
        chest
        for area in areas
        for room in area.rooms
        for chest in room.chests
        if isinstance(chest, Event)
        if chest.bmg_file_path.lower() != 'todo'
    ]

    bmg_file_paths = {chest.bmg_file_path for chest in chests}

    with open_bmg_files(bmg_file_paths, input_rom) as bmg_files:
        for chest in chests:
            item_id = ITEMS[chest.contents.name]
            if item_id == -1:
                logger.warning(f'Skipping {chest.name}, item {chest.contents.name} ID is unknown.')
                continue

            bmg_instructions = bmg_files[chest.bmg_file_path].instructions
            bmg_instructions[chest.bmg_instruction_index] = (
                bmg_instructions[chest.bmg_instruction_index][:4]
                + struct.pack('<B', ITEMS[chest.contents.name])
                + bmg_instructions[chest.bmg_instruction_index][5:]
            )


def _patch_system_bmg(input_rom: rom.NintendoDSRom) -> None:
    """
    Patches the system BMG file to include all non-global "got item" BMG messages,
    effectively making them global.
    The "got item" message is the text that pops up when Link collects an item.
    """
    gims = []

    bmg_data = bmg.BMG(input_rom.getFileByName(BMGS['MainIsland']))
    # Progressive Sword GIM
    gims.append(bmg_data.messages[0x0].stringParts)
    bmg_data = bmg.BMG(input_rom.getFileByName(BMGS['Brave']))
    # Bow GIM
    gims.append(bmg_data.messages[0x5F].stringParts)
    # Shovel GIM
    gims.append(bmg_data.messages[0x60].stringParts)
    bmg_data = bmg.BMG(input_rom.getFileByName(BMGS['Power']))
    # Bombchus GIM
    gims.append(bmg_data.messages[0x71].stringParts)
    # Crimsonine GIM
    gims.append(bmg_data.messages[0x72].stringParts)
    bmg_data = bmg.BMG(input_rom.getFileByName(BMGS['Flame']))
    # Boomerang GIM
    gims.append(bmg_data.messages[0xDC].stringParts)
    bmg_data = bmg.BMG(input_rom.getFileByName(BMGS['Kaitei']))
    # SW/NW/SE/NE Sea Charts GIM
    gims.append(bmg_data.messages[0x1].stringParts)
    gims.append(bmg_data.messages[0x2].stringParts)
    gims.append(bmg_data.messages[0x3].stringParts)
    gims.append(bmg_data.messages[0x4].stringParts)
    bmg_data = bmg.BMG(input_rom.getFileByName(BMGS['WisdomDungeon']))
    # Hammer GIM
    gims.append(bmg_data.messages[0x0].stringParts)
    # King Key GIM
    gims.append(bmg_data.messages[0x1].stringParts)
    # Aquanine GIM
    gims.append(bmg_data.messages[0x2].stringParts)
    bmg_data = bmg.BMG(input_rom.getFileByName(BMGS['Frost']))
    # Grappling Hook GIM
    gims.append(bmg_data.messages[0xDB].stringParts)
    # Azurine GIM
    gims.append(bmg_data.messages[0xDC].stringParts)
    bmg_data = bmg.BMG(input_rom.getFileByName(BMGS['Hidari']))
    # Fishing Rod GIM
    gims.append(bmg_data.messages[0x64].stringParts)
    bmg_data = bmg.BMG(input_rom.getFileByName(BMGS['Torii']))
    # Cannon GIM
    gims.append(bmg_data.messages[0x0].stringParts)
    # Salvage Arm GIM
    gims.append(bmg_data.messages[0x1].stringParts)
    bmg_data = bmg.BMG(input_rom.getFileByName(BMGS['Sea']))
    # Sun Key GIM
    gims.append(bmg_data.messages[0x1B].stringParts)
    bmg_data = bmg.BMG(input_rom.getFileByName(BMGS['Ghost']))
    # Ghost Key GIM
    gims.append(bmg_data.messages[0x3E].stringParts)
    bmg_data = bmg.BMG(input_rom.getFileByName(BMGS['Myou']))
    # Regal Necklace GIM
    gims.append(bmg_data.messages[0x0].stringParts)

    # To avoid overwriting non-empty entries
    if len(gims) > 0xA9 - 0x8A:
        raise Exception(f'Aborting GIM patching, overflow ({len(gims)}/{0xA9 - 0x8A}).')

    bmg_data = bmg.BMG(input_rom.getFileByName(BMGS['System']))
    for i, gim in enumerate(gims):
        bmg_data.messages[0x8A + i].stringParts = gim

    input_rom.setFileByName(BMGS['System'], bmg_data.save())


def patch_items(aux_data: ShufflerAuxData, input_rom: rom.NintendoDSRom) -> rom.NintendoDSRom:
    """
    Patches a ROM with the given aux data.

    Given aux data, an input rom, and an output path, this function reads the aux data and
    patches the input rom with it accordingly, returning the patched rom. Note, the base
    ROM patch is also applied and should be located at the expected location (see apply_base_patch
    function for more details).
    """
    _patch_zmb_map_objects(aux_data.areas, input_rom)
    _patch_zmb_actors(aux_data.areas, input_rom)
    _patch_shop_items(aux_data.areas, input_rom)
    _patch_bmg_events(aux_data.areas, input_rom)
    _patch_system_bmg(input_rom)
    return input_rom
