#!/usr/bin/env python

"""Cut line geometry: ending a stroke clears the area it covered.

``QDMCutLine`` derives ``boundingRect`` from ``line_points``. Qt repaints an
item by the rectangle it declared before the change, and a list replaced
without ``prepareGeometryChange`` never declares one: the view repaints the
new, empty rectangle at the origin, so the dashed stroke a user just cut with
stays on the canvas until something else repaints the viewport.
"""

import os
import unittest

# a real QApplication is required to build a Scene, keep it offscreen
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from qtpy.QtCore import QPointF, QRectF
from qtpy.QtWidgets import QApplication, QGraphicsScene, QGraphicsView

from nodeeditor.node_graphics_cutline import QDMCutLine

_app = QApplication.instance() or QApplication([])

_STROKE = [QPointF(20.0, 20.0), QPointF(160.0, 90.0), QPointF(300.0, 200.0)]


def repainted_area(regions) -> QRectF:
    """The union of the rectangles the scene reported as changed."""
    area = QRectF()
    for rect in regions:
        area = area.united(QRectF(rect))
    return area


class TestCutLineRepaint(unittest.TestCase):
    """Replacing or clearing the points repaints the stroke that was drawn."""

    def setUp(self):
        self.scene = QGraphicsScene()
        self.cutline = QDMCutLine()
        self.scene.addItem(self.cutline)
        self.view = QGraphicsView(self.scene)
        self.view.setSceneRect(-100.0, -100.0, 800.0, 600.0)
        self.view.resize(640, 480)
        self.view.show()
        _app.processEvents()

    def tearDown(self):
        self.view.close()
        self.view.deleteLater()
        self.scene.clear()

    def test_the_points_are_stored(self):
        self.cutline.line_points = _STROKE
        self.assertEqual(self.cutline.line_points, _STROKE)
        self.assertTrue(self.cutline.boundingRect().contains(QRectF(*_STROKE[:2])))

    def test_ending_a_stroke_repaints_the_area_it_covered(self):
        """The regression itself: the release empties the list, then repaints."""
        self.cutline.line_points = _STROKE
        _app.processEvents()
        stroke = self.cutline.boundingRect()
        self.assertGreater(stroke.width(), 200.0, "the stroke never drew")

        regions = []
        self.scene.changed.connect(regions.extend)

        self.cutline.line_points = []
        self.cutline.update()
        _app.processEvents()

        self.assertTrue(regions, "the scene reported no changed region")
        self.assertTrue(
            repainted_area(regions).contains(stroke),
            f"the stroke's area was never repainted: {stroke}",
        )


if __name__ == "__main__":
    unittest.main()
