"""
QDMGraphicsEdgeModel - View wrapper for EdgeModel with graphics integration.

This class bridges the EdgeModel (data) with QDMGraphicsEdge (graphics).
It manages the visual representation and coordinates updates through signals.

Features:
    - Wraps EdgeModel with graphics capabilities
    - Connects model signals to graphics updates
    - Manages edge type changes
    - Handles connection state synchronization
    - Integrates with controllers

Example:
    >>> model = EdgeModel()
    >>> graphics_edge_item = QDMGraphicsEdge(edge_obj)
    >>> graphics_edge_model = QDMGraphicsEdgeModel(model, graphics_edge_item)
    >>> # Model changes trigger graphics updates automatically
"""

from typing import TYPE_CHECKING, Optional, Any
import logging

from qtpy.QtCore import QObject, Signal

from nodeeditor.models import EdgeModel

if TYPE_CHECKING:
    from nodeeditor.views.graphics.node_graphics_edge import QDMGraphicsEdge
    from nodeeditor.controllers import EdgeController

logger = logging.getLogger(__name__)


class QDMGraphicsEdgeModel(QObject):
    """
    View wrapper that synchronizes EdgeModel with QDMGraphicsEdge.

    This class acts as a bridge between the data model (EdgeModel) and
    the graphics representation (QDMGraphicsEdge). It handles signal
    connections and synchronization of state changes.

    Signals:
        graphicsUpdated: Emitted when graphics need to be redrawn
        typeChanged(int): Emitted when edge type changes
        connectionChanged: Emitted when connection state changes

    Attributes:
        model (EdgeModel): The underlying data model
        graphics_item (QDMGraphicsEdge): The graphics representation
        controller (EdgeController): Optional controller for operations
    """

    # Signals
    graphicsUpdated = Signal()
    typeChanged = Signal(int)  # new_type
    connectionChanged = Signal()

    def __init__(
        self,
        model: EdgeModel,
        graphics_item: 'QDMGraphicsEdge',
        controller: Optional['EdgeController'] = None,
    ) -> None:
        """
        Initialize the graphics edge model wrapper.

        Args:
            model: The EdgeModel to wrap
            graphics_item: The QDMGraphicsEdge graphics representation
            controller: Optional EdgeController for operations

        Raises:
            TypeError: If model is not an EdgeModel
        """
        super().__init__()

        if not isinstance(model, EdgeModel):
            raise TypeError(f"model must be EdgeModel, got {type(model).__name__}")

        self.model = model
        self.graphics_item = graphics_item
        self.controller = controller

        self._syncing = False  # Prevent signal loops

        # Connect model signals to graphics updates
        self._connect_model_signals()

        # Sync initial state
        self._sync_model_to_graphics()

        logger.debug(f"QDMGraphicsEdgeModel initialized for edge: {model.id}")

    def _connect_model_signals(self) -> None:
        """Connect model signals to graphics update methods."""
        self.model.connectionChanged.connect(self._on_model_connection_changed)
        self.model.typeChanged.connect(self._on_model_type_changed)

    def _sync_model_to_graphics(self) -> None:
        """Sync current model state to graphics representation."""
        try:
            self._syncing = True

            # Update connection state
            if self.model.start_socket and self.model.end_socket:
                # Edge is connected - position graphics based on sockets
                self._update_graphics_from_sockets()

            # Update edge type (this affects drawing)
            self._apply_edge_type_to_graphics()

            logger.debug(f"Synced model to graphics for edge: {self.model.id}")

        finally:
            self._syncing = False

    def _update_graphics_from_sockets(self) -> None:
        """Update graphics item position based on connected sockets."""
        # This requires access to the graphics socket positions
        # The exact implementation depends on the QDMGraphicsEdge API
        # For now, emit update signal to trigger redraw
        self.graphicsUpdated.emit()

    def _apply_edge_type_to_graphics(self) -> None:
        """Apply edge type style to graphics item."""
        try:
            # Map model edge types to graphics settings
            edge_type = self.model.edge_type

            if edge_type == EdgeModel.STRAIGHT:
                self.graphics_item.edge_type = 0  # Assuming 0 = straight
            elif edge_type == EdgeModel.BEZIER:
                self.graphics_item.edge_type = 1  # Assuming 1 = bezier
            elif edge_type == EdgeModel.POLYLINE:
                self.graphics_item.edge_type = 2  # Assuming 2 = polyline

            self.graphics_item.update_path()

        except Exception as e:
            logger.warning(f"Could not apply edge type to graphics: {e}")

    # ======================== Model Signal Handlers ========================

    def _on_model_connection_changed(self) -> None:
        """Handle connection change from model."""
        if not self._syncing:
            self._update_graphics_from_sockets()
            self.connectionChanged.emit()
            self.graphicsUpdated.emit()
            logger.debug(f"Edge connection changed: {self.model.id}")

    def _on_model_type_changed(self, new_type: int) -> None:
        """Handle edge type change from model."""
        if not self._syncing:
            self._apply_edge_type_to_graphics()
            self.typeChanged.emit(new_type)
            self.graphicsUpdated.emit()
            logger.debug(f"Edge type changed to: {new_type}")

    @property
    def edge_id(self) -> str:
        """Get the edge's unique ID."""
        return self.model.id

    def set_type(self, edge_type: int) -> None:
        """Set edge type through controller or model."""
        if self.controller:
            self.controller.set_edge_type(self.model, edge_type)
        else:
            self.model.edge_type = edge_type

    def is_connected(self) -> bool:
        """Check if the edge is fully connected."""
        return self.model.start_socket is not None and self.model.end_socket is not None

    def get_start_socket(self):
        """Get the start socket model."""
        return self.model.start_socket

    def get_end_socket(self):
        """Get the end socket model."""
        return self.model.end_socket
