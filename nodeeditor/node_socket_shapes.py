# -*- coding: utf-8 -*-
"""
A module containing the Socket Shape system.

A socket shape decides two things: how a :class:`~nodeeditor.node_socket.Socket`
is painted, and which area of it counts as a hit. Four presets ship with the
library (``circle``, ``square``, ``triangle``, ``chevron``) and applications
can register their own.

Shapes are named per socket type by the owning node (see
:meth:`~nodeeditor.node_node.Node.getSocketShapeName`), so they are declared in
code and never written to the graph file.
"""
from qtpy.QtCore import QPointF
from qtpy.QtGui import QPainterPath, QPolygonF

from typing import Any, Callable, Dict, List, Optional, Tuple


#: Direction handed to a shape for an output socket (right hand side of a node)
DIRECTION_OUTPUT = 1

#: Direction handed to a shape for an input socket (left hand side of a node)
DIRECTION_INPUT = -1

#: Name of the shape every socket falls back to
DEFAULT_SHAPE = "circle"


class SocketShapeContext:
    """Everything a shape needs while it paints itself."""

    __slots__ = ("painter", "radius", "center", "brush", "pen", "color",
                 "socket", "hovered", "direction")

    def __init__(self, painter, radius: float, center: QPointF, brush, pen,
                 color, socket=None, hovered: bool = False,
                 direction: int = DIRECTION_OUTPUT) -> None:
        """
        :param painter: the `QPainter` the shape draws into
        :param radius: the socket's radius in scene units
        :param center: the socket's center in item coordinates
        :param brush: the fill brush (the socket's type color)
        :param pen: the outline pen (already switched for the hover state)
        :param color: the socket's fill color
        :param socket: the owning :class:`~nodeeditor.node_socket.Socket`
        :param hovered: ``True`` while the mouse hovers the socket
        :param direction: ``+1`` for output sockets, ``-1`` for input sockets
        """
        self.painter = painter
        self.radius = radius
        self.center = center
        self.brush = brush
        self.pen = pen
        self.color = color
        self.socket = socket
        self.hovered = hovered
        self.direction = direction


class SocketShape:
    """Base class for socket shapes.

    Subclasses describe their outline as a list of points normalized against the
    socket radius, and get the hit-test path and the painting for free.
    """

    #: Mirrors the outline for input sockets when ``True``.
    mirrors_input: bool = True

    def points(self) -> List[Tuple[float, float]]:
        """The outline as normalized points, in units of the socket radius.

        :return: list of ``(x, y)`` pairs
        """
        raise NotImplementedError

    def path(self, radius: float, direction: int = DIRECTION_OUTPUT) -> QPainterPath:
        """The outline as a path, centered on the item origin.

        :param radius: the socket's radius in scene units
        :param direction: ``+1`` for output sockets, ``-1`` for input sockets
        :return: the outline path
        """
        pts = self.points()
        if self.mirrors_input and direction < 0:
            pts = [(-x, y) for x, y in pts]
        path = QPainterPath()
        path.addPolygon(QPolygonF(
            [QPointF(x * radius, y * radius) for x, y in pts]))
        path.closeSubpath()
        return path

    def draw(self, painter, ctx: SocketShapeContext) -> None:
        """Paint the shape.

        :param painter: the `QPainter` to draw into
        :param ctx: the :class:`SocketShapeContext` for this paint
        """
        painter.setBrush(ctx.brush)
        painter.setPen(ctx.pen)
        painter.drawPath(self.path(ctx.radius, ctx.direction))


class CircleShape(SocketShape):
    """The classic socket: a filled circle."""

    def path(self, radius: float, direction: int = DIRECTION_OUTPUT) -> QPainterPath:
        """The circle as a path, centered on the item origin.

        :param radius: the socket's radius in scene units
        :param direction: ignored, a circle looks the same on both sides
        :return: the outline path
        """
        path = QPainterPath()
        path.addEllipse(QPointF(0, 0), radius, radius)
        return path


