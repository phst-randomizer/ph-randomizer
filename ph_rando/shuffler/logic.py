from __future__ import annotations

from collections import defaultdict
from copy import copy, deepcopy
from dataclasses import dataclass, field
from functools import cached_property
import itertools
import json
import logging
from pathlib import Path
import random

import inflection
from ordered_set import OrderedSet

from ph_rando.shuffler._descriptors import EdgeDescriptor
from ph_rando.shuffler._parser import annotate_logic, parse_edge_constraint
from ph_rando.shuffler.aux_models import (
    Area,
    Check,
    DigSpot,
    Enemy,
    Exit,
    IslandShop,
    Room,
    SalvageTreasure,
    Tree,
)

ENEMIES_MAPPING = json.loads((Path(__file__).parent / 'enemies.json').read_text())
LOGIC_MACROS = json.loads((Path(__file__).parent / 'macros.json').read_text())

DUNGEON_STARTING_NODES: dict[str, set[str]] = {
    'MercayGrotto': {'F1.Lower', 'F2.EastExit'},
    'FireTemple': {'F1.Entrance'},
    'CourageTemple': {'F1.Entrance'},
    'WindTemple': {'F1.Entrance'},
    'TempleOfTheOceanKing': {'F1.Lower'},
    'MutohTemple': {'F1.Entrance'},
    'IceTemple': {'F1.Entrance'},
    'GoronTemple': {'F1.Entrance'},
    'GhostShip': {'F1.Main'},
}

DUNGEON_REWARD_CHECKS: dict[str, str] = {
    'BlaazBossRoom.Main.SpiritOfPower': 'power_spirit',
    'CyclokBossRoom.Main.SpiritOfWisdom': 'wisdom_spirit',
    'CraykBossRoom.Main.SpiritOfCourage': 'courage_spirit',
    'GoronTemple.CrimsonineRoom.Crimsonine': 'crimsonine',
    'IceTemple.AzurineRoom.Azurine': 'azurine',
    'MutohTemple.B4.Aquanine': 'aquanine',
}

IMPORTANT_ITEMS: set[str] = {
    'oshus_sword',
    'wooden_shield',
    'bombs',
    'bow',
    'boomerang',
    'shovel',
    'bombchus',
    'sw_sea_chart',
    'nw_sea_chart',
    'se_sea_chart',
    'ne_sea_chart',
    'hammer',
    'grappling_hook',
    'fishing_rod',
    'cannon',
    'sun_key',
    'king_key',
    'regal_necklace',
    'salvage_arm',
    'cyclone_slate',
    'phantom_hourglass',
    'phantom_sword',
}


class AssumedFillFailed(Exception):
    pass


