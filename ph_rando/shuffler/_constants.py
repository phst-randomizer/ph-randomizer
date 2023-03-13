import json
from pathlib import Path

ENEMIES_MAPPING = json.loads((Path(__file__).parent / 'enemies.json').read_text())
LOGIC_MACROS = json.loads((Path(__file__).parent / 'macros.json').read_text())
