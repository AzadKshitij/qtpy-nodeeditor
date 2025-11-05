"""
SocketModel - MVC Model for representing sockets (ports) on nodes.

A SocketModel represents an input or output port on a node. It tracks
connections to edges and emits signals when connections change.

Signals:
    connectionChanged: Emitted when an edge connects/disconnects (object)
    validationChanged: Emitted when validation state changes (bool, str)
"""

from typing import TYPE_CHECKING, List, Optional
import logging

from qtpy.QtCore import QObject, Signal

if TYPE_CHECKING:
    from .edge_model import EdgeModel
    from .node_model import NodeModel

logger = logging.getLogger(__name__)


class SocketModel(QObject):
    """
    Model representing a socket (port) on a node.

    A SocketModel represents an input or output port on a node that can be
    connected to other sockets via edges. It tracks all connected edges
    and emits signals when connections change.

    Signals:
        connectionChanged(object): Emitted when edge connected/disconnected
        validationChanged(bool, str): Emitted when validation state changes

    Example:
        >>> socket = SocketModel("input", SocketType.INPUT)
        >>> socket.connectionChanged.connect(lambda edge: print(f"Connected: {edge}"))
        >>> # When an edge is connected, signal is emitted
    """

    # Socket type constants
    INPUT = 1
    OUTPUT = 2

    # Qt Signals
    typeChanged = Signal(int)  # Emitted when socket type changes
    connectionChanged = Signal(object)  # Emits EdgeModel or None
    validationChanged = Signal(bool, str)  # (is_valid, error_message)

    def __init__(
        self,
        name: str,
        socket_type: int,
        socket_id: Optional[str] = None,
        parent_node: Optional["NodeModel"] = None,
    ) -> None:
        """
        Initialize a new SocketModel.

        Args:
            name: Display name for the socket (e.g., "input", "output")
            socket_type: Either INPUT (1) or OUTPUT (2)
            socket_id: Optional unique identifier, auto-generated if not provided
            parent_node: Optional reference to parent NodeModel

        Raises:
            ValueError: If socket_type is not INPUT or OUTPUT
            TypeError: If name is not a string
        """
        super().__init__()

        if socket_type not in (self.INPUT, self.OUTPUT):
            raise ValueError(f"socket_type must be INPUT (1) or OUTPUT (2), got {socket_type}")

        if not isinstance(name, str):
            raise TypeError(f"name must be str, got {type(name).__name__}")

        self._id: str = socket_id or str(id(self))
        self._name: str = name
        self._type: int = socket_type
        self._edges: List['EdgeModel'] = []
        self._is_valid: bool = True
        self._validation_error: str = ""
        self._parent_node: Optional["NodeModel"] = parent_node

    @property
    def id(self) -> str:
        """
        Get the unique identifier for this socket (read-only).

        Returns:
            Unique socket ID (UUID string)
        """
        return self._id

    @property
    def name(self) -> str:
        """
        Get the socket's display name (read-only).

        Returns:
            Socket name (e.g., "input", "output")
        """
        return self._name

    @property
    def socket_type(self) -> int:
        """
        Get the socket type (read-only).

        Returns:
            Either INPUT (1) or OUTPUT (2)
        """
        return self._type

    @property
    def parent_node(self) -> Optional['NodeModel']:
        """
        Get the parent node this socket belongs to.

        Returns:
            NodeModel or None if not set
        """
        return self._parent_node

    @property
    def is_input(self) -> bool:
        """
        Check if this is an input socket.

        Returns:
            True if socket is INPUT type, False otherwise
        """
        return self._type == self.INPUT

    @property
    def is_output(self) -> bool:
        """
        Check if this is an output socket.

        Returns:
            True if socket is OUTPUT type, False otherwise
        """
        return self._type == self.OUTPUT

    @property
    def edges(self) -> List['EdgeModel']:
        """
        Get all connected edges (read-only list).

        Returns a shallow copy to prevent external modification.

        Returns:
            List of connected EdgeModel objects
        """
        return list(self._edges)

    @property
    def edge_count(self) -> int:
        """
        Get the number of connected edges.

        Returns:
            Count of connected edges
        """
        return len(self._edges)

    @property
    def is_connected(self) -> bool:
        """
        Check if this socket has any connections.

        Returns:
            True if at least one edge is connected, False otherwise
        """
        return len(self._edges) > 0

    @property
    def is_valid(self) -> bool:
        """
        Get the validation state of the socket.

        Returns:
            True if socket is in valid state, False otherwise
        """
        return self._is_valid

    @property
    def validation_error(self) -> str:
        """
        Get the validation error message (if any).

        Returns:
            Error message string, empty if no error
        """
        return self._validation_error

    def add_edge(self, edge: 'EdgeModel') -> bool:
        """
        Connect an edge to this socket.

        Args:
            edge: EdgeModel to connect

        Returns:
            True if edge was added, False if already connected

        Raises:
            TypeError: If edge is not an EdgeModel
        """
        from .edge_model import EdgeModel

        if not isinstance(edge, EdgeModel):
            raise TypeError(f"edge must be EdgeModel, got {type(edge).__name__}")

        if edge not in self._edges:
            self._edges.append(edge)
            self.connectionChanged.emit(edge)
            return True
        return False

    def remove_edge(self, edge: 'EdgeModel') -> bool:
        """
        Disconnect an edge from this socket.

        Args:
            edge: EdgeModel to disconnect

        Returns:
            True if edge was removed, False if not found

        Raises:
            TypeError: If edge is not an EdgeModel
        """
        from .edge_model import EdgeModel

        if not isinstance(edge, EdgeModel):
            raise TypeError(f"edge must be EdgeModel, got {type(edge).__name__}")

        if edge in self._edges:
            self._edges.remove(edge)
            self.connectionChanged.emit(None)
            return True
        return False

    # ------------------------------------------------------------------
    # Legacy compatibility helpers
    # ------------------------------------------------------------------

    def get_edges(self) -> List['EdgeModel']:
        """Return connected edges (legacy API)."""
        return list(self._edges)

    def has_edge(self, edge: "EdgeModel") -> bool:
        """
        Check if a specific edge is connected.

        Args:
            edge: EdgeModel to check

        Returns:
            True if edge is connected, False otherwise
        """
        return edge in self._edges

    def clear_edges(self) -> int:
        """
        Disconnect all edges from this socket.

        Returns:
            Number of edges that were disconnected
        """
        count = len(self._edges)
        self._edges.clear()
        if count > 0:
            self.connectionChanged.emit(None)
        return count

    def set_valid(self, is_valid: bool, error_message: str = "") -> None:
        """
        Set the validation state of the socket.

        Emits validationChanged signal if state changed.

        Args:
            is_valid: True if socket is valid, False otherwise
            error_message: Optional error message if invalid

        Raises:
            TypeError: If is_valid is not boolean
        """
        if not isinstance(is_valid, bool):
            raise TypeError(f"is_valid must be bool, got {type(is_valid).__name__}")

        if self._is_valid != is_valid or self._validation_error != error_message:
            self._is_valid = is_valid
            self._validation_error = error_message if not is_valid else ""
            self.validationChanged.emit(is_valid, self._validation_error)

    def serialize(self) -> dict:
        """
        Serialize the socket model to a dictionary.

        Note: Edges are not serialized here; they are handled by EdgeModel.

        Returns:
            Dictionary containing socket data
        """
        return {
            'id': self._id,
            'name': self._name,
            'type': self._type,
            'is_valid': self._is_valid,
            'validation_error': self._validation_error,
        }

    @classmethod
    def deserialize(cls, data: dict) -> 'SocketModel':
        """
        Deserialize a socket model from a dictionary.

        Args:
            data: Dictionary containing socket data

        Returns:
            New SocketModel instance

        Raises:
            KeyError: If required keys are missing
            ValueError: If data is invalid
        """
        if not isinstance(data, dict):
            raise TypeError(f"data must be dict, got {type(data).__name__}")

        try:
            socket = cls(
                name=data['name'],
                socket_type=data['type'],
                socket_id=data.get('id'),
            )
            socket._is_valid = bool(data.get('is_valid', True))
            socket._validation_error = str(data.get('validation_error', ''))
            return socket
        except KeyError as e:
            raise ValueError(f"Missing required field in socket data: {e}") from e

    def __repr__(self) -> str:
        """Return string representation of the socket model."""
        type_str = "INPUT" if self.is_input else "OUTPUT"
        return f"SocketModel(id={self._id!r}, name={self._name!r}, type={type_str}, edges={len(self._edges)})"

    def __str__(self) -> str:
        """Return human-readable string of the socket model."""
        type_str = "In" if self.is_input else "Out"
        return f"{type_str}:{self._name}"

    def __eq__(self, other: object) -> bool:
        """Check equality based on socket ID."""
        if not isinstance(other, SocketModel):
            return False
        return self._id == other._id

    def __hash__(self) -> int:
        """Make SocketModel hashable for use in sets/dicts."""
        return hash(self._id)