class Logic:
    areas: dict[str, Area]
    settings: dict[str, str | bool]

    def __init__(self, settings: dict[str, str | bool]) -> None:
        Logic.areas = self._parse_aux_data()
        Logic.settings = {inflection.camelize(k): v for k, v in settings.items()}

        annotate_logic(Logic.areas.values(), Path(__file__).parent / 'logic')

    def connect_rooms(self) -> None:
        """
        Connects all rooms with edges, forming a graph representing the entire game.

        This eliminates the distinction between different `rooms`, and discards all
        doors/entrances/exists in favor of pure nodes/edges. Thus, this method should
        be called after any entrance/exit shuffling.
        """

        def _get_dest_node(dest_node_entrance: str):
            dest_node_split = dest_node_entrance.split('.')
            area_name = dest_node_split[0]
            room_name = dest_node_split[1]
            node_name = dest_node_split[2]

            for room in self.areas[area_name].rooms:
                if room.name == room_name:
                    for node in room.nodes:
                        if node.node == node_name:
                            for entrance in node.entrances:
                                if entrance == dest_node_entrance:
                                    return node
            raise Exception(f'Entrance {dest_node_entrance!r} not found')

        for area in self.areas.values():
            for room in area.rooms:
                for src_node in room.nodes:
                    for exit in src_node.exits:
                        if not len(exit.entrance):
                            raise Exception(f'exit {exit.name!r} has no "link".')
                        if exit.entrance.split('.')[0] not in self.areas:
                            logging.error(
                                f'entrance {exit.entrance!r} not found '
                                '(no aux data exists for that area)'
                            )
                            continue
                        src_node.edges.append(
                            Edge(src=src_node, dest=_get_dest_node(exit.entrance))
                        )
        # Delete all exits from nodes. At this point they no longer have any
        # meaning, and any attempt to access them would likely be a bug.
        # TODO: maybe remove this?
        for area in self.areas.values():
            for room in area.rooms:
                for node in room.nodes:
                    node.exits = None  # type: ignore

    @property
    def starting_node(self) -> Node:
        if 'Mercay' not in self.areas:
            raise Exception('Nodes are not initialized yet.')
        starting_node_name = 'Mercay.OutsideOshus.Outside'  # TODO: randomize this
        return [
            node
            for room in self.areas['Mercay'].rooms
            for node in room.nodes
            if node.name == starting_node_name
        ][0]

    @cached_property
    def invalid_progression_checks(self) -> OrderedSet[Check]:
        """
        Returns the ordered set of checks that progression items should *not* be placed in,
        based on the settings the user selects. For example, this method will return all
        dig spot checks and all salvage arm treasure checks if the user doesn't choose to
        include those as valid locations for progression items.
        """
        excluded_checks: OrderedSet[Check] = OrderedSet()
        for setting, cls in {
            'ShopItems': IslandShop,
            'SalvageArmTreasures': SalvageTreasure,
            'DigSpots': DigSpot,
            'TreeDrops': Tree,
        }.items():
            if not self.settings[setting]:
                excluded_checks.update(
                    OrderedSet(
                        check
                        for area in self.areas.values()
                        for room in area.rooms
                        for check in room.chests
                        if type(check) == cls
                    )
                )
        return excluded_checks

    def _place_item(
        self,
        item_to_place: str,
        candidates: OrderedSet[Check] | None = None,
        exclude: OrderedSet[Check] | None = None,
        starting_nodes: list[Node] | None = None,
    ):
        """
        Randomly place an item somewhere.

        Params:
            item_to_place: The item to place.
            candidates: An optional list of candidate locations to place this item.
            If not provided, every logically reachable location not specified in `exclude`
            will be considered.
            exclude: An optional list of candidate locations that this item must *not* be
            placed in.
            starting_nodes: The node(s) that the player has initial access to. Useful when
            randomizing "subgraphs" of the overall game in isolation, i.e. when placing
            dungeon items first inside their own dungeons, without regard for the rest
            of the game's locations.
        """

        # Remove this item from list of items left to be placed
        self.items_left_to_place.pop(self.items_left_to_place.index(item_to_place))

        # Small keys are (for now) all the same item, no matter what dungeon they are for.
        if item_to_place.startswith('small_key_'):
            item_to_place = 'small_key'

        # Populate keys dict for current inventory
        keys: dict[str, int] = defaultdict(int)
        for item in self.items_left_to_place:
            if item.startswith('small_key_'):
                keys[item[len('small_key_') :]] += 1

        # Determine all reachable logic nodes
        reachable_nodes: OrderedSet[Node] = OrderedSet()
        for starting_node in starting_nodes or [self.starting_node]:
            reachable_nodes.update(
                self.assumed_search(
                    starting_node,
                    copy(self.items_left_to_place),
                    keys,
                )
            )
        reachable_checks = OrderedSet(check for node in reachable_nodes for check in node.checks)

        # Determine, out of the reachable checks, which ones still don't have an item
        reachable_candidates: OrderedSet[Check] = OrderedSet(
            check for check in reachable_checks if check.contents is None
        )

        if candidates is not None:
            # If a list of candidate locations was provided, filter out any reachable checks
            # that *aren't* in that list.
            reachable_candidates.intersection_update(candidates)
        if exclude is not None:
            # If a list of candidate locations was provided, filter out any reachable checks
            # that *are* in that list.
            reachable_candidates.difference_update(exclude)

        if not len(reachable_candidates):
            raise AssumedFillFailed(f'Failed to place {item_to_place}!!! Ran out of locations.')

        # Out of the remaining candidates, pick a random one and place the item in it.
        random_index = random.randint(0, max(len(reachable_candidates) - 1, 0))
        reachable_candidates[random_index].contents = item_to_place

        node = [
            node
            for node in reachable_nodes
            for check in node.checks
            if check == reachable_candidates[random_index]
        ][0]
        logging.info(
            f'Placed {item_to_place} at {node.name} '
            f'(chest {reachable_candidates[random_index].name})'
        )

    def place_important_items(self) -> None:
        items_to_place: list[str] = []
        for item in self.items_left_to_place:
            if item in IMPORTANT_ITEMS:
                items_to_place.append(item)

        for item in items_to_place:
            self._place_item(item, exclude=self.invalid_progression_checks)

    def place_remaining_items(self) -> None:
        for item in self.items_left_to_place:
            self._place_item(item)

        self.items_left_to_place.clear()

    def place_dungeon_rewards(self) -> None:
        # Find all checks that a dungeon reward *may* be placed in.
        # TODO: for now, just allow dungeon items to be shuffled amongst themselves.
        # In the future, we'll have an optional setting that allows dungeon rewards
        # to be placed anywhere.
        candidates = OrderedSet(
            check
            for area in self.areas.values()
            for room in area.rooms
            for check in room.chests
            if '.'.join([area.name, room.name, check.name]) in DUNGEON_REWARD_CHECKS.keys()
        )

        items_to_place: list[str] = []

        for item in self.items_left_to_place:
            if item in DUNGEON_REWARD_CHECKS.values():
                items_to_place.append(item)

        for item in items_to_place:
            self._place_item(item, candidates, exclude=self.invalid_progression_checks)

    def place_keys(self) -> None:
        """
        Place all small keys randomly within their dungeons.
        """
        # Find all checks that a key *may* be placed in.
        # For non-keysanity, that means any check that is itself in an Area that contains
        # at least one check with a small key in the vanilla game.
        candidates = [
            (area_name, check)
            for area_name, area in self.areas.items()
            for room in area.rooms
            for check in room.chests
        ]

        items_to_place: list[tuple[str, str]] = []

        # Iterate over items to find every small key that needs to be placed
        for item in self.items_left_to_place:
            if not item.startswith('small_key_'):
                continue
            area_name = item[len('small_key_') :]

            # TODO: skip these areas for now because the assumed fill fails for them,
            # and it's unclear for now whether it's because of a bug in the shuffler
            # or an error in the logic.
            if area_name in ('TempleOfTheOceanKing',):
                logging.warning(f'Skipping {area_name}...')
                continue

            items_to_place.append((item, area_name))

        for item, area_name in items_to_place:
            # Narrow down candidates for this particular key to only include checks in the
            # area it's located in.
            particular_candidates = OrderedSet(
                check for area, check in candidates if area == area_name
            )

            # Get all possible entrance nodes for the current dungeon
            starting_nodes: list[Node] = []
            for starting_node in DUNGEON_STARTING_NODES[area_name]:
                starting_room_name, starting_node_name = starting_node.split('.')
                starting_nodes.append(
                    [
                        node
                        for room in self.areas[area_name].rooms
                        for node in room.nodes
                        if room.name == starting_room_name
                        if node.node == starting_node_name
                    ][0]
                )

            self._place_item(
                item,
                candidates=particular_candidates,
                starting_nodes=starting_nodes,
                exclude=self.invalid_progression_checks,
            )

    def randomize_items(self) -> list[Area]:
        """
        Shuffles the items in the aux data.

        The Assumed Fill algorithm is used to place the items. The implementation is based on the
        following paper:
        https://digitalcommons.lsu.edu/cgi/viewcontent.cgi?article=6325&context=gradschool_theses
        There are some deviations due to how our logic is structured, but it follows the same
        general Assumed Fill algorithm described there.
        """
        all_checks = [
            (chest, area.name)
            for area in self.areas.values()
            for room in area.rooms
            for chest in room.chests
        ]

        all_checks_backup = deepcopy(all_checks)

        while True:
            # Set current inventory to all chest contents (i.e. every item
            # in the item pool) and shuffle it
            self.items_left_to_place = [
                chest.contents if chest.contents != 'small_key' else f'small_key_{area_name}'
                for chest, area_name in all_checks
                # TODO: remove the following conditional once MutohTemple/TotOK work correctly
                # if area_name not in ('TempleOfTheOceanKing',)
            ]
            random.shuffle(self.items_left_to_place)

            # Make all item locations empty
            for chest, _ in all_checks:
                # Disable type-checking for this line.
                # `contents` should normally never be `None`, but during the assumed fill it must be
                chest.contents = None  # type: ignore

            try:
                logging.info(
                    f'Placing dungeon rewards... ({len(self.items_left_to_place)} remaining)'
                )
                self.place_dungeon_rewards()
                logging.info(f'Placing dungeon keys... ({len(self.items_left_to_place)} remaining)')
                self.place_keys()
                logging.info(
                    f'Placing important items ... ({len(self.items_left_to_place)} remaining)'
                )
                self.place_important_items()
                logging.info(
                    f'Placing remaining items... ({len(self.items_left_to_place)} remaining)'
                )
                self.place_remaining_items()
                break
            except AssumedFillFailed:
                # If the assumed fill fails, restore the original chest contents and start over
                logging.info('Assumed fill failed! Trying again...')
                exit(1)  # TODO: remove
                for (chest, _), (chest_backup, _) in zip(all_checks, all_checks_backup):
                    chest.contents = chest_backup.contents
                continue

        return list(self.areas.values())

    def _get_area(self, area_name: str) -> Area | None:
        if area_name in self.areas:
            return self.areas[area_name]
        else:
            logging.error(f'Area {area_name} not found!')
            return None

    def _get_room(self, area_name: str, room_name: str) -> Room | None:
        try:
            return [room for room in self.areas[area_name].rooms if room.name == room_name][0]
        except IndexError:
            raise Exception(f'{area_name}: Room {area_name}.{room_name} not found!')

    def _parse_aux_data(self) -> dict[str, Area]:
        aux_data_directory = Path(__file__).parent / 'logic'

        areas: dict[str, Area] = {}
        for file in aux_data_directory.rglob('*.json'):
            with open(file) as fd:
                area = Area(**json.load(fd))

                # It's possible for an Area to be spread across multiple files.
                # To support this, check if this area exists first. If it does,
                # add the new area's rooms to the existing area's rooms.
                # Otherwise, add the new area.
                if area.name in areas:
                    areas[area.name].rooms.extend(area.rooms)
                else:
                    areas[area.name] = area
        return areas

    @classmethod
    def assumed_search(
        cls,
        starting_node: Node,
        inventory: list[str],
        keys: dict[str, int] | None = None,
        unlocked_doors: set[Node] | None = None,
        flags: set[str] | None = None,
        ignored_nodes: set[Node] | None = None,
        visited_nodes: OrderedSet[Node] | None = None,
    ):
        while True:
            (
                visited_nodes_first,
                inventory,
                keys,
                unlocked_doors,
                flags,
                new_ignored_nodes,
            ) = cls._assumed_search(
                starting_node,
                inventory,
                keys,
                unlocked_doors,
                flags,
                ignored_nodes,
                visited_nodes,
            )
            (
                visited_nodes_second,
                inventory,
                keys,
                unlocked_doors,
                flags,
                new_ignored_nodes,
            ) = cls._assumed_search(
                starting_node,
                inventory,
                keys,
                unlocked_doors,
                flags,
                ignored_nodes,
                visited_nodes,
            )
            if visited_nodes_second == visited_nodes_first:
                return visited_nodes_first

    @classmethod
    def _assumed_search(
        cls,
        starting_node: Node,
        inventory: list[str],
        keys: dict[str, int] | None = None,
        unlocked_doors: set[Node] | None = None,
        flags: set[str] | None = None,
        ignored_nodes: set[Node] | None = None,
        visited_nodes: OrderedSet[Node] | None = None,
    ):
        """
        Calculate the set of nodes reachable from the `starting_node` given the current inventory.

        Params:
            `starting_node`: The node to start at.
            `inventory`: Current inventory.
            `keys`: Current small keys held for each dungeon.
            `flags`: Current flags that are set.
            `visited_nodes`: Nodes that have been visited already in this traversal.

        Returns:
            The set of nodes that is reachable given the current inventory.
        """
        logging.debug(starting_node.name)

        if visited_nodes is None:
            visited_nodes = OrderedSet()

        if flags is None:
            flags = set()

        if keys is None:
            keys = {dungeon: 0 for dungeon in DUNGEON_STARTING_NODES.keys()}

        if unlocked_doors is None:
            unlocked_doors = set()

        if ignored_nodes is None:
            ignored_nodes = set()

        # For the current node, find all chests + "collect" their items
        for check in starting_node.checks:
            if check.contents and check.contents not in inventory:
                inventory.append(check.contents)

            # If this is a small key, increment key count for the associated dungeon
            if check.contents == 'small_key':
                keys[starting_node.area] += 1

        for flag in starting_node.flags:
            if flag not in flags:
                flags.add(flag)

        visited_nodes.add(starting_node)  # Acknowledge this node as "visited"

        edges_that_require_keys: list[Edge] = []

        # Check which edges are traversable and do so if they are
        for edge in starting_node.edges:
            if edge.dest in visited_nodes:
                continue
            if edge.dest in ignored_nodes:
                continue
            if edge.is_traversable(
                current_inventory=inventory,
                current_flags=flags,
                current_keys=keys,
                current_unlocked_doors=unlocked_doors,
                visited_nodes=visited_nodes,
                ignored_nodes=ignored_nodes,
            ):
                logging.debug(f'{starting_node.name} -> {edge.dest.name}')
                # If the edge requires a key and hasn't been unlocked yet, but is otherwise
                # traversable, save it to a list to be processed later
                if edge.src not in unlocked_doors and edge.requires_key:
                    edges_that_require_keys.append(edge)
                # Otherwise, just traverse the edge
                else:
                    visited_nodes.update(
                        cls._assumed_search(
                            edge.dest,
                            inventory,
                            keys,
                            unlocked_doors,
                            flags,
                            ignored_nodes,
                            visited_nodes,
                        )[0]
                    )

        # If there are any edges that require keys, but are otherwise traversable, traverse each
        # while considering worse-case key usage
        if len(edges_that_require_keys):
            key_doors = {edge.locked_door for edge in edges_that_require_keys}
            keys_to_use = min(len(key_doors), keys[starting_node.area])
            if keys_to_use > 0:
                # To determine what nodes can be reached given worst-case key usage, get
                # the sets of nodes reachable for every possible way the keys can be used,
                # then take the intersection of those sets.
                accessible_nodes_intersection: OrderedSet[Node] | None = None
                for subset in itertools.combinations(key_doors, keys_to_use):
                    for node in subset:
                        assert node
                        for edge in node.edges:
                            if edge.dest in visited_nodes:
                                continue
                            # To avoid retracing our steps, ignore any already-visited nodes in the
                            # recursive assumed search (in addition to the existing ignored_nodes)
                            new_ignored_nodes = ignored_nodes.union(set(visited_nodes))

                            # Don't modify the original `keys` dict yet; we're still not sure if
                            # this key door will be one of the ones unlocked.
                            new_keys = copy(keys)
                            new_keys[starting_node.area] -= 1  # Use the key

                            # Add the current door to unlocked doors. Again, don't modify
                            # the original for the same reasons as above.
                            new_unlocked_doors = copy(unlocked_doors)
                            if edge.locked_door:
                                new_unlocked_doors.add(edge.locked_door)

                            accessible_nodes = cls._assumed_search(
                                edge.dest,
                                copy(inventory),
                                new_keys,
                                new_unlocked_doors,
                                copy(flags),
                                ignored_nodes=new_ignored_nodes,
                                visited_nodes=visited_nodes,
                            )[0]
                            if accessible_nodes_intersection is None:
                                accessible_nodes_intersection = accessible_nodes
                            else:
                                accessible_nodes_intersection.intersection_update(accessible_nodes)

                # Assert not None to satisfy type-checker
                assert accessible_nodes_intersection is not None

                # Mark the newly accessible nodes as visited
                visited_nodes.update(accessible_nodes_intersection)

                # Figure out what doors we ended up unlocking, and record them as unlocked
                for node in visited_nodes:
                    assert isinstance(node, Node)
                    for edge in node.edges:
                        if edge.requires_key and edge.locked_door not in unlocked_doors:
                            assert edge.locked_door is not None, edge
                            unlocked = True
                            for e in edge.locked_door.edges:
                                if e.requires_key and e.dest not in accessible_nodes_intersection:
                                    unlocked = False
                            if unlocked:
                                if keys[starting_node.area] > 0:
                                    keys[starting_node.area] -= 1
                                unlocked_doors.add(edge.locked_door)

                # Collect all checks from newly accessible nodes
                for node in accessible_nodes_intersection:
                    assert isinstance(node, Node)
                    for check in node.checks:
                        if check.contents:
                            if check.contents not in inventory:
                                inventory.append(check.contents)
                            # Reset visited nodes and rooms because we may now be able to reach
                            # nodes we couldn't before with this new item
                            # visited_nodes.clear()

                            # If this is a small key, increment key count for the associated dungeon
                            if check.contents == 'small_key':
                                keys[node.area] += 1

                    for flag in node.flags:
                        if flag not in flags:
                            flags.add(flag)

        return (
            visited_nodes,
            inventory,
            keys,
            unlocked_doors,
            flags,
            ignored_nodes,
        )


