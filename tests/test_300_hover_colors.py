#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test to verify that hover colors are now dynamically updated from the color scheme.

This test verifies that:
1. All graphics items (edges, nodes, sockets) use colors from the color scheme
2. Changing the color scheme updates the graphics items
3. The refresh mechanism properly updates hover colors
"""
import sys
import os
from contextlib import contextmanager

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from qtpy.QtGui import QColor
from qtpy.QtWidgets import QApplication
from nodeeditor.node_scene import Scene
from nodeeditor.node_node import Node
from nodeeditor.node_edge import Edge
from nodeeditor.node_colors_config import get_color_scheme


_app = QApplication.instance() or QApplication([])


@contextmanager
def fresh_scene():
    """Keep color tests isolated from the global scheme and scene objects."""
    scheme = get_color_scheme()
    scheme.reset_to_defaults()
    scene = Scene()
    try:
        yield scene
    finally:
        scene.clear()
        scheme.reset_to_defaults()


def test_hover_colors_from_scheme():
    """Test that graphics items use hover colors from the color scheme"""
    with fresh_scene() as scene:
        node1 = Node(scene, "Node 1", inputs=[1], outputs=[2])
        node2 = Node(scene, "Node 2", inputs=[1], outputs=[2])
        edge = Edge(scene, node1.outputs[0], node2.inputs[0])
        scheme = get_color_scheme()
        initial_edge_hover = edge.grEdge._color_hovered
        initial_node_hover = node1.grNode._color_hovered
        assert initial_edge_hover == scheme.edges.hovered
        assert initial_node_hover == scheme.edges.hovered

        scheme.edges.hovered = "#FFFF0000"  # Red (ARGB)
        scene._refresh_colors()
        assert edge.grEdge._color_hovered != initial_edge_hover
        assert node1.grNode._color_hovered != initial_node_hover
        assert edge.grEdge._color_hovered == scheme.edges.hovered
        assert node1.grNode._color_hovered == scheme.edges.hovered


def test_scene_set_highlight_color():
    """Test that scene.setHighlightColor() updates all hover colors"""
    with fresh_scene() as scene:
        node1 = Node(scene, "Node 1", inputs=[1], outputs=[2])
        node2 = Node(scene, "Node 2", inputs=[1], outputs=[2])
        edge = Edge(scene, node1.outputs[0], node2.inputs[0])
        initial_edge_hover = edge.grEdge._color_hovered
        initial_node_hover = node1.grNode._color_hovered
        initial_socket_highlight = node1.inputs[0].grSocket._color_highlight

        new_color = "#FF00FF00"  # Green
        scene.setHighlightColor(new_color)
        assert edge.grEdge._color_hovered != initial_edge_hover
        assert node1.grNode._color_hovered != initial_node_hover
        assert node1.inputs[0].grSocket._color_highlight != initial_socket_highlight
        assert edge.grEdge._color_hovered == QColor(new_color)
        assert node1.grNode._color_hovered == QColor(new_color)
        assert node1.inputs[0].grSocket._color_highlight == QColor(new_color)


def test_edge_and_socket_color_setters():
    with fresh_scene() as scene:
        source = Node(scene, "Source", inputs=[], outputs=[1])
        target = Node(scene, "Target", inputs=[1], outputs=[])
        edge = Edge(scene, source.outputs[0], target.inputs[0])
        scene.setEdgeColors(default="#123456", selected="#abcdef", dragging="#654321")
        assert edge.grEdge._pen.color() == QColor("#123456")
        assert edge.grEdge._pen_selected.color() == QColor("#abcdef")
        assert edge.grEdge._pen_dragging.color() == QColor("#654321")
        scene.setSocketColors(outline="#abcdef", highlight="#123456")
        scene.setSocketTypeColor(1, "#654321")
        for socket in (source.outputs[0], target.inputs[0]):
            assert socket.grSocket._color_outline == QColor("#abcdef")
            assert socket.grSocket._color_highlight == QColor("#123456")
            assert socket.grSocket._color_background == QColor("#654321")


def test_reset_restores_node_colors():
    with fresh_scene():
        scheme = get_color_scheme()
        selected = scheme.nodes.selected
        scheme.nodes.selected = "#123456"
        scheme.reset_to_defaults()
        assert scheme.nodes.selected == selected
        assert not hasattr(scheme, "groups")


def test_socket_palette_preserves_existing_type_colors():
    from nodeeditor.node_graphics_socket import SOCKET_COLORS

    with fresh_scene():
        colors = get_color_scheme().sockets
        assert colors.get_all_type_colors() == SOCKET_COLORS
        for index, expected in enumerate(SOCKET_COLORS):
            assert colors.get_type_color(index) == expected
        assert colors.get_type_color(None).alpha() == 0


def test_icon_node_color_refresh_preserves_label():
    from nodeeditor.node_icon_graphics_node import QDMIconGraphicsNode

    class IconNode(Node):
        GraphicsNode_class = QDMIconGraphicsNode

    with fresh_scene() as scene:
        node = IconNode(scene, "Icon", inputs=[1], outputs=[2])
        node.setNodeLabel("Icon label", store_history=False)
        scene.setHighlightColor("#123456")
        assert node.grNode._color_hovered == QColor("#123456")
        assert node.getNodeLabel() == "Icon label"


def test_color_refresh_preserves_upstream_groups_and_labels():
    from nodeeditor.node_group import Group
    from nodeeditor.node_group_node import GroupNode

    assert GroupNode is Group
    with fresh_scene() as scene:
        source = Node(scene, "Source", inputs=[], outputs=[1])
        target = Node(scene, "Target", inputs=[1], outputs=[])
        outside = Node(scene, "Outside", inputs=[1], outputs=[])
        source.setPos(-200, 0)
        target.setPos(100, 0)
        outside.setPos(400, 0)
        internal = Edge(scene, source.outputs[0], target.inputs[0])
        external = Edge(scene, source.outputs[0], outside.inputs[0])
        source.setNodeLabel("Source label", store_history=False)
        internal.label = "Internal edge"
        external.label = "External edge"
        group = Group(scene, "Upstream group")
        group.addNode(source)
        group.addNode(target)
        group.updateBounds()
        before = scene.serialize()
        scene.setHighlightColor("#123456")
        assert scene.serialize() == before

        group.collapse()
        assert not source.grNode.isVisible()
        assert not internal.grEdge.isVisible()
        assert external.grEdge.isVisible()
        scene.setHighlightColor("#abcdef")
        assert group.isCollapsed()
        assert not source.grNode.isVisible()
        assert not internal.grEdge.isVisible()
        saved = scene.serialize()
        scene.clear()
        assert scene.deserialize(saved)
        assert len(scene.groups) == 1
        assert len(scene.edges) == 2
        restored_group = scene.groups[0]
        assert restored_group.isCollapsed()
        restored_group.expand()
        assert len(restored_group.child_nodes) == 2
        assert all(node.grNode.isVisible() for node in scene.nodes)
        assert all(edge.grEdge.isVisible() for edge in scene.edges)
        assert {edge.label for edge in scene.edges} == {"Internal edge", "External edge"}
        assert any(node.getNodeLabel() == "Source label" for node in scene.nodes)


def test_color_demo_contains_nodes_and_edge():
    from examples.example_color_config import ColorConfigDemo

    scheme = get_color_scheme()
    scheme.reset_to_defaults()
    demo = ColorConfigDemo()
    try:
        assert len(demo.editor.scene.nodes) == 2
        assert len(demo.editor.scene.edges) == 1
        demo.theme_combo.setCurrentIndex(1)
        assert demo.editor.scene.edges[0].grEdge._color == QColor("#1e1e1e")
    finally:
        demo.editor.scene.clear()
        demo.close()
        scheme.reset_to_defaults()


if __name__ == '__main__':
    try:
        test_hover_colors_from_scheme()
        test_scene_set_highlight_color()
        test_edge_and_socket_color_setters()
        test_reset_restores_node_colors()
        test_socket_palette_preserves_existing_type_colors()
        test_icon_node_color_refresh_preserves_label()
        test_color_refresh_preserves_upstream_groups_and_labels()
        test_color_demo_contains_nodes_and_edge()
        print("\n" + "="*50)
        print("✓ ALL TESTS PASSED - Hover colors are now working!")
        print("="*50)
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
