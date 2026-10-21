#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the native graph algorithms in :mod:`nodeeditor.node_graph`."""

import os
import unittest

# a real QApplication is required to build a Scene, keep it offscreen
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from qtpy.QtWidgets import QApplication  # noqa: E402

from nodeeditor.node_edge import Edge  # noqa: E402
from nodeeditor.node_graph import GraphCycleError  # noqa: E402
from nodeeditor.node_node import Node  # noqa: E402
from nodeeditor.node_scene import Scene  # noqa: E402


_app = QApplication.instance() or QApplication([])


class CountingNode(Node):
    """A node that remembers how often it was marked dirty."""

    def __init__(self, scene, title="Node", inputs=1, outputs=1):
        super().__init__(scene, title,
                         inputs=[1] * inputs, outputs=[1] * outputs)
        self.dirty_calls = 0

    def onMarkedDirty(self):
        self.dirty_calls += 1


class TestGraphAlgorithms(unittest.TestCase):
    """Reachability, ordering, components, cycles and paths."""

    def setUp(self):
        self.scene = Scene()

    def tearDown(self):
        self.scene.clear()

    # helpers -----------------------------------------------------------

    def make_node(self, title, inputs=1, outputs=1):
        return Node(self.scene, title,
                    inputs=[1] * inputs, outputs=[1] * outputs)

    def connect(self, source, target, source_socket=0, target_socket=0):
        return Edge(self.scene,
                    source.outputs[source_socket], target.inputs[target_socket])

    # ordering ----------------------------------------------------------

    def test_topological_order_respects_dependencies(self):
        a = self.make_node("A")
        b = self.make_node("B")
        c = self.make_node("C")
        self.connect(a, b)
        self.connect(b, c)

        order = self.scene.topological_order()
        self.assertEqual(order.index(a), 0)
        self.assertEqual(order.index(b), 1)
        self.assertEqual(order.index(c), 2)

    def test_topological_order_keeps_independent_nodes_in_scene_order(self):
        nodes = [self.make_node("N%d" % i) for i in range(5)]
        # a chain through the last two, so they must move to the end
        self.connect(nodes[3], nodes[4])

        order = self.scene.topological_order()
        titles = [node.title for node in order]
        self.assertEqual(titles[:3], ["N0", "N1", "N2"])
        self.assertEqual(titles[3:], ["N3", "N4"])

    def test_topological_order_is_reproducible(self):
        a = self.make_node("A")
        b = self.make_node("B")
        c = self.make_node("C")
        self.connect(a, b)
        self.connect(a, c)

        first = [node.title for node in self.scene.topological_order()]
        second = [node.title for node in self.scene.topological_order()]
        self.assertEqual(first, second)

    def test_topological_order_raises_on_cycle(self):
        a = self.make_node("A")
        b = self.make_node("B")
        self.connect(a, b)
        self.connect(b, a)

        with self.assertRaises(GraphCycleError) as caught:
            self.scene.topological_order()
        self.assertEqual(len(caught.exception.cycles), 1)

    def test_topological_order_includes_isolated_nodes(self):
        a = self.make_node("A")
        self.assertEqual(self.scene.topological_order(), [a])

    # reachability ------------------------------------------------------

    def test_descendants_and_ancestors(self):
        a = self.make_node("A")
        b = self.make_node("B")
        c = self.make_node("C")
        self.connect(a, b)
        self.connect(b, c)

        self.assertEqual(self.scene.descendants(a), [b, c])
        self.assertEqual(self.scene.descendants(c), [])
        self.assertEqual(self.scene.ancestors(c), [b, a])
        self.assertEqual(self.scene.ancestors(a), [])

    def test_descendants_lists_a_node_once_across_diamonds(self):
        a = self.make_node("A")
        b = self.make_node("B")
        c = self.make_node("C")
        d = self.make_node("D")
        self.connect(a, b)
        self.connect(a, c)
        self.connect(b, d)
        self.connect(c, d)

        found = self.scene.descendants(a)
        self.assertEqual(len(found), 3)
        self.assertEqual(found.count(d), 1)

    def test_descendants_ignores_edges_pointing_the_other_way(self):
        a = self.make_node("A")
        b = self.make_node("B")
        self.connect(a, b)
        # A must not appear among its own downstream nodes
        self.assertNotIn(a, self.scene.descendants(a))
        self.assertNotIn(b, self.scene.ancestors(a))

    # components --------------------------------------------------------

    def test_components_finds_disconnected_flocks(self):
        a = self.make_node("A")
        b = self.make_node("B")
        c = self.make_node("C")
        d = self.make_node("D")
        self.connect(a, b)
        self.connect(c, d)

        groups = self.scene.components()
        self.assertEqual(len(groups), 2)
        self.assertEqual([node.title for node in groups[0]], ["A", "B"])
        self.assertEqual([node.title for node in groups[1]], ["C", "D"])

    def test_components_treats_an_isolated_node_as_its_own(self):
        a = self.make_node("A")
        b = self.make_node("B")
        c = self.make_node("C")
        self.connect(a, b)

        groups = self.scene.components()
        self.assertEqual(len(groups), 2)
        self.assertEqual([node.title for node in groups[0]], ["A", "B"])
        self.assertEqual([node.title for node in groups[1]], ["C"])

    def test_components_ignores_direction(self):
        a = self.make_node("A")
        b = self.make_node("B")
        self.connect(a, b)

        groups = self.scene.components()
        self.assertEqual(len(groups), 1)
        self.assertEqual([node.title for node in groups[0]], ["A", "B"])

    # cycles ------------------------------------------------------------

    def test_cycles_empty_for_a_dag(self):
        a = self.make_node("A")
        b = self.make_node("B")
        self.connect(a, b)
        self.assertEqual(self.scene.cycles(), [])

    def test_cycles_finds_a_loop(self):
        a = self.make_node("A")
        b = self.make_node("B")
        c = self.make_node("C")
        self.connect(a, b)
        self.connect(b, c)
        self.connect(c, a)

        found = self.scene.cycles()
        self.assertEqual(len(found), 1)
        self.assertEqual(len(found[0]), 3)
        # the edges of the cycle are the three we made
        self.assertEqual(sorted(edge.id for edge in found[0]),
                         sorted(edge.id for edge in self.scene.edges))

    def test_cycles_finds_a_self_loop(self):
        a = self.make_node("A", inputs=1, outputs=1)
        edge = Edge(self.scene, a.outputs[0], a.inputs[0])

        found = self.scene.cycles()
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0], [edge])

    def test_cycles_finds_two_separate_loops(self):
        a = self.make_node("A")
        b = self.make_node("B")
        c = self.make_node("C")
        d = self.make_node("D")
        self.connect(a, b)
        self.connect(b, a)
        self.connect(c, d)
        self.connect(d, c)

        self.assertEqual(len(self.scene.cycles()), 2)

    # paths -------------------------------------------------------------

    def test_paths_enumerates_every_route(self):
        a = self.make_node("A")
        b = self.make_node("B")
        c = self.make_node("C")
        d = self.make_node("D")
        self.connect(a, b)
        self.connect(b, c)
        self.connect(c, d)
        self.connect(a, d)

        found = self.scene.paths(a, d)
        self.assertEqual(len(found), 2)
        for path in found:
            self.assertEqual(path[0][0], a)
            self.assertIsNone(path[0][1])
            self.assertEqual(path[-1][0], d)

    def test_paths_keeps_parallel_edges_apart(self):
        a = self.make_node("A")
        b = self.make_node("B")
        first = self.connect(a, b)
        second = self.connect(a, b)

        found = self.scene.paths(a, b)
        self.assertEqual(len(found), 2)
        # the edge of the last step is the one that reached b
        used = sorted(path[-1][1].id for path in found)
        self.assertEqual(used, sorted([first.id, second.id]))

    def test_paths_empty_when_unreachable(self):
        a = self.make_node("A")
        b = self.make_node("B")
        self.assertEqual(self.scene.paths(a, b), [])

    def test_shortest_path_picks_the_fewest_edges(self):
        a = self.make_node("A")
        b = self.make_node("B")
        c = self.make_node("C")
        d = self.make_node("D")
        self.connect(a, b)
        self.connect(b, c)
        self.connect(c, d)
        self.connect(a, d)

        path = self.scene.shortest_path(a, d)
        self.assertEqual([node.title for node, _edge in path], ["A", "D"])

    def test_shortest_path_none_when_unreachable(self):
        a = self.make_node("A")
        b = self.make_node("B")
        self.assertIsNone(self.scene.shortest_path(a, b))

    # dirty marking -----------------------------------------------------

    def test_mark_descendants_dirty_marks_the_downstream_nodes(self):
        a = CountingNode(self.scene, "A")
        b = CountingNode(self.scene, "B")
        c = CountingNode(self.scene, "C")
        self.connect(a, b)
        self.connect(b, c)

        a.markDescendantsDirty()
        self.assertEqual(b.dirty_calls, 1)
        self.assertEqual(c.dirty_calls, 1)

    def test_mark_descendants_dirty_survives_a_cycle(self):
        a = CountingNode(self.scene, "A")
        b = CountingNode(self.scene, "B")
        self.connect(a, b)
        self.connect(b, a)

        # used to raise RecursionError
        a.markDescendantsDirty()
        self.assertEqual(b.dirty_calls, 1)

    def test_mark_descendants_dirty_survives_a_deep_chain(self):
        # longer than the interpreter's recursion limit
        chain = [CountingNode(self.scene, "N%d" % i) for i in range(1200)]
        for index in range(len(chain) - 1):
            self.connect(chain[index], chain[index + 1])

        # used to raise RecursionError
        chain[0].markDescendantsDirty()
        self.assertEqual(chain[-1].dirty_calls, 1)

    def test_mark_descendants_dirty_visits_each_node_once(self):
        # a diamond: the old recursive walk re-descended once per path
        a = CountingNode(self.scene, "A")
        b = CountingNode(self.scene, "B")
        c = CountingNode(self.scene, "C")
        d = CountingNode(self.scene, "D")
        self.connect(a, b)
        self.connect(a, c)
        self.connect(b, d)
        self.connect(c, d)

        a.markDescendantsDirty()
        self.assertEqual(b.dirty_calls, 1)
        self.assertEqual(c.dirty_calls, 1)
        self.assertEqual(d.dirty_calls, 1)

    def test_mark_descendants_invalid_survives_a_cycle(self):
        a = CountingNode(self.scene, "A")
        b = CountingNode(self.scene, "B")
        self.connect(a, b)
        self.connect(b, a)

        a.markDescendantsInvalid()
        self.assertTrue(b.isInvalid())


if __name__ == "__main__":
    unittest.main()
