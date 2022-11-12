import logging
from pathlib import Path
import random
import sys

import click

from shuffler.aux_models import Area
from shuffler.logic import Logic

logging.basicConfig(level=logging.INFO)


def shuffle(seed: str | None) -> list[Area]:
    """
    Parses aux data and logic, shuffles the aux data, and returns it.

    Params:
        `seed`: Some string that will be hashed and used as a seed for the RNG.

    Returns:
        Randomized aux data.
    """
    if seed is not None:
        random.seed(seed)

    logic = Logic()

    logic.connect_rooms()

    logic.randomize_items()

    return logic.aux_data


@click.command()
@click.option('-s', '--seed', type=str, required=False, help='Seed for the RNG.')
@click.option(
    '-o',
    '--output',
    default=None,
    type=click.Path(exists=False, dir_okay=True, file_okay=False),
    help='Path to save randomized aux data to. Use -- to output to stdout.',
)
def shuffler_cli(seed: str | None, output: str | None):
    results = shuffle(seed)

    if output == '--':
        for area in results:
            print(area.json(), file=sys.stdout)
    elif output is not None:
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)
        for area in results:
            with open(output_path / f'{area.name}.json', 'w') as fd:
                fd.write(area.json())


if __name__ == '__main__':
    shuffler_cli()
