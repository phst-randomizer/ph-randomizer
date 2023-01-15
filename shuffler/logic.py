from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum, EnumMeta
import itertools
import json
import logging
from pathlib import Path
import random
import sys
from typing import Any

import inflection
from ordered_set import OrderedSet

from shuffler._parser import parse_edge_constraint, parse_logic
from shuffler.aux_models import Area, Check, Enemy, Exit, Room

ENEMIES_MAPPING = json.loads((Path(__file__).parent / 'enemies.json').read_text())

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
    # TODO: these are currently "disconnected" from the rest of the logic graph due to some aux
    # data not being complete. Once it's complete, these entries should be uncommented.
    # 'GoronTemple.CrimsonineRoom.Crimsonine': 'crimsonine',
    # 'IceTemple.AzurineRoom.Azurine': 'azurine',
    # 'MutohTemple.B4.Aquanine': 'aquanine',
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


class RecursionLimit:
    """
    Context manager that increases max recursion depth to a given value, and then decreases it
    back to the original value upon exit.
    """

    def __init__(self, limit):
        self.limit = limit

    def __enter__(self):
        self.old_limit = sys.getrecursionlimit()
        sys.setrecursionlimit(self.limit)

    def __exit__(self, *args, **kwargs):
        sys.setrecursionlimit(self.old_limit)


class AssumedFillFailed(Exception):
    pass


