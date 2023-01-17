#!/usr/bin/env python3

# type: ignore

import json
from pathlib import Path
import re

import pytest
import yaml


class PytestPlugin:
    def __init__(self):
        self.collected = []

    def pytest_collection_modifyitems(self, items):
        for item in items:
            self.collected.append(item.nodeid)


def main():
    # Collect names of all test files
    my_plugin = PytestPlugin()
    pytest.main(
        ['--collect-only', str(Path(__file__).parents[1] / 'tests' / 'desmume')],
        plugins=[my_plugin],
    )
    test_modules = list(
        {x[0] for x in [re.findall(r'.+/(.+)\.py.+', module) for module in my_plugin.collected]}
    )

    workflow_yaml = yaml.safe_load(
        (Path(__file__).parent / 'workflows' / 'build-test-release.yml').read_text()
    )
    matrix = workflow_yaml['jobs']['generate-base-patch']['strategy']['matrix']

    new_matrix = {'include': []}

    for module in test_modules:
        for include in matrix['include']:
            new_matrix['include'].append(include | {'module': module})

    (Path(__file__).parent / 'matrix.json').write_text(json.dumps(new_matrix))


if __name__ == '__main__':
    main()
