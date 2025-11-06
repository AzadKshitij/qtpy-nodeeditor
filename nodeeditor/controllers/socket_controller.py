# -*- coding: utf-8 -*-
"""
SocketController - Controller for managing SocketModel operations.

The SocketController handles operations on individual Socket objects,
managing the relationship between sockets and edges, validation, and state.
"""

from typing import TYPE_CHECKING, Optional, List
import logging

from qtpy.QtCore import QObject

if TYPE_CHECKING:
    from nodeeditor.models.socket_model import SocketModel
    from nodeeditor.node_edge import Edge

logger = logging.getLogger(__name__)


class SocketController(QObject):
    """
    Controller for managing Socket operations.

    The SocketController manages socket state, edge connections, and validation.
    It delegates to the SocketModel for data storage and handles business logic.

    Attributes:
        model (SocketModel): The underlying socket model
    """

    def __init__(self, socket_model: 'SocketModel') -> None:
        """
        Initialize the SocketController.

        Args:
            socket_model: The SocketModel instance to manage
        """
        super().__init__()
        self.model = socket_model

    # ==================== Socket Properties ====================

    @property
    def socket_type(self):
        """Get the socket type/color."""
        return self.model.socket_type

    @property
    def is_input(self) -> bool:
        """Is this an input socket?"""
        return self.model.is_input

    @property
    def is_output(self) -> bool:
        """Is this an output socket?"""
        return not self.model.is_input

    @property
    def edges(self) -> List['Edge']:
        """Get all edges connected to this socket."""
        return self.model.edges

    @property
    def is_connected(self) -> bool:
        """Is this socket connected to any edges?"""
        return len(self.model.edges) > 0

    # ==================== Edge Management ====================

    def connect_edge(self, edge: 'Edge') -> None:
        """
        Register an edge connected to this socket.

        Args:
            edge: The Edge to connect
        """
        if edge not in self.model.edges:
            self.model.edges.append(edge)
            logger.debug(f"Connected edge {edge.id} to socket {self.model.id}")

    def disconnect_edge(self, edge: 'Edge') -> None:
        """
        Unregister an edge from this socket.

        Args:
            edge: The Edge to disconnect
        """
        if edge in self.model.edges:
            self.model.edges.remove(edge)
            logger.debug(f"Disconnected edge {edge.id} from socket {self.model.id}")

    def get_connected_edges(self) -> List['Edge']:
        """Get all edges connected to this socket."""
        return self.model.edges.copy()

    def clear_edges(self) -> None:
        """Remove all edge connections."""
        self.model.edges.clear()

    # ==================== Validation ====================

    def can_connect_to(self, other_socket: 'SocketController') -> bool:
        """
        Check if this socket can connect to another socket.

        Args:
            other_socket: The other SocketController to check

        Returns:
            True if connection is possible
        """
        # Can't connect socket to itself
        if self.model.id == other_socket.model.id:
            return False

        # Can't connect two input sockets
        if self.is_input and other_socket.is_input:
            return False

        # Can't connect two output sockets
        if self.is_output and other_socket.is_output:
            return False

        return True

    # ==================== State Management ====================

    def get_position(self) -> tuple:
        """Get socket position."""
        return self.model.position

    def get_index(self) -> int:
        """Get socket index on the node."""
        return self.model.index

    def get_socket_type(self):
        """Get socket type identifier."""
        return self.model.socket_type
