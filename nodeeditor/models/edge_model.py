"""
EdgeModel - MVC Model for representing edges (connections) between nodes.

An EdgeModel represents a connection between two sockets on different nodes.
It stores references to the start and end sockets and emits signals when
the connection state changes.

Signals:
    connectionChanged: Emitted when edge connection state changes
    typeChanged: Emitted when edge type/style changes (int)
"""

from typing import TYPE_CHECKING, Optional, Callable, List
import logging

from qtpy.QtCore import QObject, Signal

if TYPE_CHECKING:
    from .socket_model import SocketModel

logger = logging.getLogger(__name__)


class EdgeModel(QObject):
    """
    Model representing an edge (connection) between two sockets.

    An EdgeModel represents a connection between two sockets on different nodes.
    It stores references to the start and end sockets and tracks the type/style
    of the edge (e.g., straight line, bezier curve).

    Signals:
        connectionChanged: Emitted when connection state changes
        typeChanged(int): Emitted when edge type changes

    Example:
        >>> edge = EdgeModel()
        >>> edge.typeChanged.connect(lambda t: print(f"Type: {t}"))
        >>> edge.edge_type = 2  # Bezier curve
        Type: 2
    """

    # Edge type constants
    STRAIGHT = 1
    BEZIER = 2
    POLYLINE = 3

    # Class variable for registered validators
    _validators: List[Callable] = []

    # Qt Signals
    connectionChanged = Signal()  # Emitted when sockets change
    typeChanged = Signal(int)     # Emitted with new type

    def __init__(
        self,
        start_socket: Optional['SocketModel'] = None,
        end_socket: Optional['SocketModel'] = None,
        edge_id: Optional[int] = None,
    ) -> None:
        """Initialize a new EdgeModel with backward compatibility support.

        This constructor supports multiple invocation patterns for legacy code:

        * ``EdgeModel()`` → creates a detached edge
        * ``EdgeModel(edge_id)`` → legacy positional ID
        * ``EdgeModel(start_socket, end_socket)`` → directly connects sockets
        * ``EdgeModel(start_socket, end_socket, edge_id="...")`` → explicit ID

        Args:
            start_socket: Optional starting socket for the edge
            end_socket: Optional ending socket for the edge
            edge_id: Optional unique identifier, auto-generated if not provided
        """
        super().__init__()


        self._id: int = edge_id or id(self)
        self._start_socket: Optional['SocketModel'] = None
        self._end_socket: Optional['SocketModel'] = None
        self._type: int = self.BEZIER
        self._data: dict = {}

        if start_socket is not None:
            self.start_socket = start_socket
        if end_socket is not None:
            self.end_socket = end_socket

    @property
    def id(self) -> int:
        """
        Get the unique identifier for this edge (read-only).

        Returns:
            Unique edge ID (UUID string)
        """
        return self._id

    @property
    def start_socket(self) -> Optional['SocketModel']:
        """
        Get the starting socket (typically an output).

        Returns:
            SocketModel or None if not connected
        """
        return self._start_socket

    @start_socket.setter
    def start_socket(self, value: Optional['SocketModel']) -> None:
        """
        Set the starting socket.

        Emits connectionChanged signal if value changed.

        Args:
            value: SocketModel or None

        Raises:
            TypeError: If value is not SocketModel or None
        """
        from .socket_model import SocketModel

        if value is not None and not isinstance(value, SocketModel):
            raise TypeError(
                f"start_socket must be SocketModel or None, got {type(value).__name__}"
            )

        if self._start_socket != value:
            self._start_socket = value
            self.connectionChanged.emit()

    @property
    def end_socket(self) -> Optional['SocketModel']:
        """
        Get the ending socket (typically an input).

        Returns:
            SocketModel or None if not connected
        """
        return self._end_socket

    @end_socket.setter
    def end_socket(self, value: Optional['SocketModel']) -> None:
        """
        Set the ending socket.

        Emits connectionChanged signal if value changed.

        Args:
            value: SocketModel or None

        Raises:
            TypeError: If value is not SocketModel or None
        """
        from .socket_model import SocketModel

        if value is not None and not isinstance(value, SocketModel):
            raise TypeError(
                f"end_socket must be SocketModel or None, got {type(value).__name__}"
            )

        if self._end_socket != value:
            self._end_socket = value
            self.connectionChanged.emit()

    @property
    def is_connected(self) -> bool:
        """
        Check if both sockets are connected.

        Returns:
            True if both start and end sockets are set, False otherwise
        """
        return self._start_socket is not None and self._end_socket is not None

    @property
    def edge_type(self) -> int:
        """
        Get the edge type/style.

        Returns:
            One of: STRAIGHT (1), BEZIER (2), POLYLINE (3)
        """
        return self._type

    @edge_type.setter
    def edge_type(self, value: int) -> None:
        """
        Set the edge type/style.

        Emits typeChanged signal if value changed.

        Args:
            value: One of: STRAIGHT (1), BEZIER (2), POLYLINE (3)

        Raises:
            ValueError: If value is not a valid edge type
        """
        if value not in (self.STRAIGHT, self.BEZIER, self.POLYLINE):
            raise ValueError(
                f"edge_type must be STRAIGHT (1), BEZIER (2), or POLYLINE (3), got {value}"
            )

        if self._type != value:
            self._type = int(value)
            self.typeChanged.emit(value)

    def get_edge_type_name(self) -> str:
        """
        Get the human-readable name of the edge type.

        Returns:
            One of: "STRAIGHT", "BEZIER", "POLYLINE"
        """
        type_names = {
            self.STRAIGHT: "STRAIGHT",
            self.BEZIER: "BEZIER",
            self.POLYLINE: "POLYLINE",
        }
        return type_names.get(self._type, "UNKNOWN")

    def set_data(self, key: str, value) -> None:
        """
        Set custom data on the edge.

        Useful for storing edge-specific information like thickness, color, etc.

        Args:
            key: Data key
            value: Data value
        """
        self._data[key] = value

    def get_data(self, key: str, default=None):
        """
        Get custom data from the edge.

        Args:
            key: Data key
            default: Default value if key not found

        Returns:
            Data value or default
        """
        return self._data.get(key, default)

    def validate_connection(self) -> tuple[bool, str]:
        """
        Validate that the edge connection is properly formed.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if self._start_socket is None:
            return False, "Start socket not set"
        if self._end_socket is None:
            return False, "End socket not set"

        if self._start_socket.is_input and self._end_socket.is_input:
            return False, "Cannot connect two input sockets"

        if self._start_socket.is_output and self._end_socket.is_output:
            return False, "Cannot connect two output sockets"

        if self._start_socket.is_input and self._end_socket.is_output:
            return False, "Data must flow from output to input"

        return True, ""

    @classmethod
    def register_edge_validator(cls, validator: Callable) -> None:
        """
        Register a new edge validator callback.

        Validators are called with (input_socket, output_socket) and should
        return True if the connection is valid, False otherwise.

        Args:
            validator: Callable that validates edge connections
        """
        if validator not in cls._validators:
            cls._validators.append(validator)

    @classmethod
    def unregister_edge_validator(cls, validator: Callable) -> None:
        """
        Unregister an edge validator callback.

        Args:
            validator: Validator to remove
        """
        if validator in cls._validators:
            cls._validators.remove(validator)

    @classmethod
    def clear_edge_validators(cls) -> None:
        """Clear all registered validators."""
        cls._validators.clear()

    @classmethod
    def get_edge_validators(cls) -> List[Callable]:
        """
        Get all registered validators.

        Returns:
            List of registered validator functions
        """
        return cls._validators.copy()

    @staticmethod
    def validate_socket_connection(start_socket: object, end_socket: object) -> bool:
        """
        Validate a potential connection between two sockets using registered validators.

        Calls all registered validators in order. If any returns False, validation fails.
        Validators can work with both Socket and SocketModel objects.

        Args:
            start_socket: Socket or SocketModel to connect from
            end_socket: Socket or SocketModel to connect to

        Returns:
            True if valid, False if any validator rejects it
        """
        # Run all registered validators
        for validator in EdgeModel._validators:
            try:
                if not validator(start_socket, end_socket):
                    return False
            except Exception as e:
                logger.warning(f"Validator error: {e}")
                return False

        return True

    def serialize(self) -> dict:
        """
        Serialize the edge model to a dictionary.

        Socket references are not directly serialized; instead their IDs
        are stored. The application layer must map IDs back to socket objects
        when deserializing.

        Returns:
            Dictionary containing edge data
        """
        return {
            'id': self._id,
            'start_socket_id': self._start_socket.id if self._start_socket else None,
            'end_socket_id': self._end_socket.id if self._end_socket else None,
            'type': self._type,
            'data': dict(self._data),
        }

    @classmethod
    def deserialize(cls, data: dict) -> 'EdgeModel':
        """
        Deserialize an edge model from a dictionary.

        Note: Socket references must be set separately after deserialization
        by mapping socket IDs to actual SocketModel objects.

        Args:
            data: Dictionary containing edge data

        Returns:
            New EdgeModel instance (with socket references set to None)

        Raises:
            KeyError: If required keys are missing
            ValueError: If data is invalid
        """
        if not isinstance(data, dict):
            raise TypeError(f"data must be dict, got {type(data).__name__}")

        try:
            edge = cls(edge_id=data.get('id'))
            edge._type = int(data.get('type', cls.BEZIER))
            edge._data = dict(data.get('data', {}))
            return edge
        except (KeyError, ValueError) as e:
            raise ValueError(f"Invalid edge data: {e}") from e

    def __repr__(self) -> str:
        """Return string representation of the edge model."""
        start = self._start_socket.id[:8] if self._start_socket else "None"
        end = self._end_socket.id[:8] if self._end_socket else "None"
        return f"EdgeModel(id={self._id!r}, {start}→{end}, type={self.get_edge_type_name()})"

    def __str__(self) -> str:
        """Return human-readable string of the edge model."""
        if self.is_connected:
            start_name = f"{self._start_socket.name}" if self._start_socket else "?"
            end_name = f"{self._end_socket.name}" if self._end_socket else "?"
            return f"{start_name} → {end_name}"
        return f"Edge({self.get_edge_type_name()})"

    def __eq__(self, other: object) -> bool:
        """Check equality based on edge ID."""
        if not isinstance(other, EdgeModel):
            return False
        return self._id == other._id

    def __hash__(self) -> int:
        """Make EdgeModel hashable for use in sets/dicts."""
        return hash(self._id)
