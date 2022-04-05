import os

from ndspy.rom import NintendoDSRom

ROM = NintendoDSRom.fromFile(os.environ.get("PH_ROM_PATH", "base/out/out.nds"))
