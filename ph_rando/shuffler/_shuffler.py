from collections import deque
from copy import copy
import logging
from pathlib import Path
import random

from ordered_set import OrderedSet

from ph_rando.shuffler._constants import get_mail_items
from ph_rando.shuffler._parser import (
    Edge,
    Node,
    annotate_logic,
    parse_aux_data,
    parse_edge_requirement,
    requirements_met,
)
from ph_rando.shuffler.aux_models import Area, Check

logger = logging.getLogger(__name__)

DUNGEON_REWARD_CHECKS: dict[str, str] = {
    'BlaazBossRoom.Main.SpiritOfPower': 'PowerSpirit',
    'CyclokBossRoom.Main.SpiritOfWisdom': 'WisdomSpirit',
    'CraykBossRoom.Main.SpiritOfCourage': 'CourageSpirit',
    'GoronTemple.CrimsonineRoom.Crimsonine': 'Crimsonine',
    'IceTemple.AzurineRoom.Azurine': 'Azurine',
    'MutohTemple.B4.Aquanine': 'Aquanine',
}

IMPORTANT_ITEMS: set[str] = {
    'Bombchus',
    'Bombs',
    'Boomerang',
    'Bow',
    'Cannon',
    'CycloneSlate',
    'FishingRod',
    'GrapplingHook',
    'Hammer',
    'KingKey',
    'NESeaChart',
    'NWSeaChart',
    'OshusSword',
    'PhantomHourglass',
    'PhantomSword',
    'RegalNecklace',
    'SalvageArm',
    'SESeaChart',
    'Shovel',
    'SunKey',
    'SWSeaChart',
    'Shield',
}


def _connect_rooms(areas: dict[str, Area]) -> None:
    def _get_dest_node(dest_node_entrance: str):
        dest_node_split = dest_node_entrance.split('.')

        area_name = dest_node_split[0]
        room_name = dest_node_split[1]

        dest_node_name = '.'.join(dest_node_split[:-1])

        for room in areas[area_name].rooms:
            if room.name == room_name:
                for node in room.nodes:
                    if dest_node_name == node.name:
                        for entrance in node.entrances:
                            if entrance == dest_node_entrance:
                                return node
        raise Exception(f'Entrance {dest_node_entrance!r} not found')

    for area in areas.values():
        for room in area.rooms:
            for src_node in room.nodes:
                for exit in src_node.exits:
                    if not len(exit.entrance):
                        raise Exception(f'exit {exit.name!r} has no "link".')
                    src_node.edges.append(
                        Edge(src=src_node, dest=_get_dest_node(exit.entrance), requirements=None)
                    )


def search(
    starting_node: Node,
    areas: dict[str, Area],
    items: list[str],
    flags: set[str],
) -> OrderedSet[Node]:
    reachable_nodes: OrderedSet[Node] = OrderedSet()

    queue: deque[Node] = deque([starting_node])

    visited_nodes: set[Node] = {starting_node}

    while len(queue) > 0:
        r = queue.popleft()
        for edge in r.edges:
            target = edge.dest

            requirements_met = edge.is_traversable(items, flags, areas)

            if requirements_met and target not in visited_nodes:
                queue.append(target)
                visited_nodes.add(target)
        reachable_nodes.add(r)

    return reachable_nodes


def assumed_search(
    starting_node: Node,
    areas: dict[str, Area],
    items: list[str],
    area: str | None = None,
) -> OrderedSet[Node]:
    # Used to keep track of what checks/flags we've encountered
    visited_checks: set[Check] = set()
    flags: set[str] = set()
    items = copy(items)  # make copy of items so we don't mutate the original list
    mail_items = get_mail_items()

    while True:
        reachable_nodes = search(starting_node, areas, items, flags)
        if area is not None:
            reachable_nodes = OrderedSet(
                [node for node in reachable_nodes if node.area.name == area]
            )
        found_new_items = False

        for node in reachable_nodes:
            for check in node.checks:
                if check.contents and check not in visited_checks:
                    items.append(check.contents)
                    found_new_items = True
                    visited_checks.add(check)
            for flag in node.flags:
                if flag not in flags:
                    flags.add(flag)
                    found_new_items = True

            # If this node contains a mailbox, check if any mail items
            # are collectable and collect them.
            if node.mailbox:
                collectable_mail_items = [
                    item
                    for item in mail_items
                    if requirements_met(
                        parse_edge_requirement(item.requirements),
                        items,
                        flags,
                        areas,
                    )
                ]
                for item in collectable_mail_items:
                    items.append(item.contents)
                    found_new_items = True
                    mail_items.remove(item)

        if not found_new_items:
            break

    return reachable_nodes


