#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for socket shapes and the socket hover highlight."""

import os
import unittest

# a real QApplication is required to build a Scene, keep it offscreen
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from qtpy.QtCore import QPointF  # noqa: E402
from qtpy.QtWidgets import QApplication  # noqa: E402

from nodeeditor.node_node import Node  # noqa: E402
from nodeeditor.node_scene import Scene  # noqa: E402
from nodeeditor.node_socket_shapes import (  # noqa: E402
    CircleShape,
    SocketShape,
    get_socket_shape,
    register_socket_shape,
)


_app = QApplication.instance() or QApplication([])


class PlainNode(Node):
    """A node that says nothing about shapes."""

    def __init__(self, scene, title="Plain", inputs=None, outputs=None):
        super().__init__(scene, title,
                         inputs=[1] if inputs is None else inputs,
                         outputs=[1] if outputs is None else outputs)


class ShapedNode(Node):
    """Input sockets are squares, output sockets are chevrons."""

    def __init__(self, scene, title="Shaped", inputs=None, outputs=None):
        super().__init__(scene, title,
                         inputs=[1] if inputs is None else inputs,
                         outputs=[1] if outputs is None else outputs)

    def initSettings(self):
        super().initSettings()
        self.input_socket_shapes = {1: "square"}
        self.output_socket_shapes = {1: "chevron"}


class WildcardNode(Node):
    """Every input socket is a triangle, whatever its type."""

    def __init__(self, scene, title="Wildcard", inputs=None, outputs=None):
        super().__init__(scene, title,
                         inputs=[1] if inputs is None else inputs,
                         outputs=[1] if outputs is None else outputs)

    def initSettings(self):
        super().initSettings()
        self.input_socket_shapes = {"*": "triangle"}


class ChevronNode(Node):
    """Chevrons on both sides."""

    def __init__(self, scene, title="Chevron", inputs=None, outputs=None):
        super().__init__(scene, title,
                         inputs=[1] if inputs is None else inputs,
                         outputs=[1] if outputs is None else outputs)

    def initSettings(self):
        super().initSettings()
        self.input_socket_shapes = {1: "chevron"}
        self.output_socket_shapes = {1: "chevron"}


class HexShape(SocketShape):
    """A shape used to test custom registration."""

    def points(self):
        return [(0.0, -1.0), (0.866, 0.5), (-0.866, 0.5)]