class Logic:
    areas: dict[str, Area]

    def __init__(self) -> None:
        Logic.areas = self._parse_aux_data()

        logic_directory = Path(__file__).parent / 'logic'

        for file in logic_directory.rglob('*.logic'):
            lines: list[str] = []
            with open(file) as fd:
                for line in fd.readlines():
                    line = line.strip()  # strip off leading and trailing whitespace
                    if '#' in line:
                        line = line[: line.index('#')]  # remove any comments
                    if line:
                        lines.append(line)
            file_contents = '\n'.join(lines)
            self._parse_logic(file_contents)

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

    def _place_item(
        self,
        item_to_place: str,
        candidates: OrderedSet[Check] | None = None,
        starting_nodes: list[Node] | None = None,
    ):
        """
        Randomly place an item somewhere.

        Params:
            item_to_place: The item to place.
            candidates: An optional list of candidate locations to place this item.
            If not provided, every logically reachable location will
            be considered.
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
                self._assumed_search(
                    starting_node,
                    deepcopy(self.items_left_to_place),
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
            # that aren't in that list.
            reachable_candidates.intersection_update(candidates)

        if not len(reachable_candidates):
            raise AssumedFillFailed(f'Failed to place {item_to_place}!!! Ran out of locations.')

        # Out of the remaining candidates, pick a random one and place the item in it.
        random_index = random.randint(0, max(len(reachable_candidates) - 1, 0))
        reachable_candidates[random_index].contents = item_to_place

    def place_important_items(self) -> None:
        items_to_place: list[str] = []
        for item in self.items_left_to_place:
            if item in IMPORTANT_ITEMS:
                items_to_place.append(item)

        for item in items_to_place:
            self._place_item(item)

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
            self._place_item(item, candidates)

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
            if area_name in ('MutohTemple', 'TempleOfTheOceanKing'):
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
                if area_name not in ('MutohTemple', 'TempleOfTheOceanKing')
            ]
            random.shuffle(self.items_left_to_place)

            # Make all item locations empty
            for chest, _ in all_checks:
                # Disable type-checking for this line.
                # `contents` should normally never be `None`, but during the assumed fill it must be
                chest.contents = None  # type: ignore

            try:
                # TODO: consider rewriting _assumed_search function with iteration instead of
                # recursion to avoid having to increase the max recursion depth here.
                with RecursionLimit(5000):
                    logging.info('Placing dungeon rewards...')
                    self.place_dungeon_rewards()
                    logging.info('Placing dungeon keys...')
                    self.place_keys()
                    logging.info('Placing important items ...')
                    self.place_important_items()
                    logging.info('Placing any remaining items...')
                    self.place_remaining_items()
                break
            except AssumedFillFailed:
                # If the assumed fill fails, restore the original chest contents and start over
                logging.info('Assumed fill failed! Trying again...')
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

    def _add_descriptor_to_node(
        self,
        node: Node,
        descriptor_type: str,
        descriptor_value: str,
    ) -> None:
        room = self._get_room(node.area, node.room)
        if not room:
            return
        match descriptor_type:
            case NodeDescriptor.CHEST.value:
                try:
                    node.checks.append(
                        [check for check in room.chests if check.name == descriptor_value][0]
                    )
                except IndexError:
                    raise Exception(
                        f'{node.area}.{room.name}: '
                        f'{descriptor_type} {descriptor_value!r} not found in aux data.'
                    )
            case (
                NodeDescriptor.ENTRANCE.value
                | NodeDescriptor.EXIT.value
                | NodeDescriptor.DOOR.value
            ):
                if descriptor_type in (NodeDescriptor.DOOR.value, NodeDescriptor.ENTRANCE.value):
                    if descriptor_value in node.entrances:
                        raise Exception(
                            f'{node.area}.{node.room}: '
                            f'entrance {descriptor_value!r} defined more than once'
                        )
                    node.entrances.add(f'{node.name}.{descriptor_value}')
                if descriptor_type in (NodeDescriptor.DOOR.value, NodeDescriptor.EXIT.value):
                    try:
                        new_exit = [exit for exit in room.exits if exit.name == descriptor_value][0]
                    except IndexError:
                        raise Exception(
                            f'{node.area}.{node.room}: '
                            f'{descriptor_type} {descriptor_value!r} not found in aux data.'
                        )
                    if new_exit.entrance.count('.') == 2:
                        new_exit.entrance = f'{node.area}.{new_exit.entrance}'
                    if new_exit.entrance.count('.') != 3:
                        # TODO: remove once aux data is complete
                        if not len(new_exit.entrance) or new_exit.entrance.lower() == 'todo':
                            logging.error(f'{node.name}: exit {new_exit.name!r} has no link.')
                            return
                        raise Exception(
                            f'{node.area}.{room.name}: ' f'Invalid exit link {new_exit.entrance!r}'
                        )
                    node.exits.append(new_exit)
            case NodeDescriptor.FLAG.value:
                node.flags.add(descriptor_value)
            case NodeDescriptor.LOCK.value:
                node.locks.add(descriptor_value)
            case NodeDescriptor.GAIN.value:
                node.states.add(descriptor_value)
            case NodeDescriptor.ENEMY.value:
                try:
                    node.enemies.append(
                        [enemy for enemy in room.enemies if enemy.name == descriptor_value][0]
                    )
                except IndexError:
                    raise Exception(
                        f'{node.area}.{room.name}: '
                        f'{descriptor_type} {descriptor_value!r} not found in aux data.'
                    )
            case other:
                if other not in NodeDescriptor:
                    raise Exception(f'{node.area}.{room.name}: Unknown node descriptor {other!r}')
                logging.warning(f'Node descriptor {other!r} not implemented yet.')
        return

    def _parse_logic(self, file_content: str) -> None:
        """
        Parse .logic files.

        First, the `parse_logic` function parses the .logic files into an intermediate
        `ParsedLogic` object. Then, it annotates the list of aux `Rooms` with the nodes
        from `ParsedLogic`.

        """

        parsed_logic = parse_logic(file_content)

        for logic_area in parsed_logic.areas:
            area = self._get_area(logic_area.name)
            if not area:  # TODO: remove when logic/aux is complete
                continue
            for logic_room in logic_area.rooms:
                room = self._get_room(logic_area.name, logic_room.name)
                if not room:  # TODO: remove when logic/aux is complete
                    continue
                for logic_node in logic_room.nodes:
                    full_node_name = '.'.join([logic_area.name, logic_room.name, logic_node.name])
                    node = Node(full_node_name)
                    for descriptor in logic_node.descriptors or []:
                        self._add_descriptor_to_node(node, descriptor.type, descriptor.value)
                    room.nodes.append(node)
                for edge in logic_room.edges:
                    for node1 in room.nodes:
                        if node1.node == edge.source_node:
                            for node2 in room.nodes:
                                if node2.node == edge.destination_node:
                                    node1.edges.append(
                                        Edge(
                                            src=node1,
                                            dest=node2,
                                            constraints=edge.constraints,
                                        )
                                    )
                                    if edge.direction == '<->':
                                        node2.edges.append(
                                            Edge(
                                                src=node2,
                                                dest=node1,
                                                constraints=edge.constraints,
                                            )
                                        )
                                    break
                            else:
                                raise Exception(
                                    f'{area.name}.{room.name}: '
                                    f"node {edge.destination_node} doesn't exist"
                                )
                            break
                    else:
                        raise Exception(
                            f'{area.name}.{room.name}: ' f"node {edge.source_node} doesn't exist"
                        )
                if f'{area.name}.{room.name}' not in [f'{area.name}.{r.name}' for r in area.rooms]:
                    area.rooms.append(room)

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
    def _assumed_search(
        cls,
        starting_node: Node,
        inventory: list[str],
        keys: dict[str, int] | None = None,
        flags: set[str] | None = None,
        states: set[str] | None = None,
        visited_nodes: OrderedSet[Node] | None = None,
    ) -> OrderedSet[Node]:
        """
        Calculate the set of nodes reachable from the `starting_node` given the current inventory.

        Params:
            `starting_node`: The node to start at.
            `inventory`: Current inventory.
            `keys`: Current small keys held for each dungeon.
            `flags`: Current flags that are set.
            `states`: Current logical states that have been "gained".
            `visited_nodes`: Nodes that have been visited already in this traversal.

        Returns:
            The set of nodes that is reachable given the current inventory.
        """
        logging.debug(starting_node.name)

        if visited_nodes is None:
            visited_nodes = OrderedSet()

        if states is None:
            states = set()

        if flags is None:
            flags = set()

        if keys is None:
            keys = {dungeon: 0 for dungeon in DUNGEON_STARTING_NODES.keys()}

        # For the current node, find all chests + "collect" their items
        for check in starting_node.checks:
            if check.contents and check.contents not in inventory:
                inventory.append(check.contents)
                # Reset visited nodes and rooms because we may now be able to reach
                # nodes we couldn't before with this new item
                visited_nodes.clear()

                # If this is a small key, increment key count for the associated dungeon
                if check.contents == 'small_key':
                    keys[starting_node.area] += 1

        for flag in starting_node.flags:
            if flag not in flags:
                flags.add(flag)
                # Reset visited nodes and rooms because we may now be able to reach
                # nodes we couldn't before with this new flag set
                visited_nodes.clear()

        for state in starting_node.states:
            if state not in states:
                states.add(state)

        visited_nodes.add(starting_node)  # Acknowledge this node as "visited"

        edges_that_require_keys: list[Edge] = []

        # Check which edges are traversable and do so if they are
        for edge in starting_node.edges:
            if edge.dest in visited_nodes:
                continue
            if edge.is_traversable(inventory, flags, states):
                logging.debug(f'{starting_node.name} -> {edge.dest.name}')
                # If the edge requires a key, but is otherwise traversable, save it to a list
                # to be processed later
                if edge.requires_key:
                    edges_that_require_keys.append(edge)
                # Otherwise, just traverse the edge
                else:
                    # Remove states lost by traversing this edge
                    new_states = {
                        state
                        for state in states
                        if not edge.states_to_lose or state not in edge.states_to_lose
                    }
                    visited_nodes.update(
                        cls._assumed_search(
                            edge.dest,
                            inventory,
                            keys,
                            flags,
                            new_states,
                            visited_nodes,
                        )
                    )

        # If there are any edges that require keys, but are otherwise traversable, traverse each
        # while considering worse-case key usage
        if len(edges_that_require_keys):
            keys_to_use = min(len(edges_that_require_keys), keys[starting_node.area])
            if keys_to_use > 0:
                keys[starting_node.area] -= keys_to_use

                # To determine what nodes can be reached given worst-case key usage, get
                # the sets of nodes reachable for every possible way the keys can be used,
                # then take the intersection of those sets.
                accessible_nodes_intersection: OrderedSet[Node] | None = None
                for subset in itertools.combinations(edges_that_require_keys, keys_to_use):
                    for edge in subset:
                        # Remove states lost by traversing this edge
                        new_states = {
                            state
                            for state in states
                            if not edge.states_to_lose or state not in edge.states_to_lose
                        }
                        accessible_nodes = cls._assumed_search(
                            edge.dest,
                            deepcopy(inventory),
                            deepcopy(keys),
                            deepcopy(flags),
                            new_states,
                            visited_nodes,
                        )
                        if accessible_nodes_intersection is None:
                            accessible_nodes_intersection = accessible_nodes
                        else:
                            accessible_nodes_intersection.intersection_update(accessible_nodes)
                if accessible_nodes_intersection is not None:
                    visited_nodes.update(accessible_nodes_intersection)
        return visited_nodes


@dataclass
class Node:
    name: str
    edges: list[Edge] = field(default_factory=list)
    checks: list[Check] = field(default_factory=list)
    exits: list[Exit] = field(default_factory=list)
    entrances: set[str] = field(default_factory=set)
    enemies: list[Enemy] = field(default_factory=list)
    flags: set[str] = field(default_factory=set)
    locks: set[str] = field(default_factory=set)
    states: set[str] = field(default_factory=set)

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
    states_to_lose: set[str] | None

    def __init__(self, src: Node, dest: Node, constraints: str | None = None) -> None:
        self.src = src
        self.dest = dest

        def _get_states_to_lose(
            constraints: list[str | list[str | list]],
            states: set[str] | None = None,
        ) -> set[str]:
            if states is None:
                states = set()
            for i, elem in enumerate(constraints):
                if isinstance(elem, list):
                    return _get_states_to_lose(elem, states)
                elif elem == EdgeDescriptor.LOSE.value:
                    state_name = constraints[i + 1]
                    assert isinstance(state_name, str)
                    states.add(state_name)
            return states

        logging.debug(f'Evaluating {constraints!r}...')

        # Parse edge constraint string
        if constraints is not None:
            self.constraints = parse_edge_constraint(constraints)
            assert len(self.constraints), f'Failed to parsed edge {constraints!r}'
            self.states_to_lose = _get_states_to_lose(self.constraints)
            if not len(self.states_to_lose):
                self.states_to_lose = None
        else:
            self.constraints = constraints
            self.states_to_lose = None

    def __repr__(self):
        r = f'{self.src.node} -> {self.dest.node}'
        if self.constraints:
            r += f': {str(self.constraints)}'
        return r

    @property
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
                    contains_open = True
            return contains_open

        return _contains_open(self.constraints) if self.constraints else False

    def is_traversable(
        self,
        current_inventory: list[str],
        current_flags: set[str],
        current_states: set[str],
    ) -> bool:
        """
        Determine if this edge is traversable given the current player state.

        Params:
            current_inventory: A list of strings representing the "current inventory", i.e. all
            items currently accessible given the current shuffled state.

            current_flags: A set of strings containing all `flags` that are logically set.
        """
        if self.constraints is not None and len(self.constraints):
            return self._is_traversable(
                parsed_expr=self.constraints,
                inventory=current_inventory,
                flags=current_flags,
                states=current_states,
            )
        return True

    def _is_traversable(
        self,
        # TODO: technically this is a recursive type. But, mypy doesn't support them currently
        # (ref: https://github.com/python/mypy/issues/731), so we're limited to this for now.
        # If recursive types are ever supported, this should be updated accordingly.
        parsed_expr: list[str | list[str | Any]],
        inventory: list[str],
        flags: set[str],
        states: set[str],
        result=True,
    ) -> bool:
        current_op = None  # variable to track current logical operation (AND or OR), if applicable

        while len(parsed_expr):
            # If the complex expression contains another complex expression, recursively evaluate it
            if isinstance(parsed_expr[0], list):
                sub_expression = parsed_expr.pop(0)
                assert isinstance(sub_expression, list)
                current_result = self._is_traversable(
                    parsed_expr=sub_expression,
                    inventory=inventory,
                    flags=flags,
                    states=states,
                    result=result,
                )
            else:
                # Extract type and value (e.g., 'item' and 'Bombs')
                expr_type = parsed_expr.pop(0)
                assert isinstance(expr_type, str)
                expr_value = parsed_expr.pop(0)
                assert isinstance(expr_value, str)

                current_result = self._evaluate_constraint(
                    expr_type, expr_value, inventory, flags, states
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
                current_op = parsed_expr.pop(0)

        return result

    def _evaluate_constraint(
        self,
        type: str,
        value: str,
        inventory: list[str],
        flags: set[str],
        states: set[str],
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
                return inflection.underscore(value) in inventory
            case EdgeDescriptor.FLAG.value:
                # Translate item name from PascalCase to snake_case
                return inflection.underscore(value) in flags
            case EdgeDescriptor.STATE.value | EdgeDescriptor.LOSE.value:
                return value in states
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
                                inventory,
                                flags,
                                states,
                            )
                raise Exception(
                    f'{self.src.name} (Edge "...{type} {value}..."): ' f'enemy {value} not found!'
                )
            case EdgeDescriptor.OPEN.value:
                accessible_nodes = Logic._assumed_search(
                    self.src,
                    deepcopy(inventory),
                    None,
                    deepcopy(flags),
                )
                for node in accessible_nodes:
                    if value in node.locks:
                        return True
                return False
            case other:
                if other not in EdgeDescriptor:
                    raise Exception(f'Invalid edge descriptor {other!r}')
                logging.warning(f'Edge descriptor {other!r} not implemented yet.')
                return False


class MetaEnum(EnumMeta):
    def __contains__(cls, item):
        try:
            cls(item)
        except ValueError:
            return False
        return True


class NodeDescriptor(Enum, metaclass=MetaEnum):
    CHEST = 'chest'
    FLAG = 'flag'
    DOOR = 'door'
    ENTRANCE = 'entrance'
    EXIT = 'exit'
    MAIL = 'mail'
    HINT = 'hint'
    ENEMY = 'enemy'
    LOCK = 'lock'
    GAIN = 'gain'
    SHOP = 'shop'


class EdgeDescriptor(Enum, metaclass=MetaEnum):
    ITEM = 'item'
    FLAG = 'flag'
    OPEN = 'open'
    DEFEATED = 'defeated'
    SETTING = 'setting'
    STATE = 'state'
    LOSE = 'lose'
