from typing import Literal

from pydantic import BaseModel
import pyparsing as pp


class LogicEdge(BaseModel):
    source_node: str
    destination_node: str
    direction: Literal['->'] | Literal['<->']
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
    from shuffler.logic import EdgeDescriptor

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


def parse_logic(logic_file_contents: str) -> ParsedLogic:
    from shuffler.logic import NodeDescriptor

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
