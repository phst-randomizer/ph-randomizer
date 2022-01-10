#!/usr/bin/env python3

from pathlib import Path
import subprocess
import sys

from common import BLZ_EXECUTABLE_PATH, NDSTOOL_EXECUTABLE_PATH, overlays_to_modify


def extract_arm9():
    """Extract + decompress the arm9.bin binary + overlays."""
    # seperate the uncompressed and compressed parts of arm9.bin into different files
    with open("arm9.bin", "rb") as input_arm9, open("arm9_header.bin", "wb") as output_header, open(
        "arm9_original.bin", "wb"
    ) as output_arm9:
        output_header.write(input_arm9.read(0x4000))
        data = input_arm9.read()
        data = data[: len(data) - 0xC]
        output_arm9.write(data)

    # decompress the main code section of arm9 the arm9 binary
    subprocess.run([BLZ_EXECUTABLE_PATH, "-d", "arm9_original.bin"])

    # decompress the overlay binaries
    for overlay in overlays_to_modify:
        subprocess.run([BLZ_EXECUTABLE_PATH, "-d", f"overlay/overlay_{overlay}.bin"])

    Path("arm9.bin").unlink()


def unpack(filename: str):
    subprocess.run(
        [
            NDSTOOL_EXECUTABLE_PATH,
            "-v",
            "-x",
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
    extract_arm9()


if __name__ == "__main__":
    argv = sys.argv
    if len(argv) > 1:
        filename = argv[1]
    else:
        filename = "in.nds"
    unpack(filename)
