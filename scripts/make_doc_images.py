#!/usr/bin/env python
"""Generate the screenshots used in the documentation.

Run it from the repository root::

    python scripts/make_doc_images.py

The images are written to ``docs/images/`` and are checked into the repository,
so this only needs running when the look of the editor changes.

The script paints the scene into a QImage instead of taking a screenshot of a
window, so it needs a working Qt platform plugin but no visible screen. Do not
run it with ``QT_QPA_PLATFORM=offscreen``: that platform has no fonts, and the
text comes out as empty boxes.
"""
from __future__ import annotations

from pathlib import Path

from qtpy.QtCore import QRectF, Qt
from qtpy.QtGui import QColor, QImage, QPainter, QPen
from qtpy.QtWidgets import QApplication, QLabel, QVBoxLayout

from nodeeditor.node_content_widget import QDMNodeContentWidget
from nodeeditor.node_edge import Edge
from nodeeditor.node_graph import shortest_path
from nodeeditor.node_group import Group
from nodeeditor.node_graphics_node import QDMGraphicsNode
from nodeeditor.node_multi_input_node import MultiInputNode
from nodeeditor.node_node import Node
from nodeeditor.node_scene import Scene

OUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "images"
MARGIN = 45


def render(scene: Scene, name: str, margin: int = MARGIN) -> None:
    """Render the scene to a PNG file in ``docs/images``."""
    rect = scene.grScene.itemsBoundingRect().adjusted(-margin, -margin, margin, margin)
    width = max(int(rect.width()), 1)
    height = max(int(rect.height()), 1)

    image = QImage(width, height, QImage.Format.Format_ARGB32)
    painter = QPainter(image)
    scene.grScene.render(painter, QRectF(0, 0, width, height), rect)
    painter.end()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / name
    image.save(str(path))
    print(f"wrote docs/images/{name} ({width}x{height})")


class DocGraphicsNode(QDMGraphicsNode):
    """Graphics node with a compact box, like the nodes in the examples."""

    def initSizes(self):
        super().initSizes()
        self.width = 160
        self.height = 72
        self.edge_roundness = 6
        self.edge_padding = 8


class CaptionContent(QDMNodeContentWidget):
    """Content widget showing a single caption instead of the default widgets."""

    def initUI(self):
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        self.wdg_label = QLabel(self.node.caption)
        self.wdg_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.layout.addWidget(self.wdg_label)


class CaptionNode(Node):
    """A node with a clean, single-caption body."""

    GraphicsNode_class = DocGraphicsNode
    NodeContent_class = CaptionContent

    def __init__(self, scene, title, caption="", inputs=None, outputs=None, **kwargs):
        self.caption = caption
        super().__init__(scene, title=title, inputs=inputs or [], outputs=outputs or [], **kwargs)


class ShapeNode(CaptionNode):
    """A node whose sockets are all drawn with the same shape."""

    def __init__(self, scene, title, shape, caption, inputs, outputs):
        self.shape = shape
        super().__init__(scene, title=title, caption=caption, inputs=inputs, outputs=outputs)

    def initSettings(self):
        super().initSettings()
        self.input_socket_shapes = {"*": self.shape}
        self.output_socket_shapes = {"*": self.shape}


class SumNode(MultiInputNode, CaptionNode):
    """A node that reads an ordered number of inputs."""


def quickstart() -> Scene:
    scene = Scene()
    source = CaptionNode(scene, title="Value", caption="42", outputs=[1], output_text=["out"])
    source.setPos(-170, -20)
    sink = CaptionNode(scene, title="Print", caption="print(42)", inputs=[1], input_text=["in"])
    sink.setPos(170, -20)
    Edge(scene, source.outputs[0], sink.inputs[0])
    return scene


def socket_shapes() -> Scene:
    scene = Scene()
    shapes = [("circle", None), ("square", "square"), ("triangle", "triangle"), ("chevron", "chevron")]
    x = -330
    for title, shape in shapes:
        if shape is None:
            node = CaptionNode(scene, title=title, caption="value", inputs=[1], outputs=[1])
        else:
            node = ShapeNode(scene, title=title, shape=shape, caption="value", inputs=[1], outputs=[1])
        node.setPos(x, 0)
        x += 220
    return scene


