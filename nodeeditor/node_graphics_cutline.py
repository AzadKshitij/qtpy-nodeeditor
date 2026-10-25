# -*- coding: utf-8 -*-
"""
A module containing the class for Cutting Line
"""
from qtpy.QtGui import QPen, QPainterPath, QPolygonF, QPainter
from qtpy.QtWidgets import QGraphicsItem, QWidget
from qtpy.QtCore import Qt, QRectF, QPointF


class QDMCutLine(QGraphicsItem):
    """Class representing Cutting Line used for cutting multiple `Edges` with one stroke"""

    def __init__(self, parent: QGraphicsItem = None) -> None:
        """
        :param parent: parent widget
        :type parent: ``QWidget``
        """
        super().__init__(parent)

        self.line_points: list = []

        self._pen = QPen(Qt.GlobalColor.white)
        self._pen.setWidthF(2.0)
        self._pen.setDashPattern([3, 3])

        self.setZValue(2)

    def boundingRect(self) -> QRectF:
        """Defining Qt' bounding rectangle

        Inflated by half the pen, because ``paint`` strokes the polyline: a
        rectangle of the bare path leaves the outer half of the stroke outside
        the area Qt repaints, so a moving cut line leaves a trail of old lines.
        """
        pen = getattr(self, "_pen", None)
        margin = (pen.widthF() / 2.0 if pen is not None else 0.0) + 1.0
        return self.shape().boundingRect().adjusted(-margin, -margin, margin, margin)

    def shape(self) -> QPainterPath:
        """Calculate the QPainterPath object from list of line points

        :return: shape function returning ``QPainterPath`` representation of Cutting Line
        :rtype: ``QPainterPath``
        """
        poly = QPolygonF(self.line_points)

        if len(self.line_points) > 1:
            path = QPainterPath(self.line_points[0])
            for pt in self.line_points[1:]:
                path.lineTo(pt)
        else:
            path = QPainterPath(QPointF(0, 0))
            path.lineTo(QPointF(1, 1))

        return path

    def paint(self, painter, QStyleOptionGraphicsItem, widget=None) -> None:
        """Paint the Cutting Line"""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(self._pen)

        poly = QPolygonF(self.line_points)
        painter.drawPolyline(poly)
