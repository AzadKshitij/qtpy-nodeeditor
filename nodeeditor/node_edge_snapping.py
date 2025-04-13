# -*- coding: utf-8 -*-
"""
A module containing the Edge Snapping functions which are used in :class:`~nodeeditor.node_graphics_view.QDMGraphicsView` class.
"""


from qtpy.QtCore import QPointF, QRectF
from qtpy.QtGui import QMouseEvent

from nodeeditor.node_graphics_socket import QDMGraphicsSocket

from typing import TYPE_CHECKING, List, Optional, Tuple, Any


if TYPE_CHECKING:
    from nodeeditor.node_graphics_view import QDMGraphicsView
    from nodeeditor.node_edge import Edge
    from nodeeditor.node_socket import Socket


class EdgeSnapping():
    def __init__(self, grView: 'QDMGraphicsView', snapping_radius: float = 24) -> None:
        self.grView = grView
        self.grScene = self.grView.grScene
        self.edge_snapping_radius = snapping_radius

    def getSnappedSocketItem(self, event: 'QMouseEvent') -> Optional['QDMGraphicsSocket']:
        """Returns :class:`~nodeeditor.node_graphics_socket.QDMGraphicsSocket` which we should snap to"""
        scenepos = self.grView.mapToScene(event.pos())
        grSocket, pos = self.getSnappedToSocketPosition(scenepos)

        if grSocket is None:
            return None

        return grSocket

    def getSnappedToSocketPosition(self, scenepos: QPointF) -> Tuple[Optional['QDMGraphicsSocket'], QPointF]:
        """
        Returns grSocket and Scene position to nearest Socket or original position if no nearby Socket found

        :param scenepos: From which point should I snap?
        :type scenepos: ``QPointF``
        :return: grSocket and Scene postion to nearest socket
        """
        scanrect = QRectF(
            scenepos.x() - self.edge_snapping_radius,
            scenepos.y() - self.edge_snapping_radius,
            self.edge_snapping_radius * 2,
            self.edge_snapping_radius * 2
        )
        items = self.grScene.items(scanrect)
        socket_items = list(
            filter(lambda x: isinstance(x, QDMGraphicsSocket), items))

        if not socket_items:
            return None, scenepos

        selected_item = socket_items[0]
        if len(socket_items) > 1:
            # calculate the nearest socket
            nearest = float('inf')
            for grsock in socket_items:
                if not isinstance(grsock, QDMGraphicsSocket) or not grsock.socket or not grsock.socket.node:
                    continue

                grsock_scenepos = grsock.socket.node.getSocketScenePosition(
                    grsock.socket)
                qpdist = QPointF(*grsock_scenepos) - scenepos
                dist = qpdist.x() * qpdist.x() + qpdist.y() * qpdist.y()
                if dist < nearest:
                    nearest, selected_item = dist, grsock

        if not isinstance(selected_item, QDMGraphicsSocket) or not selected_item.socket or not selected_item.socket.node:
            return None, scenepos

        selected_item.isHighlighted = True

        calcpos = selected_item.socket.node.getSocketScenePosition(
            selected_item.socket)

        return selected_item, QPointF(*calcpos)
