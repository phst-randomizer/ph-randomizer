from collections.abc import Callable
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TypeVar

from PIL import Image
from hacktools.nitro import NCER, NCGR, drawNCER, readNCER, readNCGR, readNCLR
from ndspy import lz10
from ndspy.narc import NARC
from ndspy.rom import NintendoDSRom

from ph_rando.patcher._items import ITEMS

_SPRITE_COORDS: dict[str, tuple[int, int, int, int]] = {
    'Shovel': (0, 16, 32, 48),
    'Bow': (0, 16, 50, 66),
    'Bombs': (0, 16, 67, 83),
    'Boomerang': (0, 14, 84, 98),
}

assert set(_SPRITE_COORDS.keys()).issubset(ITEMS.keys())


def _extract_tiled_image(ncgr: bytes, nclr: bytes, ncer: bytes) -> Image.Image:
    T = TypeVar('T')

    def _read_file_hacktools(data: bytes, fn: Callable[[str], T]) -> T:
        with NamedTemporaryFile('rb+') as f:
            f.write(data)
            f.seek(0)
            return fn(f.name)

    ncgr_file: NCGR = _read_file_hacktools(ncgr, readNCGR)
    nclr_file = _read_file_hacktools(nclr, readNCLR)
    ncer_file: NCER = _read_file_hacktools(ncer, readNCER)

    with NamedTemporaryFile('rb+') as f:
        drawNCER(f.name, ncer_file, ncgr_file, nclr_file)
        return Image.open(f.name)


def _extract_bbox(image: Image.Image, xmin: int, xmax: int, ymin: int, ymax: int) -> Image.Image:
    new_img = Image.new('RGB', (xmax - xmin, ymax - ymin))

    for y in range(ymin, ymax):
        for x in range(xmin, xmax):
            new_img.putpixel((x - xmin, y - ymin), image.getpixel((x, y)))

    return new_img


def extract_item_sprites(rom: NintendoDSRom) -> dict[str, Image.Image]:
    file = rom.getFileByName('English/Menu/UI_main/UIMField.bin')

    narc_file = NARC(lz10.decompress(file))

    ncgr: bytes = narc_file.getFileByName('UIMField.ncgr')
    nclr: bytes = narc_file.getFileByName('UIMField.NCLR')
    ncer: bytes = narc_file.getFileByName('UIMField.ncer')

    image = _extract_tiled_image(ncgr, nclr, ncer)

    item_images: dict[str, Image.Image] = {}

    for item_name, coords in _SPRITE_COORDS.items():
        item_images[item_name] = _extract_bbox(image, *coords)

    return item_images


def insert_item_sprites(rom: NintendoDSRom, images: dict[str, Image.Image]) -> NintendoDSRom:
    pass


def main() -> None:
    nds_rom = NintendoDSRom.fromFile(Path(__file__).parent / 'out.nds')

    extract_item_sprites(nds_rom)


main()
