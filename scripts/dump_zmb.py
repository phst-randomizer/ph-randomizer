import argparse
from pathlib import Path

from ndspy import lz10
from ndspy.fnt import Folder
from ndspy.narc import NARC
from ndspy.rom import NintendoDSRom
from tqdm import tqdm

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Dumps all ZMB files from a Zelda Phantom Hourglass ROM.'
    )
    parser.add_argument('rom_path', type=str, help='Path to your Zelda: Phantom Hourglass ROM.')

    rom_path: str = parser.parse_args().rom_path

    rom = NintendoDSRom.fromFile(rom_path)

    output_dir = Path.cwd() / 'zmbs'
    output_dir.mkdir(exist_ok=True)

    for folder in tqdm(rom.filenames.subfolder('Map').folders):
        folder_name = folder[0]
        file_path = f'Map/{folder_name}'
        for subfolder in folder:
            if isinstance(subfolder, Folder):
                for file in subfolder.files:
                    if not file.startswith('map'):
                        continue
                    narc_path = f'{file_path}/{file}'
                    narc_file = NARC(lz10.decompress(rom.getFileByName(narc_path)))
                    map_number = file[3:5]
                    zmb_filename = f'zmb/{folder_name}_{map_number}.zmb'
                    outfile = f'{folder_name}_{map_number}.zmb'
                    (output_dir / outfile).write_bytes(
                        narc_file.getFileByName(f'zmb/{folder_name}_{map_number}.zmb')
                    )
                    tqdm.write(f'Saved "{outfile}"')
