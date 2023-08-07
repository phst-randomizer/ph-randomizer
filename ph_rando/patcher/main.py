from collections.abc import Iterable
import hashlib
from io import BytesIO
import logging
from pathlib import Path
import re
import struct

import click
import inflection
from ndspy import code, rom
from ndspy.codeCompression import compress, decompress
from vidua import bps

from ph_rando.common import RANDOMIZER_SETTINGS, ShufflerAuxData, click_setting_options
from ph_rando.patcher._items import ITEMS
from ph_rando.patcher._util import GD_MODELS, open_bmg_files, open_zmb_files
from ph_rando.shuffler.aux_models import Area, Chest, DigSpot, Event, SalvageTreasure, Shop, Tree

logger = logging.getLogger(__name__)


def apply_base_patch(input_rom_data: bytes) -> rom.NintendoDSRom:
    """Apply the base patch to `input_rom`."""
    # Calculate sha256 of provided ROM
    sha256_calculator = hashlib.sha256()
    sha256_calculator.update(input_rom_data)
    sha256 = sha256_calculator.hexdigest()

    # Get the path to the base patch for the given ROM, erroring out of it doesn't exist
    base_patch_path = Path(__file__).parents[2] / 'base' / 'out' / f'{sha256}.bps'
    if not base_patch_path.exists():
        raise Exception(f'Invalid ROM! No base patch found for a ROM with sha256 of {sha256}.')

    # Apply the base patch to the ROM
    with open(base_patch_path, 'rb') as patch_file:
        patched_rom = bps.patch(source=BytesIO(input_rom_data), bps_patch=patch_file)

    return rom.NintendoDSRom(data=patched_rom.read())


def _patch_zmb_map_objects(aux_data: Iterable[Area], input_rom: rom.NintendoDSRom) -> None:
    chests = [
        chest
        for area in aux_data
        for room in area.rooms
        for chest in room.chests
        if isinstance(chest, Chest | Tree)
    ]

    zmb_file_paths = {
        chest.zmb_file_path for chest in chests if chest.zmb_file_path.lower() != 'todo'
    }

    with open_zmb_files(zmb_file_paths, input_rom) as zmb_files:
        for chest in chests:
            if chest.zmb_file_path.lower() == 'todo':
                logger.warning(f'Skipping {chest.name}, zmb_file_path is "TODO"')
                continue
            zmb_files[chest.zmb_file_path].mapObjects[chest.zmb_mapobject_index].unk08 = ITEMS[
                chest.contents.name
            ]


def _patch_zmb_actors(areas: Iterable[Area], input_rom: rom.NintendoDSRom) -> None:
    salvage_treasures = {
        chest
        for area in areas
        for room in area.rooms
        for chest in room.chests
        if type(chest) == SalvageTreasure
    }

    dig_spots = {
        chest
        for area in areas
        for room in area.rooms
        for chest in room.chests
        if type(chest) == DigSpot
    }

    all_chests = salvage_treasures | dig_spots

    zmb_file_paths = {
        chest.zmb_file_path for chest in all_chests if chest.zmb_file_path.lower() != 'todo'
    }

    with open_zmb_files(zmb_file_paths, input_rom) as zmb_files:
        for chest in all_chests:
            if chest.zmb_file_path.lower() == 'todo':
                logger.warning(f'Skipping {chest.name}, zmb_file_path is "TODO"')
                continue
            zmb_files[chest.zmb_file_path].actors[chest.zmb_actor_index].unk0C = ITEMS[
                chest.contents.name
            ]
            if type(chest) == SalvageTreasure:
                zmb_files[chest.zmb_file_path].actors[chest.zmb_actor_index].unk0C |= 0x8000


