#!/usr/bin/env python

"""Label geometry: every item declares the plate it paints.

A label paints a rounded plate padded by 6x3 px around its text, and a node
paints that label above its body. Both items declared less than they drew. Qt
repaints a moved item by the rectangle it declared at the old position and
dirties its children only at the new one, so the old plate was never cleared:
dragging a node left a stack of label plates behind it.
"""

import os
import unittest

# a real QApplication is required to build a Scene, keep it offscreen
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from qtpy.QtCore import QPointF, QRectF
from qtpy.QtWidgets import QApplication, QGraphicsView

from nodeeditor.node_node import Node
from nodeeditor.node_scene import Scene

_app = QApplication.instance() or QApplication([])


class LabelledNode(Node):
    """A node with a floating label, visible."""

    def __init__(self, scene):
        super().__init__(scene, "Label")
        self.setNodeLabel("Formula")


def plate_rect(label):
    """The box the label paints, in the label's own coordinates."""
    return label.textRect().adjusted(
        -label._pad_x, -label._pad_y, label._pad_x, label._pad_y
    )


class TestLabelGeometry(unittest.TestCase):
    """The label plate is drawn inside a declared rectangle."""

    def setUp(self):
        self.scene = Scene()
        self.node = LabelledNode(self.scene)
        self.gr_node = self.node.grNode
        self.label = self.gr_node.label_item

    def tearDown(self):
        self.scene.clear()

    def test_the_label_declares_the_plate_it_paints(self):
        """The regression itself: the plate is padded beyond the text."""
        self.assertGreater(plate_rect(self.label).width(), self.label.textRect().width())
        self.assertGreater(
            plate_rect(self.label).height(), self.label.textRect().height()
        )
        self.assertTrue(self.label.boundingRect().contains(plate_rect(self.label)))

    def test_the_text_rectangle_stays_available_for_positioning(self):
        """Callers centre the text, so the padded box must not replace it."""
        self.assertLessEqual(self.label.textRect().width(), self.label.boundingRect().width())

    def test_the_node_declares_the_label_above_it(self):
        self.assertTrue(self.gr_node.isLabelVisible())
        self.assertTrue(self.gr_node.boundingRect().contains(self.gr_node.labelRect()))
        self.assertLess(self.gr_node.labelRect().top(), 0.0)
        self.assertLess(self.gr_node.boundingRect().top(), 0.0)

    def test_a_hidden_label_leaves_the_body_alone(self):
        self.gr_node.setLabelVisible(False)
        self.assertEqual(
            self.gr_node.boundingRect(),
            QRectF(0.0, 0.0, self.gr_node.width, self.gr_node.height).normalized(),
        )

    def test_an_empty_label_is_not_declared(self):
        self.gr_node.setLabelText("")
        self.assertFalse(self.gr_node.isLabelVisible())
        self.assertEqual(
            self.gr_node.boundingRect(),
            QRectF(0.0, 0.0, self.gr_node.width, self.gr_node.height).normalized(),
        )

    def test_moving_the_node_dirties_the_plate_it_leaves(self):
        """What the scene repaints has to cover the plate's old place too."""
        view = QGraphicsView(self.scene.grScene)
        view.setSceneRect(-1000.0, -1000.0, 2000.0, 2000.0)
        view.resize(800, 600)
        view.show()
        _app.processEvents()
        try:
            self.gr_node.setPos(0.0, 0.0)
            _app.processEvents()

            before = self.gr_node.labelRect().translated(self.gr_node.pos())
            regions = []
            self.scene.grScene.changed.connect(regions.extend)

            self.gr_node.setPos(self.gr_node.pos() + QPointF(0.0, 24.0))
            _app.processEvents()

            after = self.gr_node.labelRect().translated(self.gr_node.pos())
        finally:
            view.close()
            view.deleteLater()

        self.assertTrue(regions, "the scene reported no changed region for the move")
        repainted = QRectF(regions[0])
        for rect in regions[1:]:
            repainted = repainted.united(QRectF(rect))

        self.assertTrue(repainted.contains(before), f"old plate left behind: {before}")
        self.assertTrue(repainted.contains(after), f"new plate clipped away: {after}")


if __name__ == "__main__":
    unittest.main()
