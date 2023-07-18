from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from functools import cache, cached_property
import json
import logging
from pathlib import Path
import re
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel
import pyparsing as pp

from ph_rando.common import ShufflerAuxData
from ph_rando.patcher._items import ITEMS
from ph_rando.shuffler._descriptors import EdgeDescriptor, NodeDescriptor
from ph_rando.shuffler.aux_models import Area, Check, Enemy, Exit, Room

if TYPE_CHECKING:
    from pyparsing import ParserElement

logger = logging.getLogger(__name__)

# Name of node that represents the singleton "Mailbox" object.
# In format <area>.<room>.<node_name>
# TODO: make this a configurable setting in shuffler
MAILBOX_NODE_NAME = 'Mail.Mail.Mail'


@dataclass
class Node:
    name: str
    area: Area
    room: Room
    checks: list[Check] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    exits: list[Exit] = field(default_factory=list)
    entrances: set[str] = field(default_factory=set)
    enemies: list[Enemy] = field(default_factory=list)
    flags: set[str] = field(default_factory=set)
    lock: str = field(default_factory=str)
    states_gained: set[str] = field(default_factory=set)
    states_lost: set[str] = field(default_factory=set)
    mailbox: bool = False

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Node):
            return __o.name == self.name
        raise Exception('Invalid comparison')


@dataclass
class Edge:
    src: Node
    dest: Node
    requirements: list[str | list[str | list]] | None

    def __repr__(self) -> str:
        return f'{self.src.name} -> {self.dest.name}'

    def is_traversable(
        self,
        items: list[str],
        flags: set[str],
        states: set[str],
        aux_data: ShufflerAuxData,
    ) -> bool:
        """
        Determine if this edge is traversable given the current player state.

        Params:
            items: A list of strings representing the "current inventory", i.e. all
                               items currently accessible given the current shuffled state.
            flags: A set of strings containing all `flags` that are logically set.

        """
        if self.requirements is not None and len(self.requirements):
            return requirements_met(
                parsed_expr=self.requirements,
                items=items,
                flags=flags,
                states=states,
                aux_data=aux_data,
                edge_instance=self,
            )
        return True

    @cached_property
    def locked_door(self) -> str | None:
        """
        Returns the name of the locked door this edge is associated with, if any.
        """

        def _contains_open(constraints: list[str | list[str | list]]) -> str | None:
            contains_open = None
            for elem in constraints:
                if isinstance(elem, list):
                    contains_open = _contains_open(elem)
                elif EdgeDescriptor.OPEN.value == elem:
                    lock_name = constraints[constraints.index(elem) + 1]
                    assert isinstance(lock_name, str)
                    return '.'.join([self.src.area.name, self.src.room.name, lock_name])
            return contains_open

        return _contains_open(self.requirements) if self.requirements else None

    @classmethod
    @cache
    def get_edge_parser(cls) -> ParserElement:
        """
        Return a `pyparsing.ParserElement` parser that parses edge requirements into
        a usable format.

        Creating this object is relatively expensive, so we cache it to ensure that
        it's only created once.
        """
        edge_item = None
        for edge_descriptor in EdgeDescriptor:
            if edge_item is None:
                edge_item = pp.Keyword(edge_descriptor.value)
            else:
                edge_item |= pp.Keyword(edge_descriptor.value)
        edge_item += pp.Word(pp.alphanums + '[]')  # type: ignore
        return pp.infix_notation(
            edge_item,  # type: ignore
            [
                (pp.Literal('&'), 2, pp.opAssoc.LEFT),
                (pp.Literal('|'), 2, pp.opAssoc.LEFT),
            ],
        )


