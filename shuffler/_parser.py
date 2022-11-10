from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, EnumMeta
import logging
from pathlib import Path
from typing import Any, Literal

import inflection
import pyparsing

from shuffler.aux_models import Area, Check, Door


@dataclass
class Node:
    name: str
    edges: list[Edge]
    checks: list[Check]
    exits: list[Door]
    entrances: set[str]
    flags: set[str]

    @property
    def area(self):
        return self.name.split('.')[0]

    @property
    def room(self):
        return self.name.split('.')[1]

    @property
    def node(self):
        return self.name.split('.')[2]

    # Provide implementations of __eq__ and __hash__ so that Nodes can be added to a `set`
    def __eq__(self, other_node) -> bool:
        return self.name == other_node.name

    def __hash__(self) -> int:
        return hash(repr(self))


class Edge:
    def __init__(self, dest: Node, constraints: str | None = None) -> None:
        self.dest = dest

        # Initialize edge constraint parser
        operand = None
        for element in EdgeDescriptor:
            if operand is None:
                operand = pyparsing.Keyword(element.value)
            else:
                operand |= pyparsing.Keyword(element.value)
        operand += pyparsing.Word(pyparsing.alphanums)  # type: ignore
        parser = pyparsing.infix_notation(
            operand,  # type: ignore
            [
                (pyparsing.Literal('&'), 2, pyparsing.opAssoc.LEFT),
                (pyparsing.Literal('|'), 2, pyparsing.opAssoc.LEFT),
            ],
        )

        logging.debug(f'Evaluating "{constraints}"...')
        # Parse edge constraint string
        self.constraints = parser.parse_string(constraints) if constraints else None

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
                parsed_expr=self.constraints.as_list(),
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

    @classmethod
    def _evaluate_constraint(
        cls, type: str, value: str, inventory: list[str], flags: set[str]
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
    nodes: list[Node] | None


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


class EdgeDescriptor(Enum, metaclass=MetaEnum):
    ITEM = 'item'
    FLAG = 'flag'
    OPEN = 'open'
    DEFEATED = 'defeated'
    SETTING = 'setting'
    STATE = 'state'
    LOSE = 'lose'


def parse_node(
    lines: list[str], node_name: str, room: LogicalRoom
) -> tuple[list[Check], list[Door], set[str], set[str]]:
    checks: list[Check] = []
    exits: list[Door] = []
    entrances: set[str] = set()
    flags: set[str] = set()

    while lines and (lines[0].lstrip().split(' ')[0] in NodeDescriptor):
        line = lines.pop(0).strip().split(' ')
        descriptor_type = line[0]
        descriptor_value = line[1]

        logging.debug(f'      {descriptor_type} {descriptor_value}')
        assert descriptor_type in NodeDescriptor, f'Unknown node descriptor "{descriptor_type}"'

        match descriptor_type:
            case 'chest':
                try:
                    checks.append(
                        [
                            check
                            for r in room.area.rooms
                            for check in r.chests
                            if r.name == room.name
                            if check.name == descriptor_value
                        ][0]
                    )
                except IndexError:
                    raise Exception(
                        f'{descriptor_type} "{descriptor_value}" not found in aux data.'
                    )
            case (
                NodeDescriptor.ENTRANCE.value
                | NodeDescriptor.EXIT.value
                | NodeDescriptor.DOOR.value
            ):
                if descriptor_type in (NodeDescriptor.DOOR.value, NodeDescriptor.ENTRANCE.value):
                    if descriptor_value in entrances:
                        raise Exception(f'entrance "{descriptor_value}" defined more than once')
                    entrances.add(f'{node_name}.{descriptor_value}')
                if descriptor_type in (NodeDescriptor.DOOR.value, NodeDescriptor.EXIT.value):
                    try:
                        new_exit = [
                            door
                            for r in room.area.rooms
                            for door in r.doors
                            if r.name == room.name
                            if door.name == descriptor_value
                        ][0]
                    except IndexError:
                        raise Exception(
                            f'{descriptor_type} "{descriptor_value}" not found in aux data.'
                        )
                    if new_exit.link.count('.') == 2:
                        new_exit.link = f'{room.area.name}.{new_exit.link}'
                    if new_exit.link.count('.') != 3:
                        # TODO: remove once aux data is complete
                        if not len(new_exit.link) or new_exit.link.lower() == 'todo':
                            logging.warning(f'exit "{new_exit.name} has no link.')
                            continue
                        raise Exception(f'Invalid exit link "{new_exit.link}"')
                    exits.append(new_exit)
            case NodeDescriptor.FLAG.value:
                flags.add(descriptor_value)
            case other:
                if other not in NodeDescriptor:
                    raise Exception(f'Unknown node descriptor "{other}"')
                logging.warning(f'Node descriptor "{other}" not implemented yet.')

    return checks, exits, entrances, flags


def parse_edge(
    area_name: str,
    room_name: str,
    line: str,
    edge_direction: Literal['<-', '->'],
    nodes: list[Node],
):
    source_node_name = (
        f"{f'{area_name}.{room_name}'}."
        f"{line.split('<->' if '<->' in line else edge_direction)[0].strip()}"
    )
    dest_node_name = (
        f'{f"{area_name}.{room_name}"}.'
        f"{line.split('<->' if '<->' in line else edge_direction)[1].strip().split(':')[0]}"
    )

    edge_content = None
    if ':' in line:
        edge_content = line.split(':')[1].strip()

    try:
        node1 = [node for node in nodes if node.name == source_node_name][0]
    except IndexError:
        raise Exception(f'ERROR in edge "{line}": node {source_node_name} not found!')
    try:
        node2 = [node for node in nodes if node.name == dest_node_name][0]
    except IndexError:
        raise Exception(f'ERROR in edge "{line}": node {dest_node_name} not found!')

    if edge_direction == '->':
        node1.edges.append(Edge(dest=node2, constraints=edge_content))
    elif edge_direction == '<-':
        node2.edges.append(Edge(dest=node1, constraints=edge_content))
    else:
        raise NotImplementedError(f'Invalid edge direction token "{edge_direction}"')


def parse_room(room: LogicalRoom, lines: list[str]) -> list[Node]:
    nodes: list[Node] = []

    while lines and (
        lines[0].lstrip().startswith('node')
        or '<->' in lines[0].lstrip()
        or '->' in lines[0].lstrip()
    ):
        line = lines.pop(0).strip()
        line_split = line.split(' ')
        match line_split:
            case ['node', _]:
                node_name = f"{room.area.name}.{room.name}.{line_split[1].rstrip(':')}"
                logging.debug(f'    node {node_name.split(".")[-1]}')
                checks, exits, entrances, flags = parse_node(lines, node_name, room)
                nodes.append(
                    Node(
                        # Also make sure to remove last character if its a colon
                        name=node_name,
                        edges=[],
                        checks=checks,
                        exits=exits,
                        entrances=entrances,
                        flags=flags,
                    )
                )
            # Note: special case of a one-liner node (for ex- `node X: item B`)
            case ['node', *_]:
                node_name = f"{room.area.name}.{room.name}.{line_split[1].rstrip(':')}"
                logging.debug(f'    node {node_name.split(".")[-1]}')
                checks, exits, entrances, flags = parse_node(
                    [' '.join(line_split[2:])] + lines, node_name, room
                )
                nodes.append(
                    Node(
                        # Also make sure to remove last character if its a colon
                        name=node_name,
                        edges=[],
                        checks=checks,
                        exits=exits,
                        entrances=entrances,
                        flags=flags,
                    )
                )
            case [node1, '->', node2, *_]:  # noqa: F841
                parse_edge(room.area.name, room.name, line, '->', nodes)
            case [node1, '<->', node2, *_]:  # noqa: F841
                parse_edge(room.area.name, room.name, line, '->', nodes)
                parse_edge(room.area.name, room.name, line, '<-', nodes)
    return nodes


def parse_area(area: Area, lines: list[str]) -> list[LogicalRoom]:
    rooms: list[LogicalRoom] = []
    while lines and (lines[0].lstrip().startswith('room')):
        line = lines.pop(0).strip()
        assert line.split(' ')[0] == 'room'
        assert line.endswith(':')
        room_name = line.split(' ')[1].rstrip(':')
        logging.debug(f'  room {room_name}')
        room = LogicalRoom(area=area, name=room_name, nodes=[])
        rooms.append(room)
        nodes = parse_room(room, lines)
        room.nodes = nodes
    return rooms


def parse_logic_file(lines: list[str], aux_data: list[Area]) -> list[LogicalRoom]:
    rooms: list[LogicalRoom] = []
    while lines and (lines[0].lstrip().startswith('area')):
        line = lines.pop(0)
        assert line.startswith('area')
        assert line.endswith(':')
        area_name = line.split(' ')[1].rstrip(':')
        logging.debug(f'area {area_name}')
        all_areas = [area for area in aux_data if area.name == area_name]
        if not len(all_areas):
            logging.warning(f'Aux data JSON for area "{area_name}" not found')
            continue
        current_area = all_areas[0]
        rooms += parse_area(current_area, lines)

    return rooms


def parse(logic_directory: Path, aux_data: list[Area]) -> list[LogicalRoom]:
    rooms: list[LogicalRoom] = []
    for file in logic_directory.rglob('*.logic'):
        if 'Mercay.logic' not in str(file):
            continue
        if file.stem not in [area.name for area in aux_data]:
            logging.warning(f'No aux data found for {file.name}')
            continue
        lines: list[str] = []
        with open(file) as fd:
            for line in fd.readlines():
                line = line.strip()  # strip off leading and trailing whitespace
                if '#' in line:
                    line = line[: line.index('#')]  # remove any comments
                if line:
                    lines.append(line)
        rooms += parse_logic_file(lines, aux_data)

    return rooms
