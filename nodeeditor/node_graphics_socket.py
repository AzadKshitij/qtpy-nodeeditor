# -*- coding: utf-8 -*-
"""
A module containing Graphics representation of a :class:`~nodeeditor.node_socket.Socket`
"""
from qtpy.QtWidgets import QGraphicsItem
from qtpy.QtGui import QColor, QBrush, QPen, QFont, QPainterPath
from qtpy.QtCore import Qt, QRectF, QPointF

from nodeeditor.node_colors_config import get_color_scheme
from nodeeditor.node_socket_shapes import (
    DIRECTION_INPUT,
    DIRECTION_OUTPUT,
    SocketShape,
    SocketShapeContext,
    get_socket_shape,
)

from typing import TYPE_CHECKING, List, Optional, Tuple, Any


if TYPE_CHECKING:
    from nodeeditor.node_graphics_view import QDMGraphicsView
    from nodeeditor.node_edge import Edge
    from nodeeditor.node_socket import Socket

# Deprecated: Use NodeEditorColorScheme.sockets.get_type_color() instead
SOCKET_COLORS = [
    QColor("#FFFF7700"),
    QColor("#FF52e220"),
    QColor("#FF0056a6"),
    QColor("#FFa86db1"),
    QColor("#FFb54747"),
    QColor("#FFdbe220"),
    QColor("#FF888888"),
    QColor("#FFFF7700"),
    QColor("#FF52e220"),
    QColor("#FF0056a6"),
    QColor("#FFa86db1"),
    QColor("#FFb54747"),
    QColor("#FFdbe220"),
    QColor("#FF888888"),
]


