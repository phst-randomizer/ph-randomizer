# type: ignore

from pathlib import Path
import sys

from shuffler._parser import parse
from shuffler.main import flatten_rooms, load_aux_data

try:
    import pygraphviz as pgv
except ModuleNotFoundError:
    print("'pygraphviz' must be installed to generate logic graph visualization.", file=sys.stderr)
    exit(1)


def main():
    # Parse aux data files
    aux_data = load_aux_data(Path(__file__).parent / 'auxiliary')

    # Parse logic files into series of rooms
    rooms = parse(Path(__file__).parent / 'logic', aux_data)

    # Convert logical rooms into flat nodes/edge graph structure
    nodes = flatten_rooms(rooms)

    G = pgv.AGraph(strict=False, directed=True)

    for node in nodes:
        G.add_node(node.name)
        for edge in node.edges:
            G.add_edge(node.name, edge.dest.name)

    graph_dir = Path.cwd() / 'graphs'
    graph_dir.mkdir(exist_ok=True)
    for graph_viz_layout in ['neato', 'dot', 'twopi', 'circo', 'sfdp']:
        try:
            G.layout(prog=graph_viz_layout)
            G.draw(str(graph_dir / f'{graph_viz_layout}.png'))
        except OSError:
            print(
                f"Couldn't generate graph viz using program \"{graph_viz_layout}\".",
                file=sys.stderr,
            )


if __name__ == '__main__':
    main()
