from collections import defaultdict
from itertools import zip_longest
from typing import Dict, List, Optional, Sequence, Tuple

from networkx import MultiDiGraph, NetworkXNoCycle, find_cycle, topological_sort

round_corners = {
    "┌": "╭",
    "┐": "╮",
    "┘": "╯",
    "└": "╰",
}


def compgraph2txt(graph: MultiDiGraph, rounded_corners: bool = True) -> str:
    """Constructs a text-based visualization of a computational graph.

    A computational graph is a directed graph where (1) nodes correspond to
    operations and (2) edges describe the data flow between them.

    compgraph2txt defines each node to have any number of inputs and outputs;
    each edge connects the outputs of one node to the input of another.

    Each node in the graph is visualized if and only if it has the following
    attributes:
      - inputs (sequence of str): List of named inputs to the node.
      - outputs (sequence of str): List of named outputs of the node.
      - name (str, optional): Name of the node. Defaults to the node key.

    Since each node can have multiple inputs and outputs, edges must declare
    which input and output they connect to via the following edge attributes:
      - output (str): Name of the output of the 'from' node.
      - input (str): Name of input of the 'to' node.

    Edges between visualized nodes (have inputs/outputs attributes) and
    non-visualized nodes (missing inputs/outputs attributes) are visualized
    differently than edges between visualized nodes.

    e.g.,

    ```python
    graph = MultiDiGraph()
    graph.add_node("A", name="A!", inputs=["w", "x"], outputs=["y", "z"])
    graph.add_node("B", inputs=["i", "j"], outputs=["k"])

    graph.add_edge("ext1", "A", input="x")
    graph.add_edge("ext1", "B", input="i")
    graph.add_edge("A", "B", output="z", input="j")
    graph.add_edge("A", "ext2", output="y")

    print(compgraph2txt(graph))
    # │ ╭────────╮
    # │ │   A!   │
    # │ ├────────┤
    # │ │─ w  y ─┼→
    # ├─┼→ x  z ─┼─╮
    # │ ╰────────╯ │
    # │ ╭──────────╯
    # │ │ ╭─────────╮
    # │ │ │    B    │
    # │ │ ├─────────┤
    # ╰───┼→ i   k ─│
    #   ╰─┼→ j      │
    #     ╰─────────╯
    ```

    Args:
        graph (MultiDiGraph): Computational graph.
        rounded_corners (bool, optional): Whether to use rounded corners (True)
            or square corners (False) for node boxes and arrow lines. Defaults
            to True.

    Returns:
        str: Text-based visualization of the computational graph.
    """
    _validate_graph(graph)

    # List containing each "source" - i.e. (node-name, output-name) - that makes up the
    # left margin. Mutated as each node is processed
    sources: List[Optional[Tuple[str, Optional[str]]]] = []

    # Inverse mapping of sources
    source_to_index: Dict[Tuple[str, Optional[str]], int] = {}

    # Number of subscribers of each source
    # None if edge output is not used, 0 if external, 1+ if used internally
    num_subscribers: Dict[str, Optional[int]] = defaultdict(lambda: None)

    # Identify external sources and count degree of each edge
    for source_node, dest_node, data in graph.edges(data=True):
        source = (source_node, data.get("output"))
        if "outputs" not in graph.nodes[source_node] and source not in source_to_index:
            source_to_index[source] = len(sources)
            sources.append(source)

        if source not in num_subscribers:
            num_subscribers[source] = 0
        if "inputs" in graph.nodes[dest_node]:
            num_subscribers[source] += 1

    # Build the visualization
    lines = []
    for node in topological_sort(graph):
        data = graph.nodes[node]
        name = data.get("name", node)
        try:
            inputs = data["inputs"]
            outputs = data["outputs"]
        except KeyError:
            # Skip external nodes
            continue

        # Figure out the width of the box
        max_input_len = max([len(i) for i in inputs], default=-2)
        max_output_len = max([len(o) for o in outputs], default=-2)
        text_width = max(len(name), max_input_len + max_output_len + 2)

        # Ensure that the node name is centered
        if len(name) % 2 != text_width % 2:
            text_width += 1

        # Write the top half of the box
        source_lines = _get_source_lines(sources)
        lines.append(f"{source_lines}┌──{'─' * text_width}──┐")
        padding = " " * ((text_width - len(name)) // 2)
        lines.append(f"{source_lines}│  {padding}{name}{padding}  │")
        lines.append(f"{source_lines}├──{'─' * text_width}──┤")

        # Write the bottom half of the box
        internal_outputs = []
        for input_, output in zip_longest(inputs, outputs):
            if input_ is None:
                input_ = ""
            if output is None:
                output = ""
            gap = " " * (text_width - len(input_) - len(output))

            # Build visualization for each input
            line_indent = source_lines
            if input_:
                input_source = _get_source(node, input_, graph)
                if input_source is not None:
                    index = source_to_index[input_source]

                    num_subscribers[input_source] -= 1
                    # Source of this input is either (1) ending at this input or
                    # (2) continuing down to another node/input
                    if num_subscribers[input_source] == 0:
                        source_to_index.pop(input_source)
                        sources[index] = None
                        source_lines = _get_source_lines(sources)
                        char = "└"
                    else:
                        char = "├"
                    line_indent = f"{source_lines[:index * 2]}{char}{'─' * (len(source_lines) - index * 2 - 1)}"
                    input_ = f"┼→ {input_}"
                else:
                    input_ = f"│─ {input_}"
            else:
                # Handle case where there are more outputs than inputs
                input_ = f"│  {input_}"

            # Build visualization for each output
            if output:
                output_source = (node, output)
                # Output is either:
                # (1) unused
                if num_subscribers[output_source] is None:
                    spacing = " │" * len(internal_outputs)
                    output = f"{output} ─│{spacing}"
                # (2) going to 1+ external node(s) but no internal nodes
                elif num_subscribers[output_source] == 0:
                    spacing = "─" * (len(internal_outputs) * 2)
                    output = f"{output} ─┼{spacing}→"
                # (3) going to 1+ internal nodes
                else:
                    spacing = "─" * (len(internal_outputs) * 2 + 1)
                    internal_outputs.append(output)
                    output = f"{output} ─┼{spacing}┐"
            else:
                # Handle case where there are more inputs than outputs
                spacing = " │" * len(internal_outputs)
                output = f"{output}  │{spacing}"

            lines.append(f"{line_indent}{input_}{gap}{output}")

        # Finish the box
        spacing = "│ " * len(internal_outputs)
        source_lines = _get_source_lines(sources)
        lines.append(f"{source_lines}└──{'─' * text_width}──┘ {spacing}")

        # Write lines that move the node output into the left margin
        left_margin = len(source_lines)
        for i, output in enumerate(internal_outputs):
            output_source = (node, output)

            try:
                index = sources.index(None)
            except ValueError:
                index = len(sources)
                sources.append(output_source)
                source_to_index[output_source] = index
            else:
                sources[index] = output_source
                source_to_index[output_source] = index

            source_lines = _get_source_lines(sources)

            line_indent = f"{source_lines[:index * 2]}┌{'─' * (left_margin + text_width + 6 - len(source_lines[:index * 2]) + i * 2)}"
            suffix = " │" * (len(internal_outputs) - i - 1)
            lines.append(f"{line_indent}┘{suffix}")

        # The left margin can sometimes get clogged with Nones
        # Basically applies "rstrip" to the left margin
        while sources and sources[-1] is None:
            sources.pop()

    output = "\n".join(lines)

    # Swap hard corners with round corners (if requested)
    if rounded_corners:
        output = "".join([round_corners.get(c, c) for c in output])

    return output


def _validate_graph(graph: MultiDiGraph):
    if not isinstance(graph, MultiDiGraph):
        raise TypeError("Graph must be a MultiDiGraph.")
    try:
        find_cycle(graph)
    except NetworkXNoCycle:
        pass
    else:
        raise ValueError("Graph cannot contain a cycle.")

    external_nodes = set()
    internal_nodes = set()
    for node, data in graph.nodes(data=True):
        if "inputs" in data and "outputs" in data:
            internal_nodes.add(node)
        else:
            external_nodes.add(node)
            continue

        inputs = set()
        for input_ in data["inputs"]:
            # Assert no duplicate inputs
            if input_ in inputs:
                raise ValueError(
                    f"Node '{node}' contains two instances of the same input "
                    f"'{input_}'."
                )
            inputs.add(input_)

        outputs = set()
        for output in data["outputs"]:
            # Assert no duplicate outputs
            if output in outputs:
                raise ValueError(
                    f"Node '{node}' contains two instances of the same output "
                    f"'{output}'."
                )
            outputs.add(output)

    if not internal_nodes:
        raise ValueError(
            "Graph nodes must have both 'inputs' and 'outputs' attributes to be "
            "displayed. None of the nodes in the provided graph have both 'inputs' and "
            "'outputs' attributes."
        )

    dest_to_source = {}
    for source_node, dest_node, data in graph.edges(data=True):
        if source_node in internal_nodes:
            if "output" not in data:
                raise ValueError(
                    f"Edge from '{source_node}' to '{dest_node}' requires the 'output' "
                    f"attribute, which specifies the output of '{dest_node}' from "
                    "which the edge originates."
                )
            elif data["output"] not in graph.nodes[source_node]["outputs"]:
                raise ValueError(
                    f"Edge from '{source_node}' to '{dest_node}' references output "
                    f"'{data['output']}' of '{source_node}', which does not exist."
                )

        if dest_node in internal_nodes:
            if "input" not in data:
                raise ValueError(
                    f"Edge from '{source_node}' to '{dest_node}' requires the 'input' "
                    f"attribute, which specifies the input of '{source_node}' to "
                    "which the edge ends."
                )
            elif data["input"] not in graph.nodes[dest_node]["inputs"]:
                raise ValueError(
                    f"Edge from '{source_node}' to '{dest_node}' references input "
                    f"'{data['input']}' of '{dest_node}', which does not exist."
                )

            source = (source_node, data.get("output"))
            dest = (dest_node, data.get("input"))
            if dest in dest_to_source:
                if source == dest_to_source[dest]:
                    raise ValueError(
                        f"Edge from output '{data.get('output')}' of node "
                        f"'{source_node}' to input '{data.get('input')}' of node "
                        f"'{dest_node}' exists twice in the graph."
                    )
                else:
                    raise ValueError(
                        "Each node input may have at most one source. Two (or more) "
                        f"sources exist for input '{data.get('input')}' of node "
                        f"'{dest_node}'."
                    )
            dest_to_source[dest] = source


def _get_source_lines(sources: Sequence[Optional[Tuple[str, Optional[str]]]]):
    return "".join(["  " if s is None else "│ " for s in sources])


def _get_source(
    node: str, input_: str, graph: MultiDiGraph
) -> Optional[Tuple[str, Optional[str]]]:
    for source_node, _, data in graph.in_edges(node, data=True):
        if data["input"] == input_:
            return (source_node, data.get("output"))
