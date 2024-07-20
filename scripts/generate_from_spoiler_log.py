import argparse
import json
from pathlib import Path

from ph_rando import __version__
from ph_rando.patcher._patcher import Patcher
from ph_rando.shuffler._shuffler import Shuffler

# TODO: move this into randomizer package itself, maybe?


def main() -> None:
    parser = argparse.ArgumentParser(prog='generate_from_spoiler_log')
    parser.add_argument('rom', help='Path to PH rom.')
    parser.add_argument(
        'spoiler_log',
        help='Area to generate map for. Must be a folder name in the Map/ directory,'
        ' i.e. "dngn_main", "isle_flame", etc.',
    )
    args = parser.parse_args()

    rom_path: str = args.rom
    spoiler_log_path: str = args.spoiler_log

    spoiler_log = json.loads(Path(spoiler_log_path).read_text())

    if spoiler_log['version'] != __version__:
        raise Exception(
            f'Spoiler log has different version ({spoiler_log["version"]}) '
            'than current randomizer checkout ({__version__})'
        )

    shuffled_aux_data = Shuffler(spoiler_log['seed'], spoiler_log['settings']).generate()
    patcher = Patcher(
        rom=Path(rom_path), aux_data=shuffled_aux_data, settings=spoiler_log['settings']
    )

    patched_rom = patcher.generate()

    patched_rom.saveToFile(
        Path(rom_path).parent / f'{Path(rom_path).stem}_patched{Path(rom_path).suffix}'
    )


if __name__ == '__main__':
    main()
