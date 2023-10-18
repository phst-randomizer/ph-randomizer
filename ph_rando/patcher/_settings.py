from __future__ import annotations

from typing import TYPE_CHECKING

from ndspy.codeCompression import compress, decompress

if TYPE_CHECKING:
    from ph_rando.patcher._patcher import Patcher

# address specified by .fill directive in main.asm. TODO: get this dynamically
BASE_FLAGS_ADDR = 0x58180


def mercay_bridge_repaired(value: bool, patcher: Patcher) -> None:
    if value:
        arm9_bin: bytearray = decompress(patcher.rom.arm9)

        # This needs to match up with MERCAY_BRIDGE_REPAIRED_FROM_START
        # in base/code/rando_settings.h
        flag_offset, flag_bit = 0, 0x1

        arm9_bin[BASE_FLAGS_ADDR + flag_offset] |= flag_bit
        patcher.rom.arm9 = compress(arm9_bin, isArm9=True)