def node_labels() -> Scene:
    scene = Scene()
    read = CaptionNode(scene, title="Read file", caption="image.png", outputs=[1], output_text=["pixels"])
    read.setPos(-220, -30)
    read.setNodeLabel("reads the image")
    read.setNodeLabelVisible(True)

    process = CaptionNode(scene, title="Process", caption="blur(3)", inputs=[1], outputs=[1],
                          input_text=["in"], output_text=["out"])
    process.setPos(60, -30)
    process.setNodeLabel("applies the filter")
    process.setNodeLabelVisible(True)

    Edge(scene, read.outputs[0], process.inputs[0])
    return scene


def edge_labels() -> Scene:
    scene = Scene()
    a = CaptionNode(scene, title="Source", caption="rgb", outputs=[1], output_text=["out"])
    a.setPos(-260, -60)
    b = CaptionNode(scene, title="Convert", caption="rgba", inputs=[1], outputs=[1],
                    input_text=["in"], output_text=["out"])
    b.setPos(0, -60)
    c = CaptionNode(scene, title="Target", caption="out.png", inputs=[1], input_text=["in"])
    c.setPos(260, -60)

    Edge(scene, a.outputs[0], b.inputs[0], label="pixels")
    Edge(scene, b.outputs[0], c.inputs[0], label="mask")
    return scene


def group_nodes(collapsed: bool = False) -> Scene:
    scene = Scene()
    a = CaptionNode(scene, title="Load", caption="data.json", outputs=[1], output_text=["out"])
    a.setPos(-230, -40)
    b = CaptionNode(scene, title="Normalize", caption="0..1", inputs=[1], outputs=[1],
                    input_text=["in"], output_text=["out"])
    b.setPos(0, -40)
    c = CaptionNode(scene, title="Save", caption="clean.json", inputs=[1], input_text=["in"])
    c.setPos(260, -40)
    Edge(scene, a.outputs[0], b.inputs[0])
    Edge(scene, b.outputs[0], c.inputs[0])

    group = Group(scene, title="Preprocess")
    group.addNode(a)
    group.addNode(b)
    group.updateBounds()

    if collapsed:
        group.collapse()
    return scene


def multi_input() -> Scene:
    scene = Scene()
    sources = []
    for index, title in enumerate(("A", "B", "C")):
        node = CaptionNode(scene, title=title, caption=str(index + 1), outputs=[1], output_text=["out"])
        node.setPos(-300, (index - 1) * 140)
        sources.append(node)

    total = SumNode(scene, title="Sum", caption="total", inputs=[1], outputs=[1],
                    input_text=["in"], output_text=["out"])
    total.setPos(120, 0)

    for node in sources:
        Edge(scene, node.outputs[0], total.inputs[0])
    total.updateInputOrderLabels()
    return scene


def graph_algorithms() -> Scene:
    scene = Scene()
    start = CaptionNode(scene, title="Start", caption="source", outputs=[1], output_text=["out"])
    start.setPos(-300, -80)
    middle = CaptionNode(scene, title="Step", caption="step 1", inputs=[1], outputs=[1],
                         input_text=["in"], output_text=["out"])
    middle.setPos(-40, -80)
    other = CaptionNode(scene, title="Detour", caption="long way", inputs=[1], outputs=[1],
                         input_text=["in"], output_text=["out"])
    other.setPos(-40, 100)
    end = CaptionNode(scene, title="End", caption="target", inputs=[1], input_text=["in"])
    end.setPos(220, -80)

    Edge(scene, start.outputs[0], middle.inputs[0])
    Edge(scene, middle.outputs[0], end.inputs[0])
    Edge(scene, start.outputs[0], other.inputs[0])
    Edge(scene, other.outputs[0], end.inputs[0])

    path = shortest_path(scene, start, end)
    if path:
        for _node, edge in path:
            if edge is None or edge.grEdge is None:
                continue
            edge.grEdge.setPen(QPen(QColor("#37A6FF"), 4.0))
    start.setNodeLabel("shortest path")
    start.setNodeLabelVisible(True)
    return scene


def main() -> None:
    app = QApplication([])  # noqa: F841 - Qt needs a living application
    render(quickstart(), "quickstart.png")
    render(socket_shapes(), "socket-shapes.png")
    render(node_labels(), "node-labels.png")
    render(edge_labels(), "edge-labels.png")
    render(group_nodes(), "group-nodes.png")
    render(group_nodes(collapsed=True), "group-collapsed.png")
    render(multi_input(), "multi-input.png")
    render(graph_algorithms(), "graph-algorithms.png")


if __name__ == "__main__":
    main()
