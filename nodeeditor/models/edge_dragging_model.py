"""
EdgeDraggingModel - MVC Model for edge dragging state management.

An EdgeDraggingModel manages the state of an edge being dragged from one
socket to another. It tracks the drag state without graphics coupling.

Signals:
    dragStarted(edge_id, socket_id): Emitted when drag begins
    dragUpdated(x, y): Emitted when drag position updates
    dragEnded(socket_id, valid): Emitted when drag ends
    dragCancelled: Emitted when drag is cancelled
"""

from typing import Optional
import logging

from qtpy.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class EdgeDraggingModel(QObject):
    """
    Model representing the state of an edge being dragged.

    Tracks the drag state for an edge being created/modified during user
    interaction. Emits signals when drag state changes.

    Signals:
        dragStarted(edge_id, socket_id): When drag starts
        dragUpdated(x, y): When drag position updates
        dragEnded(socket_id, valid): When drag ends
        dragCancelled: When drag is cancelled

    Attributes:
        is_dragging (bool): Whether currently dragging
        edge_id (str): ID of edge being dragged
        start_socket_id (int): ID of starting socket
    """

    # Qt Signals
    dragStarted = Signal(str, int)      # edge_id, socket_id
    dragUpdated = Signal(float, float)  # x, y
    dragEnded = Signal(int, bool)       # socket_id, is_valid
    dragCancelled = Signal()

    def __init__(self) -> None:
        """Initialize a new EdgeDraggingModel."""
        super().__init__()
        self._is_dragging: bool = False
        self._edge_id: Optional[str] = None
        self._start_socket_id: Optional[int] = None
        self._last_x: float = 0.0
        self._last_y: float = 0.0

    @property
    def is_dragging(self) -> bool:
        """
        Check if currently dragging an edge.

        Returns:
            True if dragging, False otherwise
        """
        return self._is_dragging

    @property
    def edge_id(self) -> Optional[str]:
        """
        Get the ID of the edge being dragged.

        Returns:
            Edge ID or None if not dragging
        """
        return self._edge_id

    @property
    def start_socket_id(self) -> Optional[int]:
        """
        Get the ID of the starting socket.

        Returns:
            Socket ID or None if not dragging
        """
        return self._start_socket_id

    @property
    def last_position(self) -> tuple:
        """
        Get the last drag position.

        Returns:
            (x, y) tuple with last position
        """
        return (self._last_x, self._last_y)

    def start_drag(self, edge_id: str, socket_id: int) -> None:
        """
        Start a drag operation.

        Args:
            edge_id: ID of the edge being dragged
            socket_id: ID of the starting socket
        """
        self._is_dragging = True
        self._edge_id = edge_id
        self._start_socket_id = socket_id
        self.dragStarted.emit(edge_id, socket_id)

    def update_position(self, x: float, y: float) -> None:
        """
        Update the drag position.

        Args:
            x: New X coordinate
            y: New Y coordinate
        """
        if not self._is_dragging:
            return

        self._last_x = x
        self._last_y = y
        self.dragUpdated.emit(x, y)

    def end_drag(self, end_socket_id: int, is_valid: bool = True) -> None:
        """
        End a drag operation.

        Args:
            end_socket_id: ID of the ending socket
            is_valid: Whether the drag resulted in a valid connection
        """
        if not self._is_dragging:
            return

        self._is_dragging = False
        self.dragEnded.emit(end_socket_id, is_valid)
        
        # Reset state
        self._edge_id = None
        self._start_socket_id = None
        self._last_x = 0.0
        self._last_y = 0.0

    def cancel_drag(self) -> None:
        """Cancel the current drag operation."""
        if not self._is_dragging:
            return

        self._is_dragging = False
        self.dragCancelled.emit()
        
        # Reset state
        self._edge_id = None
        self._start_socket_id = None
        self._last_x = 0.0
        self._last_y = 0.0
