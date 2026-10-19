#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the per-element detail policy (`QDMGraphicsScene.set_detail_policy`).

The scene resolves a policy into one on/off map per element, so a node's
content, its sockets and its floating label can be dropped independently of
each other, and an application can register an element of its own.
"""

import os
import unittest

# a real QApplication is required to build a Scene, keep it offscreen
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from qtpy.QtWidgets import QApplication  # noqa: E402

from nodeeditor.node_node import Node  # noqa: E402
from nodeeditor.node_scene import Scene  # noqa: E402


_app = QApplication.instance() or QApplication([])


class DetailPolicyNode(Node):
    """A node with a socket and a floating label to observe."""

    def __init__(self, scene):
        super().__init__(scene, "Policy", inputs=[1], outputs=[1])
        self.setNodeLabel("policy")


class TestDetailPolicy(unittest.TestCase):
    """Per-element detail behaviour."""

    def setUp(self):
        self.scene = Scene()
        self.node = DetailPolicyNode(self.scene)
        self.gr_scene = self.scene.grScene
        self.socket = self.node.inputs[0].grSocket

    def tearDown(self):
        self.scene.clear()

    def label_visible(self):
        return self.node.grNode.label_item.isVisible()

    def test_auto_follows_the_zoom(self):
        self.assertTrue(self.gr_scene.updateDetailLod(0.2))
        self.assertFalse(self.socket.isVisible())
        self.assertFalse(self.label_visible())

    def test_always_survives_the_flip(self):
        self.gr_scene.set_detail_policy({"sockets": "always", "label": "always"})
        self.gr_scene.updateDetailLod(0.2)
        self.assertTrue(self.socket.isVisible())
        self.assertTrue(self.label_visible())

    def test_never_stays_hidden_at_full_zoom(self):
        self.gr_scene.set_detail_policy({"sockets": "never"})
        self.assertFalse(self.socket.isVisible())
        self.gr_scene.updateDetailLod(1.0)
        self.assertFalse(self.socket.isVisible())

    def test_an_element_without_a_policy_follows_the_zoom(self):
        self.gr_scene.set_detail_policy({"sockets": "always"})
        self.gr_scene.updateDetailLod(0.2)
        self.assertTrue(self.socket.isVisible())
        self.assertFalse(self.label_visible())

    def test_the_threshold_moves_the_flip_point(self):
        self.gr_scene.detail_lod_threshold = 0.2
        self.assertFalse(self.gr_scene.updateDetailLod(0.3))
        self.assertTrue(self.socket.isVisible())
        self.assertTrue(self.gr_scene.updateDetailLod(0.1))
        self.assertFalse(self.socket.isVisible())

    def test_an_unknown_mode_is_ignored(self):
        self.gr_scene.set_detail_policy({"sockets": "sometimes"})
        self.assertEqual(self.gr_scene.detail_policy["sockets"], "auto")
        self.gr_scene.updateDetailLod(0.2)
        self.assertFalse(self.socket.isVisible())

    def test_the_legacy_entry_point_still_hides_everything(self):
        self.node.grNode.setDetailVisible(False)
        self.assertFalse(self.socket.isVisible())
        self.assertFalse(self.label_visible())

    def test_an_application_can_register_its_own_element(self):
        self.gr_scene.set_detail_policy({"badge": "always"})
        self.gr_scene.updateDetailLod(0.2)
        self.assertTrue(self.gr_scene.detail_enabled("badge"))
        self.gr_scene.set_detail_policy({"badge": "never"})
        self.assertFalse(self.gr_scene.detail_enabled("badge"))
