import json
import logging
from parser import Descriptor, Edge, Node, parse
from pathlib import Path
from random import randint
import sys
from typing import Any

import click

logging.basicConfig(level=logging.INFO)

END_NODE = "Mercay.AboveMercayTown.Island"  # Name of node that player must reach to beat the game

# Global variables
nodes: list[Node]  # List of nodes that make up the world graph
edges: dict[str, list[Edge]]  # List of edges that connect nodes. Maps node names to edges.
inventory: list[str]


def load_aux_data(directory: Path):
    # Find all aux data files in the given directory
    aux_files = list(directory.rglob("*.json"))

    areas: list[dict] = []
    for file in aux_files:
        with open(file, "r") as fd:
            areas.append(json.load(fd))
    return areas


def randomize_aux_data(aux_data_directory: Path):
    """
    Return aux data for the logic with the item locations randomized.

    Note: the item locations are *not* guaranteed (and are unlikely) to be logic-compliant.
    This function just performs a "dumb" shuffle and returns the results.

    Params:
        aux_data_directory: Directory that contains the initial aux data
    """
    areas = load_aux_data(aux_data_directory)

    # List of every item in the game
    chest_items: list[str] = []

    # Record all items in the game
    for area in areas:
        for room in area["rooms"]:
            if "chests" in room:
                for chest in room["chests"]:
                    chest_items.append(chest["contents"])

    # Randomize the items
    for area in areas:
        for room in area["rooms"]:
            if "chests" in room:
                for chest in room["chests"]:
                    chest["contents"] = chest_items.pop(randint(0, len(chest_items) - 1))
    return areas


def edge_is_traversable(edge: Edge):
    """Determine if this edge is traversable given the current state of the game."""
    # TODO: implement this
    match edge.constraints:
        case "item Sword":
            return "oshus_sword" in inventory
        case "(item Bombs | item Bombchus)":
            return "bombs" in inventory or "bombchus" in inventory
        case "item Bow":
            return "bow" in inventory
        case "item Boomerang":
            return "boomerang" in inventory
        case "flag BridgeRepaired":
            return True  # TODO: for now, assume bridge is always repaired
    return False


def get_chest_contents(
    area_name: str, room_name: str, chest_name: str, aux_data: list[dict[Any, Any]]
) -> str:
    for area in aux_data:
        if area_name == area["name"]:
            for room in area["rooms"]:
                if room_name == room["name"]:
                    for chest in room["chests"]:
                        if chest["name"] == chest_name:
                            return chest["contents"]
    raise Exception(f"{chest_name} not found in the given aux data.")


