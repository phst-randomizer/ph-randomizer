import argparse

from ndspy import lz10
from ndspy.narc import NARC
from ndspy.rom import NintendoDSRom
from zed.common import Game
from zed.zmb import ZMB

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='generate-zmb-maps')
    parser.add_argument('rom', help='Path to PH rom.')
    parser.add_argument(
        '-a',
        '--area',
        required=True,
        help='Area to generate map for. Must be a folder name in the Map/ directory,'
        ' i.e. "dngn_main", "isle_flame", etc.',
    )
    parser.add_argument(
        '-m', '--map-num', required=True, help='Map number within the area (i.e. XX in mapXX.bin).'
    )
    args = parser.parse_args()

    rom_path: str = args.rom
    area: str = args.area
    map_num: str = args.map_num

    rom = NintendoDSRom.fromFile(rom_path)
    map_num_fixed = map_num.rjust(2, '0')

    narc_filepath = f'Map/{area}/map{map_num_fixed}.bin'
    narc = NARC(lz10.decompress(rom.getFileByName(narc_filepath)))

    zmb_filepath = f'zmb/{area}_{map_num_fixed}.zmb'

    zmb = ZMB(game=Game.PhantomHourglass, data=narc.getFileByName(zmb_filepath))

    zmb.renderPNG().save(f'{area}_{map_num_fixed}.bmp')
