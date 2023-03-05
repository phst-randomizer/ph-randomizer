import json
from pathlib import Path

from ph_rando.shuffler.aux_models import Area

# def test_graph_connectedness(settings) -> None:
#     logic = Logic(settings=settings)
#     logic.connect_rooms()

#     # Compute list of tuples of each check its area.
#     all_checks = [
#         (chest, area.name)
#         for area in logic.areas.values()
#         for room in area.rooms
#         for chest in room.chests
#     ]

#     # Put every item in the game in the current inventory, appending the area name to each
#     # small_key so we know which key goes to which area.
#     inventory = [
#         chest.contents if chest.contents != 'small_key' else f'small_key_{area_name}'
#         for chest, area_name in all_checks
#     ]

#     # Populate the `keys` dict for the assumed search function with all of
#     # the small keys in the inventory.
#     keys: dict[str, int] = defaultdict(int)
#     for item in inventory:
#         if item.startswith('small_key_'):
#             keys[item[len('small_key_') :]] += 1

#     reachable_nodes = logic.assumed_search(
#         logic.starting_node,
#         inventory,
#         keys,
#     )

#     # Create set consisting of all areas reported as reachable by the assumed search
#     reachable_areas = {node.area for node in reachable_nodes}

#     # Create set consisting of all areas in the logic
#     all_areas = {area.name for area in logic.areas.values()}

#     assert reachable_areas == all_areas

#     # TODO: assert that rooms + nodes are identical too


def test_aux_data_validation():
    """Run every aux data json through validation."""
    aux_data_files = list(
        (Path(__file__).parents[1] / 'ph_rando' / 'shuffler' / 'logic').rglob('*.json')
    )
    assert len(aux_data_files) > 0
    for filename in aux_data_files:
        with open(filename) as fd:
            Area(**json.load(fd))