@dataclass
class Node:
    name: str
    edges: list[Edge] = field(default_factory=list)
    checks: list[Check] = field(default_factory=list)
    exits: list[Exit] = field(default_factory=list)
    entrances: set[str] = field(default_factory=set)
    enemies: list[Enemy] = field(default_factory=list)
    flags: set[str] = field(default_factory=set)
    lock: str = field(default_factory=str)

    @property
    def area(self) -> str:
        return self.name.split('.')[0]

    @property
    def room(self) -> str:
        return self.name.split('.')[1]

    @property
    def node(self) -> str:
        return self.name.split('.')[2]

    # Provide implementations of __eq__ and __hash__ so that Nodes can be added to a `set`
    def __eq__(self, other_node) -> bool:
        return self.name == other_node.name

    def __hash__(self) -> int:
        return hash(self.name)


class Edge:
    src: Node
    dest: Node
    constraints: list[str | list[str | list]] | None
    locked_door: Node | None

    def __init__(self, src: Node, dest: Node, constraints: str | None = None) -> None:
        self.src = src
        self.dest = dest

        def _get_descriptors(
            constraints: list[str | list[str | list]],
            descriptor: str,
            values: set[str] | None = None,
        ) -> set[str]:
            if values is None:
                values = set()
            for i, elem in enumerate(constraints):
                if isinstance(elem, list):
                    return _get_descriptors(elem, descriptor, values)
                elif elem == descriptor:
                    name = constraints[i + 1]
                    assert isinstance(name, str)
                    values.add(name)
            return values

        self.constraints = None
        self.locked_door = None

        logging.debug(f'Evaluating {constraints!r}...')

        # Parse edge constraint string
        if constraints is not None:
            self.constraints = parse_edge_constraint(constraints)
            assert len(self.constraints), f'Failed to parsed edge {constraints!r}'
            locks = _get_descriptors(self.constraints, EdgeDescriptor.OPEN.value)
            for lock_name in locks:
                for area in Logic.areas.values():
                    if area.name != self.src.area:
                        continue
                    for room in area.rooms:
                        if room.name != self.src.room:
                            continue
                        for node in room.nodes:
                            if node.lock == lock_name:
                                self.locked_door = node

    def __repr__(self):
        r = f'{self.src.name} -> {self.dest.name}'
        if self.constraints:
            r += f': {str(self.constraints)}'
        return r

    @cached_property
    def required_items(self) -> list[str]:
        def _get_required_items(
            constraints: list[str | list[str | list]], required_items: list[str]
        ):
            for i, elem in enumerate(constraints):
                if isinstance(elem, list):
                    _get_required_items(elem, required_items)
                elif EdgeDescriptor.ITEM.value == elem:
                    required_items.append(inflection.underscore(constraints[i + 1]))  # type: ignore

        items: list[str] = []
        if self.constraints:
            _get_required_items(self.constraints, items)
        return items

    def __hash__(self) -> int:
        return id(self)

    @cached_property
    def required_flags(self) -> list[str]:
        def _get_required_items(
            constraints: list[str | list[str | list]], required_flags: list[str]
        ):
            for i, elem in enumerate(constraints):
                if isinstance(elem, list):
                    _get_required_items(elem, required_flags)
                elif EdgeDescriptor.FLAG.value == elem:
                    required_flags.append(constraints[i + 1])  # type: ignore

        flags: list[str] = []
        if self.constraints:
            _get_required_items(self.constraints, flags)
        return flags

    @cached_property
    def requires_key(self) -> bool:
        """
        Whether or not this edge requires a key to traverse, i.e. if it represents a locked door.
        """

        def _contains_open(constraints: list[str | list[str | list]]):
            contains_open = False
            for elem in constraints:
                if isinstance(elem, list):
                    contains_open = _contains_open(elem)
                elif EdgeDescriptor.OPEN.value in elem:
                    return True
            return contains_open

        return _contains_open(self.constraints) if self.constraints else False

    def is_traversable(
        self,
        current_inventory: list[str],
        current_flags: set[str] | None = None,
        current_keys: dict[str, int] | None = None,
        current_unlocked_doors: set[Node] | None = None,
        visited_nodes: OrderedSet[Node] | None = None,
        ignored_nodes: set[Node] | None = None,
    ) -> bool:
        """
        Determine if this edge is traversable given the current player state.

        Params:
            current_inventory: A list of strings representing the "current inventory", i.e. all
                               items currently accessible given the current shuffled state.
            current_flags: A set of strings containing all `flags` that are logically set.
            ignored_nodes: Nodes to ignore when a assumed search is needed. Can be used to avoid
                           an infinite recursion where is_traversable calls _assumed_search which
                           calls is_traversable which calls _assumed_search, etc.

        """
        if self.constraints is not None and len(self.constraints):
            return self._is_traversable(
                parsed_expr=self.constraints,
                current_inventory=current_inventory,
                current_flags=current_flags,
                current_keys=current_keys,
                current_unlocked_doors=current_unlocked_doors,
                visited_nodes=visited_nodes,
                ignored_nodes=ignored_nodes,
            )
        return True

    def _is_traversable(
        self,
        parsed_expr: list[str | list[str | list]],
        current_inventory: list[str],
        current_flags: set[str] | None = None,
        current_keys: dict[str, int] | None = None,
        current_unlocked_doors: set[Node] | None = None,
        visited_nodes: OrderedSet[Node] | None = None,
        ignored_nodes: set[Node] | None = None,
        result=True,
    ) -> bool:
        current_op = None  # variable to track current logical operation (AND or OR), if applicable
        while len(parsed_expr):
            # If the complex expression contains another complex expression, recursively evaluate it
            if isinstance(parsed_expr[0], list):
                sub_expression = parsed_expr[0]
                parsed_expr = parsed_expr[1:]
                assert isinstance(sub_expression, list)
                current_result = self._is_traversable(
                    sub_expression,
                    current_inventory,
                    current_flags,
                    current_keys,
                    current_unlocked_doors,
                    visited_nodes,
                    ignored_nodes,
                    result,
                )
            else:
                # Extract type and value (e.g., 'item' and 'Bombs')
                expr_type = parsed_expr[0]
                assert isinstance(expr_type, str)
                expr_value = parsed_expr[1]
                assert isinstance(expr_value, str)

                parsed_expr = parsed_expr[2:]

                current_result = self._evaluate_constraint(
                    expr_type,
                    expr_value,
                    current_inventory,
                    current_flags,
                    current_keys,
                    current_unlocked_doors,
                    visited_nodes,
                    ignored_nodes,
                )

            # Apply any pending logical operations
            if current_op == '&':
                result &= current_result
            elif current_op == '|':
                result |= current_result
            else:
                result = current_result

            # Queue up a logical AND or OR for the next expression if needed
            if len(parsed_expr) and parsed_expr[0] in ('&', '|'):
                current_op = parsed_expr[0]
                parsed_expr = parsed_expr[1:]

        return result

    def _evaluate_constraint(
        self,
        type: str,
        value: str,
        current_inventory: list[str],
        current_flags: set[str] | None = None,
        current_keys: dict[str, int] | None = None,
        current_unlocked_doors: set[Node] | None = None,
        visited_nodes: OrderedSet[Node] | None = None,
        ignored_nodes: set[Node] | None = None,
    ) -> bool:
        """
        Given an edge constraint "type value", determines if the edge is traversable
        given the current game state (inventory, set flags, etc).

        Params:
            type: The type of edge constraint, e.g. "item", "flag", etc.

            value: The value of the edge constraint, e.g. "Bombs", "BridgeRepaired", etc.

            inventory: A list of strings representing the "current inventory", i.e. all
            items currently accessible given the current shuffled state.
        """
        match type:
            case EdgeDescriptor.ITEM.value:
                # Special case: "Sword" means either OshusSword or PhantomSword.
                if value == 'Sword':
                    value = 'OshusSword'
                # Translate item name from PascalCase to snake_case
                return inflection.underscore(value) in current_inventory
            case EdgeDescriptor.FLAG.value:
                return current_flags is not None and value in current_flags
            case EdgeDescriptor.DEFEATED.value:
                for room in Logic.areas[self.src.area].rooms:
                    if room.name == self.src.room:
                        for enemy in room.enemies:
                            if enemy.name != value:
                                continue
                            elif enemy.type not in ENEMIES_MAPPING:
                                raise Exception(
                                    f'{self.src.name}: invalid enemy type {enemy.type!r}'
                                )
                            return self._is_traversable(
                                parse_edge_constraint(ENEMIES_MAPPING[enemy.type]),
                                current_inventory,
                                current_flags,
                                current_keys,
                                current_unlocked_doors,
                                ignored_nodes=ignored_nodes.union({self.dest})
                                if ignored_nodes
                                else {self.dest},
                            )
                raise Exception(
                    f'{self.src.name} (Edge "...{type} {value}..."): ' f'enemy {value} not found!'
                )
            case EdgeDescriptor.OPEN.value:
                # Check if the node that the `lock` is on has already been visited.
                # This is a small optimization to avoid making a recursive call to
                # `_assumed_search()` if it can be avoided.
                if visited_nodes:
                    for node in visited_nodes:
                        if value == node.lock:
                            return True
                # It's possible that the node containing the referenced `lock` *is* accessible,
                # but we haven't visited it yet. So, now we try an assumed search starting at
                # the source of the current edge.
                new_ignored_nodes = (
                    ignored_nodes.union({self.dest}) if ignored_nodes else {self.dest}
                )
                accessible_nodes = Logic._assumed_search(
                    starting_node=self.src,
                    inventory=copy(current_inventory),
                    flags=copy(current_flags),
                    ignored_nodes=new_ignored_nodes,
                )[0]
                for node in accessible_nodes:
                    if value == node.lock:
                        return True
                return False
            case EdgeDescriptor.SETTING.value:
                if value not in Logic.settings:
                    raise Exception(f'Invalid setting {value}, not found in settings.json.')
                setting_is_set = Logic.settings[value]
                assert isinstance(
                    setting_is_set, bool
                ), f'Setting {value} must have `flag=true` to be used in logic.'
                return setting_is_set
            case EdgeDescriptor.MACRO.value:
                if value not in LOGIC_MACROS:
                    raise Exception(f'Invalid macro "{value}", not found in macros.json!')
                return self._is_traversable(
                    parse_edge_constraint(LOGIC_MACROS[value]),
                    current_inventory,
                    current_flags,
                    current_keys,
                    current_unlocked_doors,
                    ignored_nodes=ignored_nodes.union({self.dest})
                    if ignored_nodes
                    else {self.dest},
                )
            # TODO: implement these
            case EdgeDescriptor.STATE.value:
                return True
            case EdgeDescriptor.LOSE.value:
                return True
            case other:
                if other not in EdgeDescriptor:
                    raise Exception(f'Invalid edge descriptor {other!r}')
                logging.warning(f'Edge descriptor {other!r} not implemented yet.')
                return False
