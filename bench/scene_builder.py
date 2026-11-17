"""Deterministic scenes for the performance harness.

Everything here is built the normal public way (``Scene``, ``Node``,
``Edge``), so the harness measures the same code an application runs. The
layout is fixed: a grid of ``count`` nodes with one edge per consecutive
pair, which gives a reproducible item count and a reproducible visible
subset at each zoom level.
"""

import os

# Must happen before the first QApplication is created.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_SCALE_FACTOR", "1")
os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "0")

from typing import List, Tuple  # noqa: E402

from qtpy.QtWidgets import QApplication  # noqa: E402

from nodeeditor.node_edge import Edge  # noqa: E402
from nodeeditor.node_node import Node  # noqa: E402
from nodeeditor.node_scene import Scene  # noqa: E402


_APP = None


def app() -> QApplication:
    """The one offscreen ``QApplication`` for this process."""
    global _APP
    if _APP is None:
        _APP = QApplication.instance() or QApplication([])
    return _APP


def build_scene(
    count: int = 300,
    columns: int = 10,
    spacing_x: int = 260,
    spacing_y: int = 320,
) -> Tuple[Scene, List[Node]]:
    """A ``count``-node grid with ``count - 1`` edges chaining the nodes."""
    app()
    scene = Scene()
    nodes = [
        Node(scene, "Node %d" % index, inputs=[1, 1], outputs=[1, 1])
        for index in range(count)
    ]
    for index, node in enumerate(nodes):
        node.setPos((index % columns) * spacing_x, (index // columns) * spacing_y)
    for index in range(count - 1):
        Edge(scene, nodes[index].outputs[0], nodes[index + 1].inputs[0])
    return scene, nodes
