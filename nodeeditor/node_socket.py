# -*- coding: utf-8 -*-
"""
Socket - MVC-based implementation of a socket (port) in a node.

The Socket class wraps SocketModel and SocketController to provide MVC-based
socket management while maintaining the existing public API.
"""
from collections import OrderedDict
from qtpy.QtCore import QObject

from nodeeditor.node_serializable import Serializable
from nodeeditor.views.graphics.node_graphics_socket import QDMGraphicsSocket

from typing import TYPE_CHECKING, List, Optional, Tuple, Any, Callable

if TYPE_CHECKING:
    from nodeeditor.views.graphics.node_graphics_view import QDMGraphicsView
    from nodeeditor.node_scene import Scene
    from nodeeditor.node_edge import Edge
    from nodeeditor.node_node import Node

# Socket position constants
LEFT_TOP = 1
LEFT_CENTER = 2
LEFT_BOTTOM = 3
RIGHT_TOP = 4
RIGHT_CENTER = 5
RIGHT_BOTTOM = 6

DEBUG = False
DEBUG_REMOVE_WARNINGS = False


class Socket(QObject, Serializable):
    """
    Socket class representing a port/connection point on a node using MVC architecture.

    The Socket wraps SocketModel and SocketController to provide data management
    and operations while maintaining the public API.
    """

    Socket_GR_Class = QDMGraphicsSocket

    def __init__(
        self,
        node: 'Node',
        index: int = 0,
        position: int = LEFT_TOP,
        socket_type: int = 1,
        multi_edges: bool = True,
        count_on_this_node_side: int = 1,
        is_input: bool = False
    ) -> None:
        """
        Initialize a Socket with MVC components.

        :param node: reference to the Node containing this Socket
        :param index: Current index of this socket in the position
        :param position: Socket position constant (LEFT_TOP, RIGHT_BOTTOM, etc.)
        :param socket_type: Constant defining type/color of this socket
        :param multi_edges: Can this socket have multiple Edges connected?
        :param count_on_this_node_side: Total number of sockets on this position
        :param is_input: Is this an input Socket?
        """
        QObject.__init__(self)
        Serializable.__init__(self)

        # Import here to avoid circular imports
        from nodeeditor.models.socket_model import SocketModel
        from nodeeditor.controllers.socket_controller import SocketController

        # Reference to node
        self.node: 'Node' = node

        # Socket configuration
        self.position: int = position
        self.index: int = index
        self.socket_type: int = socket_type
        self.count_on_this_node_side: int = count_on_this_node_side
        self.is_multi_edges: bool = multi_edges
        self.is_input: bool = is_input
        self.is_output: bool = not self.is_input

        if DEBUG:
            print("Socket -- creating with", self.index, self.position, "for node", self.node)

        # Create graphics socket
        self.grSocket: QDMGraphicsSocket = self.__class__.Socket_GR_Class(self)

        # Set position
        self.setSocketPosition()

        # MVC components - Create model with correct parameters
        # Convert is_input to socket_type (INPUT=1, OUTPUT=2)
        model_socket_type = SocketModel.INPUT if is_input else SocketModel.OUTPUT
        self.model: SocketModel = SocketModel(
            name=f"{'input' if is_input else 'output'}_{index}",
            socket_type=model_socket_type,
            socket_id=None,  # Auto-generate ID
            parent_node=node.model if hasattr(node, "model") else None,
        )
        self.controller: SocketController = SocketController(self.model)

        # Edge connections
        self.edges: List['Edge'] = []

        # Connect model signals
        self.model.typeChanged.connect(self._on_type_changed)

    def __str__(self) -> str:
        """String representation of the socket."""
        return "<Socket #%d %s %s..%s>" % (
            self.index,
            "ME" if self.is_multi_edges else "SE",
            hex(id(self))[2:5],
            hex(id(self))[-3:]
        )

    # ==================== Signal Handlers ====================

    def _on_type_changed(self, new_type: int) -> None:
        """Handle model type change - update graphics."""
        if self.grSocket:
            self.grSocket.changeSocketType()

    # ==================== Socket Management ====================

    def delete(self) -> None:
        """Delete this Socket from graphics scene."""
        self.grSocket.setParentItem(None)
        self.node.scene.grScene.removeItem(self.grSocket)
        del self.grSocket

    def changeSocketType(self, new_socket_type: int) -> bool:
        """
        Change the Socket Type.

        :param new_socket_type: new socket type constant
        :return: True if the socket type was actually changed
        """
        if self.socket_type != new_socket_type:
            self.socket_type = new_socket_type
            # Note: SocketModel.socket_type is immutable, so we only update the Socket wrapper
            # and trigger the graphics update
            self.grSocket.changeSocketType()
            return True
        return False

    def setSocketPosition(self) -> None:
        """
        Helper function to set Graphics Socket position.

        Exact socket position is calculated inside Node.
        """
        self.grSocket.setPos(
            *self.node.getSocketPosition(
                self.index,
                self.position,
                self.count_on_this_node_side
            )
        )

    def getSocketPosition(self) -> List[float]:
        """
        Get this Socket's position according to the Node implementation.

        :return: [x, y] position list
        """
        if DEBUG:
            print("  GSP: ", self.index, self.position, "node:", self.node)
        res = self.node.getSocketPosition(
            self.index,
            self.position,
            self.count_on_this_node_side
        )
        if DEBUG:
            print("  res", res)
        return res

    # ==================== Edge Management ====================

    def hasAnyEdge(self) -> bool:
        """
        Check if any Edge is connected to this socket.

        :return: True if any Edge is connected to this socket
        """
        return len(self.edges) > 0

    def isConnected(self, edge: 'Edge') -> bool:
        """
        Check if an Edge is connected to this Socket.

        :param edge: Edge to check if it is connected to this Socket
        :return: True if Edge is connected to this socket
        """
        return edge in self.edges

    def addEdge(self, edge: 'Edge') -> None:
        """
        Append an Edge to the list of connected Edges.

        :param edge: Edge to connect to this Socket
        """
        self.edges.append(edge)

    def removeEdge(self, edge: 'Edge') -> None:
        """
        Disconnect an Edge from this Socket.

        :param edge: Edge to disconnect
        """
        if edge in self.edges:
            self.edges.remove(edge)
        else:
            if DEBUG_REMOVE_WARNINGS:
                print("!W:", "Socket::removeEdge", "wanna remove edge", edge,
                      "from self.edges but it's not in the list!")

    def removeAllEdges(self, silent: bool = False) -> None:
        """
        Disconnect all Edges from this Socket.

        :param silent: If True, edges are removed without notifications
        """
        while self.edges:
            edge = self.edges.pop(0)
            if silent:
                edge.remove(silent_for_socket=self)
            else:
                edge.remove()  # Remove with notifications

    # ==================== Serialization ====================

    def determineMultiEdges(self, data: dict) -> bool:
        """
        Deserialization helper to determine multi-edges support.

        Handles legacy file format compatibility.

        :param data: Socket data in dict format
        :return: True if this Socket should support multi_edges
        """
        if 'multi_edges' in data:
            return data['multi_edges']
        else:
            # Older version of file: make RIGHT socket multi-edged by default
            return data['position'] in (RIGHT_BOTTOM, RIGHT_TOP)

    def serialize(self) -> OrderedDict:
        """Serialize the socket to OrderedDict."""
        return OrderedDict([
            ('id', self.id),
            ('index', self.index),
            ('multi_edges', self.is_multi_edges),
            ('position', self.position),
            ('socket_type', self.socket_type),
        ])

    def deserialize(
        self,
        data: dict,
        hashmap: dict = {},
        restore_id: bool = True
    ) -> bool:
        """Deserialize the socket from dict data."""
        if restore_id:
            self.id = data['id']
        self.is_multi_edges = self.determineMultiEdges(data)
        self.changeSocketType(data['socket_type'])
        hashmap[data['id']] = self
        return True
