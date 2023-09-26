import hashlib
import importlib
from io import BytesIO
import logging
from pathlib import Path
from typing import Self

from ndspy.rom import NintendoDSRom
from vidua import bps

from ph_rando.common import ShufflerAuxData
from ph_rando.settings import PatcherHook
from ph_rando.shuffler._parser import parse_aux_data
from ph_rando.shuffler.aux_models import Area, Check

from ._util import patch_items

logger = logging.getLogger(__name__)


class Patcher:
    settings: dict[str, str | list[str] | bool]
    aux_data: ShufflerAuxData
    rom: NintendoDSRom

    _original_areas: list[Area]
    _checks_to_exclude: set[Check]

    def __init__(
        self: Self,
        rom: Path,
        aux_data: ShufflerAuxData,
        settings: dict[str, str | list[str] | bool],
    ) -> None:
        self.settings = settings
        self.aux_data = aux_data

        # Figure out which items are still in their vanilla locations, and add them to
        # a blacklist so we can avoid redundant work.
        vanilla_areas = {
            '.'.join([area.name, room.name, chest.name]): chest.contents
            for area in parse_aux_data().areas
            for room in area.rooms
            for chest in room.chests
        }
        self._checks_to_exclude = set()
        for area in self.aux_data.areas:
            for room in area.rooms:
                for chest in room.chests:
                    chest_name = '.'.join([area.name, room.name, chest.name])
                    if (
                        vanilla_areas[chest_name].name,
                        vanilla_areas[chest_name].states,
                    ) == (
                        chest.contents.name,
                        chest.contents.states,
                    ):
                        self._checks_to_exclude.add(chest)

        self.rom = self._apply_base_patch(rom.read_bytes())
        self._apply_settings()

    def generate(self: Self) -> NintendoDSRom:
        return patch_items(self.aux_data, self.rom)

    def _apply_settings(self) -> None:
        from ph_rando.common import RANDOMIZER_SETTINGS

        for setting_name, setting_value in self.settings.items():
            patcher_hook = RANDOMIZER_SETTINGS[setting_name].patcher_hook
            if patcher_hook:
                fn: PatcherHook = getattr(
                    importlib.import_module('ph_rando.patcher._settings'), patcher_hook
                )
                fn(value=setting_value, patcher=self)

    def _apply_base_patch(self: Self, rom_data: bytes) -> NintendoDSRom:
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

        return NintendoDSRom(data=patched_rom.read())
