from pathlib import Path
import struct
import sys

from ndspy import code, codeCompression, fnt, lz10, narc
from ndspy.rom import NintendoDSRom

NEW_OVERLAY_ADDRESS = (
    0x23C0900  # some empty space in the ARM9 RAM area. TODO: verify this is safe to use
)
NEW_OVERLAY_SIZE = 32512


NPC_MODELS_TO_COPY = [
    'SwB',
    'Husband',
]


def _inject_new_get_item_models(rom: NintendoDSRom, folder: fnt.Folder) -> None:
    for npc_modelname in NPC_MODELS_TO_COPY:
        nsbmd = narc.NARC(
            lz10.decompress(data=rom.getFileByName(f'Npc/{npc_modelname}.bin'))
        ).getFileByName('model.nsbmd')
        nsbtx = rom.getFileByName(f'Npc/{npc_modelname}.nsbtx')

        folder.files.append(f'{npc_modelname}.nsbmd')
        rom.files.append(nsbmd)
        folder.files.append(f'{npc_modelname}.nsbtx')
        rom.files.append(nsbtx)


def inject_new_data_files(rom: NintendoDSRom) -> None:
    new_folder = fnt.Folder(folders=[], files=[], firstID=sorted(rom.sortedFileIds)[-1] + 2)
    rom.filenames.folders.append(
        (
            'r',
            new_folder,
        )
    )

    _inject_new_get_item_models(rom, new_folder)


def reinsert_arm9(rom: NintendoDSRom, arm9_header_file: Path, arm9_code_file: Path) -> None:
    arm9_header = arm9_header_file.read_bytes()
    arm9_code = arm9_code_file.read_bytes()

    arm9 = arm9_header + codeCompression.compress(data=arm9_code, isArm9=True)

    arm9_length = len(arm9) + 0x2000000
    arm9 = arm9[:0xB78] + struct.pack('<I', arm9_length) + arm9[0xB7C:]

    rom.arm9 = arm9

    print('Rebuilt arm9.bin')


def reinsert_overlays(rom: NintendoDSRom, overlay_directory: Path) -> None:
    ot = code.loadOverlayTable(
        tableData=rom.arm9OverlayTable,
        fileCallback=lambda overlayID, fileID: rom.files[fileID],
    )

    # Calculate new file id and overlay number for new overlay
    new_overlay_file_id = sorted(rom.sortedFileIds)[-1] + 1
    new_overlay_number = max(ot.keys()) + 1

    # First, reinsert all the existing overlays
    for overlay_file in overlay_directory.iterdir():
        overlay_number = int(overlay_file.stem.split('_')[-1])

        if overlay_number == new_overlay_number:
            # we'll handle adding the new overlay after this loop
            continue

        ot[overlay_number].data = overlay_file.read_bytes()
        rom.files[ot[overlay_number].fileID] = ot[overlay_number].save(compress=False)
        print(f'Rebuilt overlay_{str(overlay_number).rjust(4, "0")}.bin')

    # Now, add the new overlay
    new_overlay_file = overlay_directory / f'overlay_{str(new_overlay_number).rjust(4, "0")}.bin'
    new_overlay_data = new_overlay_file.read_bytes().rstrip(b'\x00')  # trim padding

    if len(new_overlay_data) > NEW_OVERLAY_SIZE:
        raise ValueError(
            f'Overlay {new_overlay_file} is too large: {len(new_overlay_data)} bytes '
            f'(max: {NEW_OVERLAY_SIZE} bytes)'
        )

    new_overlay = code.Overlay(
        data=new_overlay_data,
        ramAddress=NEW_OVERLAY_ADDRESS,
        ramSize=len(new_overlay_data),
        bssSize=0,
        staticInitStart=0,
        staticInitEnd=0,
        fileID=new_overlay_file_id,
        compressedSize=len(new_overlay_data),
        flags=0,
    )
    ot[new_overlay_number] = new_overlay
    rom.files.append(None)
    rom.files[new_overlay_file_id] = new_overlay.save(compress=False)
    print(
        f'Added new overlay_{str(new_overlay_number).rjust(4, "0")}.bin '
        f'(size: {len(new_overlay_data)} bytes)'
    )

    rom.arm9OverlayTable = code.saveOverlayTable(ot)


if __name__ == '__main__':
    rom = NintendoDSRom.fromFile(sys.argv[1])

    reinsert_arm9(rom, Path(sys.argv[3]), Path(sys.argv[4]))
    reinsert_overlays(rom, Path(sys.argv[2]))
    inject_new_data_files(rom)

    rom.saveToFile(sys.argv[5])
