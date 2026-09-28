# -*- coding: utf-8 -*-
"""
A module containing the Graphics representation of an Edge
"""
from qtpy.QtWidgets import QGraphicsPathItem, QWidget, QGraphicsItem, QGraphicsSceneHoverEvent, QGraphicsSimpleTextItem
from qtpy.QtGui import QColor, QPen, QBrush, QPainterPath, QFont
from qtpy.QtCore import Qt, QRectF, QPointF

from nodeeditor.node_graphics_edge_path import GraphicsEdgePathBezier, GraphicsEdgePathDirect, GraphicsEdgePathSquare, GraphicsEdgePathImprovedSharp, GraphicsEdgePathImprovedBezier
from nodeeditor.node_colors_config import get_color_scheme

from typing import TYPE_CHECKING, List, Optional, Tuple, Any


if TYPE_CHECKING:
    from nodeeditor.node_graphics_view import QDMGraphicsView
    from nodeeditor.node_edge import Edge
    from nodeeditor.node_socket import Socket


class QDMGraphicsEdge(QGraphicsPathItem):
    """Base class for Graphics Edge"""

    def __init__(self, edge: 'Edge', parent: QGraphicsPathItem = None) -> None:
        """
        :param edge: reference to :class:`~nodeeditor.node_edge.Edge`
        :type edge: :class:`~nodeeditor.node_edge.Edge`
        :param parent: parent widget
        :type parent: ``QWidget``

        :Instance attributes:

            - **edge** - reference to :class:`~nodeeditor.node_edge.Edge`
            - **posSource** - ``[x, y]`` source position in the `Scene`
            - **posDestination** - ``[x, y]`` destination position in the `Scene`
        """
        super().__init__(parent)

        self.edge = edge

        # create instance of our path class
        self.pathCalculator = self.determineEdgePathClass()(self)

        # init our flags
        self._last_selected_state = False
        self.hovered = False

        # init our variables
        self.posSource: List[float] = [0, 0]
        self.posDestination: List[float] = [200, 100]

        # code-settable, user-read-only label drawn on top of the edge path.
        # Never editable/selectable/movable: users cannot change it, code can
        # via QDMGraphicsEdge.setLabel() / Edge.label.
        self._label_offset = QPointF(0, -18)
        self.labelItem = QGraphicsSimpleTextItem(self)
        self.labelItem.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.labelItem.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.labelItem.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, False)
        self.labelItem.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        self.labelItem.setAcceptHoverEvents(False)
        # QGraphicsSimpleTextItem has no text-interaction/editing API at all,
        # which is exactly what we want: code-only, never user-editable.
        self.labelItem.setBrush(QBrush(QColor("#ffffff")))
        self.labelItem.setZValue(1)
        self.labelItem.setVisible(False)

        self.initAssets()
        self.initUI()

    def initUI(self) -> None:
        """Set up this ``QGraphicsPathItem``"""
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.setZValue(-1)

    def initAssets(self) -> None:
        """Initialize ``QObjects`` like ``QColor``, ``QPen`` and ``QBrush``"""
        # Get colors from global color scheme
        scheme = get_color_scheme()
        self._color = self._default_color = scheme.edges.default
        self._color_selected = scheme.edges.selected
        self._color_hovered = scheme.edges.hovered
        self._pen = QPen(self._color)
        self._pen_selected = QPen(self._color_selected)
        self._pen_dragging = QPen(scheme.edges.dragging)
        self._pen_hovered = QPen(self._color_hovered)
        self._pen_dragging.setStyle(Qt.PenStyle.DashLine)
        self._pen.setWidthF(3.0)
        self._pen_selected.setWidthF(3.0)
        self._pen_dragging.setWidthF(3.0)
        self._pen_hovered.setWidthF(5.0)

    def createEdgePathCalculator(self):
        """Create instance of :class:`~nodeeditor.node_graphics_edge_path.GraphicsEdgePathBase`"""
        self.pathCalculator = self.determineEdgePathClass()(self)
        return self.pathCalculator

    def determineEdgePathClass(self):
        """Decide which GraphicsEdgePath class should be used to calculate path according to edge.edge_type value"""
        from nodeeditor.node_edge import EDGE_TYPE_BEZIER, EDGE_TYPE_DIRECT, EDGE_TYPE_SQUARE, EDGE_TYPE_IMPROVED_SHARP, EDGE_TYPE_IMPROVED_BEZIER
        if self.edge.edge_type == EDGE_TYPE_BEZIER:
            return GraphicsEdgePathBezier
        if self.edge.edge_type == EDGE_TYPE_DIRECT:
            return GraphicsEdgePathDirect
        if self.edge.edge_type == EDGE_TYPE_SQUARE:
            return GraphicsEdgePathSquare
        if self.edge.edge_type == EDGE_TYPE_IMPROVED_SHARP:
            return GraphicsEdgePathImprovedSharp
        if self.edge.edge_type == EDGE_TYPE_IMPROVED_BEZIER:
            return GraphicsEdgePathImprovedBezier

        else:
            return GraphicsEdgePathImprovedBezier

    def makeUnselectable(self) -> None:
        """Used for drag edge to disable click detection over this graphics item"""
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.setAcceptHoverEvents(False)

    def changeColor(self, color) -> None:
        """Change color of the edge from string hex value '#00ff00'"""
        # print("^Called change color to:", color.red(), color.green(), color.blue(), "on edge:", self.edge)
        self._color = QColor(color) if type(color) == str else color
        self._pen = QPen(self._color)
        self._pen.setWidthF(3.0)

    def setColorFromSockets(self) -> bool:
        """Change color according to connected sockets. Returns ``True`` if color can be determined"""
        socket_type_start = self.edge.start_socket.socket_type
        socket_type_end = self.edge.end_socket.socket_type
        if socket_type_start != socket_type_end:
            return False
        self.changeColor(
            self.edge.start_socket.grSocket.getSocketColor(socket_type_start))

        return True

    def label(self) -> str:
        """Return the current code-set edge label (``""`` when unset)."""
        return self.labelItem.text()

    def setLabel(self, text: str) -> None:
        """Set the text drawn on top of the edge.

        Code-only API: the label item is not selectable, movable, focusable
        and accepts no mouse buttons, so users cannot edit it directly.

        :param text: label text, ``""``/``None`` hides the label
        """
        self.labelItem.setText(text or "")
        self.labelItem.setVisible(bool(text))
        self.updateLabelPosition()
        self.update()

    def setLabelColor(self, color) -> None:
        """Set label text color from ``QColor`` or hex string."""
        self.labelItem.setBrush(QBrush(QColor(color) if isinstance(color, str) else color))
        self.update()

    def setLabelFont(self, font: QFont) -> None:
        """Set label font, then recenter it on the edge path."""
        self.labelItem.setFont(font)
        self.updateLabelPosition()
        self.update()

    def setLabelOffset(self, x: float, y: float) -> None:
        """Offset (in px) applied to the centered label position."""
        self._label_offset = QPointF(x, y)
        self.updateLabelPosition()
        self.update()

    def updateLabelPosition(self) -> None:
        """Center the label on top of the current edge path."""
        if not self.labelItem.isVisible():
            return
        try:
            path = self.path()
            mid = path.pointAtPercent(0.5) if path.length() > 0 else QPointF(
                (self.posSource[0] + self.posDestination[0]) / 2.0,
                (self.posSource[1] + self.posDestination[1]) / 2.0,
            )
        except Exception:
            mid = QPointF(
                (self.posSource[0] + self.posDestination[0]) / 2.0,
                (self.posSource[1] + self.posDestination[1]) / 2.0,
            )
        rect = self.labelItem.boundingRect()
        self.labelItem.setPos(mid + self._label_offset - QPointF(rect.width() / 2.0, rect.height() / 2.0))

    def onSelected(self) -> None:
        """Our event handling when the edge was selected"""
        self.edge.scene.grScene.itemSelected.emit()

    def doSelect(self, new_state: bool = True) -> None:
        """Safe version of selecting the `Graphics Node`. Takes care about the selection state flag used internally

        :param new_state: ``True`` to select, ``False`` to deselect
        :type new_state: ``bool``
        """
        self.setSelected(new_state)
        self._last_selected_state = new_state
        if new_state:
            self.onSelected()

    def mouseReleaseEvent(self, event) -> None:
        """Overridden Qt's method to handle selecting and deselecting this `Graphics Edge`"""
        super().mouseReleaseEvent(event)
        if self._last_selected_state != self.isSelected():
            self.edge.scene.resetLastSelectedStates()
            self._last_selected_state = self.isSelected()
            self.onSelected()

    def hoverEnterEvent(self, event: Optional['QGraphicsSceneHoverEvent']) -> None:
        """Handle hover effect

        :param event: The hover event
        :type event: Optional[QGraphicsSceneHoverEvent]
        """
        self.hovered = True
        self.update()

    def hoverLeaveEvent(self, event: Optional['QGraphicsSceneHoverEvent']) -> None:
        """Handle hover effect

        :param event: The hover event
        :type event: Optional[QGraphicsSceneHoverEvent]
        """
        self.hovered = False
        self.update()

    def setSource(self, x: float, y: float) -> None:
        """ Set source point

        :param x: x position
        :type x: ``float``
        :param y: y position
        :type y: ``float``
        """
        self.posSource = [x, y]

    def setDestination(self, x: float, y: float) -> None:
        """ Set destination point

        :param x: x position
        :type x: ``float``
        :param y: y position
        :type y: ``float``
        """
        self.posDestination = [x, y]

    def boundingRect(self) -> QRectF:
        """Defining Qt' bounding rectangle (path united with label rect)."""
        base = self.shape().boundingRect()
        try:
            if self.labelItem.isVisible():
                label_rect = self.labelItem.boundingRect().translated(self.labelItem.pos())
                return base.united(label_rect)
        except Exception:
            pass
        return base

    def shape(self) -> QPainterPath:
        """Returns ``QPainterPath`` representation of this `Edge`

        :return: path representation
        :rtype: ``QPainterPath``
        """
        return self.calcPath()

    def paint(self, painter, QStyleOptionGraphicsItem, widget=None) -> None:
        """Qt's overridden method to paint this Graphics Edge. Path calculated
            in :func:`~nodeeditor.node_graphics_edge.QDMGraphicsEdge.calcPath` method"""
        self.setPath(self.calcPath())
        self.updateLabelPosition()

        painter.setBrush(Qt.BrushStyle.NoBrush)

        if self.hovered and self.edge.end_socket is not None:
            painter.setPen(self._pen_hovered)
            painter.drawPath(self.path())

        if self.edge.end_socket is None:
            painter.setPen(self._pen_dragging)
        else:
            painter.setPen(self._pen if not self.isSelected()
                           else self._pen_selected)

        painter.drawPath(self.path())

    def intersectsWith(self, p1: QPointF, p2: QPointF) -> bool:
        """Does this Graphics Edge intersect with the line between point A and point B ?

        :param p1: point A
        :type p1: ``QPointF``
        :param p2: point B
        :type p2: ``QPointF``
        :return: ``True`` if this `Graphics Edge` intersects
        :rtype: ``bool``
        """
        cutpath = QPainterPath(p1)
        cutpath.lineTo(p2)
        path = self.calcPath()
        return cutpath.intersects(path)

    def calcPath(self) -> QPainterPath:
        """Will handle drawing QPainterPath from Point A to B. Internally there exist self.pathCalculator which
        is an instance of derived :class:`~nodeeditor.node_graphics_edge_path.GraphicsEdgePathBase` class
        containing the actual `calcPath()` function - computing how the edge should look like.

        :returns: ``QPainterPath`` of the edge connecting `source` and `destination`
        :rtype: ``QPainterPath``
        """
        return self.pathCalculator.calcPath()
