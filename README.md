# compgraph2txt 

[![Testing](https://github.com/adamviola/compgraph2txt/actions/workflows/tests.yml/badge.svg)](https://github.com/adamviola/compgraph2txt/actions/workflows/testing.yml)
![Codecov](https://img.shields.io/codecov/c/github/adamviola/compgraph2txt)


A tiny library for visualizing computational graphs in the terminal.

```
│ │ │ ╭─────────╮
│ │ │ │    A    │
│ │ │ ├─────────┤
│ ╰───┼→ a   e ─┼─╮
│   │ │─ b   f ─┼──→
├─────┼→ c   g ─┼───╮
│   │ │─ d   h ─│ │ │
│   │ │      i ─┼────→
│   │ ╰─────────╯ │ │ 
│ ╭───────────────╯ │
│ │ │ ╭─────────────╯
│ │ │ │ ╭─────────╮
│ │ │ │ │    Z    │
│ │ │ │ ├─────────┤
│ ╰─────┼→ t   x ─┼→
│   │ ╰─┼→ u   y ─│
╰───────┼→ v   z ─┼→
    ╰───┼→ w      │
        ╰─────────╯
```

<details>
<summary>Source</summary>

```python
from compgraph2txt import compgraph2txt
from networkx import MultiDiGraph

graph = MultiDiGraph()
graph.add_node(
    "A", inputs=["a", "b", "c", "d"], outputs=["e", "f", "g", "h", "i"]
)
graph.add_node("Z", inputs=["t", "u", "v", "w"], outputs=["x", "y", "z"])

# Add edges from external sources
graph.add_edge("ext1", "A", input="c")
graph.add_edge("ext1", "Z", input="v")
graph.add_edge("ext2", "A", input="a")
graph.add_edge("ext3", "Z", input="w")

# Add edges to external sinks
graph.add_edge("A", "ext", output="f")
graph.add_edge("A", "ext", output="i")
graph.add_edge("Z", "ext", output="x")
graph.add_edge("Z", "ext", output="z")
graph.add_edge("Z", "ext", output="x")
graph.add_edge("Z", "ext", output="z")

# Add edges between nodes
graph.add_edge("A", "Z", output="e", input="t")
graph.add_edge("A", "Z", output="g", input="u")

print(compgraph2txt(graph))
```

</details>

## Example: Image Background Blur Pipeline

### Source
```python
from compgraph2txt import compgraph2txt
from networkx import MultiDiGraph

graph = MultiDiGraph()
graph.add_node("Camera", inputs=[], outputs=["Image"])
graph.add_node("Foreground Detection", inputs=["Image"], outputs=["Foreground", "Background"])
graph.add_node("Blur", inputs=["Image"], outputs=["Blurred Image"])
graph.add_node("Image Overlay", inputs=["Foreground", "Background"], outputs=["Image"])
graph.add_node("Application", inputs=["Image"], outputs=[])

graph.add_edge("Camera", "Foreground Detection", output="Image", input="Image")
graph.add_edge("Foreground Detection", "Blur", output="Background", input="Image")
graph.add_edge("Blur", "Image Overlay", output="Blurred Image", input="Background")
graph.add_edge("Foreground Detection", "Image Overlay", output="Foreground", input="Foreground")
graph.add_edge("Image Overlay", "Application", output="Image", input="Image")

print(compgraph2txt(graph))
```

### Output
```
╭──────────╮
│  Camera  │
├──────────┤
│   Image ─┼─╮
╰──────────╯ │ 
╭────────────╯
│ ╭────────────────────────╮
│ │  Foreground Detection  │
│ ├────────────────────────┤
╰─┼→ Image     Foreground ─┼─╮
  │            Background ─┼───╮
  ╰────────────────────────╯ │ │ 
╭────────────────────────────╯ │
│ ╭────────────────────────────╯
│ │ ╭────────────────────────╮
│ │ │          Blur          │
│ │ ├────────────────────────┤
│ ╰─┼→ Image  Blurred Image ─┼─╮
│   ╰────────────────────────╯ │ 
│ ╭────────────────────────────╯
│ │ ╭─────────────────────╮
│ │ │    Image Overlay    │
│ │ ├─────────────────────┤
╰───┼→ Foreground  Image ─┼─╮
  ╰─┼→ Background         │ │
    ╰─────────────────────╯ │ 
╭───────────────────────────╯
│ ╭───────────────╮
│ │  Application  │
│ ├───────────────┤
╰─┼→ Image        │
  ╰───────────────╯
```
