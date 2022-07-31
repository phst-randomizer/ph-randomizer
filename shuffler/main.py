from copy import deepcopy
import json
import logging
from pathlib import Path
import random
import sys

import click

from shuffler._parser import Descriptor, Edge, Node, NodeContents, parse
from shuffler.aux_models import Area

logging.basicConfig(level=logging.INFO)

END_NODE = 'Mercay.AboveMercayTown.Island'  # Name of node that player must reach to beat the game


def load_aux_data(directory: Path) -> list[Area]:
    # Find all aux data files in the given directory
    aux_files = list(directory.rglob('*.json'))

    areas: list[Area] = []
    for file in aux_files:
        with open(file) as fd:
            areas.append(Area(**json.load(fd)))
    return areas


def randomize_aux_data(aux_data: list[Area]) -> list[Area]:
    """
    Return aux data for the logic with the item locations randomized.

    Note: the item locations are *not* guaranteed (and are unlikely) to be logic-compliant.
    This function just performs a "dumb" shuffle and returns the results.

    Params:
        aux_data_directory: Directory that contains the initial aux data
    """
    # List of every item in the game
    chest_items: list[str] = []

    # Record all items in the game
    for area in aux_data:
        for room in area.rooms:
            for chest in room.chests or []:
                chest_items.append(chest.contents)

    # Randomize the items
    for area in aux_data:
        for room in area.rooms:
            for chest in room.chests or []:
                chest.contents = chest_items.pop(random.randint(0, len(chest_items) - 1))
    return aux_data


def get_chest_contents(
    area_name: str, room_name: str, chest_name: str, aux_data: list[Area]
) -> str:
    for area in aux_data:
        if area_name == area.name:
            for room in area.rooms:
                if room_name == room.name:
                    for chest in room.chests or []:
                        if chest_name == chest.name:
                            return chest.contents
    raise Exception(f'{chest_name} not found in the given aux data.')


def get_chest_from_node_contents(node: Node, node_contents: NodeContents, aux_data: list[Area]):
    for area in aux_data:
        if node.area == area.name:
            for room in area.rooms:
                if node.room == room.name:
                    for chest in room.chests:
                        if node_contents.data == chest.name:
                            return chest
    raise Exception(f'{node_contents.data} not found in the given aux data.')


def assumed_search(
    starting_node: Node,
    nodes: list[Node],
    edges: dict[str, list[Edge]],
    aux_data: list[Area],
    inventory: list[str],
    flags: set[str],
    visited_rooms: set[str],
    visited_nodes: set[str],
) -> set[Node]:
    """
    Calculate the set of nodes reachable from the `starting_node` given the current inventory.

    Params:
        `starting_node`: The node to start at.
        `nodes`: The nodes that make up the game's logic graph.
        `edges`: The edges that connect the `nodes`.
        `aux_data`: Complete aux data for the game as a list of `Area`s.
        `inventory`: Current inventory.
        `visited_rooms`: Rooms that have been visited already in this traversal.
        `visited_nodes`: Same as `visited_rooms`, but for nodes.

    Returns:
        The set of nodes that is reachable given the current inventory.
    """
    logging.debug(starting_node.name)

    reachable_nodes: set[Node] = {starting_node}

    doors_to_enter: list[str] = []

    # For the current node, find all chests + "collect" their items and note every door so
    # we can go through them later
    for node_info in starting_node.contents:
        if node_info.type == Descriptor.CHEST.value:
            item = get_chest_contents(
                starting_node.area, starting_node.room, node_info.data, aux_data
            )
            if item and item not in inventory:
                inventory.append(item)
                # Reset visited nodes and rooms because we may now be able to reach
                # nodes we couldn't before with this new item
                visited_nodes.clear()
                visited_rooms.clear()
        elif node_info.type == Descriptor.FLAG.value:
            if node_info.data not in flags:
                flags.add(node_info.data)
                # Reset visited nodes and rooms because we may now be able to reach
                # nodes we couldn't before with this new flag set
                visited_nodes.clear()
                visited_rooms.clear()
    for node_info in starting_node.contents:
        if node_info.type in (
            Descriptor.DOOR.value,
            Descriptor.ENTRANCE.value,
            Descriptor.EXIT.value,
        ):
            full_room_name = node_info.data
            # Get "path" to node, including Area and Room, if they're not included
            if len(full_room_name.split('.')) == 2:
                full_room_name = f'{starting_node.area}.{full_room_name}'
            elif len(full_room_name.split('.')) == 1:
                full_room_name = f'{starting_node.area}.{starting_node.room}.{full_room_name}'

            if full_room_name not in visited_rooms:
                doors_to_enter.append(full_room_name)
                visited_rooms.add(full_room_name)

    visited_nodes.add(starting_node.name)  # Acknowledge this node as "visited"

    # Check which edges are traversable and do so if they are
    for edge in edges[starting_node.name]:
        if edge.dest.name in visited_nodes:
            continue
        if edge.is_traversable(inventory, flags):
            logging.debug(f'{edge.source.name} -> {edge.dest.name}')
            return reachable_nodes.union(
                assumed_search(
                    edge.dest,
                    nodes,
                    edges,
                    aux_data,
                    inventory,
                    flags,
                    visited_rooms,
                    visited_nodes,
                )
            )

    # Go through each door and traverse each of their room graphs
    for door_name in doors_to_enter:
        area_name = door_name.split('.')[0]
        room_name = door_name.split('.')[1]
        door_name = door_name.split('.')[2]
        for area in aux_data:
            if area_name == area.name:
                for room in area.rooms:
                    if room_name == room.name:
                        for door in room.doors:
                            if door_name == door.name:
                                for other_node in nodes:
                                    link = door.link

                                    # Remove the `door`/`entrance` that this `door`/`exit` links to.
                                    # It is only used for entrance randomization; for chest
                                    # randomization, we don't care about it.
                                    link = '.'.join(link.split('.')[:-1])

                                    # TODO: remove this if statement once aux data is complete
                                    if 'todo' in link.lower():
                                        continue

                                    # Append current area if the linked node doesn't have one specified
                                    # (i.e. `Room1.Node1` is fine and will be transformed to `Area1.Room1.Node1`)
                                    if link.count('.') == 1:
                                        link = f'{starting_node.area}.{link}'
                                    elif link.count('.') != 2:
                                        raise ValueError(
                                            f'ERROR: "{link}" is not a valid node name.'
                                        )

                                    if link == other_node.name:
                                        logging.debug(f'{starting_node.name} -> {other_node.name}')
                                        return reachable_nodes.union(
                                            assumed_search(
                                                other_node,
                                                nodes,
                                                edges,
                                                aux_data,
                                                inventory,
                                                flags,
                                                visited_rooms,
                                                visited_nodes,
                                            )
                                        )
    return reachable_nodes


