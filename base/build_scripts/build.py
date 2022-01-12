#!/usr/bin/env python3

from pathlib import Path
import shutil
import struct
import subprocess
import sys

from common import (
    ARMIPS_EXECUTABLE_PATH,
    BLZ_EXECUTABLE_PATH,
    NDSTOOL_EXECUTABLE_PATH,
    overlays_to_modify,
)


def build_arm9():
    root_directory = (Path(__file__).parent.parent.parent).resolve()
    asm_directory = (Path(__file__).parent.parent / "asm").resolve()
    # important: cast the generator to a list unless you want this
    # loop to keep running until your harddrive runs out of space :)
    for file in list(root_directory.rglob("*.bin")):
        file = Path(file).relative_to(root_directory)
        Path(asm_directory / file.parent).mkdir(parents=True, exist_ok=True)
        shutil.move(root_directory / file, asm_directory / file)
    subprocess.run([ARMIPS_EXECUTABLE_PATH, "main.asm", "-root", str(asm_directory)])
    # important: cast to list, see above commment
    for file in list(asm_directory.rglob("*.bin")):
        file = Path(file).relative_to(asm_directory)
        Path(root_directory / file.parent).mkdir(parents=True, exist_ok=True)
        shutil.move(asm_directory / file, root_directory / file)

    subprocess.run([BLZ_EXECUTABLE_PATH, "-eo", "arm9_compressed.bin"])

    # Recreate arm9.bin
    with open("arm9_compressed.bin", "rb") as input_arm9, open(
        "arm9_header.bin", "rb"
    ) as input_header, open("arm9.bin", "wb") as output_arm9:
        data = input_header.read() + input_arm9.read()
        data = data[:0xB78] + struct.pack("<I", len(data) + 0x2000000) + data[0xB7C:]
        output_arm9.write(data)

    Path("arm9_compressed.bin").unlink()
    Path("arm9_header.bin").unlink()
    Path("arm9_original.bin").unlink()

    for overlay in overlays_to_modify:
        subprocess.run([BLZ_EXECUTABLE_PATH, "-eo", f"overlay/overlay_{overlay}.bin"])


def build(filename: str):
    build_arm9()
    subprocess.run(
        [
            NDSTOOL_EXECUTABLE_PATH,
            "-c",
            filename,
            "-9",
            "arm9.bin",
            "-7",
            "arm7.bin",
            "-y9",
            "y9.bin",
            "-y7",
            "y7.bin",
            "-d",
            "data",
            "-y",
            "overlay",
            "-t",
            "banner.bin",
            "-h",
            "header.bin",
        ]
    )


if __name__ == "__main__":
    argv = sys.argv
    if len(argv) > 1:
        filename = argv[1]
    else:
        filename = "out.nds"
    build(filename)
