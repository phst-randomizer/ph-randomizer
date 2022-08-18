import json
from pathlib import Path
import shutil

import pytest

from shuffler._parser import Edge, Node, parse
from shuffler.aux_models import Area
from shuffler.main import load_aux_data


@pytest.fixture
def aux_data_directory(tmp_path: Path):
    dest = tmp_path / 'auxiliary'
    shutil.copytree(Path(__file__).parent.parent / 'shuffler' / 'auxiliary', dest)

    # Add a new chest to Mercay aux data containing bombs, so that a beatable seed can actually
    # be generated.
    # TODO: Remove this once there's enough aux data completed to generate a beatable seed.
    with open(dest / 'SW Sea' / 'Mercay Island' / 'Mercay.json') as fd:
        mercay_json = json.load(fd)
    mercay_json['rooms'][0]['chests'].append(
        {
            'name': 'test',
            'type': 'npc',
            'contents': 'bombs',
            'bmg_file_path': 'TODO',
            'bmg_instruction_index': -1,
        }
    )
    with open(dest / 'SW Sea' / 'Mercay Island' / 'Mercay.json', 'w') as fd:
        fd.write(json.dumps(mercay_json))

    return str(dest)


@pytest.fixture
def aux_data(aux_data_directory: str) -> list[Area]:
    return load_aux_data(Path(aux_data_directory))


@pytest.fixture
def logic_directory(tmp_path: Path):
    dest = tmp_path / 'logic'
    shutil.copytree(Path(__file__).parent.parent / 'shuffler' / 'logic', dest)
    return str(dest)


@pytest.fixture
def logic(logic_directory: str) -> tuple[list[Node], dict[str, list[Edge]]]:
    nodes, edges = parse(Path(logic_directory))
    return nodes, edges
