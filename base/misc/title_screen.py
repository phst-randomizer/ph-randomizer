from __future__ import annotations

from PIL import Image, ImageDraw
import click
from ndspy import color, lz10, narc, rom


class AutoList(list):
    def __setitem__(self, index, value):
        if index >= len(self):
            self.extend([None] * (index + 1 - len(self)))
        list.__setitem__(self, index, value)


def extract_image(image: bytes, palette: list[tuple[int, int, int, int]]) -> Image.Image:
    img = Image.new('RGB', (256, 128), (0, 0, 0))
    for y in range(128):
        for x in range(256):
            px = palette[image[y * 256 + x]]
            # RGB values are off by a factor of 8 in ndspy 4.0.0 for some reason
            px = (px[0] * 8, px[1] * 8, px[2] * 8, px[3] * 8)
            img.putpixel((x, y), px)
    return img


def insert_image(img: Image.Image) -> tuple[bytes, bytes]:
    image = AutoList()
    palette: list[tuple[int, int, int]] = []
    for y in range(128):
        for x in range(256):
            px = img.getpixel((x, y))
            if px in palette:
                image[y * 256 + x] = palette.index(px)
            else:
                palette.append(px)
                image[y * 256 + x] = len(palette) - 1
    assert len(palette) <= 256, 'Error: image contains more than 256 colors'
    # Divide by 8 b/c RGB values are off by a factor of 8 in ndspy 4.0.0 for some reason
    return bytes(image), color.savePalette([(r // 8, g // 8, b // 8, 0) for (r, g, b) in palette])


@click.command()
@click.option(
    '-i/-e',
    '--insert/--extract',
    default=False,
    help='Whether to insert a new title screen image, or extract the existing one',
)
@click.option('--input', type=str, required=True, help='Source ROM')
@click.option(
    '--output',
    type=str,
    required=True,
    help='File to save output to (either a new ROM or an image)',
)
@click.option(
    '--image', type=str, required=False, help='(insert only) Image to replace title screen with'
)
@click.option('--version_string', type=str)
def title_screen(insert: bool, input: str, output: str, image: str, version_string: str):
    nds_rom = rom.NintendoDSRom.fromFile(input)
    narc_file = narc.NARC(lz10.decompress(nds_rom.getFileByName('English/Menu/Tex2D/title.bin')))

    if insert:
        img = Image.open(image).convert('RGB')

        if version_string:
            draw = ImageDraw.Draw(img)
            img_width, img_height = img.size
            text_width, text_height = draw.textsize(version_string)
            x = img_width - text_width - 2
            y = img_height - text_height

            # draw border around letters
            stroke_color = (24, 66, 115)
            draw.text((x - 1, y), version_string, fill=stroke_color)
            draw.text((x + 1, y), version_string, fill=stroke_color)
            draw.text((x, y - 1), version_string, fill=stroke_color)
            draw.text((x, y + 1), version_string, fill=stroke_color)

            # draw text
            draw.text(
                (x, y), version_string, fill=(214, 41, 41), stroke_width=4, stroke_fill=(0, 0, 0)
            )

        new_image, new_palette = insert_image(img)
        narc_file.setFileByName('title.ntft', new_image)
        narc_file.setFileByName('title.ntfp', new_palette)
        nds_rom.setFileByName('English/Menu/Tex2D/title.bin', lz10.compress(narc_file.save()))
        nds_rom.saveToFile(output)

    else:
        image_file: bytes = narc_file.getFileByName('title.ntft')
        palette = color.loadPalette(narc_file.getFileByName('title.ntfp'))
        extracted_image: Image.Image = extract_image(image_file, palette)
        if not output.endswith('.bmp'):
            output = f'{output}.bmp'
        extracted_image.save(output, compress_level=0)


if __name__ == '__main__':
    title_screen()
