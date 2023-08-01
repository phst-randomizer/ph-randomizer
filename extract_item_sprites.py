from collections.abc import Callable
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TypeVar

from PIL import Image
from hacktools.nitro import NCER, NCGR, drawNCER, readNCER, readNCGR, readNCLR
from ndspy import color, lz10
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


def extract_tiled_item_sprites(rom: NintendoDSRom) -> dict[str, Image.Image]:
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


def extract_image(image_data: bytes, palette: list[color.ColorTuple]) -> Image.Image:
    img = Image.new('RGB', (32, 32))
    for y in range(32):
        for x in range(16):
            current_byte = image_data[y * 16 + x]
            pixel_2_index = current_byte & 0xF
            pixel_1_index = (current_byte & 0xF0) >> 4

            px = palette[pixel_2_index]
            px = (px[0] * 8, px[1] * 8, px[2] * 8, px[3] * 8)
            img.putpixel((x, y), px)

            px = palette[pixel_1_index]
            px = (px[0] * 8, px[1] * 8, px[2] * 8, px[3] * 8)
            img.putpixel((x + 1, y), px)
    return img


def insert_image(img: Image.Image) -> tuple[bytes, bytes]:
    image: list[int] = []
    palette: list[tuple[int, int, int]] = []

    for y in range(32):
        for x in range(16):
            try:
                px2 = img.getpixel((x, y))
            except IndexError:
                px2 = (0, 0, 0)
            if px2 in palette:
                pal2_index = palette.index(px2)
            else:
                palette.append(px2)
                pal2_index = len(palette) - 1
            try:
                px1 = img.getpixel((x + 1, y))
            except IndexError:
                px1 = (0, 0, 0)
            if px1 in palette:
                pal1_index = palette.index(px1)
            else:
                palette.append(px1)
                pal1_index = len(palette) - 1

            image_index = y * 16 + x

            # Ensure image list is long enough
            if len(image) <= image_index:
                image.extend([-1] * (image_index + 1 - len(image)))

            image[image_index] = pal2_index | (pal1_index << 4)

    assert len(palette) <= 16, 'Error: image contains more than 16 colors'
    # Divide by 8 b/c RGB values are off by a factor of 8 in ndspy 4.0.0 for some reason
    return bytes(image), color.savePalette([(r // 8, g // 8, b // 8, 255) for (r, g, b) in palette])


def main() -> None:
    rom = NintendoDSRom.fromFile(Path(__file__).parent / 'out.nds')

    other = NARC(lz10.decompress(rom.getFileByName('Other/other.bin')))

    # ######################
    # #     Extraction     #
    # ######################
    # rupee_g_ntfp: bytes = other.getFileByName('rupee_G.ntfp')
    # rupee_r_ntft: bytes = other.getFileByName('rupee_R.ntft')

    # # Load tiles + palette
    # palette = color.loadPalette(rupee_g_ntfp)

    # Convert binary data to PIL Image
    # extracted_img = extract_image(image_data=rupee_r_ntft, palette=palette)

    item_sprites = extract_tiled_item_sprites(rom)

    bow = (
        item_sprites['Shovel']
        .crop(item_sprites['Shovel'].getbbox())
        .resize((16, 32))
        .quantize(colors=16)
        .convert('RGB')
    )

    # bow.save('test1.bmp')

    new_image, new_palette = insert_image(bow)

    # Replace green rupee sprite with shovel sprite
    other.setFileByName('rupee_G.ntfp', new_palette)
    other.setFileByName('rupee_R.ntft', new_image)

    rom.setFileByName('Other/other.bin', lz10.compress(other.save()))

    rom.saveToFile('out1.nds')


main()
