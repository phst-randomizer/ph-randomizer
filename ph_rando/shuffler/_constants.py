from __future__ import annotations

from functools import cache
import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .aux_models import Mail

ENEMIES_MAPPING = json.loads((Path(__file__).parent / 'enemies.json').read_text())
LOGIC_MACROS = json.loads((Path(__file__).parent / 'macros.json').read_text())


@cache
def get_mail_items() -> list[Mail]:
    """Returns list of all mail items in the game and the requirements to get them."""
    from .aux_models import Mail

    return Mail.list_from_file(Path(__file__).parent / 'mail.json')
