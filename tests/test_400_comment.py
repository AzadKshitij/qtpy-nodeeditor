#!/usr/bin/env python

"""Tests for the reusable canvas Comment item."""

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from qtpy.QtWidgets import QApplication

from nodeeditor.node_comment import Comment
from nodeeditor.node_scene import Scene

_app = QApplication.instance() or QApplication([])


class TestComment(unittest.TestCase):
    """Create, edit, serialize, restore and remove a canvas note."""

    def setUp(self):
        self.scene = Scene()

    def tearDown(self):
        self.scene.clear()

    def test_create_registers_and_sets_text_position(self):
        comment = self.scene.addComment("hello\nworld", x=12, y=34, width=200)
        self.assertIsInstance(comment, Comment)
        self.assertIn(comment, self.scene.comments)
        self.assertIn(comment, self.scene.grScene.items())
        self.assertEqual(comment.text(), "hello\nworld")
        self.assertEqual((comment.pos().x(), comment.pos().y()), (12.0, 34.0))
        self.assertGreaterEqual(comment.rect().width(), Comment.MIN_WIDTH)

    def test_inline_edit_commits_and_cancel_restores(self):
        comment = self.scene.addComment("before")
        self.assertTrue(comment.begin_edit())
        comment.editor().setPlainText("after")
        self.assertTrue(comment.finish_edit())
        self.assertEqual(comment.text(), "after")
        self.assertFalse(comment.is_editing())

        self.assertTrue(comment.begin_edit())
        comment.editor().setPlainText("discard me")
        comment.cancel_edit()
        self.assertEqual(comment.text(), "after")

    def test_serialize_round_trip(self):
        comment = self.scene.addComment("note", x=5, y=6, width=210, height=90)
        comment.setBackgroundColor((10, 20, 30, 200))
        comment.bringToFront()
        data = self.scene.serialize()
        self.assertEqual(data["comments"][0]["type"], "Comment")

        restored = Scene()
        try:
            self.assertTrue(restored.deserialize(data))
            self.assertEqual(len(restored.comments), 1)
            copy = restored.comments[0]
            self.assertEqual(copy.text(), "note")
            self.assertEqual((copy.pos().x(), copy.pos().y()), (5.0, 6.0))
            self.assertEqual(copy.backgroundColor().getRgb(), (10, 20, 30, 200))
            self.assertEqual(copy.zValue(), comment.zValue())
        finally:
            restored.clear()

    def test_old_scene_without_comments_still_loads(self):
        old = {"id": 1, "nodes": [], "edges": [], "groups": []}
        self.assertTrue(self.scene.deserialize(old))
        self.assertEqual(self.scene.comments, [])

    def test_remove_drops_item_and_list_entry(self):
        comment = self.scene.addComment("bye")
        comment.remove()
        self.assertNotIn(comment, self.scene.comments)
        self.assertNotIn(comment, self.scene.grScene.items())

    def test_minimum_size_is_enforced(self):
        comment = Comment(self.scene, "x", width=1, height=1)
        self.assertGreaterEqual(comment.rect().width(), Comment.MIN_WIDTH)
        self.assertGreaterEqual(comment.rect().height(), Comment.MIN_HEIGHT)
        comment.setSize(1, 1)
        self.assertGreaterEqual(comment.rect().width(), Comment.MIN_WIDTH)

    def test_history_undo_redo_restores_text(self):
        comment = self.scene.addComment("first")
        self.scene.history.storeHistory("Baseline")
        comment.setText("second", store_history=True)
        self.assertEqual(comment.text(), "second")
        self.scene.history.undo()
        self.assertEqual(comment.text(), "first")
        self.scene.history.redo()
        self.assertEqual(comment.text(), "second")