def _patch_shop_items(areas: Iterable[Area], input_rom: rom.NintendoDSRom) -> None:
    items = {
        chest
        for area in areas
        for room in area.rooms
        for chest in room.chests
        if type(chest) == Shop
    }

    # Load arm9.bin and overlay table
    arm9_executable = bytearray(code.MainCodeFile(input_rom.arm9, 0x02000000).save(compress=False))
    overlay_table: dict[int, code.Overlay] = input_rom.loadArm9Overlays()

    for shop_item in items:
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
        overlay_table[shop_item.overlay].data[overlay_offset] = ITEMS[shop_item.contents.name]

        # Set new name of NSBMD/NSBTX 3D model
        new_model_name = f'gd_{GD_MODELS[ITEMS[shop_item.contents.name]]}'
        offset = arm9_executable.index(f'Player/get/{original_model_name}.nsbmd'.encode('ascii'))
        new_data = bytearray(f'Player/get/{new_model_name}.nsbmd'.encode('ascii') + b'\x00')
        arm9_executable = (
            arm9_executable[:offset] + new_data + arm9_executable[offset + len(new_data) :]
        )
        offset = arm9_executable.index(f'Player/get/{original_model_name}.nsbtx'.encode('ascii'))
        new_data = bytearray(f'Player/get/{new_model_name}.nsbtx'.encode('ascii') + b'\x00')
        arm9_executable = (
            arm9_executable[:offset] + new_data + arm9_executable[offset + len(new_data) :]
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


def _patch_bmg_events(areas: Iterable[Area], input_rom: rom.NintendoDSRom) -> None:
    chests = [
        chest
        for area in areas
        for room in area.rooms
        for chest in room.chests
        if isinstance(chest, Event)
    ]

    bmg_file_paths = {
        chest.bmg_file_path for chest in chests if chest.bmg_file_path.lower() != 'todo'
    }

    with open_bmg_files(bmg_file_paths, input_rom) as bmg_files:
        for chest in chests:
            bmg_instructions = bmg_files[chest.bmg_file_path].instructions
            bmg_instructions[chest.bmg_instruction_index] = (
                bmg_instructions[chest.bmg_instruction_index][:4]
                + struct.pack('<B', ITEMS[chest.contents.name])
                + bmg_instructions[chest.bmg_instruction_index][5:]
            )


def patch_items(aux_data: ShufflerAuxData, input_rom: rom.NintendoDSRom) -> rom.NintendoDSRom:
    """
    Patches a ROM with the given aux data.

    Given aux data, an input rom, and an output path, this function reads the aux data and
    patches the input rom with it accordingly, returning the patched rom. Note, the base
    ROM patch is also applied and should be located at the expected location (see apply_base_patch
    function for more details).
    """
    _patch_zmb_map_objects(aux_data.areas.values(), input_rom)
    _patch_zmb_actors(aux_data.areas.values(), input_rom)
    _patch_shop_items(aux_data.areas.values(), input_rom)
    _patch_bmg_events(aux_data.areas.values(), input_rom)

    return input_rom


def apply_settings_patches(
    base_patched_rom: rom.NintendoDSRom,
    settings: dict[str, bool | str],
) -> rom.NintendoDSRom:
    base_flags_addr = 0x58180  # address specified by .fill directive in main.asm
    flags_header_file = (
        Path(__file__).parents[2] / 'base' / 'code' / 'rando_settings.h'
    ).read_text()
    arm9_bin: bytearray = decompress(base_patched_rom.arm9)

    for setting in RANDOMIZER_SETTINGS:
        setting_value = settings[inflection.underscore(setting.name)]
        logger.debug(f'Setting {setting.name!r} set to {setting_value!r}.')

        if isinstance(setting_value, bool) and not setting_value:
            continue
        elif isinstance(setting_value, bool):
            setting_name_header = inflection.underscore(setting.name[2:]).upper()
            matches = re.findall(rf'#define {setting_name_header} (.+), (.+)', flags_header_file)

            if not len(matches):
                continue

            assert len(matches) == 1
            flag_offset, flag_bit = matches[0]
            arm9_bin[base_flags_addr + int(flag_offset, 16)] |= int(flag_bit, 16)
        else:
            # TODO: implement string-based settings here
            pass

    base_patched_rom.arm9 = compress(arm9_bin, isArm9=True)
    return base_patched_rom


@click.command()
@click.option(
    '-a',
    '--aux-data-directory',
    required=True,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help='Path to directory containing the aux data to patch the ROM with.',
)
@click.option(
    '-i',
    '--input-rom-path',
    required=True,
    type=click.Path(exists=False, path_type=Path),
    help='Path to ROM to patch.',
)
@click.option(
    '-o', '--output-rom-path', default=None, type=str, help='Path to save patched ROM to.'
)
@click.option(
    '-l',
    '--log-level',
    type=click.Choice(
        list(logging.getLevelNamesMapping().keys()),
        case_sensitive=False,
    ),
    default='INFO',
)
@click_setting_options
def patcher_cli(
    aux_data_directory: Path,
    input_rom_path: Path,
    output_rom_path: str | None,
    log_level: str,
    **settings: bool | str,
) -> None:
    from ph_rando.shuffler._shuffler import parse_aux_data

    logging.basicConfig(level=logging.getLevelNamesMapping()[log_level])

    new_aux_data = parse_aux_data(
        areas_directory=aux_data_directory,
        enemy_mapping_file=Path(__file__).parents[1] / 'shuffler' / 'enemies.json',
        macros_file=Path(__file__).parents[1] / 'shuffler' / 'macros.json',
    )

    patched_rom = apply_base_patch(input_rom_path.read_bytes())

    patched_rom = apply_settings_patches(patched_rom, settings)

    patched_rom = patch_items(new_aux_data, patched_rom)

    if output_rom_path is not None:
        # Save the ROM to disk
        patched_rom.saveToFile(output_rom_path)


if __name__ == '__main__':
    patcher_cli()
