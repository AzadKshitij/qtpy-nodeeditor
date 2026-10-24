#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for canvas comments (:mod:`nodeeditor.node_comment`)."""

import os
import unittest

# a real QApplication is required to build a Scene, keep it offscreen
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from qtpy.QtCore import QEvent, Qt  # noqa: E402
from qtpy.QtGui import QColor, QFocusEvent, QKeyEvent  # noqa: E402
from qtpy.QtWidgets import QApplication  # noqa: E402

from nodeeditor.node_comment import Comment  # noqa: E402
from nodeeditor.node_graphics_view import QDMGraphicsView  # noqa: E402
from nodeeditor.node_scene import Scene  # noqa: E402


_app = QApplication.instance() or QApplication([])


class TestComment(unittest.TestCase):
    """Canvas notes: creation, editing, movement, serialization and removal."""

    def setUp(self):
        self.scene = Scene()

    def tearDown(self):
        self.scene.clear()

    # creation -----------------------------------------------------------

    def test_create_registers_visual_item_with_text_position_and_size(self):
        comment = Comment(
            self.scene, "first line\nsecond line",
            x=12, y=34, width=260, height=120,
        )

        self.assertIn(comment, self.scene.comments)
        self.assertIn(comment, self.scene.grScene.items())
        self.assertIs(comment.scene, self.scene)
        self.assertEqual(comment.text(), "first line\nsecond line")
        self.assertEqual((comment.pos().x(), comment.pos().y()), (12, 34))
        self.assertEqual(
            (comment.rect().width(), comment.rect().height()), (260, 120)
        )
        # a comment is a visual item, not an executable node
        self.assertNotIn(comment, self.scene.nodes)
        self.assertFalse(hasattr(comment, "inputs"))
        self.assertFalse(hasattr(comment, "outputs"))

    def test_scene_add_comment_creates_and_is_idempotent(self):
        note = self.scene.addComment("a note", x=5, y=6)

        self.assertIsInstance(note, Comment)
        self.assertIs(self.scene.getCommentById(note.id), note)
        self.assertEqual(note.text(), "a note")
        self.assertEqual((note.pos().x(), note.pos().y()), (5, 6))

        # registering the same item again does not duplicate it
        self.assertIs(self.scene.addComment(note), note)
        self.assertEqual(self.scene.comments.count(note), 1)

    def test_selected_comments_helper(self):
        note = Comment(self.scene, "select me")
        note.setSelected(True)
        self.assertEqual(self.scene.getSelectedComments(), [note])

    # editing ------------------------------------------------------------

    def test_begin_edit_and_commit_updates_text_and_grows_height(self):
        note = Comment(self.scene, "short", width=180, height=80)
        before = note.rect().height()

        self.assertTrue(note.begin_edit())
        self.assertTrue(note.is_editing())
        note.editor().setPlainText("\n".join("line %d" % i for i in range(20)))
        self.assertTrue(note.finish_edit())

        self.assertFalse(note.is_editing())
        self.assertEqual(note.text().splitlines()[0], "line 0")
        self.assertEqual(len(note.text().splitlines()), 20)
        self.assertGreater(note.rect().height(), before)
        self.assertEqual(
            self.scene.history.history_stack[-1]["desc"], "Edited comment"
        )

    def test_cancel_edit_restores_original_text(self):
        note = Comment(self.scene, "original")

        note.begin_edit()
        note.editor().setPlainText("discard me")
        note.cancel_edit()

        self.assertFalse(note.is_editing())
        self.assertEqual(note.text(), "original")
        self.assertEqual(self.scene.history.history_stack, [])

    def test_focus_out_commits_edit(self):
        note = Comment(self.scene, "before")

        note.begin_edit()
        note.editor().setPlainText("after focus")
        note.editor().focusOutEvent(QFocusEvent(QEvent.Type.FocusOut))

        self.assertFalse(note.is_editing())
        self.assertEqual(note.text(), "after focus")
        self.assertEqual(
            self.scene.history.history_stack[-1]["desc"], "Edited comment"
        )

    def test_escape_cancels_edit(self):
        note = Comment(self.scene, "keep me")

        note.begin_edit()
        note.editor().setPlainText("discard me")
        escape = QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_Escape,
            Qt.KeyboardModifier.NoModifier,
        )
        note.editor().keyPressEvent(escape)

        self.assertFalse(note.is_editing())
        self.assertEqual(note.text(), "keep me")
        self.assertEqual(self.scene.history.history_stack, [])

    def test_set_text_programmatically(self):
        note = Comment(self.scene, "old")
        self.assertTrue(note.setText("new\nbody"))
        self.assertEqual(note.text(), "new\nbody")
        self.assertFalse(note.setText("new\nbody"))

    def test_text_edit_is_undoable_through_scene_history(self):
        note = Comment(self.scene, "first")
        self.scene.history.storeHistory("Baseline")

        note.setText("second", store_history=True)
        self.assertEqual(note.text(), "second")

        self.scene.history.undo()
        self.assertEqual(note.text(), "first")

        self.scene.history.redo()
        self.assertEqual(note.text(), "second")

    # movement -----------------------------------------------------------

    def test_move_updates_scene_position_and_serializes(self):
        note = Comment(self.scene, "movable")
        note.setPos(150, -40)

        self.assertEqual((note.pos().x(), note.pos().y()), (150, -40))
        payload = self.scene.serialize()["comments"][0]
        self.assertEqual((payload["x"], payload["y"]), (150, -40))

    # serialization ------------------------------------------------------

    def test_serialize_deserialize_round_trip(self):
        note = Comment(
            self.scene, "remember\nthe milk",
            x=40, y=25, width=300, height=150,
        )
        note.setZValue(7.5)
        note.setBackgroundColor("#ffeeaa")
        note.setBorderColor((10, 20, 30))
        note.setTextColor("#112233")

        data = self.scene.serialize()
        self.assertEqual(len(data["comments"]), 1)
        payload = data["comments"][0]
        self.assertEqual(payload["type"], "Comment")
        self.assertEqual(payload["version"], 1)

        restored = Scene()
        try:
            self.assertTrue(restored.deserialize(data))
            self.assertEqual(len(restored.comments), 1)
            copy = restored.comments[0]
            self.assertEqual(copy.text(), "remember\nthe milk")
            self.assertEqual((copy.pos().x(), copy.pos().y()), (40, 25))
            self.assertEqual(
                (copy.rect().width(), copy.rect().height()), (300, 150)
            )
            self.assertEqual(copy.zValue(), 7.5)
            self.assertEqual(copy.backgroundColor(), QColor("#ffeeaa"))
            self.assertEqual(copy.borderColor(), QColor(10, 20, 30))
            self.assertEqual(copy.textColor(), QColor("#112233"))
        finally:
            restored.clear()

    def test_missing_style_loads_neutral_defaults(self):
        note = Comment(self.scene, "before")
        note.setColors(
            background="#000000",
            border="#ff0000",
            text="#00ff00",
        )

        self.assertTrue(note.deserialize({"id": note.id, "text": "minimal"}))

        self.assertEqual(
            note.backgroundColor().getRgb(), Comment.DEFAULT_BACKGROUND
        )
        self.assertEqual(note.borderColor().getRgb(), Comment.DEFAULT_BORDER)
        self.assertEqual(note.textColor().getRgb(), Comment.DEFAULT_TEXT)

    def test_old_scene_without_comments_loads_and_drops_stale_notes(self):
        stale = Comment(self.scene, "stale")
        old_data = {
            "id": 42,
            "nodes": [],
            "edges": [],
            "groups": [],
        }

        self.assertTrue(self.scene.deserialize(old_data))

        self.assertEqual(self.scene.comments, [])
        self.assertNotIn(stale, self.scene.grScene.items())

    # removal ------------------------------------------------------------

    def test_delete_key_removes_selected_comment(self):
        note = Comment(self.scene, "delete me")
        view = QDMGraphicsView(self.scene.grScene)
        try:
            note.setSelected(True)
            self.assertEqual(self.scene.getSelectedComments(), [note])

            view.deleteSelected()

            self.assertNotIn(note, self.scene.comments)
            self.assertNotIn(note, self.scene.grScene.items())
            self.assertEqual(
                self.scene.history.history_stack[-1]["desc"],
                "Delete selected",
            )
        finally:
            view.deleteLater()

    def test_remove_detaches_comment(self):
        note = Comment(self.scene, "remove me")
        note.remove()

        self.assertNotIn(note, self.scene.comments)
        self.assertNotIn(note, self.scene.grScene.items())

    # size and order -----------------------------------------------------

    def test_minimum_size_is_enforced(self):
        note = Comment(self.scene, "", width=5, height=5)
        self.assertEqual(note.rect().width(), Comment.MIN_WIDTH)
        self.assertEqual(note.rect().height(), Comment.MIN_HEIGHT)

        note.setSize(1, 1)
        self.assertEqual(note.rect().width(), Comment.MIN_WIDTH)
        self.assertEqual(note.rect().height(), Comment.MIN_HEIGHT)

    def test_long_text_grows_past_minimum_height(self):
        note = Comment(self.scene, "word " * 300, width=180, height=1)
        self.assertEqual(note.rect().width(), 180)
        self.assertGreater(note.rect().height(), Comment.MIN_HEIGHT)

    def test_bring_to_front_send_to_back_and_reset(self):
        other = Comment(self.scene, "other")
        other.setZValue(10)
        note = Comment(self.scene, "me")

        note.bringToFront()
        self.assertGreater(note.zValue(), other.zValue())

        note.sendToBack()
        self.assertLess(note.zValue(), other.zValue())

        note.resetZValue()
        self.assertEqual(note.zValue(), Comment.DEFAULT_Z_VALUE)


if __name__ == "__main__":
    unittest.main()
