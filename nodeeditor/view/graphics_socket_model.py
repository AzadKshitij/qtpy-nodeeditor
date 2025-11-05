"""
QDMGraphicsSocketModel - View wrapper for SocketModel with graphics integration.

This class bridges the SocketModel (data) with QDMGraphicsSocket (graphics).
It manages the visual representation and coordinates updates through signals.

Features:
    - Wraps SocketModel with graphics capabilities
    - Connects model signals to graphics updates
    - Manages validation state display
    - Handles connection updates
    - Integrates with controllers

Example:
    >>> model = SocketModel("input", SocketModel.INPUT)
    >>> graphics_socket_item = QDMGraphicsSocket(socket_obj)
    >>> graphics_socket_model = QDMGraphicsSocketModel(model, graphics_socket_item)
    >>> # Model changes trigger graphics updates automatically
"""

from typing import TYPE_CHECKING, Optional, Any
import logging

from qtpy.QtCore import QObject, Signal
from qtpy.QtGui import QColor

from nodeeditor.models import SocketModel

if TYPE_CHECKING:
    from nodeeditor.node_graphics_socket import QDMGraphicsSocket

logger = logging.getLogger(__name__)


class QDMGraphicsSocketModel(QObject):
    """
    View wrapper that synchronizes SocketModel with QDMGraphicsSocket.

    This class acts as a bridge between the data model (SocketModel) and
    the graphics representation (QDMGraphicsSocket). It handles signal
    connections and synchronization of state changes.

    Signals:
        graphicsUpdated: Emitted when graphics need to be redrawn
        validationChanged(bool, str): Emitted when validation state changes
        connectionChanged: Emitted when connection state changes

    Attributes:
        model (SocketModel): The underlying data model
        graphics_item (QDMGraphicsSocket): The graphics representation
    """

    # Signals
    graphicsUpdated = Signal()
    validationChanged = Signal(bool, str)  # (is_valid, error_message)
    connectionChanged = Signal()

    def __init__(
        self,
        model: SocketModel,
        graphics_item: 'QDMGraphicsSocket',
    ) -> None:
        """
        Initialize the graphics socket model wrapper.

        Args:
            model: The SocketModel to wrap
            graphics_item: The QDMGraphicsSocket graphics representation

        Raises:
            TypeError: If model is not a SocketModel
        """
        super().__init__()

        if not isinstance(model, SocketModel):
            raise TypeError(f"model must be SocketModel, got {type(model).__name__}")

        self.model = model
        self.graphics_item = graphics_item

        self._syncing = False  # Prevent signal loops
        self._validation_color_valid = QColor("#FF52e220")  # Green
        self._validation_color_invalid = QColor("#FFb54747")  # Red
        self._validation_color_default = QColor("#FF0056a6")  # Blue

        # Connect model signals to graphics updates
        self._connect_model_signals()

        # Sync initial state
        self._sync_model_to_graphics()

        logger.debug(f"QDMGraphicsSocketModel initialized for socket: {model.id}")

    def _connect_model_signals(self) -> None:
        """Connect model signals to graphics update methods."""
        self.model.connectionChanged.connect(self._on_model_connection_changed)
        self.model.validationChanged.connect(self._on_model_validation_changed)

    def _sync_model_to_graphics(self) -> None:
        """Sync current model state to graphics representation."""
        try:
            self._syncing = True

            # Update validation color
            if not self.model.is_valid:
                self._apply_validation_color(self._validation_color_invalid)
            else:
                self._apply_validation_color(self._validation_color_default)

            # Update socket type color if needed
            self._update_socket_color()

            logger.debug(f"Synced model to graphics for socket: {self.model.id}")

        finally:
            self._syncing = False

    def _apply_validation_color(self, color: QColor) -> None:
        """Apply validation color to graphics item."""
        try:
            # Update the socket color based on validation state
            # Exact implementation depends on QDMGraphicsSocket API
            self.graphics_item._color_background = color
            self.graphics_item._brush.setColor(color)
            self.graphics_item.update()
        except Exception as e:
            logger.warning(f"Could not apply validation color: {e}")

    def _update_socket_color(self) -> None:
        """Update socket color based on type."""
        try:
            # This syncs the socket type to graphics
            self.graphics_item.changeSocketType()
        except Exception as e:
            logger.warning(f"Could not update socket color: {e}")

    # ======================== Model Signal Handlers ========================

    def _on_model_connection_changed(self, edge: Any = None) -> None:
        """Handle connection change from model."""
        if not self._syncing:
            self.connectionChanged.emit()
            self.graphicsUpdated.emit()
            logger.debug(f"Socket connection changed: {self.model.id}")

    def _on_model_validation_changed(self, is_valid: bool, error_msg: str) -> None:
        """Handle validation change from model."""
        if not self._syncing:
            # Update color based on validation state
            if is_valid:
                self._apply_validation_color(self._validation_color_valid)
            else:
                self._apply_validation_color(self._validation_color_invalid)

            self.validationChanged.emit(is_valid, error_msg)
            self.graphicsUpdated.emit()
            logger.debug(f"Socket validation changed: valid={is_valid}")

    @property
    def socket_id(self) -> str:
        """Get the socket's unique ID."""
        return self.model.id

    @property
    def socket_type(self) -> int:
        """Get the socket type (INPUT or OUTPUT)."""
        return self.model.socket_type

    @property
    def is_input(self) -> bool:
        """Check if this is an input socket."""
        return self.model.socket_type == SocketModel.INPUT

    @property
    def is_output(self) -> bool:
        """Check if this is an output socket."""
        return self.model.socket_type == SocketModel.OUTPUT

    @property
    def edge_count(self) -> int:
        """Get the number of connected edges."""
        return len(self.model.edges)

    def is_connected(self) -> bool:
        """Check if the socket has any connections."""
        return len(self.model.edges) > 0

    def set_validation_error(self, error_msg: str) -> None:
        """Set a validation error on this socket."""
        self.model.is_valid = False
        self.model.validation_error = error_msg

    def clear_validation(self) -> None:
        """Clear validation errors."""
        self.model.is_valid = True
        self.model.validation_error = ""

    def set_validation_color_valid(self, color: QColor) -> None:
        """Set the color to use for valid sockets."""
        self._validation_color_valid = color

    def set_validation_color_invalid(self, color: QColor) -> None:
        """Set the color to use for invalid sockets."""
        self._validation_color_invalid = color
