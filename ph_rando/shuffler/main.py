import json
import logging
from pathlib import Path
import random
import string
import sys

import click

from ph_rando.common import ShufflerAuxData, click_setting_options
from ph_rando.shuffler._shuffler import assumed_fill, init_logic_graph
from ph_rando.shuffler._spoiler_log import generate_spoiler_log


def shuffle(seed: str) -> ShufflerAuxData:
    """
    Parses aux data and logic, shuffles the aux data, and returns it.

    Params:
        `seed`: Some string that will be hashed and used as a seed for the RNG.

    Returns:
        Randomized aux data.
    """
    random.seed(seed)

    aux_data = init_logic_graph()
    aux_data.seed = seed

    return assumed_fill(aux_data)


@click.command()
@click.option('-s', '--seed', type=str, required=False, help='Seed for the RNG.')
@click.option(
    '--spoiler-log',
    required=False,
    type=str,
    default=None,
    help='Generate a spoiler log for this seed.',
)
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
    spoiler_log: str | None,
    **settings: bool | str,
) -> None:
    logging.basicConfig(level=logging.getLevelNamesMapping()[log_level])

    # Generate random seed if one isn't provided
    if seed is None:
        seed = ''.join(random.choices(string.ascii_letters, k=20))

    results = shuffle(seed)

    if output == '--':
        for area in results.areas:
            print(area.json(), file=sys.stdout)
        print(f'Seed: {seed}')
    elif output is not None:
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)
        for area in results.areas:
            (output_path / f'{area.name}.json').write_text(area.json())
        (output_path / 'seed.txt').write_text(seed)

    if spoiler_log:
        sl = generate_spoiler_log(results).dict()
        Path(spoiler_log).write_text(json.dumps(sl, indent=2))


if __name__ == '__main__':
    shuffler_cli()