def shuffle(
    seed: str | None,
    nodes: list[Node],
    edges: dict[str, list[Edge]],
    aux_data: list[Area],
    output: str | None = None,
) -> list[Area]:
    """
    Given aux data and logic, shuffles the aux data and returns it.

    The Assumed Fill algorithm is used to place the items. The implementation is based on the
    following paper:
    https://digitalcommons.lsu.edu/cgi/viewcontent.cgi?article=6325&context=gradschool_theses
    There are some deviations due to how our logic is structured, but it follows the same general
    Assumed Fill algorithm described there; where possible, variable/function names are identical
    to their counterparts in the pseudo-code in that paper.

    Params:
        `seed`: Some string that will be hashed and used as a seed for the RNG.
        `nodes`: The nodes that make up the game's logic graph.
        `edges`: The edges that connect the `nodes`.
        `aux_data`: Complete aux data for the game as a list of `Area`s.
        `output`: Optional directory to output randomized aux data to, or '--' to output to stdout.

    Returns:
        Randomized aux data.
    """
    if seed is not None:
        random.seed(seed)

    # Starting node is Mercay outside of Oshus's house.
    # This would need to be randomized to support entrance rando
    starting_node = [node for node in nodes if node.name == 'Mercay.OutsideOshus.Outside'][0]

    # Set G to all chests
    G = [chest for area in aux_data for room in area.rooms for chest in room.chests]

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
        R = assumed_search(starting_node, nodes, edges, aux_data, deepcopy(I), set(), set(), set())

        # Determine which of these nodes contain items, and thus are candidates for item placement
        candidates = [
            get_chest_from_node_contents(node, content, aux_data)
            for node in R
            for content in node.contents
            if content.type == Descriptor.CHEST.value
        ]

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
                f'Error: shuffler ran out of locations to place item. Remaining items: {[i] + I}'
            )

        # TODO: these conditions should both become true at the same time, once shuffling
        # is complete. If one is true but not the other, that indicates that either not all items
        # were placed, or not every location received an item. However, until the aux data and
        # logic are complete, this will not be true; once they are complete, this statement should
        # be changed to an `and` instead of `or` and an explicit check should be added to avoid
        # an infinite loop.
        if not len(I) or None not in {r.contents for r in candidates}:
            break

    if output == '--':
        for area in aux_data:
            print(area.json(), file=sys.stdout)
    elif output is not None:
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)
        for area in aux_data:
            with open(output_path / f'{area.name}.json', 'w') as fd:
                fd.write(area.json())

    return aux_data


@click.command()
@click.option(
    '-a',
    '--aux-data-directory',
    required=True,
    type=click.Path(exists=True),
    help='File path to directory that contains aux data.',
)
@click.option('-l', '--logic-directory', required=True, type=click.Path(exists=True))
@click.option(
    '-o',
    '--output',
    default=None,
    type=click.Path(exists=False, dir_okay=True, file_okay=False),
    help='Path to save randomized aux data to. Use -- to output to stdout.',
)
@click.option('-s', '--seed', type=str, required=False, help='Seed for the RNG.')
def shuffler_cli(
    aux_data_directory: str, logic_directory: str, output: str | None, seed: str | None
):
    # Parse logic files
    nodes, edges = parse(Path(logic_directory))

    # Parse aux data files
    aux_data = load_aux_data(Path(aux_data_directory))

    return shuffle(seed, nodes, edges, aux_data, output)


if __name__ == '__main__':
    shuffler_cli()