def traverse_graph(
    node: Node, aux_data: list[dict[Any, Any]], visited_rooms: set[str], visited_nodes: set[str]
):
    """
    Traverse the graph (i.e. the nodes and edges) of the current room, starting at `node`.

    Params:
        `node`: The node to start the traversal at
        `area_aux_data`: The aux data for the current area.
        `visited_rooms`: Rooms that have been visited already in this traversal.
        `visited_nodes`: Same as `visited_rooms`, but for nodes.

    Returns:
        `True` if the `END_NODE` was reached, `False` otherwise.
    """
    global nodes, edges, inventory
    logging.debug(node.name)

    if node.name == END_NODE:
        return True

    doors_to_enter: list[str] = []

    # For the current node, find all chests + "collect" their items and note every door so
    # we can go through them later
    for node_info in node.contents:
        if node_info.type == Descriptor.CHEST.value:
            item = get_chest_contents(node.area, node.room, node_info.data, aux_data)
            if item not in inventory:
                inventory.append(item)
                # Reset visited nodes and rooms because we may now be able to reach
                # nodes we couldn't before with this new item
                visited_nodes.clear()
                visited_rooms.clear()
    for node_info in node.contents:
        if node_info.type in (
            Descriptor.DOOR.value,
            Descriptor.ENTRANCE.value,
            Descriptor.EXIT.value,
        ):
            full_room_name = node_info.data
            # Get "path" to node, including Area and Room, if they're not included
            if len(full_room_name.split(".")) == 2:
                full_room_name = f"{node.area}.{full_room_name}"
            elif len(full_room_name.split(".")) == 1:
                full_room_name = f"{node.area}.{node.room}.{full_room_name}"

            if full_room_name not in visited_rooms:
                doors_to_enter.append(full_room_name)
                visited_rooms.add(full_room_name)

    visited_nodes.add(node.name)  # Acknowledge this node as "visited"

    # Check which edges are traversable and do so if they are
    for edge in edges[node.name]:
        if edge.dest.name in visited_nodes:
            continue
        if edge_is_traversable(edge):
            logging.debug(f"{edge.source.name} -> {edge.dest.name}")
            if traverse_graph(edge.dest, aux_data, visited_rooms, visited_nodes):
                return True

    # Go through each door and traverse each of their room graphs
    for door_name in doors_to_enter:
        area_name = door_name.split(".")[0]
        room_name = door_name.split(".")[1]
        door_name = door_name.split(".")[2]
        for area in aux_data:
            if area_name == area["name"]:
                for room in area["rooms"]:
                    if room_name == room["name"]:
                        for door in room["doors"]:
                            if door_name == door["name"]:
                                for other_node in nodes:
                                    link: str = door["link"]

                                    # TODO: remove this if statement once aux data is complete
                                    if "todo" in link.lower():
                                        continue

                                    # Append current area if the linked node doesn't have one specified
                                    # (i.e. `Room1.Node1` is fine and will be transformed to `Area1.Room1.Node1`)
                                    if link.count(".") == 1:
                                        link = f"{node.area}.{link}"
                                    elif link.count(".") != 2:
                                        raise ValueError(
                                            f'ERROR: "{link}" is not a valid node name.'
                                        )

                                    if link == other_node.name:
                                        logging.debug(f"{node.name} -> {other_node.name}")
                                        if traverse_graph(
                                            other_node, aux_data, visited_rooms, visited_nodes
                                        ):
                                            return True
    return False


def shuffler(aux_data_directory: str, logic_directory: str, output: str | None):
    global nodes, edges, visited_nodes, inventory

    nodes, edges = parse(Path(logic_directory))

    # Starting node is Mercay outside of Oshus's house.
    # This would need to be randomized to support entrance rando
    starting_node = [node for node in nodes if node.name == "Mercay.OutsideOshus.Outside"][0]

    # Begin the random fill algorithm.
    # The program will generate a completely random seed without using logic.
    # It will then attempt to traverse the seed's world graph. If it fails to reach the node
    # required to beat the game, it will generate another seed and check it again. This repeats
    # until a valid seed is generated.
    # TODO: we'll want to instead use the assumed fill algorithm eventually, but this naive
    # approach is sufficient for now.
    tries = 0
    while True:
        tries += 1
        # Initialize global variables
        inventory = []

        areas = randomize_aux_data(Path(aux_data_directory))
        if traverse_graph(starting_node, areas, set(), set()):
            break

    logging.debug(f"{tries} tries were needed to get a valid seed.")

    if output == "--":
        print(json.dumps(areas), file=sys.stdout)
    elif output is not None:
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)
        for area in areas:
            with open(output_path / f"{area['name']}.json", "w") as fd:
                fd.write(json.dumps(area))

    return areas


@click.command()
@click.option(
    "-a",
    "--aux-data-directory",
    required=True,
    type=click.Path(exists=True),
    help="File path to directory that contains aux data.",
)
@click.option("-l", "--logic-directory", required=True, type=click.Path(exists=True))
@click.option(
    "-o",
    "--output",
    default=None,
    type=click.Path(exists=False, dir_okay=True, file_okay=False),
    help="Path to save randomized aux data to. Use -- to output to stdout.",
)
def shuffler_cli(aux_data_directory: str, logic_directory: str, output: str | None):
    return shuffler(aux_data_directory, logic_directory, output)


if __name__ == "__main__":
    shuffler_cli()