def _place_item(
    item: str,
    starting_node: Node,
    remaining_item_pool: list[str],
    areas: dict[str, Area],
    candidates: OrderedSet[Check] | None = None,
) -> None:
    # Figure out what nodes are accessible
    reachable_nodes = assumed_search(starting_node, areas, remaining_item_pool)

    # Out of the accessible nodes, get all item checks that are still empty
    reachable_null_checks: dict[Check, Node] = {}
    for node in reachable_nodes:
        for check in node.checks:
            if candidates is not None and check not in candidates:
                continue
            if check.contents is None:
                reachable_null_checks[check] = node

    # Place the current item into a random location
    r = list(reachable_null_checks.keys())[
        random.randint(0, max(0, len(reachable_null_checks) - 1))
    ]
    r.contents = item

    logger.info(f'Placed {item} at {reachable_null_checks[r].name}')


def _place_dungeon_rewards(
    starting_node: Node,
    item_pool: list[str],
    areas: dict[str, Area],
) -> None:
    dungeon_reward_pool = [item for item in item_pool if item in DUNGEON_REWARD_CHECKS.values()]
    for item in dungeon_reward_pool:
        possible_checks = OrderedSet(
            [
                check
                for area in areas.values()
                for room in area.rooms
                for node in room.nodes
                for check in node.checks
                if f'{node.area.name}.{node.room.name}.{check.name}' in DUNGEON_REWARD_CHECKS
            ]
        )
        item_pool.remove(item)
        _place_item(item, starting_node, item_pool, areas, possible_checks)


def _place_small_keys(
    starting_node: Node,
    item_pool: list[str],
    areas: dict[str, Area],
) -> None:
    """Place all small keys in `item_pool`."""
    key_pool = [item for item in item_pool if item.startswith('SmallKey_')]
    for item in key_pool:
        possible_checks = OrderedSet(
            [
                check
                for area in areas.values()
                for room in area.rooms
                for node in room.nodes
                for check in node.checks
                if node.area.name == item[9:]
            ]
        )
        item_pool.remove(item)
        _place_item(item[:8], starting_node, item_pool, areas, possible_checks)


def _place_important_items(
    starting_node: Node,
    item_pool: list[str],
    areas: dict[str, Area],
) -> None:
    """Place all "important" items in the given item_pool."""
    important_items = [item for item in item_pool if item in IMPORTANT_ITEMS]
    for item in important_items:
        item_pool.remove(item)
        _place_item(item, starting_node, item_pool, areas)


def _place_rest_of_items(
    starting_node: Node,
    item_pool: list[str],
    areas: dict[str, Area],
) -> None:
    """Place all items remaining in item_pool."""
    for item in item_pool:
        _place_item(item, starting_node, item_pool, areas)
    item_pool.clear()


def assumed_fill(
    areas: dict[str, Area],
    starting_node_name: str = 'Mercay.OutsideOshus.Outside',
) -> list[Area]:
    # Copy all items to a list and set all checks to null
    item_pool: list[str] = []
    for area in areas.values():
        for room in area.rooms:
            for check in room.chests:
                item = check.contents

                # Append area name for small keys, so that we know where we can place
                # it later on.
                if item == 'SmallKey':
                    item += f'_{area.name}'
                item_pool.append(item)
                check.contents = None  # type: ignore

    # Shuffle the item pool
    random.shuffle(item_pool)

    starting_node = [
        node
        for area in areas.values()
        for room in area.rooms
        for node in room.nodes
        if node.name == starting_node_name
    ][0]

    # Grab an item from the shuffled item pool
    item = item_pool.pop()

    _place_dungeon_rewards(starting_node, item_pool, areas)
    _place_small_keys(starting_node, item_pool, areas)
    _place_important_items(starting_node, item_pool, areas)
    _place_rest_of_items(starting_node, item_pool, areas)

    return list(areas.values())


def init_logic_graph(
    logic_directory: Path | None = None, aux_directory: Path | None = None
) -> dict[str, Area]:
    areas = parse_aux_data(aux_data_directory=aux_directory)
    annotate_logic(areas.values(), logic_directory=logic_directory)
    _connect_rooms(areas)
    return areas
