from pathlib import Path
import sys

from ndspy.rom import NintendoDSRom

rom = NintendoDSRom.fromFile(sys.argv[1])

for overlay_number, overlay in rom.loadArm9Overlays().items():
    overlay_data = overlay.data
    overlay_file_id = overlay_number
    overlay_file_name = f'overlay_{str(overlay_file_id).rjust(4, "0")}.bin'
    overlay_file = Path(sys.argv[2]) / overlay_file_name

    overlay_file.parent.mkdir(exist_ok=True)

    with open(overlay_file, 'wb') as f:
        f.write(rom.files[overlay_file_id])

    print(f'Extracted {overlay_file_name}')
