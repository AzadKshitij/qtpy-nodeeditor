import math
from qtpy.QtCore import QPointF
from qtpy.QtGui import QPainterPath

from typing import TYPE_CHECKING, List, Optional, Tuple, Any


if TYPE_CHECKING:
    from nodeeditor.node_graphics_view import QDMGraphicsView
    from nodeeditor.node_edge import Edge
    from nodeeditor.node_socket import Socket
    from nodeeditor.node_graphics_edge import QDMGraphicsEdge


EDGE_CP_ROUNDNESS = 100     #: Bezier control point distance on the line
#: factor for square edge to change the midpoint between start and end socket
WEIGHT_SOURCE = 0.2

#: Scale EDGE_CURVATURE with distance of the edge endpoints
EDGE_IBCP_ROUNDNESS = 75
NODE_DISTANCE = 12
EDGE_CURVATURE = 2


class GraphicsEdgePathBase:
    """Base Class for calculating the graphics path to draw for an graphics Edge"""

    def __init__(self, owner: 'QDMGraphicsEdge') -> None:
        # keep the reference to owner GraphicsEdge class
        self.owner = owner

    def calcPath(self):
        """Calculate the Direct line connection

        :returns: ``QPainterPath`` of the graphics path to draw
        :rtype: ``QPainterPath`` or ``None``
        """
        return None


class GraphicsEdgePathDirect(GraphicsEdgePathBase):
    """Direct line connection Graphics Edge"""

    def calcPath(self) -> QPainterPath:
        """Calculate the Direct line connection

        :returns: ``QPainterPath`` of the direct line
        :rtype: ``QPainterPath``
        """
        path = QPainterPath(
            QPointF(self.owner.posSource[0], self.owner.posSource[1]))
        path.lineTo(self.owner.posDestination[0], self.owner.posDestination[1])
        return path


class GraphicsEdgePathBezier(GraphicsEdgePathBase):
    """Cubic line connection Graphics Edge"""

    def calcPath(self) -> QPainterPath:
        """Calculate the cubic Bezier line connection with 2 control points

        :returns: ``QPainterPath`` of the cubic Bezier line
        :rtype: ``QPainterPath``
        """
        s = self.owner.posSource
        d = self.owner.posDestination
        dist = (d[0] - s[0]) * 0.5

        cpx_s: float = +dist
        cpx_d: float = -dist
        cpy_s: float = 0.0
        cpy_d: float = 0.0

        if self.owner.edge.start_socket is not None:
            ssin = self.owner.edge.start_socket.is_input
            ssout = self.owner.edge.start_socket.is_output

            if (s[0] > d[0] and ssout) or (s[0] < d[0] and ssin):
                cpx_d *= -1
                cpx_s *= -1

                cpy_d = (
                    (s[1] - d[1]) / math.fabs(
                        (s[1] - d[1]) if (s[1] - d[1]) != 0 else 0.00001
                    )
                ) * EDGE_CP_ROUNDNESS
                cpy_s = (
                    (d[1] - s[1]) / math.fabs(
                        (d[1] - s[1]) if (d[1] - s[1]) != 0 else 0.00001
                    )
                ) * EDGE_CP_ROUNDNESS

        path = QPainterPath(
            QPointF(self.owner.posSource[0], self.owner.posSource[1]))
        path.cubicTo(s[0] + cpx_s, s[1] + cpy_s, d[0] + cpx_d, d[1] + cpy_d,
                     self.owner.posDestination[0], self.owner.posDestination[1])

        return path


class GraphicsEdgePathSquare(GraphicsEdgePathBase):
    """Square line connection Graphics Edge"""

    def __init__(self, *args, handle_weight: float=0.5, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.rand = None
        self.handle_weight = handle_weight

    def calcPath(self):
        """Calculate the square edge line connection

        :returns: ``QPainterPath`` of the edge square line
        :rtype: ``QPainterPath``
        """

        s = self.owner.posSource
        d = self.owner.posDestination

        mid_x = s[0] + ((d[0] - s[0]) * self.handle_weight)

        path = QPainterPath(QPointF(s[0], s[1]))
        path.lineTo(mid_x, s[1])
        path.lineTo(mid_x, d[1])
        path.lineTo(d[0], d[1])

        return path


class GraphicsEdgePathImprovedSharp(GraphicsEdgePathBase):
    """Better Cubic line connection Graphics Edge"""

    def calcPath(self) -> QPainterPath:
        """Calculate the Direct line connection

        :returns: ``QPainterPath`` of the painting line
        :rtype: ``QPainterPath``
        """
        sx, sy = self.owner.posSource
        dx, dy = self.owner.posDestination
        distx, disty = dx-sx, dy-sy
        dist = math.sqrt(distx*distx + disty*disty)

        # is start / end socket on left side?
        sleft = self.owner.edge.start_socket.position <= 3

        # if the drag edge started from input socket, we should connect to output socket...
        eleft = self.owner.edge.start_socket.position > 3

        if self.owner.edge.end_socket is not None:
            eleft = self.owner.edge.end_socket.position <= 3

        node_sdist = (-NODE_DISTANCE) if sleft else NODE_DISTANCE
        node_edist = (-NODE_DISTANCE) if eleft else NODE_DISTANCE

        path = QPainterPath(QPointF(sx, sy))

        if abs(dist) > NODE_DISTANCE:
            path.lineTo(sx + node_sdist, sy)
            path.lineTo(dx + node_edist, dy)

        path.lineTo(dx, dy)

        return path


class GraphicsEdgePathImprovedBezier(GraphicsEdgePathBase):
    """Better Cubic line connection Graphics Edge"""

    def calcPath(self) -> QPainterPath:
        """Calculate the Direct line connection

        :returns: ``QPainterPath`` of the painting line
        :rtype: ``QPainterPath``
        """
        sx, sy = self.owner.posSource
        dx, dy = self.owner.posDestination
        distx, disty = dx-sx, dy-sy
        dist = math.sqrt(distx*distx + disty*disty)

        # is start / end socket on left side?
        sleft = self.owner.edge.start_socket.position <= 3

        # if the drag edge started from input socket, we should connect to output socket...
        eleft = self.owner.edge.start_socket.position > 3

        if self.owner.edge.end_socket is not None:
            eleft = self.owner.edge.end_socket.position <= 3

        path = QPainterPath(QPointF(sx, sy))

        if abs(dist) > NODE_DISTANCE:
            curvature = max(EDGE_CURVATURE, (EDGE_CURVATURE *
                            abs(dist)) / EDGE_IBCP_ROUNDNESS)

            node_sdist = (-NODE_DISTANCE) if sleft else NODE_DISTANCE
            node_edist = (-NODE_DISTANCE) if eleft else NODE_DISTANCE

            path.lineTo(sx + node_sdist, sy)

            path.cubicTo(
                QPointF(sx + node_sdist * curvature, sy),
                QPointF(dx + node_edist * curvature, dy),
                QPointF(dx + node_edist, dy)
            )

            path.lineTo(dx + node_edist, dy)

        path.lineTo(dx, dy)

        return path
