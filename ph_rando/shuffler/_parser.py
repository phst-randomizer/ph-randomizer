from collections.abc import Iterable
import json
import logging
from pathlib import Path
from typing import Literal

from pydantic import BaseModel
import pyparsing as pp

from ph_rando.shuffler.aux_models import Area


class LogicEdge(BaseModel):
    source_node: str
    destination_node: str
    direction: Literal['->', '<->']
    constraints: str | None


class LogicNodeDescriptor(BaseModel):
    type: str
    value: str


class LogicNode(BaseModel):
    name: str
    descriptors: list[LogicNodeDescriptor] | None


class LogicRoom(BaseModel):
    name: str
    nodes_and_edges: list[LogicNode | LogicEdge]

    @property
    def nodes(self):
        return [n for n in self.nodes_and_edges if isinstance(n, LogicNode)]

    @property
    def edges(self):
        return [e for e in self.nodes_and_edges if isinstance(e, LogicEdge)]


class LogicArea(BaseModel):
    name: str
    rooms: list[LogicRoom]


class ParsedLogic(BaseModel):
    areas: list[LogicArea]


def parse_edge_constraint(constraint: str) -> list[str | list[str | list]]:
    from ph_rando.shuffler._descriptors import EdgeDescriptor

    edge_item = None
    for edge_descriptor in EdgeDescriptor:
        if edge_item is None:
            edge_item = pp.Keyword(edge_descriptor.value)
        else:
            edge_item |= pp.Keyword(edge_descriptor.value)
    edge_item += pp.Word(pp.alphanums)  # type: ignore
    edge_constraint = pp.infix_notation(
        edge_item,  # type: ignore
        [
            (pp.Literal('&'), 2, pp.opAssoc.LEFT),
            (pp.Literal('|'), 2, pp.opAssoc.LEFT),
        ],
    )
    return edge_constraint.parse_string(constraint).as_list()  # type: ignore


def _parse_logic_file(logic_file_contents: str) -> ParsedLogic:
    from ph_rando.shuffler._descriptors import NodeDescriptor

    edge_parser = (
        pp.Word(pp.alphanums)('source_node')
        + pp.one_of(['->', '<->'])('direction')
        + pp.Word(pp.alphanums)('destination_node')
        + pp.Optional(pp.Literal(':').suppress() + pp.SkipTo(pp.LineEnd())('constraints'))
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

    return ParsedLogic(**parsed)


def annotate_logic(aux_data: Iterable[Area], logic_directory: Path) -> None:
    """
    Parse .logic files and annotate the given aux data with them.

    First, the `parse_logic` function parses the .logic files into an intermediate
    `ParsedLogic` object. Then, it annotates the list of aux `Rooms` with the nodes
    from `ParsedLogic`.
    """

    from ph_rando.shuffler._descriptors import NodeDescriptor
    from ph_rando.shuffler.logic import Edge, Node

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
            area = [area for area in aux_data if area.name == logic_area.name][0]
            if not area:  # TODO: remove when logic/aux is complete
                continue
            for logic_room in logic_area.rooms:
                room = [room for room in area.rooms if room.name == logic_room.name][0]
                if not room:  # TODO: remove when logic/aux is complete
                    continue
                for logic_node in logic_room.nodes:
                    full_node_name = '.'.join([logic_area.name, logic_room.name, logic_node.name])
                    node = Node(full_node_name)
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
                                        f'{node.area}.{room.name}: '
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
                                            f'{node.area}.{node.room}: '
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
                                            f'{node.area}.{node.room}: '
                                            f'{descriptor.type} {descriptor.value!r} '
                                            'not found in aux data.'
                                        )
                                    if new_exit.entrance.count('.') == 2:
                                        new_exit.entrance = f'{node.area}.{new_exit.entrance}'
                                    if new_exit.entrance.count('.') != 3:
                                        raise Exception(
                                            f'{node.area}.{room.name}: '
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
                                        f'{node.area}.{room.name}: '
                                        f'{descriptor.type} {descriptor.value!r} '
                                        'not found in aux data.'
                                    )
                            case other:
                                if other not in NodeDescriptor:
                                    raise Exception(
                                        f'{node.area}.{room.name}: Unknown '
                                        f'node descriptor {other!r}'
                                    )
                                logging.warning(f'Node descriptor {other!r} not implemented yet.')
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
                                            areas=aux_data,
                                            constraints=edge.constraints,
                                        )
                                    )
                                    if edge.direction == '<->':
                                        node2.edges.append(
                                            Edge(
                                                src=node2,
                                                dest=node1,
                                                areas=aux_data,
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


def parse_aux_data(aux_data_directory: Path | None = None) -> dict[str, Area]:
    if aux_data_directory is None:
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