class TestSocketShapes(unittest.TestCase):
    """Socket shapes: presets, per-side maps and the registry."""

    def setUp(self):
        self.scene = Scene()

    def tearDown(self):
        self.scene.clear()

    # lookup -----------------------------------------------------------
    def test_unmapped_type_falls_back_to_circle(self):
        node = PlainNode(self.scene, inputs=[7], outputs=[7])
        self.assertEqual(node.inputs[0].shape, "circle")
        self.assertEqual(node.outputs[0].shape, "circle")

    def test_sides_can_use_different_shapes_for_the_same_type(self):
        node = ShapedNode(self.scene)
        self.assertEqual(node.inputs[0].shape, "square")
        self.assertEqual(node.outputs[0].shape, "chevron")

    def test_wildcard_covers_every_unmapped_type(self):
        node = WildcardNode(self.scene, inputs=[7])
        self.assertEqual(node.inputs[0].shape, "triangle")

    def test_specific_type_wins_over_the_wildcard(self):
        class MixedNode(Node):
            def __init__(self, scene, title="Mixed", inputs=None, outputs=None):
                super().__init__(scene, title,
                                 inputs=[1] if inputs is None else inputs,
                                 outputs=[1] if outputs is None else outputs)

            def initSettings(self):
                super().initSettings()
                self.input_socket_shapes = {"*": "triangle", 7: "square"}

        node = MixedNode(self.scene, inputs=[7, 8], outputs=[])
        self.assertEqual(node.inputs[0].shape, "square")
        self.assertEqual(node.inputs[1].shape, "triangle")

    def test_unknown_shape_name_falls_back_to_circle(self):
        node = PlainNode(self.scene)
        node.input_socket_shapes = {1: "does-not-exist"}
        self.assertEqual(
            node.getSocketShapeName(1, True), "circle")

    # registry ---------------------------------------------------------
    def test_registering_a_shape_class(self):
        register_socket_shape("hex", HexShape)
        self.assertIsInstance(get_socket_shape("hex"), HexShape)

    def test_registering_a_callback(self):
        def draw(painter, ctx):
            painter.setBrush(ctx.brush)
            painter.setPen(ctx.pen)
            painter.drawEllipse(-ctx.radius, -ctx.radius,
                                2 * ctx.radius, 2 * ctx.radius)

        register_socket_shape("callback-shape", draw)
        shape = get_socket_shape("callback-shape")
        # a callback cannot describe an outline, so it hits like a circle
        self.assertFalse(shape.path(6).contains(QPointF(5.0, 5.0)))

    def test_unknown_shape_name_resolves_to_the_circle(self):
        self.assertIsInstance(get_socket_shape("nope"), CircleShape)
        self.assertIsInstance(get_socket_shape(None), CircleShape)

    # hit testing ------------------------------------------------------
    def test_circle_leaves_its_corners_out(self):
        node = PlainNode(self.scene)
        path = node.inputs[0].grSocket.shape()
        self.assertTrue(path.contains(QPointF(0, 0)))
        self.assertFalse(path.contains(QPointF(5.0, 5.0)))

    def test_square_covers_its_corners(self):
        node = ShapedNode(self.scene)
        path = node.inputs[0].grSocket.shape()
        self.assertTrue(path.contains(QPointF(5.0, 5.0)))

    def test_bounding_rect_covers_the_shape(self):
        node = ShapedNode(self.scene)
        gr_socket = node.inputs[0].grSocket
        self.assertTrue(gr_socket.boundingRect().contains(gr_socket.shape().boundingRect()))

    # orientation ------------------------------------------------------
    def test_triangle_mirrors_on_inputs(self):
        node = WildcardNode(self.scene, inputs=[1], outputs=[])
        path = node.inputs[0].grSocket.shape()
        # the tip points left, into the node
        self.assertTrue(path.contains(QPointF(-5.0, 0)))
        self.assertFalse(path.contains(QPointF(5.0, 0)))

    def test_chevron_never_mirrors(self):
        node = ChevronNode(self.scene)
        in_path = node.inputs[0].grSocket.shape()
        out_path = node.outputs[0].grSocket.shape()
        # the tip points right on both sides
        self.assertTrue(in_path.contains(QPointF(4.5, 0)))
        self.assertTrue(out_path.contains(QPointF(4.5, 0)))
        self.assertFalse(in_path.contains(QPointF(-4.5, 0)))
        self.assertFalse(out_path.contains(QPointF(-4.5, 0)))

    # type changes -----------------------------------------------------
    def test_shape_follows_the_socket_type(self):
        node = ShapedNode(self.scene)
        socket = node.inputs[0]
        self.assertEqual(socket.shape, "square")
        socket.changeSocketType(2)
        self.assertEqual(socket.shape, "circle")
        socket.changeSocketType(1)
        self.assertEqual(socket.shape, "square")

    # deserialization --------------------------------------------------
    def test_sockets_created_while_deserializing_get_the_shape(self):
        node = ShapedNode(self.scene, "Shaped")
        data = self.scene.serialize()

        other = Scene()
        other.setNodeClassSelector(lambda node_data: ShapedNode)
        other.deserialize(data)

        self.assertEqual(len(other.nodes), 1)
        loaded = other.nodes[0]
        self.assertEqual(loaded.inputs[0].shape, "square")
        self.assertEqual(loaded.outputs[0].shape, "chevron")
        other.clear()

    def test_socket_serialized_keys_are_unchanged(self):
        node = ShapedNode(self.scene)
        self.assertEqual(
            set(node.inputs[0].serialize().keys()),
            {"id", "index", "multi_edges", "position", "socket_type"},
        )


class TestSocketHover(unittest.TestCase):
    """The socket hover highlight."""

    def setUp(self):
        self.scene = Scene()
        self.node = PlainNode(self.scene)

    def tearDown(self):
        self.scene.clear()

    def test_hover_toggles_the_hovered_flag(self):
        gr_socket = self.node.inputs[0].grSocket
        self.assertFalse(gr_socket.hovered)

        gr_socket.hoverEnterEvent(None)
        self.assertTrue(gr_socket.hovered)

        gr_socket.hoverLeaveEvent(None)
        self.assertFalse(gr_socket.hovered)

    def test_hover_does_not_touch_the_snapping_highlight(self):
        gr_socket = self.node.inputs[0].grSocket
        gr_socket.isHighlighted = True

        gr_socket.hoverEnterEvent(None)
        self.assertTrue(gr_socket.isHighlighted)
        self.assertTrue(gr_socket.hovered)

        gr_socket.hoverLeaveEvent(None)
        self.assertTrue(gr_socket.isHighlighted)
        self.assertFalse(gr_socket.hovered)

    def test_the_node_holds_back_its_hover_outline(self):
        # a socket sits inside the node's own hit area, so Qt reports the
        # node as hovered too. The node must not light up its border while
        # one of its own sockets is highlighted.
        gr_socket = self.node.inputs[0].grSocket
        self.assertFalse(self.node.grNode._isSocketHovered())

        gr_socket.hoverEnterEvent(None)
        self.assertTrue(self.node.grNode._isSocketHovered())

        gr_socket.hoverLeaveEvent(None)
        self.assertFalse(self.node.grNode._isSocketHovered())

    def test_a_hovered_socket_holds_back_only_its_own_node(self):
        other = PlainNode(self.scene, "Other")
        gr_socket = self.node.inputs[0].grSocket

        gr_socket.hoverEnterEvent(None)
        self.assertTrue(self.node.grNode._isSocketHovered())
        self.assertFalse(other.grNode._isSocketHovered())

        gr_socket.hoverLeaveEvent(None)
        self.assertFalse(self.node.grNode._isSocketHovered())


if __name__ == "__main__":
    unittest.main()