def requirements_met(
    parsed_expr: list[str | list[str | list]],
    items: list[str],
    flags: set[str],
    states: set[str],
    aux_data: ShufflerAuxData,
    edge_instance: Edge | None = None,
    result: bool = True,
) -> bool:
    current_op = None  # variable to track current logical operation (AND or OR), if applicable
    while len(parsed_expr):
        # If the complex expression contains another complex expression, recursively evaluate it
        if isinstance(parsed_expr[0], list):
            sub_expression = parsed_expr[0]
            parsed_expr = parsed_expr[1:]
            assert isinstance(sub_expression, list)
            current_result = requirements_met(
                sub_expression,
                items,
                flags,
                states,
                aux_data,
                edge_instance,
                result,
            )
        else:
            # Extract type and value (e.g., 'item' and 'Bombs')
            expr_type = parsed_expr[0]
            assert isinstance(expr_type, str)
            expr_value = parsed_expr[1]
            assert isinstance(expr_value, str)

            parsed_expr = parsed_expr[2:]

            current_result = evaluate_requirement(
                type=expr_type,
                value=expr_value,
                items=items,
                flags=flags,
                states=states,
                aux_data=aux_data,
                edge_instance=edge_instance,
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


def evaluate_requirement(
    type: str,
    value: str,
    items: list[str],
    flags: set[str],
    states: set[str],
    aux_data: ShufflerAuxData,
    edge_instance: Edge | None = None,
) -> bool:
    """
    Given a single edge requirement in the form "type value", determines if the edge is traversable
    given the current game state (items, set flags, etc).

    Params:
        type: The type of edge requirement, e.g. "item", "flag", etc.

        value: The value of the edge requirement, e.g. "Bombs", "BridgeRepaired", etc.

        items: A list of strings representing the "current inventory", i.e. all
        items currently accessible given the current shuffled state.
    """
    match type:
        case EdgeDescriptor.ITEM.value:
            # If a certain number of this item is required, check that.
            # Otherwise, just check if we have one of this item.
            count_descriptor = re.match(r'(.+)\[(\d+)\]', value)
            if count_descriptor is not None:
                item_name, item_count = count_descriptor.groups()
                assert (
                    item_count.isdigit()
                ), f'Invalid requirement {value}, brackets must contain a valid number.'
                return items.count(item_name) >= int(item_count)
            elif value not in ITEMS:
                raise Exception(f'Invalid item "{value}"')
            else:
                return value in items
        case EdgeDescriptor.FLAG.value:
            return flags is not None and value in flags
        case EdgeDescriptor.STATE.value:
            return value in states
        case EdgeDescriptor.DEFEATED.value:
            if edge_instance is None:
                raise Exception(
                    "Can't evaluate requirement of type 'defeated' with 'edge_instance' of None!!"
                )
            for enemy in edge_instance.src.room.enemies:
                if enemy.name != value:
                    continue
                elif enemy.type not in aux_data.enemy_requirements:
                    raise Exception(f'{edge_instance.src.name}: invalid enemy type {enemy.type!r}')
                return requirements_met(
                    parse_edge_requirement(aux_data.enemy_requirements[enemy.type]),
                    items,
                    flags,
                    states,
                    aux_data,
                    edge_instance,
                )
            raise Exception(
                f'{edge_instance.src.name} (Edge "...{type} {value}..."): '
                f'enemy {value} not found!'
            )
        case EdgeDescriptor.MACRO.value:
            if value not in aux_data.requirement_macros:
                raise Exception(f'Invalid macro "{value}", not found in macros.json!')
            return requirements_met(
                parse_edge_requirement(aux_data.requirement_macros[value]),
                items,
                flags,
                states,
                aux_data,
                edge_instance,
            )
        case other:
            if other not in EdgeDescriptor:
                raise Exception(f'Invalid edge descriptor {other!r}')
            logger.debug(f'Edge descriptor {other!r} not implemented yet.')
            return True


@cache
def parse_edge_requirement(requirement: str) -> list[str | list[str | list]]:
    """
    Parse an edge requirement into a recursive list of strings for further processing
    by the Edge._evaluate_requirement() method.
    """
    parser = Edge.get_edge_parser()
    return parser.parse_string(requirement).as_list()  # type: ignore


# Helper classes for parsing dict outputted by pyparsing.
class _LogicEdge(BaseModel):
    source_node: str
    destination_node: str
    direction: Literal['->', '<->']
    requirements: str | None


class _LogicNodeDescriptor(BaseModel):
    type: str
    value: str


class _LogicNode(BaseModel):
    name: str
    descriptors: list[_LogicNodeDescriptor] | None


class _LogicRoom(BaseModel):
    name: str
    nodes_and_edges: list[_LogicNode | _LogicEdge]

    @property
    def nodes(self) -> list[_LogicNode]:
        return [n for n in self.nodes_and_edges if isinstance(n, _LogicNode)]

    @property
    def edges(self) -> list[_LogicEdge]:
        return [e for e in self.nodes_and_edges if isinstance(e, _LogicEdge)]


class _LogicArea(BaseModel):
    name: str
    rooms: list[_LogicRoom]


class _ParsedLogic(BaseModel):
    areas: list[_LogicArea]


def _parse_logic_file(logic_file_contents: str) -> _ParsedLogic:
    from ph_rando.shuffler._descriptors import NodeDescriptor

    edge_parser = (
        pp.Word(pp.alphanums)('source_node')
        + pp.one_of(['->', '<->'])('direction')
        + pp.Word(pp.alphanums)('destination_node')
        + pp.Optional(pp.Literal(':').suppress() + pp.SkipTo(pp.LineEnd())('requirements'))
    )

    node_item = None
    for node_descriptor in NodeDescriptor:
        if node_item is None:
            node_item = pp.Keyword(node_descriptor.value)
        else:
            node_item |= pp.Keyword(node_descriptor.value)
    node_element = node_item('type') + pp.Word(pp.alphanums)('value')  # type: ignore

    node_parser = (
        pp.Literal('node').suppress()
        + pp.Word(pp.alphanums)('name')
        + pp.Optional(
            pp.Literal(':').suppress() + pp.OneOrMore(pp.Group(node_element))('descriptors')
        )
    )

    room_parser = (
        pp.Literal('room').suppress()
        + pp.Word(pp.alphanums)('name')
        + pp.Literal(':').suppress()
        + pp.OneOrMore(pp.Group(node_parser | edge_parser))('nodes_and_edges')
    )

    area_parser = (
        pp.Literal('area').suppress()
        + pp.Word(pp.alphanums)('name')
        + pp.Literal(':').suppress()
        + pp.OneOrMore(pp.Group(room_parser))('rooms')
    )

    logic_parser = pp.OneOrMore(pp.Group(area_parser))('areas')

    parsed = logic_parser.parse_string(logic_file_contents).as_dict()

    return _ParsedLogic(**parsed)


def annotate_logic(areas: Iterable[Area], logic_directory: Path | None = None) -> None:
    """
    Parse .logic files and annotate the given aux data with them.

    First, the `parse_logic` function parses the .logic files into an intermediate
    `ParsedLogic` object. Then, it annotates the list of aux `Rooms` with the nodes
    from `ParsedLogic`.
    """
    from ph_rando.shuffler._shuffler import Edge, Node

    if logic_directory is None:
        logic_directory = Path(__file__).parent / 'logic'

    for file in logic_directory.rglob('*.logic'):
        lines: list[str] = []

        for line in file.read_text().splitlines():
            line = line.strip()  # strip off leading and trailing whitespace
            if '#' in line:
                line = line[: line.index('#')]  # remove any comments
            if line:
                lines.append(line)

        file_contents = '\n'.join(lines)

        parsed_logic = _parse_logic_file(file_contents)

        for logic_area in parsed_logic.areas:
            _areas = [area for area in areas if area.name == logic_area.name]
            assert len(_areas), f'Area {logic_area.name} not found!'
            assert len(_areas) == 1, f'Multiple areas with name "{logic_area.name}" found!'
            area = _areas[0]
            for logic_room in logic_area.rooms:
                room = [room for room in area.rooms if room.name == logic_room.name][0]
                for logic_node in logic_room.nodes:
                    full_node_name = '.'.join([logic_area.name, logic_room.name, logic_node.name])
                    node = Node(name=full_node_name, area=area, room=room)
                    for descriptor in logic_node.descriptors or []:
                        match descriptor.type:
                            case NodeDescriptor.CHEST.value:
                                try:
                                    node.checks.append(
                                        [
                                            check
                                            for check in room.chests
                                            if check.name == descriptor.value
                                        ][0]
                                    )
                                except IndexError:
                                    raise Exception(
                                        f'{node.area.name}.{room.name}: '
                                        f'{descriptor.type} {descriptor.value!r} '
                                        'not found in aux data.'
                                    )
                            case (
                                NodeDescriptor.ENTRANCE.value
                                | NodeDescriptor.EXIT.value
                                | NodeDescriptor.DOOR.value
                            ):
                                if descriptor.type in (
                                    NodeDescriptor.DOOR.value,
                                    NodeDescriptor.ENTRANCE.value,
                                ):
                                    if descriptor.value in node.entrances:
                                        raise Exception(
                                            f'{node.area.name}.{node.room.name}: '
                                            f'entrance {descriptor.value!r} defined more than once'
                                        )
                                    node.entrances.add(f'{node.name}.{descriptor.value}')
                                if descriptor.type in (
                                    NodeDescriptor.DOOR.value,
                                    NodeDescriptor.EXIT.value,
                                ):
                                    try:
                                        new_exit = [
                                            exit
                                            for exit in room.exits
                                            if exit.name == descriptor.value
                                        ][0]
                                    except IndexError:
                                        raise Exception(
                                            f'{node.area.name}.{node.room.name}: '
                                            f'{descriptor.type} {descriptor.value!r} '
                                            'not found in aux data.'
                                        )
                                    if new_exit.entrance.count('.') == 2:
                                        new_exit.entrance = f'{node.area.name}.{new_exit.entrance}'
                                    if new_exit.entrance.count('.') != 3:
                                        raise Exception(
                                            f'{node.area.name}.{room.name}: '
                                            f'Invalid exit link {new_exit.entrance!r}'
                                        )
                                    node.exits.append(new_exit)
                            case NodeDescriptor.FLAG.value:
                                node.flags.add(descriptor.value)
                            case NodeDescriptor.LOCK.value:
                                assert (
                                    not node.lock
                                ), f'Node {node} already has a locked door associated with it.'
                                node.lock = descriptor.value
                            case NodeDescriptor.ENEMY.value:
                                try:
                                    node.enemies.append(
                                        [
                                            enemy
                                            for enemy in room.enemies
                                            if enemy.name == descriptor.value
                                        ][0]
                                    )
                                except IndexError:
                                    raise Exception(
                                        f'{node.area.name}.{room.name}: '
                                        f'{descriptor.type} {descriptor.value!r} '
                                        'not found in aux data.'
                                    )
                            case NodeDescriptor.MAIL.value:
                                if node.mailbox:
                                    raise Exception(
                                        f'Node "{node.name}" contains more than one mailbox!'
                                    )
                                node.mailbox = True
                            case NodeDescriptor.GAIN.value:
                                node.states_gained.add(descriptor.value)
                            case NodeDescriptor.LOSE.value:
                                node.states_lost.add(descriptor.value)
                            case other:
                                if other not in NodeDescriptor:
                                    raise Exception(
                                        f'{node.area.name}.{room.name}: Unknown '
                                        f'node descriptor {other!r}'
                                    )
                                logger.warning(f'Node descriptor {other!r} not implemented yet.')
                    room.nodes.append(node)
                for edge in logic_room.edges:
                    for node1 in room.nodes:
                        if node1.name.split('.')[2] == edge.source_node:
                            for node2 in room.nodes:
                                if node2.name.split('.')[2] == edge.destination_node:
                                    node1.edges.append(
                                        Edge(
                                            src=node1,
                                            dest=node2,
                                            requirements=parse_edge_requirement(edge.requirements)
                                            if edge.requirements
                                            else None,
                                        )
                                    )
                                    if edge.direction == '<->':
                                        node2.edges.append(
                                            Edge(
                                                src=node2,
                                                dest=node1,
                                                requirements=parse_edge_requirement(
                                                    edge.requirements
                                                )
                                                if edge.requirements
                                                else None,
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


def connect_rooms(areas: dict[str, Area]) -> None:
    """
    Replaces `entrance`/`exit`/`door` node descriptors with actual edges.

    Any entrance randomization should take place *before* this
    function is called.
    """

    def _get_dest_node(dest_node_entrance: str) -> Node:
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


def connect_mail_nodes(areas: Iterable[Area], mail_node_name: str = MAILBOX_NODE_NAME) -> None:
    """Connect all nodes with a `mail` descriptor to the "Mail" node."""
    mailbox_node: Node | None = None

    # Find mailbox_node
    found = False
    for area in areas:
        if found:
            break
        for room in area.rooms:
            if found:
                break
            for node in room.nodes:
                if found:
                    break
                if node.name == mail_node_name:
                    mailbox_node = node
                    found = True

    if not found:
        raise Exception(f'Mailbox node "{mail_node_name}" not found!')

    assert mailbox_node is not None  # for type-checker

    # Add edge between the mailbox node and each node that has a `mail` descriptor
    for area in areas:
        for room in area.rooms:
            for node in room.nodes:
                if node.mailbox:
                    node.edges.append(Edge(src=node, dest=mailbox_node, requirements=None))


def parse_aux_data(
    areas_directory: Path | None = None,
    enemy_mapping_file: Path | None = None,
    macros_file: Path | None = None,
) -> ShufflerAuxData:
    if areas_directory is None:
        areas_directory = Path(__file__).parent / 'logic'
    if enemy_mapping_file is None:
        enemy_mapping_file = Path(__file__).parent / 'enemies.json'
    if macros_file is None:
        macros_file = Path(__file__).parent / 'macros.json'

    areas: dict[str, Area] = {}
    for file in areas_directory.rglob('*.json'):
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

    enemy_mapping = json.loads(enemy_mapping_file.read_text())
    macros = json.loads(macros_file.read_text())

    return ShufflerAuxData(
        areas=areas,
        enemy_requirements=enemy_mapping,
        requirement_macros=macros,
    )
