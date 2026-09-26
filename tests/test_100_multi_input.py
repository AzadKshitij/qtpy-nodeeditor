#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for ordered multi-edge inputs (`MultiInputNode` / `Edge.input_index`)."""

import os
import unittest

# a real QApplication is required to build a Scene, keep it offscreen
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from qtpy.QtWidgets import QApplication  # noqa: E402

from nodeeditor.node_edge import Edge  # noqa: E402
from nodeeditor.node_multi_input_node import MultiInputNode  # noqa: E402
from nodeeditor.node_node import Node  # noqa: E402
from nodeeditor.node_scene import Scene  # noqa: E402


_app = QApplication.instance() or QApplication([])


class SourceNode(Node):
    """Minimal node producing a fixed value."""

    def __init__(self, scene, value, title=None):
        super().__init__(scene, title or ("Src %s" % value), inputs=[], outputs=[1])
        self.value = value

    def eval(self):
        return self.value


class TestMultiInputNode(unittest.TestCase):
    """Ordered multi-edge input behaviour."""

    def setUp(self):
        self.scene = Scene()
        self.target = MultiInputNode(self.scene, "Sink", inputs=[2], outputs=[1])
        # one input socket, and it must accept many edges
        self.assertEqual(len(self.target.inputs), 1)
        self.assertTrue(self.target.inputs[0].is_multi_edges)

    def tearDown(self):
        self.scene.clear()

    def make_source(self, value, title=None):
        node = SourceNode(self.scene, value, title=title)
        node.setPos(-200, 0)
        return node

    def connect(self, source, index=-1):
        edge = Edge(self.scene, source.outputs[0], self.target.inputs[0],
                    input_index=index)
        # mirror EdgeDragging.edgeDragEnd: a real GUI connection notifies
        # both ends (this is also what triggers eval/dirty-marking)
        self.target.onEdgeConnectionChanged(edge)
        return edge

    # reading -----------------------------------------------------------

    def test_reads_in_order_of_connection(self):
        first = self.connect(self.make_source(1))
        second = self.connect(self.make_source(2))
        third = self.connect(self.make_source(3))

        self.assertEqual(
            [edge.input_index for edge in (first, second, third)], [0, 1, 2])
        self.assertEqual(self.target.getOrderedEdges(), [first, second, third])
        self.assertEqual(self.target.getOrderedValues(), [1, 2, 3])

    def test_explicit_edge_number_on_connect(self):
        first = self.connect(self.make_source(1))
        self.connect(self.make_source(2))
        self.connect(self.make_source(3), index=0)     # insert at the front

        self.assertEqual(self.target.getOrderedValues(), [3, 1, 2])
        self.assertEqual(
            [edge.input_index for edge in self.target.getOrderedEdges()], [0, 1, 2])
        self.assertEqual(self.target.getOrderedEdges()[0].input_index, 0)
        self.assertEqual(first.input_index, 1)

    def test_out_of_range_index_appends(self):
        self.connect(self.make_source(1))
        self.connect(self.make_source(2), index=99)
        self.assertEqual(self.target.getOrderedValues(), [1, 2])

    def test_duplicate_source_keeps_one_entry_per_edge(self):
        source = self.make_source(7)
        self.connect(source)
        self.connect(source)
        self.assertEqual(self.target.getOrderedValues(), [7, 7])
        self.assertEqual(self.target.getOrderedNodes(), [source, source])

    # compaction --------------------------------------------------------

    def test_removal_closes_the_gap(self):
        first = self.connect(self.make_source(1))
        second = self.connect(self.make_source(2))
        third = self.connect(self.make_source(3))

        second.remove()

        self.assertEqual(self.target.getOrderedValues(), [1, 3])
        self.assertEqual(
            [edge.input_index for edge in (first, third)], [0, 1])
        self.assertEqual(second.input_index, -1)   # detached edges forget their slot

    def test_middle_removal_closes_the_gap(self):
        self.connect(self.make_source(1))
        second = self.connect(self.make_source(2))
        self.connect(self.make_source(3))

        second.remove()
        self.assertEqual(self.target.getOrderedValues(), [1, 3])

    def test_reconnect_keeps_read_position(self):
        src1 = self.make_source(1)
        src2 = self.make_source(2)
        self.connect(src1)
        second = self.connect(src2)

        # move the edge's end from the ordered input to an output socket:
        # a read position is only meaningful on inputs, so it is forgotten
        second.reconnect(self.target.inputs[0], src1.outputs[0])
        self.assertEqual(second.input_index, -1)   # now dangling on an output

    # manual ordering ---------------------------------------------------

    def test_move_edge_to(self):
        first = self.connect(self.make_source(1))
        second = self.connect(self.make_source(2))
        third = self.connect(self.make_source(3))

        self.assertTrue(self.target.moveEdgeTo(third, 0))
        self.assertEqual(self.target.getOrderedValues(), [3, 1, 2])
        self.assertEqual(
            [edge.input_index for edge in (third, first, second)], [0, 1, 2])

        self.assertFalse(self.target.moveEdgeTo(third, 3))   # out of range
        self.assertFalse(self.target.moveEdgeTo(third, -1))

    def test_move_edge_by_is_clamped(self):
        first = self.connect(self.make_source(1))
        second = self.connect(self.make_source(2))

        self.assertFalse(self.target.moveEdgeBy(first, -1))
        self.assertTrue(self.target.moveEdgeBy(second, -1))
        self.assertEqual(self.target.getOrderedValues(), [2, 1])
        self.assertEqual(self.target.getOrderedEdges(), [second, first])

    def test_swap_edges(self):
        first = self.connect(self.make_source(1))
        second = self.connect(self.make_source(2))
        third = self.connect(self.make_source(3))

        self.assertTrue(self.target.swapEdges(first, third))
        self.assertEqual(self.target.getOrderedValues(), [3, 2, 1])
        self.assertEqual(self.target.getOrderedEdges(), [third, second, first])
        self.assertFalse(self.target.swapEdges(first, first))

    def test_set_edge_order_partial_list_keeps_the_rest(self):
        first = self.connect(self.make_source(1))
        second = self.connect(self.make_source(2))
        third = self.connect(self.make_source(3))

        self.assertTrue(self.target.setEdgeOrder([third, first]))
        self.assertEqual(self.target.getOrderedEdges(), [third, first, second])

    def test_set_edge_order_by_nodes(self):
        a = self.make_source(1)
        b = self.make_source(2)
        c = self.make_source(3)
        self.connect(a)
        self.connect(b)
        self.connect(c)

        self.assertTrue(self.target.setEdgeOrderByNodes([c, a, b]))
        self.assertEqual(self.target.getOrderedValues(), [3, 1, 2])

    def test_reverse_edge_order(self):
        first = self.connect(self.make_source(1))
        second = self.connect(self.make_source(2))
        self.connect(self.make_source(3))

        self.assertTrue(self.target.reverseEdgeOrder())
        self.assertEqual(self.target.getOrderedEdges()[-1], first)
        self.assertEqual(self.target.getOrderedEdges()[1], second)
        self.assertEqual(self.target.getOrderedValues(), [3, 2, 1])

    def test_direct_input_index_assignment_needs_compaction(self):
        first = self.connect(self.make_source(1))
        second = self.connect(self.make_source(2))

        first.input_index = 5        # raw assignment, as documented
        # stable sort puts `second` (index 1) before `first` (index 5)
        self.assertTrue(self.target.compactEdgeOrder())
        self.assertEqual(
            [edge.input_index for edge in (first, second)], [1, 0])
        self.assertEqual(self.target.getOrderedValues(), [2, 1])
        self.assertFalse(self.target.compactEdgeOrder())   # second call: no change

    def test_describe_input_order(self):
        a = self.make_source(1, title="Alpha")
        self.connect(a)
        self.assertEqual(self.target.describeInputOrder(), "0: Alpha [out 0]")

    # non ordered sockets ----------------------------------------------

    def test_single_edged_input_is_untouched(self):
        scene = Scene()
        try:
            node = Node(scene, "Plain", inputs=[2], outputs=[1])
            self.assertFalse(node.inputs[0].is_multi_edges)

            # NOTE: the single-edge replacement policy lives in the
            # EdgeDragging interaction layer, not in Edge/Socket: direct
            # construction just appends. The ordering machinery must still
            # stay consistent on such sockets.
            edge = Edge(scene, self.make_source(1).outputs[0], node.inputs[0])
            other = Edge(scene, self.make_source(2).outputs[0], node.inputs[0])
            self.assertTrue(node.inputs[0].isConnected(edge))
            self.assertTrue(node.inputs[0].isConnected(other))
            self.assertEqual(
                [e.input_index for e in node.inputs[0].edges], [0, 1])

            # socket-level reorder helpers refuse non-input... and accept inputs:
            # outputs are unordered, inputs are ordered even when single-edged
            self.assertFalse(node.outputs[0].setEdgeOrder([]))
            self.assertFalse(node.outputs[0].compactEdgeOrder())
        finally:
            scene.clear()

    def test_edge_index_lookup(self):
        first = self.connect(self.make_source(1))
        self.connect(self.make_source(2))
        socket = self.target.inputs[0]
        self.assertEqual(socket.edgeIndex(first), 0)
        dangling = Edge(self.scene, None, None)
        try:
            self.assertEqual(socket.edgeIndex(dangling), -1)
        finally:
            dangling.remove(silent=True)

    # persistence -------------------------------------------------------

    def test_input_index_is_serialized(self):
        first = self.connect(self.make_source(1))
        self.connect(self.make_source(2))
        third = self.connect(self.make_source(3))
        self.target.moveEdgeTo(third, 0)

        data = [edge.serialize() for edge in (first, third)]
        self.assertEqual(data[0]['input_index'], 1)
        self.assertEqual(data[1]['input_index'], 0)

    def test_deserialize_restores_order_regardless_of_file_order(self):
        src = [self.make_source(v) for v in (1, 2, 3)]
        edges = [self.connect(s) for s in src]
        self.target.setEdgeOrder([edges[2], edges[0], edges[1]])
        payloads = [edge.serialize() for edge in edges]

        # drop all edges, then re-attach in scrambled file order
        for edge in edges:
            edge.remove(silent=True)
        self.assertEqual(self.target.getOrderedEdges(), [])
        hashmap = {socket.id: socket
                   for node in (self.target, *src)
                   for socket in (node.inputs + node.outputs)}

        restored = []
        for payload in (payloads[1], payloads[2], payloads[0]):
            edge = Edge(self.scene)
            self.assertTrue(edge.deserialize(payload, hashmap))
            restored.append(edge)

        self.assertEqual(
            [edge.input_index for edge in self.target.getOrderedEdges()], [0, 1, 2])
        self.assertEqual(self.target.getOrderedValues(), [3, 1, 2])
        # attached scrambled, read ordered: [payloads[2], payloads[0], payloads[1]]
        self.assertEqual(
            [id(edge) for edge in self.target.getOrderedEdges()],
            [id(restored[1]), id(restored[2]), id(restored[0])])

    def test_deserialize_old_file_without_input_index_appends(self):
        src = self.make_source(1)
        payload = Edge(self.scene, src.outputs[0], self.target.inputs[0]).serialize()
        del payload['input_index']

        edge = Edge(self.scene)
        hashmap = {socket.id: socket
                   for node in (self.target, src)
                   for socket in (node.inputs + node.outputs)}
        self.assertTrue(edge.deserialize(payload, hashmap))
        self.assertEqual(self.target.getOrderedEdges()[-1], edge)

    def test_scene_serialize_roundtrip_preserves_manual_order(self):
        src = [self.make_source(v) for v in (1, 2, 3)]
        edges = [self.connect(s) for s in src]
        self.target.setEdgeOrder([edges[2], edges[0], edges[1]])

        data = self.scene.serialize()
        self.scene.deserialize(data)
        self.assertEqual(
            [edge.input_index for edge in self.target.getOrderedEdges()], [0, 1, 2])
        self.assertEqual(self.target.getOrderedValues(), [3, 1, 2])

    def test_undo_redo_restores_manual_order(self):
        """docs claim the read order survives undo/redo, so pin it down"""
        first = self.connect(self.make_source(1))
        second = self.connect(self.make_source(2))
        third = self.connect(self.make_source(3))
        self.scene.history.storeHistory("Connected inputs")

        self.target.moveEdgeTo(third, 0)
        self.scene.history.storeHistory("Reordered inputs", setModified=True)
        self.assertEqual(self.target.getOrderedValues(), [3, 1, 2])

        self.scene.history.undo()
        self.assertEqual(self.target.getOrderedValues(), [1, 2, 3])
        self.assertEqual(self.target.getOrderedEdges(), [first, second, third])

        self.scene.history.redo()
        self.assertEqual(self.target.getOrderedValues(), [3, 1, 2])
        self.assertEqual(self.target.getOrderedEdges(), [third, first, second])

    # order labels --------------------------------------------------------

    def test_edges_labeled_in_connection_order(self):
        first = self.connect(self.make_source(1))
        second = self.connect(self.make_source(2))
        third = self.connect(self.make_source(3))
        self.assertEqual(
            [edge.getLabel() for edge in (first, second, third)],
            ["#1", "#2", "#3"])

    def test_labels_follow_reorder(self):
        first = self.connect(self.make_source(1))
        second = self.connect(self.make_source(2))
        third = self.connect(self.make_source(3))

        self.target.moveEdgeTo(third, 0)
        self.assertEqual(
            [edge.getLabel() for edge in (third, first, second)],
            ["#1", "#2", "#3"])
        self.assertEqual(
            [edge.getLabel() for edge in self.target.getOrderedEdges()],
            ["#1", "#2", "#3"])

    def test_labels_compact_on_removal_and_detached_edge_cleared(self):
        first = self.connect(self.make_source(1))
        second = self.connect(self.make_source(2))
        third = self.connect(self.make_source(3))

        second.remove()
        self.assertEqual(
            [edge.getLabel() for edge in (first, third)], ["#1", "#2"])
        self.assertEqual(second.getLabel(), "")

    def test_custom_label_preserved_on_disconnect(self):
        first = self.connect(self.make_source(1))
        first.setLabel("my-data")
        first.remove()
        self.assertEqual(first.getLabel(), "my-data")

    def test_labels_opt_out(self):
        self.target.show_input_order_labels = False
        first = self.connect(self.make_source(1))
        self.connect(self.make_source(2))
        self.assertEqual(first.getLabel(), "")
        # re-enabling backfills labels for existing connections
        self.target.show_input_order_labels = True
        self.target.updateInputOrderLabels()
        self.assertEqual(first.getLabel(), "#1")

    def test_labels_survive_serialize_roundtrip(self):
        self.connect(self.make_source(1))
        self.connect(self.make_source(2))
        data = self.scene.serialize()
        self.scene.deserialize(data)
        self.assertEqual(
            [edge.getLabel() for edge in self.target.getOrderedEdges()],
            ["#1", "#2"])


if __name__ == "__main__":
    unittest.main()