class QDMGraphicsSocket(QGraphicsItem):
    """Class representing Graphic `Socket` in ``QGraphicsScene``"""

    def __init__(self, socket: 'Socket') -> None:
        """
        :param socket: reference to :class:`~nodeeditor.node_socket.Socket`
        :type socket: :class:`~nodeeditor.node_socket.Socket`
        """
        super().__init__(socket.node.grNode)

        self.socket = socket

        self.isHighlighted = False

        #: ``True`` while the mouse hovers this socket
        self.hovered = False

        self.radius = 6
        self._text = ""
        self.outline_width = 1
        self._font: Optional[QFont] = None  # Will be initialized in initAssets

        #: the shape this socket is drawn (and hit-tested) with
        self._shape: SocketShape = get_socket_shape(
            getattr(socket, "shape", None))

        self.initAssets()

        # sockets take part in the hover highlight
        self.setAcceptHoverEvents(True)

    @property
    def socket_type(self):
        """The socket's type, used to look up its color."""
        return self.socket.socket_type

    @property
    def direction(self) -> int:
        """``+1`` on an output socket, ``-1`` on an input socket.

        Shapes that must not flip (the chevron) simply ignore it.
        """
        return DIRECTION_INPUT if self.socket.is_input else DIRECTION_OUTPUT

    @property
    def shape(self) -> SocketShape:
        """The :class:`~nodeeditor.node_socket_shapes.SocketShape` in use"""
        return self._shape

    def getSocketColor(self, key):
        """Returns the ``QColor`` for this ``key``"""
        scheme = get_color_scheme()
        return scheme.sockets.get_type_color(key)

    def changeSocketType(self) -> None:
        """Change the Socket Type"""
        self._color_background = self.getSocketColor(self.socket_type)
        self._brush = QBrush(self._color_background)
        # print("Socket changed to:", self._color_background.getRgbF())
        self.update()

    def setShape(self, name: str) -> None:
        """Draw this socket with the shape registered under ``name``.

        :param name: the registered shape name
        """
        shape = get_socket_shape(name)
        if shape is self._shape:
            return
        self.prepareGeometryChange()
        self._shape = shape
        self.update()

    def initAssets(self) -> None:
        """Initialize ``QObjects`` like ``QColor``, ``QPen`` and ``QBrush``"""

        # Get colors from global color scheme
        scheme = get_color_scheme()

        # determine socket color
        self._color_background = self.getSocketColor(self.socket_type)
        self._color_outline = scheme.sockets.outline
        self._color_highlight = scheme.sockets.highlight

        self._pen = QPen(self._color_outline)
        self._pen.setWidthF(self.outline_width)
        self._pen_highlight = QPen(self._color_highlight)
        self._pen_highlight.setWidthF(2.0)
        self._brush = QBrush(self._color_background)

        # Initialize font and text pen
        self._font = QFont("Ubuntu", 7)
        self._font.setBold(True)
        self._pen_text = QPen(Qt.GlobalColor.black)

    def setText(self, text: str) -> None:
        """Set the text to display inside socket"""
        self._text = text
        self.update()

    def setDetailVisible(self, visible: bool) -> None:
        """Show or hide this socket's circle at low zoom.

        Pushed by the owning node when the scene drops to its level-of-detail
        state. A dozen sockets per node at normal zoom costs more per frame than
        the node itself; at that scale the circles are a couple of pixels wide
        and cannot be aimed at, so wiring is a zoomed-in activity.
        """
        self.setVisible(bool(visible))

    def paint(self, painter, QStyleOptionGraphicsItem, widget=None) -> None:
        """Painting the socket shape and its label"""
        ctx = SocketShapeContext(
            painter=painter,
            radius=self.radius,
            center=QPointF(0, 0),
            brush=self._brush,
            # the hover highlight and the edge-snapping highlight share the
            # same pen, they only differ in what turns it on
            pen=self._pen_highlight if (self.hovered or self.isHighlighted)
            else self._pen,
            color=self._color_background,
            socket=self.socket,
            hovered=self.hovered,
            direction=self.direction,
        )
        self._shape.draw(painter, ctx)

        # Draw text if present
        if self._text:
            painter.save()
            try:
                # the label never spills outside the socket's own outline
                painter.setClipPath(
                    self._shape.path(self.radius, self.direction))
                painter.setFont(self._font)
                painter.setPen(self._pen_text)

                # Create text rect slightly smaller than socket for padding
                painter.drawText(
                    self._textRect(),
                    Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter,
                    self._text
                )
            finally:
                painter.restore()

    def _textRect(self) -> QRectF:
        """The rectangle the socket label is drawn in"""
        return QRectF(
            -self.radius + 1,  # Add 1px padding
            -self.radius + 1,  # Add 1px padding
            2 * (self.radius - 1),  # Remove 2px for padding
            2 * (self.radius - 1)   # Remove 2px for padding
        )

    def _penMargin(self) -> float:
        """Half the widest pen this socket can paint with, plus an antialias pixel.

        A stroke reaches half its width past the path on both sides, so the
        bounding rectangle has to grow with it or the outer band of the
        previous paint stays on screen.
        """
        widest = 0.0
        for pen in (self._pen, self._pen_highlight):
            if pen is not None:
                widest = max(widest, pen.widthF())
        return widest / 2.0 + 1.0

    def shape(self) -> QPainterPath:
        """The outline used for hit testing.

        What is drawn is what can be clicked: a click on a corner of a square
        socket misses it, exactly like a click beside a circle does.
        """
        return self._shape.path(self.radius, self.direction)

    def boundingRect(self) -> QRectF:
        """Defining Qt' bounding rectangle"""
        margin = self._penMargin()
        rect = self.shape().boundingRect()
        if self._text:
            rect = rect.united(self._textRect())
        return rect.adjusted(-margin, -margin, margin, margin)

    def hoverEnterEvent(self, event) -> None:
        """Handle hover effect"""
        self.hovered = True
        if event is not None:
            # keep the event here, the parent node must not light up as well
            event.accept()
        self.update()
        self._updateParent()

    def hoverLeaveEvent(self, event) -> None:
        """Handle hover effect"""
        self.hovered = False
        if event is not None:
            event.accept()
        self.update()
        self._updateParent()

    def _updateParent(self) -> None:
        """Repaint the node, its hover outline depends on this socket's state.

        A socket sits inside the node's own hit area, so Qt reports the node
        as hovered while the mouse is over the socket. The node then holds
        back its hover outline, which means it has to be repainted when the
        socket's hover state changes.
        """
        parent = self.parentItem()
        if parent is not None:
            parent.update()

    # def onSelected(self) -> None:
    #     """Handle selection event"""
    #     self.isHighlighted = True
    #     self.update()
