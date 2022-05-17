from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path
from typing import Literal


@dataclass
class NodeContents:
    type: str
    data: str


@dataclass
class Node:
    name: str
    contents: list[NodeContents]

    @property
    def area(self):
        return self.name.split(".")[0]

    @property
    def room(self):
        return self.name.split(".")[1]

    @property
    def node(self):
        return self.name.split(".")[2]


@dataclass
class Edge:
    source: Node
    dest: Node
    constraints: str | None  # TODO: parse this. For now, just store it as a string


@dataclass
class Room:
    name: str
    nodes: list[Node]
    edges: list[Edge]


@dataclass
class Area:
    rooms: list[Room]


nodes: list[Node] = []
edges: dict[str, list[Edge]] = defaultdict(list)  # Maps node names to edges


class Descriptor(Enum):
    CHEST = "chest"
    DOOR = "door"
    ENTRANCE = "entrance"
    EXIT = "exit"
    MAIL = "mail"
    HINT = "hint"
    ENEMY = "enemy"
    LOCK = "lock"


VALID_DESCRIPTORS = [element.value for element in Descriptor]


def parse_node(lines: list[str]) -> list[NodeContents]:
    node_contents: list[NodeContents] = []
    while lines and (lines[0].lstrip().split(" ")[0] in VALID_DESCRIPTORS):
        line = lines.pop(0).strip().split(" ")
        node_type = line[0]
        node_contents.append(NodeContents(type=node_type, data=" ".join(line[1:])))
        logging.debug(f"      {node_contents[-1].type} {node_contents[-1].data}")
    return node_contents


def parse_edge(node_prefix: str, line: str, edge_direction: Literal["<-", "->"]):
    source_node_name = (
        f"{node_prefix}.{line.split('<->' if '<->' in line else edge_direction)[0].strip()}"
    )
    dest_node_name = f"{node_prefix}.{line.split('<->' if '<->' in line else edge_direction)[1].strip().split(':')[0]}"

    edge_content = None
    if ":" in line:
        edge_content = line.split(":")[1].strip()

    node1 = [node for node in nodes if node.name == source_node_name][0]
    node2 = [node for node in nodes if node.name == dest_node_name][0]
    if edge_direction == "->":
        edges[node1.name].append(Edge(source=node1, dest=node2, constraints=edge_content))
    elif edge_direction == "<-":
        edges[node2.name].append(Edge(source=node2, dest=node1, constraints=edge_content))
    else:
        raise NotImplementedError(f'Invalid edge direction token "{edge_direction}"')


def parse_room_contents(node_prefix: str, lines: list[str]):
    while lines and (
        lines[0].lstrip().startswith("node")
        or "<->" in lines[0].lstrip()
        or "<-" in lines[0].lstrip()
        or "->" in lines[0].lstrip()
    ):
        line = lines.pop(0).strip()
        line_split = line.split(" ")
        match line_split:
            case ["node", _]:
                logging.debug(f"    node {line_split[1]}")
                nodes.append(
                    Node(
                        # Also make sure to remove last character if its a colon
                        name=f"{node_prefix}.{line_split[1].rstrip(':')}",
                        contents=parse_node(lines),
                    )
                )
            # Note: special case of a one-liner node (for ex- `node X: item B`)
            case ["node", *_]:
                logging.debug(f"    node {line_split[1]}")
                nodes.append(
                    Node(
                        # Also make sure to remove last character if its a colon
                        name=f"{node_prefix}.{line_split[1].rstrip(':')}",
                        contents=parse_node([" ".join(line_split[2:])] + lines),
                    )
                )
            case [node1, "->", node2, *_]:  # noqa: F841
                parse_edge(node_prefix, line, "->")
            case [node1, "<-", node2, *_]:  # noqa: F841
                parse_edge(node_prefix, line, "<-")
            case [node1, "<->", node2, *_]:  # noqa: F841
                parse_edge(node_prefix, line, "->")
                parse_edge(node_prefix, line, "<-")


def parse_rooms(node_prefix: str, lines: list[str]):
    while lines and (lines[0].lstrip().startswith("room")):
        line = lines.pop(0).strip()
        assert line.split(" ")[0] == "room"
        room_name = line.split(" ")[1].rstrip(":")
        logging.debug(f"  room {room_name}")
        parse_room_contents(f"{node_prefix}.{room_name}", lines)


def parse_area(lines: list[str]):
    while lines and (lines[0].lstrip().startswith("area")):
        line = lines.pop(0)
        assert line.startswith("area")
        area_name = line.split(" ")[1].rstrip(":")
        logging.debug(f"area {area_name}")
        parse_rooms(area_name, lines)


def parse():
    # logic_files = list(Path(__file__).parent.rglob("*.logic"))
    # TODO: Limit to just Mercay for now
    logic_files = [Path(__file__).parent / "logic" / "SW Sea" / "Mercay Island" / "Mercay.logic"]

    for file in logic_files:
        with open(file, "r") as fd:
            lines = [line.strip() for line in fd.readlines() if line and line.strip()]
        parse_area(lines)

    return nodes, edges
