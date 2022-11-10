from copy import deepcopy
import json
import logging
from pathlib import Path
import random
import sys

import click

from shuffler._parser import Edge, LogicalRoom, Node, parse
from shuffler.aux_models import Area

logging.basicConfig(level=logging.INFO)

END_NODE = 'Mercay.AboveMercayTown.Island'  # Name of node that player must reach to beat the game


def load_aux_data(directory: Path) -> list[Area]:
    # Find all aux data files in the given directory
    aux_files = list(directory.rglob('*.json'))

    areas: list[Area] = []
    for file in aux_files:
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


def flatten_rooms(rooms: list[LogicalRoom]) -> list[Node]:
    """
    Given a list of `LogicalRooms`, flattens it into a series of nodes and edges.

    TODO: shuffle entrances/exits at start of this function
    """

    nodes: list[Node] = []

    def _get_dest_node(dest_node_entrance: str):
        entrance_split = dest_node_entrance.split('.')
        room_name = entrance_split[1]
        node_name = entrance_split[2]

        for room in rooms:
            assert room.nodes
            if room_name == room_name:
                for node in room.nodes:
                    if node.node == node_name:
                        for entrance in node.entrances:
                            if entrance == dest_node_entrance:
                                return node
        raise Exception(f'Entrance "{dest_node_entrance}" not found')

    for room in rooms:
        assert room.nodes
        for src_node in room.nodes:
            nodes.append(src_node)
            for exit in src_node.exits:
                if not len(exit.link):
                    # TODO: make this throw an actual error once aux data is complete
                    logging.warning(f'exit "{exit.name}" has no "link".')
                    continue
                if exit.link.split('.')[0] not in [r.area.name for r in rooms]:
                    logging.warning(
                        f'entrance "{exit.link}" not found (no aux data exists for that area)'
                    )
                    continue
                src_node.edges.append(Edge(dest=_get_dest_node(exit.link)))

    return nodes


def assumed_search(
    starting_node: Node,
    nodes: list[Node],
    aux_data: list[Area],
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
                assumed_search(
                    edge.dest,
                    nodes,
                    aux_data,
                    inventory,
                    flags,
                    visited_nodes,
                )
            )
    return visited_nodes


def shuffle(
    seed: str | None,
    logical_rooms: list[LogicalRoom],
    aux_data: list[Area],
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
        `aux_data`: Complete aux data for the game as a list of `Area`s.

    Returns:
        Randomized aux data.
    """
    if seed is not None:
        random.seed(seed)

    nodes = flatten_rooms(logical_rooms)

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
        R = assumed_search(starting_node, nodes, aux_data, deepcopy(I), set(), set())

        # Determine which of these nodes contain items, and thus are candidates for item placement
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
        # is complete. If one is true but not the other, that indicates that either not all items
        # were placed, or not every location received an item. However, until the aux data and
        # logic are complete, this will not be true; once they are complete, this statement should
        # be changed to an `and` instead of `or` and an explicit check should be added to avoid
        # an infinite loop.
        if not len(I) or None not in {r.contents for r in candidates}:
            break

    return aux_data


@click.command()
@click.option(
    '-a',
    '--aux-data-directory',
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help='File path to directory that contains aux data.',
)
@click.option(
    '-l',
    '--logic-directory',
    required=True,
    type=click.Path(exists=True, path_type=Path),
)
@click.option(
    '-o',
    '--output',
    default=None,
    type=click.Path(exists=False, dir_okay=True, file_okay=False),
    help='Path to save randomized aux data to. Use -- to output to stdout.',
)
@click.option('-s', '--seed', type=str, required=False, help='Seed for the RNG.')
def shuffler_cli(
    aux_data_directory: Path,
    logic_directory: Path,
    output: str | None,
    seed: str | None,
):
    # Parse aux data files
    aux_data = load_aux_data(aux_data_directory)

    # Parse logic files into series of rooms
    rooms = parse(logic_directory, aux_data)

    results = shuffle(seed, rooms, aux_data)

    if output == '--':
        for area in results:
            print(area.json(), file=sys.stdout)
    elif output is not None:
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)
        for area in results:
            with open(output_path / f'{area.name}.json', 'w') as fd:
                fd.write(area.json())


if __name__ == '__main__':
    shuffler_cli()
