from dataclasses import astuple, dataclass
from pathlib import Path
import struct

import click


@dataclass
class OverlayTableEntry:
    overlay_number: int
    ram_addr: int
    ram_size: int
    bss_size: int
    stat_beginning: int
    stat_ending: int
    file_id: int
    compressed_size_plus_flag: int

    @property
    def compressed_size(self) -> int:
        return self.compressed_size_plus_flag & 0xFFFFFF

    @compressed_size.setter
    def compressed_size(self, value: int) -> None:
        self.compressed_size_plus_flag = ((self.compressed_size_plus_flag >> 24) << 24) | value
        assert self.compressed_size == value


@click.command()
@click.argument(
    'y9_file',
    type=click.Path(path_type=Path, dir_okay=False, file_okay=True),
    required=True,
)
@click.argument(
    'overlay_dir',
    type=click.Path(path_type=Path, dir_okay=True, file_okay=False),
    required=True,
)
def fix_y9(y9_file: Path, overlay_dir: Path) -> None:
    overlay_table_entries: list[OverlayTableEntry] = []
    with open(y9_file, 'rb') as f1:
        for _ in range(0x0, y9_file.stat().st_size, 0x20):
            table_entry = OverlayTableEntry(*struct.unpack('<8I', f1.read(0x20)))

            overlay_file = overlay_dir / f'overlay_{str(table_entry.file_id).rjust(4, "0")}.bin'

            actual_size = overlay_file.stat().st_size

            if table_entry.compressed_size != actual_size:
                click.echo(f'Updating {overlay_file.stem}')

            table_entry.compressed_size = actual_size

            overlay_table_entries.append(table_entry)

    with open(y9_file, 'wb') as f2:
        for table_entry in overlay_table_entries:
            f2.write(struct.pack('<8I', *astuple(table_entry)))


if __name__ == '__main__':
    fix_y9()
