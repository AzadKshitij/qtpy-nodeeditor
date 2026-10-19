#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example demonstrating the Socket Shape feature in qtpy-nodeeditor

This example shows how to:
1. Pick a socket shape per socket type, per side of a node
2. Register a custom socket shape of your own
3. See the socket hover highlight

Run it with::

    python examples/example_socket_shapes.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from qtpy.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QLabel, QGroupBox
)
from qtpy.QtCore import Qt, QRectF

from nodeeditor.node_edge import Edge
from nodeeditor.node_editor_widget import NodeEditorWidget
from nodeeditor.node_node import Node
from nodeeditor.node_socket_shapes import (
    SocketShape,
    register_socket_shape,
)


# ---------------------------------------------------------------------------
# a custom shape, drawn by the application
# ---------------------------------------------------------------------------


class HexagonShape(SocketShape):
    """A hexagon.

    A shape describes its outline as points normalized against the socket
    radius. The hit area follows the outline, so a click outside the hexagon
    misses the socket.
    """

    def points(self):
        return [
            (math.cos(math.radians(60 * i)),
             math.sin(math.radians(60 * i)))
            for i in range(6)
        ]


def draw_pill(painter, ctx):
    """A shape drawn by a plain callback.

    A callback only knows how to draw, so its hit area falls back to the
    circle.
    """
    painter.setBrush(ctx.brush)
    painter.setPen(ctx.pen)
    painter.drawRoundedRect(
        QRectF(-ctx.radius, -ctx.radius * 0.6,
               2 * ctx.radius, 2 * ctx.radius * 0.6),
        ctx.radius * 0.6, ctx.radius * 0.6
    )


register_socket_shape("hexagon", HexagonShape())
register_socket_shape("pill", draw_pill)


# ---------------------------------------------------------------------------
# nodes using the shapes
# ---------------------------------------------------------------------------


class ShapedNode(Node):
    """A node whose sockets declare their shapes per side."""

    #: shape of this node's input sockets, by socket type
    input_shape = "circle"
    #: shape of this node's output sockets, by socket type
    output_shape = "circle"

    def initSettings(self):
        super().initSettings()
        self.input_socket_shapes = {1: self.input_shape}
        self.output_socket_shapes = {1: self.output_shape}


class CircleNode(ShapedNode):
    input_shape = "circle"
    output_shape = "circle"


class SquareNode(ShapedNode):
    input_shape = "square"
    output_shape = "square"


class TriangleNode(ShapedNode):
    input_shape = "triangle"
    output_shape = "triangle"


class ChevronNode(ShapedNode):
    input_shape = "chevron"
    output_shape = "chevron"


class HexagonNode(ShapedNode):
    input_shape = "hexagon"
    output_shape = "hexagon"


class PillNode(ShapedNode):
    input_shape = "pill"
    output_shape = "pill"


class MixedNode(Node):
    """Two socket types, two shapes, on the same side."""

    def initSettings(self):
        super().initSettings()
        self.input_socket_shapes = {1: "triangle", 2: "square"}
        self.output_socket_shapes = {1: "chevron"}


NODE_TYPES = [
    (CircleNode, "Circle"),
    (SquareNode, "Square"),
    (TriangleNode, "Triangle"),
    (ChevronNode, "Chevron"),
    (HexagonNode, "Hexagon (custom class)"),
    (PillNode, "Pill (custom callback)"),
]


class SocketShapesDemo(QMainWindow):
    """Main window demonstrating the socket shapes"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Node Editor - Socket Shapes Demo')
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout(central_widget)

        self.editor = NodeEditorWidget()
        layout.addWidget(self.editor, 1)

        layout.addWidget(self._create_control_panel())

        self._create_demo_nodes()

    def _create_control_panel(self) -> QGroupBox:
        """Create the control panel"""
        panel = QGroupBox('Socket Shapes')
        panel_layout = QVBoxLayout()

        info = QLabel(
            'Hover a socket to see the highlight.\n\n'
            'Shapes are declared by the node in code,\n'
            'one map per side, keyed by socket type.'
        )
        info.setWordWrap(True)
        panel_layout.addWidget(info)

        for node_class, label in NODE_TYPES:
            button = QPushButton(label)
            button.clicked.connect(
                lambda _checked=False, cls=node_class, text=label:
                self._add_node(cls, text))
            panel_layout.addWidget(button)

        panel_layout.addStretch()
        panel.setLayout(panel_layout)
        return panel

    def _add_node(self, node_class, title, pos=None, inputs=(1,), outputs=(1,)):
        """Add a node of the given type to the scene"""
        node = node_class(self.editor.scene, title,
                          inputs=list(inputs), outputs=list(outputs))
        if pos is None:
            pos = (100 + 40 * len(self.editor.scene.nodes), 100)
        node.setPos(*pos)
        return node

    def _create_demo_nodes(self):
        """Create a small graph showing every shape"""
        scene = self.editor.scene

        source = self._add_node(ChevronNode, "Chevron in / out",
                                (-340, -120), inputs=(), outputs=(1,))
        square = self._add_node(SquareNode, "Squares", (-60, -300))
        hexagon = self._add_node(HexagonNode, "Custom hexagon", (-60, -40))
        pill = self._add_node(PillNode, "Custom callback", (-60, 220))
        mixed = self._add_node(MixedNode, "Two types, two shapes",
                               (-60, 460), inputs=(1, 2))
        target = self._add_node(TriangleNode, "Triangles", (280, -120),
                                inputs=(1, 1, 1))

        for node in (square, hexagon, pill):
            Edge(scene, source.outputs[0], node.inputs[0])
        Edge(scene, square.outputs[0], target.inputs[0])
        Edge(scene, hexagon.outputs[0], target.inputs[1])
        Edge(scene, pill.outputs[0], target.inputs[2])
        Edge(scene, source.outputs[0], mixed.inputs[0])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SocketShapesDemo()
    window.show()
    sys.exit(app.exec_())
