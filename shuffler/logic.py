from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from enum import Enum, EnumMeta
import json
import logging
from pathlib import Path
import random
from typing import Any

import inflection

from shuffler._parser import parse_edge_constraint, parse_logic
from shuffler.aux_models import Area, Check, Door, Room


class Logic:
    nodes: list[Node]
    _aux_data: list[Area]

    def __init__(self) -> None:
        self._aux_data = self._parse_aux_data()
        self._logical_rooms: list[LogicalRoom] = []
        self.nodes = []

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

    def connect_rooms(self):
        """
        Connects all `LogicalRooms` with edges, forming a graph representing the entire game.
        """

        def _get_dest_node(dest_node_entrance: str):
            entrance_split = dest_node_entrance.split('.')
            area_name = entrance_split[0]
            room_name = entrance_split[1]
            node_name = entrance_split[2]

            for room in self._logical_rooms:
                assert room.nodes
                if area_name == room.area.name and room_name == room.name:
                    for node in room.nodes:
                        if node.node == node_name:
                            for entrance in node.entrances:
                                if entrance == dest_node_entrance:
                                    return node
            raise Exception(f'Entrance "{dest_node_entrance}" not found')

        for room in self._logical_rooms:
            assert room.nodes
            for src_node in room.nodes:
                self.nodes.append(src_node)
                for exit in src_node.exits:
                    if not len(exit.link):
                        # TODO: make this throw an actual error once aux data is complete
                        logging.warning(f'exit "{exit.name}" has no "link".')
                        continue
                    if exit.link.split('.')[0] not in [r.area.name for r in self._logical_rooms]:
                        logging.warning(
                            f'entrance "{exit.link}" not found (no aux data exists for that area)'
                        )
                        continue
                    src_node.edges.append(Edge(dest=_get_dest_node(exit.link)))

    def randomize_items(self) -> list[Area]:
        """
        Shuffles the items in the aux data.

        The Assumed Fill algorithm is used to place the items. The implementation is based on the
        following paper:
        https://digitalcommons.lsu.edu/cgi/viewcontent.cgi?article=6325&context=gradschool_theses
        There are some deviations due to how our logic is structured, but it follows the same
        general Assumed Fill algorithm described there; where possible, variable/function names
        are identical to their counterparts in the pseudo-code in that paper.
        """
        starting_node_name = 'Mercay.OutsideOshus.Outside'  # TODO: randomize this
        starting_node = [node for node in self.nodes if node.name == starting_node_name][0]

        # Set G to all chests
        G = [chest for area in self._aux_data for room in area.rooms for chest in room.chests]

        # Set I to all chest contents (i.e. every item in the item pool) and shuffle it
        I = [chest.contents for chest in G]  # noqa: E741
        random.shuffle(I)

        # Make all item locations empty
        for chest in G:
            # Disable type-checking for this line.
            # `contents` should normally never be `None`, but during the assumed fill it must be.
            chest.contents = None  # type: ignore

        I_prime: list[str] = []

        while True:
            # Select a random item to place
            i = I.pop()

            # Determine all reachable logic nodes
            R = self._assumed_search(starting_node, deepcopy(I), set(), set())

            # Determine which of these nodes contain items,
            # and thus are candidates for item placement
            candidates = [check for node in R for check in node.checks]

            # Shuffle them
            random.shuffle(candidates)

            # Find an empty item location and place the item in it
            for chest in candidates:
                if chest.contents is None:
                    chest.contents = i
                    I_prime.append(i)
                    break
            else:
                raise Exception(
                    'Error: shuffler ran out of locations to place item.'
                    f'Remaining items: {[i] + I} ({len([i] + I)})'
                )

            # TODO: these conditions should both become true at the same time, once shuffling
            # is complete. If one is true but not the other, that indicates that either not
            # all items were placed, or not every location received an item. However, until
            # the aux data and logic are complete, this will not be true; once they are complete,
            # this statement should be changed to an `and` instead of `or` and an explicit check
            # should be added to avoid an infinite loop.
            if not len(I) or None not in {r.contents for r in candidates}:
                break
        return self.aux_data

    @property
    def aux_data(self) -> list[Area]:
        return self._aux_data

    def _get_area(self, area_name: str) -> Area | None:
        try:
            return [area for area in self._aux_data if area.name == area_name][0]
        except IndexError:
            logging.warning(f'Area {area_name} not found!')
            return None

    def _get_room(self, area_name: str, room_name: str) -> Room | None:
        try:
            return [
                room
                for area in self._aux_data
                for room in area.rooms
                if area.name == area_name
                if room.name == room_name
            ][0]
        except IndexError:
            logging.warning(f'Room {area_name}.{room_name} not found!')
            return None

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
                        f'{descriptor_type} "{descriptor_value}" not found in aux data.'
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
                            f'entrance "{descriptor_value}" defined more than once'
                        )
                    node.entrances.add(f'{node.name}.{descriptor_value}')
                if descriptor_type in (NodeDescriptor.DOOR.value, NodeDescriptor.EXIT.value):
                    try:
                        new_exit = [door for door in room.doors if door.name == descriptor_value][0]
                    except IndexError:
                        raise Exception(
                            f'{node.area}.{node.room}: '
                            f'{descriptor_type} "{descriptor_value}" not found in aux data.'
                        )
                    if new_exit.link.count('.') == 2:
                        new_exit.link = f'{node.area}.{new_exit.link}'
                    if new_exit.link.count('.') != 3:
                        # TODO: remove once aux data is complete
                        if not len(new_exit.link) or new_exit.link.lower() == 'todo':
                            logging.warning(f'{node.name}: exit "{new_exit.name} has no link.')
                            return
                        raise Exception(
                            f'{node.area}.{room.name}: ' f'Invalid exit link "{new_exit.link}"'
                        )
                    node.exits.append(new_exit)
            case NodeDescriptor.FLAG.value:
                node.flags.add(descriptor_value)
            case other:
                if other not in NodeDescriptor:
                    raise Exception(f'{node.area}.{room.name}: Unknown node descriptor "{other}"')
                logging.warning(f'Node descriptor "{other}" not implemented yet.')
        return

    def _parse_logic(self, file_content: str) -> None:
        """Parses .logic files into LogicalRooms."""

        parsed_logic = parse_logic(file_content)

        for area in parsed_logic.areas:
            aux_area = self._get_area(area.name)
            if not aux_area:  # TODO: remove when logic/aux is complete
                continue
            for room in area.rooms:
                logical_room = None
                for lr in self._logical_rooms:
                    if lr.area.name == aux_area.name and lr.name == room.name:
                        logical_room = lr
                        break
                else:
                    logical_room = LogicalRoom(area=aux_area, name=room.name, nodes=[])

                for node in room.nodes:
                    full_node_name = '.'.join([area.name, room.name, node.name])
                    _node = Node(
                        full_node_name,
                        edges=[],
                        checks=[],
                        exits=[],
                        entrances=set(),
                        flags=set(),
                    )
                    for descriptor in node.descriptors or []:
                        self._add_descriptor_to_node(_node, descriptor.type, descriptor.value)
                    logical_room.nodes.append(_node)
                for edge in room.edges:
                    for node1 in logical_room.nodes:
                        if node1.node == edge.source_node:
                            for node2 in logical_room.nodes:
                                if node2.node == edge.destination_node:
                                    node1.edges.append(
                                        Edge(dest=node2, constraints=edge.constraints)
                                    )
                                    if edge.direction == '<->':
                                        node2.edges.append(
                                            Edge(dest=node1, constraints=edge.constraints)
                                        )
                                    break
                            else:
                                raise Exception(
                                    f'{logical_room.area.name}.{logical_room.name}: '
                                    f"node {edge.destination_node} doesn't exist"
                                )
                            break
                    else:
                        raise Exception(
                            f'{logical_room.area.name}.{logical_room.name}: '
                            f"node {edge.source_node} doesn't exist"
                        )
                if f'{logical_room.area.name}.{logical_room.name}' not in [
                    f'{r.area.name}.{r.name}' for r in self._logical_rooms
                ]:
                    self._logical_rooms.append(logical_room)

    def _parse_aux_data(self) -> list[Area]:
        aux_data_directory = Path(__file__).parent / 'logic'

        areas: list[Area] = []
        for file in aux_data_directory.rglob('*.json'):
            with open(file) as fd:
                area = Area(**json.load(fd))

                # It's possible for an Area to be spread across multiple files.
                # To support this, check if this area exists first. If it does,
                # add the new area's rooms to the existing area's rooms.
                # Otherwise, add the new area to the list.
                for existing_area in areas:
                    if area.name == existing_area.name:
                        existing_area.rooms.extend(area.rooms)
                        break
                else:
                    areas.append(area)
        return areas

    def _assumed_search(
        self,
        starting_node: Node,
        inventory: list[str],
        flags: set[str],
        visited_nodes: set[Node],
    ) -> set[Node]:
        """
        Calculate the set of nodes reachable from the `starting_node` given the current inventory.

        Params:
            `starting_node`: The node to start at.
            `nodes`: The nodes that make up the game's logic graph.
            `aux_data`: Complete aux data for the game as a list of `Area`s.
            `inventory`: Current inventory.
            `flags`: Current flags that are set.
            `visited_nodes`: Nodes that have been visited already in this traversal.

        Returns:
            The set of nodes that is reachable given the current inventory.
        """
        logging.debug(starting_node.name)

        # For the current node, find all chests + "collect" their items and note every door so
        # we can go through them later
        for check in starting_node.checks:
            if check.contents and check.contents not in inventory:
                inventory.append(check.contents)
                # Reset visited nodes and rooms because we may now be able to reach
                # nodes we couldn't before with this new item
                visited_nodes.clear()

        for flag in starting_node.flags:
            if flag not in flags:
                flags.add(flag)
                # Reset visited nodes and rooms because we may now be able to reach
                # nodes we couldn't before with this new flag set
                visited_nodes.clear()

        visited_nodes.add(starting_node)  # Acknowledge this node as "visited"

        # Check which edges are traversable and do so if they are
        for edge in starting_node.edges:
            if edge.dest in visited_nodes:
                continue
            if edge.is_traversable(inventory, flags):
                logging.debug(f'{starting_node.name} -> {edge.dest.name}')
                visited_nodes = visited_nodes.union(
                    self._assumed_search(
                        edge.dest,
                        inventory,
                        flags,
                        visited_nodes,
                    )
                )
        return visited_nodes


