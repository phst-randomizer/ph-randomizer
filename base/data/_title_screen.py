from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw
from ndspy import color, lz10, narc
from ndspy.rom import NintendoDSRom

TITLE_SCREEN_BMP_PATH = Path(__file__).parent / 'title_screen.bmp'


class AutoList(list):
    """List that automatically extends when given an index greater than its length."""

    def __setitem__(self, index: int | Any, value: Any) -> None:
        assert isinstance(index, int)
        if index >= len(self):
            self.extend([None] * (index + 1 - len(self)))
        list.__setitem__(self, index, value)


def extract_title_screen(rom: NintendoDSRom) -> Image.Image:
    """Extracts the title screen graphic from the given rom and saves it as `title_screen.png`"""
    narc_file = narc.NARC(lz10.decompress(rom.getFileByName('English/Menu/Tex2D/title.bin')))
    image_data: bytes = narc_file.getFileByName('title.ntft')
    palette = color.loadPalette(narc_file.getFileByName('title.ntfp'))

    img = Image.new('RGB', (256, 128), (0, 0, 0))
    for y in range(128):
        for x in range(256):
            px = palette[image_data[y * 256 + x]]
            # RGB values are off by a factor of 8 in ndspy 4.0.0 for some reason
            px = (px[0] * 8, px[1] * 8, px[2] * 8, px[3] * 8)
            img.putpixel((x, y), px)

    img.save(TITLE_SCREEN_BMP_PATH, compress_level=0)

    return img


def insert_title_screen(
    input_rom: NintendoDSRom,
    version_string: str | None = None,
) -> NintendoDSRom:
    """Inserts `title_screen.bmp` into the ROM as the title screen."""
    narc_file = narc.NARC(lz10.decompress(input_rom.getFileByName('English/Menu/Tex2D/title.bin')))
    img = Image.open(TITLE_SCREEN_BMP_PATH).convert('RGB')

    if version_string:
        draw = ImageDraw.Draw(img)
        draw.fontmode = '1'  # disable anti-aliasing on text

        # Calculate size/location to put version string
        img_width, img_height = img.size
        _, _, text_width, text_height = draw.textbbox(xy=(0, 0), text=version_string, font_size=10)
        x = img_width - text_width - 2
        y = img_height - text_height - 2

        # draw text
        draw.text((x, y), version_string, fill=(20, 68, 115), font_size=10)

    image_data = AutoList()
    palette_data: list[tuple[int, int, int]] = []
    for y in range(128):
        for x in range(256):
            px = img.getpixel((x, y))
            if px in palette_data:
                image_data[y * 256 + x] = palette_data.index(px)
            else:
                palette_data.append(px)
                image_data[y * 256 + x] = len(palette_data) - 1

    assert (
        len(palette_data) <= 256
    ), f'Error: image contains more than 256 colors ({len(palette_data)})'

    narc_file.setFileByName('title.ntft', bytes(image_data))
    # Divide by 8 b/c RGB values are off by a factor of 8 in ndspy 4.0.0 for some reason
    narc_file.setFileByName(
        'title.ntfp', color.savePalette([(r // 8, g // 8, b // 8, 0) for (r, g, b) in palette_data])
    )
    input_rom.setFileByName('English/Menu/Tex2D/title.bin', lz10.compress(narc_file.save()))

    return input_rom
