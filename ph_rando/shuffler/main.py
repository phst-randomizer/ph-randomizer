import logging
from pathlib import Path
import random
import sys

import click

from ph_rando.common import ShufflerAuxData, click_setting_options
from ph_rando.shuffler._shuffler import assumed_fill, init_logic_graph


def shuffle(seed: str | None) -> ShufflerAuxData:
    """
    Parses aux data and logic, shuffles the aux data, and returns it.

    Params:
        `seed`: Some string that will be hashed and used as a seed for the RNG.

    Returns:
        Randomized aux data.
    """
    if seed is not None:
        random.seed(seed)

    aux_data = init_logic_graph()

    return assumed_fill(aux_data)


@click.command()
@click.option('-s', '--seed', type=str, required=False, help='Seed for the RNG.')
@click.option(
    '-o',
    '--output',
    default=None,
    type=click.Path(exists=False, dir_okay=True, file_okay=False),
    help='Path to save randomized aux data to. Use -- to output to stdout.',
)
@click.option(
    '-l',
    '--log-level',
    type=click.Choice(
        list(logging.getLevelNamesMapping().keys()),
        case_sensitive=False,
    ),
    default='INFO',
)
@click_setting_options
def shuffler_cli(
    seed: str | None,
    output: str | None,
    log_level: str,
    **settings: bool | str,
) -> None:
    logging.basicConfig(level=logging.getLevelNamesMapping()[log_level])

    results = shuffle(seed)

    if output == '--':
        for area in results.areas.values():
            print(area.json(), file=sys.stdout)
    elif output is not None:
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)
        for area in results.areas.values():
            (output_path / f'{area.name}.json').write_text(area.json())


if __name__ == '__main__':
    shuffler_cli()
