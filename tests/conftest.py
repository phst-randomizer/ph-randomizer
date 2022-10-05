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