class SquareShape(SocketShape):
    """A square socket.

    The half side is ``0.85 * radius``, which reads as the same weight as the
    circle next to it.
    """

    HALF_SIDE = 0.85

    def points(self) -> List[Tuple[float, float]]:
        """The square's four corners, in units of the socket radius.

        :return: list of ``(x, y)`` pairs
        """
        h = self.HALF_SIDE
        return [(-h, -h), (h, -h), (h, h), (-h, h)]


class TriangleShape(SocketShape):
    """A triangular socket.

    The tip points away from the node: right on an output socket, left on an
    input socket.
    """

    def points(self) -> List[Tuple[float, float]]:
        """The triangle's three corners, in units of the socket radius.

        The tip points right, so the outline mirrors on input sockets.

        :return: list of ``(x, y)`` pairs
        """
        return [(-0.8, -0.9), (0.9, 0.0), (-0.8, 0.9)]


class ChevronShape(SocketShape):
    """A chevron socket: the concave hexagon, pointing right.

    The shape never mirrors, on either side of a node. A chevron on an input
    socket aims its tip into the node, so the two sides of a graph read as one
    left-to-right flow: in, processed, out.
    """

    mirrors_input = False

    def points(self) -> List[Tuple[float, float]]:
        """The chevron's six corners, in units of the socket radius.

        :return: list of ``(x, y)`` pairs
        """
        return [(0.847, 0.0), (0.284, 1.0), (-0.847, 1.0),
                (-0.331, 0.0), (-0.847, -1.0), (0.284, -1.0)]


class CallbackShape(SocketShape):
    """Wraps a plain ``fn(painter, ctx)`` callback as a shape.

    A callback only knows how to draw, not what its outline is, so the hit
    area falls back to the circle.
    """

    def __init__(self, func: Callable) -> None:
        """
        :param func: called as ``func(painter, ctx)`` to paint the socket
        """
        self.func = func

    def path(self, radius: float, direction: int = DIRECTION_OUTPUT) -> QPainterPath:
        """The circle used as the hit area of a callback shape.

        :param radius: the socket's radius in scene units
        :param direction: ignored, the fallback outline is always a circle
        :return: the outline path
        """
        path = QPainterPath()
        path.addEllipse(QPointF(0, 0), radius, radius)
        return path

    def draw(self, painter, ctx: SocketShapeContext) -> None:
        """Paint the shape by handing the paint over to the wrapped callback.

        :param painter: the `QPainter` to draw into
        :param ctx: the :class:`SocketShapeContext` for this paint
        """
        self.func(painter, ctx)


#: All registered socket shapes, by name
SOCKET_SHAPES: Dict[str, SocketShape] = {}


def register_socket_shape(name: str, shape) -> SocketShape:
    """Register a socket shape under ``name``.

    ``shape`` may be a :class:`SocketShape` instance, a :class:`SocketShape`
    subclass, or a plain callable ``fn(painter, ctx)``. Registering an existing
    name replaces the old shape.

    :param name: the name nodes use to select this shape
    :param shape: the shape, its class, or a drawing callback
    :return: the registered shape
    """
    if isinstance(shape, type):
        if not issubclass(shape, SocketShape):
            raise TypeError(
                "socket shape class must inherit from SocketShape, got %r"
                % (shape,))
        shape = shape()

    if not isinstance(shape, SocketShape):
        if callable(shape):
            shape = CallbackShape(shape)
        else:
            raise TypeError(
                "socket shape must be a SocketShape, a SocketShape subclass or "
                "a callable, got %r" % (shape,))

    SOCKET_SHAPES[name] = shape
    return shape


def get_socket_shape(name: Optional[str]) -> SocketShape:
    """The shape registered under ``name``.

    Unknown names fall back to the circle rather than raising, so a typo in a
    node's shape map cannot break a graph.

    :param name: the registered shape name
    :return: the shape to draw with
    """
    if isinstance(name, str):
        shape = SOCKET_SHAPES.get(name)
        if shape is not None:
            return shape
    return SOCKET_SHAPES[DEFAULT_SHAPE]


# the presets
register_socket_shape(DEFAULT_SHAPE, CircleShape())
register_socket_shape("square", SquareShape())
register_socket_shape("triangle", TriangleShape())
register_socket_shape("chevron", ChevronShape())
