from pathlib import Path

import click
from ndspy import lz10, narc, rom

NPC_MODELS = {
    'SwB': 'battle.bmg',
}


def _copy_npc_models(ph_rom: rom.NintendoDSRom) -> None:
    for npc_modelname, dest_file in NPC_MODELS.items():
        nsbmd = narc.NARC(
            lz10.decompress(data=ph_rom.getFileByName(f'Npc/{npc_modelname}.bin'))
        ).getFileByName('model.nsbmd')
        nsbtx = ph_rom.getFileByName(f'Npc/{npc_modelname}.nsbtx')
        ph_rom.setFileByName(f'Spanish/Message/{dest_file}', nsbmd)
        ph_rom.setFileByName(f'French/Message/{dest_file}', nsbtx)


@click.command()
@click.option(
    '-i',
    '--input-rom',
    type=click.Path(exists=False, path_type=Path),
    required=True,
    help='Source ROM',
)
@click.option(
    '-o',
    '--output-rom',
    type=click.Path(path_type=Path),
    required=True,
    help='Dest ROM',
)
def preprocess(input_rom: Path, output_rom: Path) -> None:
    ph_rom = rom.NintendoDSRom.fromFile(str(input_rom))

    _copy_npc_models(ph_rom)

    ph_rom.saveToFile(str(output_rom))


if __name__ == '__main__':
    preprocess()
