import pytest
from networkx import MultiDiGraph

from compgraph2txt import compgraph2txt


def assert_correct_output(output: str, gt: str) -> None:
    lines = output.split("\n")
    for line, gt_line in zip(lines, gt.strip().split("\n")):
        line = line.strip()
        gt_line = gt_line.strip()
        assert line == gt_line, f"'{line}' != '{gt_line}'"


def test_single_node():
    graph = MultiDiGraph()
    graph.add_node("A", name="B", inputs=["a", "x", "y", "z"], outputs=["b", "c", "d"])
    graph.add_edge("ext1", "A", input="x")
    graph.add_edge("ext1", "A", input="z")
    graph.add_edge("ext2", "A", input="y")
    graph.add_edge("A", "ext", output="c")

    output = compgraph2txt(graph)
    gt = """
        │ │ ╭─────────╮
        │ │ │    B    │
        │ │ ├─────────┤
        │ │ │─ a   b ─│
        ├───┼→ x   c ─┼→
        │ ╰─┼→ y   d ─│
        ╰───┼→ z      │
            ╰─────────╯
    """
    assert_correct_output(output, gt)


def test_simple():
    graph = MultiDiGraph()
    graph.add_node("A", name="A", inputs=[], outputs=["a"])
    graph.add_node("B", name="B", inputs=["b"], outputs=[])
    graph.add_edge("A", "B", output="a", input="b")

    output = compgraph2txt(graph)
    gt = """
        ╭─────╮
        │  A  │
        ├─────┤
        │  a ─┼─╮
        ╰─────╯ │ 
        ╭───────╯
        │ ╭─────╮
        │ │  B  │
        │ ├─────┤
        ╰─┼→ b  │
          ╰─────╯
    """
    assert_correct_output(output, gt)


def test_difficult():
    graph = MultiDiGraph()
    graph.add_node(
        "A", name="A", inputs=["a", "b", "c", "d"], outputs=["e", "f", "g", "h", "i"]
    )
    graph.add_node("B", name="B", inputs=["t", "u", "v", "w"], outputs=["x", "y", "z"])

    # Add edges from external sources
    graph.add_edge("ext1", "A", input="c")
    graph.add_edge("ext1", "B", input="v")
    graph.add_edge("ext2", "A", input="a")
    graph.add_edge("ext3", "B", input="w")
    graph.add_edge("ext4", "A", input="b")
    graph.add_edge("ext5", "A", input="d")

    # Add edges to external sinks
    graph.add_edge("A", "ext", output="g")
    graph.add_edge("A", "ext", output="i")
    graph.add_edge("B", "ext", output="x")
    graph.add_edge("B", "ext", output="z")
    graph.add_edge("B", "ext", output="x")
    graph.add_edge("B", "ext", output="z")

    # Add edges between nodes
    graph.add_edge("A", "B", output="f", input="t")
    graph.add_edge("A", "B", output="h", input="u")

    output = compgraph2txt(graph)
    gt = """
        │ │ │ │ │ ╭─────────╮
        │ │ │ │ │ │    A    │
        │ │ │ │ │ ├─────────┤
        │ ╰───────┼→ a   e ─│
        │   │ ╰───┼→ b   f ─┼─╮
        ├─────────┼→ c   g ─┼──→
        │   │   ╰─┼→ d   h ─┼───╮
        │   │     │      i ─┼────→
        │   │     ╰─────────╯ │ │ 
        │ ╭───────────────────╯ │
        │ │ │ ╭─────────────────╯
        │ │ │ │ ╭─────────╮
        │ │ │ │ │    B    │
        │ │ │ │ ├─────────┤
        │ ╰─────┼→ t   x ─┼→
        │   │ ╰─┼→ u   y ─│
        ╰───────┼→ v   z ─┼→
            ╰───┼→ w      │
                ╰─────────╯
    """
    assert_correct_output(output, gt)


def test_cycle():
    graph = MultiDiGraph()
    graph.add_node("A", name="A", inputs=["a"], outputs=["b"])
    graph.add_node("B", name="B", inputs=["c"], outputs=["d"])
    graph.add_edge("A", "B", output="b", input="c")
    graph.add_edge("B", "A", output="d", input="a")

    with pytest.raises(ValueError, match="Graph cannot contain a cycle."):
        compgraph2txt(graph)


def test_duplicate():
    graph = MultiDiGraph()
    graph.add_node("A", name="A", inputs=["a"], outputs=["b"])
    graph.add_node("B", name="B", inputs=["c"], outputs=["d"])
    graph.add_edge("A", "B", output="b", input="c")
    graph.add_edge("A", "B", output="b", input="c")

    with pytest.raises(ValueError, match="exists twice in the graph"):
        compgraph2txt(graph)


def test_two_sources():
    graph = MultiDiGraph()
    graph.add_node("A", name="A", inputs=["a"], outputs=["b"])
    graph.add_node("B", name="B", inputs=["c"], outputs=["d"])
    graph.add_edge("A", "B", output="b", input="c")
    graph.add_edge("ext", "B", input="c")

    with pytest.raises(ValueError, match="Two \(or more\) sources exist"):
        compgraph2txt(graph)


def test_empty():
    graph = MultiDiGraph()
    with pytest.raises(ValueError, match="None of the nodes in the provided graph"):
        compgraph2txt(graph)

    graph.add_node("A")
    with pytest.raises(ValueError, match="None of the nodes in the provided graph"):
        compgraph2txt(graph)


def test_same_input():
    graph = MultiDiGraph()
    graph.add_node("A", name="A", inputs=["a", "a"], outputs=["b"])
    with pytest.raises(ValueError, match="contains two instances of the same input"):
        compgraph2txt(graph)


def test_same_output():
    graph = MultiDiGraph()
    graph.add_node("A", name="A", inputs=["a"], outputs=["b", "b"])
    with pytest.raises(ValueError, match="contains two instances of the same output"):
        compgraph2txt(graph)


def test_wrong_type():
    with pytest.raises(TypeError, match="Graph must be a MultiDiGraph"):
        compgraph2txt(4)


def test_invalid_edge():
    graph = MultiDiGraph()
    graph.add_node("A", name="A", inputs=["a"], outputs=["b"])
    graph.add_node("B", name="B", inputs=["c"], outputs=["d"])

    graph.add_edge("A", "B", output="z", input="c")
    with pytest.raises(ValueError, match="output 'z' of 'A', which does not exist"):
        compgraph2txt(graph)
    graph.remove_edge("A", "B")

    graph.add_edge("A", "B", output="b", input="z")
    with pytest.raises(ValueError, match="input 'z' of 'B', which does not exist"):
        compgraph2txt(graph)
    graph.remove_edge("A", "B")

    graph.add_edge("A", "B", output="b")
    with pytest.raises(ValueError, match="requires the 'input' attribute"):
        compgraph2txt(graph)
    graph.remove_edge("A", "B")

    graph.add_edge("A", "B", input="c")
    with pytest.raises(ValueError, match="requires the 'output' attribute"):
        compgraph2txt(graph)
    graph.remove_edge("A", "B")
