# type: ignore

from pathlib import Path
import sys

from ph_rando.shuffler.logic import Logic

try:
    import pygraphviz as pgv
except ModuleNotFoundError:
    print("'pygraphviz' must be installed to generate logic graph visualization.", file=sys.stderr)
    exit(1)


def main():
    logic = Logic()

    logic.connect_rooms()

    G = pgv.AGraph(strict=False, directed=True)

    for area in logic.areas.values():
        for room in area.rooms:
            for node in room.nodes:
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
                f"Couldn't generate graph viz using program {graph_viz_layout!r}.",
                file=sys.stderr,
            )


if __name__ == '__main__':
    main()
