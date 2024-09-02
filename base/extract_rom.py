from pathlib import Path
import sys

from ndspy import codeCompression, fnt
from ndspy.rom import NintendoDSRom


def extract_arm9(rom: NintendoDSRom, output_dir: Path) -> None:
    arm9_file = output_dir / 'arm9_original.bin'
    arm9_header_file = output_dir / 'arm9_header.bin'

    arm9_header_file.write_bytes(rom.arm9[:0x4000])
    arm9_file.write_bytes(codeCompression.decompress(rom.arm9[0x4000:]))

    print('Extracted arm9.bin')


def extract_overlays(rom: NintendoDSRom, output_dir: Path) -> None:
    output_dir.mkdir(exist_ok=True)
    for overlay in rom.loadArm9Overlays().values():
        overlay_file_name = f'overlay_{str(overlay.fileID).rjust(4, "0")}.bin'

        overlay_file = output_dir / overlay_file_name

        with open(overlay_file, 'wb') as f:
            f.write(codeCompression.decompress(rom.files[overlay.fileID]))

        print(f'Extracted {overlay_file_name}')


def _extract_data_recursive(folder: fnt.Folder, output_dir: Path) -> None:
    for child_file in folder.files:
        out_file = output_dir / child_file
        out_file.parent.mkdir(exist_ok=True, parents=True)
        out_file.write_bytes(rom.files[folder.idOf(child_file)])
    for child_folder_name, child_folder in folder.folders:
        _extract_data_recursive(child_folder, output_dir / child_folder_name)


def extract_data(rom: NintendoDSRom, output_dir: Path) -> None:
    return _extract_data_recursive(rom.filenames, output_dir)


if __name__ == '__main__':
    rom = NintendoDSRom.fromFile(sys.argv[1])

    root_dir = Path(sys.argv[2])
    root_dir.mkdir(exist_ok=True)

    extract_arm9(rom, root_dir)
    extract_overlays(rom, root_dir / 'overlay')
    extract_data(rom, root_dir / 'data')