@dataclass
class Node:
    name: str
    edges: list[Edge]
    checks: list[Check]
    exits: list[Door]
    entrances: set[str]
    flags: set[str]

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
        return hash(repr(self))


class Edge:
    dest: Node
    constraints: list[str | list[str | list]] | None

    def __init__(self, dest: Node, constraints: str | None = None) -> None:
        self.dest = dest

        logging.debug(f'Evaluating "{constraints}"...')

        # Parse edge constraint string
        if constraints is not None:
            self.constraints = parse_edge_constraint(constraints)
            assert len(self.constraints), f'Failed to parsed edge "{constraints}"'
        else:
            self.constraints = constraints

    def is_traversable(self, current_inventory: list[str], current_flags: set[str]) -> bool:
        """
        Determine if this edge is traversable given the current player state.

        Params:
            current_inventory: A list of strings representing the "current inventory", i.e. all
            items currently accessible given the current shuffled state.

            current_flags: A set of strings containing all `flags` that are logically set.
        """
        if self.constraints is not None:
            return self._is_traversable(
                parsed_expr=self.constraints,
                inventory=current_inventory,
                flags=current_flags,
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
                    result=result,
                )
            else:
                # Extract type and value (e.g., 'item' and 'Bombs')
                expr_type = parsed_expr.pop(0)
                assert isinstance(expr_type, str)
                expr_value = parsed_expr.pop(0)
                assert isinstance(expr_value, str)

                # Convert items in PascalCase or camelCase to snake_case.
                # The logic format is flexible and supports either of the three formats,
                # so the shuffler needs to normalize everything to snake_case at runtime.
                expr_value = inflection.underscore(expr_value)
                assert isinstance(expr_value, str)

                current_result = self._evaluate_constraint(expr_type, expr_value, inventory, flags)

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
        self, type: str, value: str, inventory: list[str], flags: set[str]
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
                return value in inventory
            case EdgeDescriptor.FLAG.value:
                return value in flags
            case other:
                if other not in EdgeDescriptor:
                    raise Exception(f'Invalid edge descriptor "{other}"')
                logging.warning(f'Edge descriptor "{other}" not implemented yet.')
                return False


@dataclass
class LogicalRoom:
    """
    A collection of nodes and edges making up an in-game room.

    Note: every `LogicalRoom` has an implicit one-to-one correspondence with every aux data `Room`.
    """

    area: Area
    name: str
    nodes: list[Node]


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
