from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path
from typing import Any, Literal

import inflection
import pyparsing


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
    constraints: str | None

    def is_traversable(self, current_inventory: list[str]) -> bool:
        if self.constraints:
            parsed = edge_parser.parse_string(self.constraints)
            return edge_is_tranversable(parsed.as_list(), current_inventory)
        return True


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

# Python type for edge values.
# TODO: ideally we use the first, commented out option, but it doesn't work due to the lack
# of recursive type support in mypy (ref: https://github.com/python/mypy/issues/731).
# If recursive types are ever supported, this should be updated accordingly.
# EdgeExpression = list[str | 'EdgeExpression']
EdgeExpression = list[str | Any]

# pyparsing parser for parsing edges in .logic files:
operand: pyparsing.ParserElement = (
    pyparsing.Keyword("item") | pyparsing.Keyword("flag")
) + pyparsing.Word(pyparsing.alphas)
edge_parser: pyparsing.ParserElement = pyparsing.infix_notation(
    operand,
    [
        (pyparsing.Literal("&"), 2, pyparsing.opAssoc.LEFT),
        (pyparsing.Literal("|"), 2, pyparsing.opAssoc.LEFT),
    ],
)


def _evaluate_constraint(type: str, value: str, inventory: list[str]) -> bool:
    """
    Given an edge constraint "type value", determines if the edge is traversable
    given the current game state (inventory, set flags, etc).

    Params:
        type: The type of edge constraint, e.g. "item", "flag", etc.

        value: The value of the edge constraint, e.g. "Bombs", "BridgeRepaired", etc.

        inventory: A list of strings representing the "current inventory", i.e. all items currently
        accessible given the current shuffled state.
    """
    match type:
        case "item":
            return value in inventory
        case "flag":
            raise NotImplementedError("Edges with type 'flag' are not implemented yet.")
        case other:
            raise Exception(f'Invalid edge type "{other}"')


def edge_is_tranversable(parsed_expr: EdgeExpression, inventory: list[str], result=True) -> bool:
    """
    Determine if the given edge expression is traversable.

    Params:
        parsed_expr: Expression to evaluate. The expression must be a nested list of strings
        representing a valid pyparsing expression generated from the `edge_parser` parser.
        The easiest way to do this is to call .as_list() on the `ParseResults` object
        returned by pyparsing.

        inventory: A list of strings representing the "current inventory", i.e. all items currently
        accessible given the current shuffled state.

        result: The current boolean "state" of the expression, i.e. whether it is True or False.
        It's used internally as part of the recursion, but shouldn't need to be set when calling
        this function externally.
    """
    current_op = None  # variable to track current logical operation (AND or OR), if applicable

    while len(parsed_expr):
        # If the complex expression contains another complex expression, recursively evaluate it
        if isinstance(parsed_expr[0], list):
            # TODO: remove 'type: ignore' comment below. see prev note about `EdgeExpression` type.
            sub_expression: EdgeExpression = parsed_expr.pop(0)  # type: ignore
            current_result = edge_is_tranversable(sub_expression, inventory, result)
        else:
            # Extract type and value (e.g., 'item' and 'Bombs')
            expr_type = parsed_expr.pop(0)
            # Convert items in PascalCase or camelCase to snake_case.
            # The logic format is flexible and supports either of the three formats,
            # so the shuffler needs to normalize everything to snake_case at runtime.
            expr_value = inflection.underscore(parsed_expr.pop(0))

            current_result = _evaluate_constraint(expr_type, expr_value, inventory)

        # Apply any pending logical operations
        if current_op == "&":
            result &= current_result
        elif current_op == "|":
            result |= current_result
        else:
            result = current_result

        # Queue up a logical AND or OR for the next expression if needed
        if len(parsed_expr) and parsed_expr[0] in ("&", "|"):
            current_op = parsed_expr.pop(0)

    return result


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
    return nodes


def clear_nodes():
    nodes.clear()


def parse(directory: Path):
    logic_files = list(directory.rglob("*.logic"))

    for file in logic_files:
        lines: list[str] = []
        with open(file, "r") as fd:
            for line in fd.readlines():
                line = line.strip()  # strip off leading and trailing whitespace
                if "#" in line:
                    line = line[: line.index("#")]  # remove any comments
                if line:
                    lines.append(line)
        parse_area(lines)

    return nodes, edges
