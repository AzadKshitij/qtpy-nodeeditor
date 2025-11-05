"""
QDMGraphicsNodeModel - View wrapper for NodeModel with graphics integration.

This class bridges the NodeModel (data) with QDMGraphicsNode (graphics).
It manages the visual representation and coordinates updates through signals.

Features:
    - Wraps NodeModel with graphics capabilities
    - Connects model signals to graphics updates
    - Maintains position synchronization
    - Handles selection state
    - Integrates with controllers

Example:
    >>> model = NodeModel("my_node", "MyNode")
    >>> graphics_node_model = QDMGraphicsNodeModel(model, node_graphics_item)
    >>> # Model changes trigger graphics updates automatically
"""

from typing import TYPE_CHECKING, Optional, Tuple, Any
import logging

from qtpy.QtCore import QObject, Signal, QPointF
from qtpy.QtGui import QColor, QPen, QBrush

from nodeeditor.models import NodeModel

if TYPE_CHECKING:
    from nodeeditor.node_graphics_node import QDMGraphicsNode
    from nodeeditor.controllers import NodeController

logger = logging.getLogger(__name__)


class QDMGraphicsNodeModel(QObject):
    """
    View wrapper that synchronizes NodeModel with QDMGraphicsNode.

    This class acts as a bridge between the data model (NodeModel) and
    the graphics representation (QDMGraphicsNode). It handles signal
    connections and synchronization of state changes.

    Signals:
        graphicsUpdated: Emitted when graphics need to be redrawn
        selectionChanged(bool): Emitted when selection state changes
        positionChanged(QPointF): Emitted when position changes

    Attributes:
        model (NodeModel): The underlying data model
        graphics_item (QDMGraphicsNode): The graphics representation
        controller (NodeController): Optional controller for operations
    """

    # Signals
    graphicsUpdated = Signal()
    selectionChanged = Signal(bool)  # is_selected
    positionChanged = Signal(QPointF)

    def __init__(
        self,
        model: NodeModel,
        graphics_item: 'QDMGraphicsNode',
        controller: Optional['NodeController'] = None,
    ) -> None:
        """
        Initialize the graphics node model wrapper.

        Args:
            model: The NodeModel to wrap
            graphics_item: The QDMGraphicsNode graphics representation
            controller: Optional NodeController for operations

        Raises:
            TypeError: If model is not a NodeModel
        """
        super().__init__()

        if not isinstance(model, NodeModel):
            raise TypeError(f"model must be NodeModel, got {type(model).__name__}")

        self.model = model
        self.graphics_item = graphics_item
        self.controller = controller

        self._syncing = False  # Prevent signal loops

        # Connect model signals to graphics updates
        self._connect_model_signals()

        # Sync initial state
        self._sync_model_to_graphics()

        logger.debug(f"QDMGraphicsNodeModel initialized for node: {model.id}")

    def _connect_model_signals(self) -> None:
        """Connect model signals to graphics update methods."""
        self.model.titleChanged.connect(self._on_model_title_changed)
        self.model.positionChanged.connect(self._on_model_position_changed)
        self.model.selectedChanged.connect(self._on_model_selected_changed)
        self.model.visibleChanged.connect(self._on_model_visible_changed)
        self.model.propertyChanged.connect(self._on_model_property_changed)

    def _sync_model_to_graphics(self) -> None:
        """Sync current model state to graphics representation."""
        try:
            self._syncing = True

            # Update title
            self.graphics_item.title = self.model.title

            # Update position
            pos = self.model.position
            self.graphics_item.setPos(QPointF(pos[0], pos[1]))

            # Update selection state
            self.graphics_item.setSelected(self.model.selected)

            # Update visibility
            self.graphics_item.setVisible(self.model.visible)

            logger.debug(f"Synced model to graphics for node: {self.model.id}")

        finally:
            self._syncing = False

    def update_from_graphics(self) -> None:
        """Sync graphics state changes back to model."""
        try:
            self._syncing = True

            # Update position from graphics
            graphics_pos = self.graphics_item.pos()
            if self.controller:
                self.controller.set_node_position(
                    self.model,
                    (graphics_pos.x(), graphics_pos.y())
                )
            else:
                self.model.position = (graphics_pos.x(), graphics_pos.y())

            # Update selection from graphics
            if self.controller:
                self.controller.set_node_selected(self.model, self.graphics_item.isSelected())
            else:
                self.model.selected = self.graphics_item.isSelected()

            logger.debug(f"Synced graphics to model for node: {self.model.id}")

        finally:
            self._syncing = False

    # ======================== Model Signal Handlers ========================

    def _on_model_title_changed(self, title: str) -> None:
        """Handle title change from model."""
        if not self._syncing:
            self.graphics_item.title = title
            self.graphicsUpdated.emit()
            logger.debug(f"Node title updated: {title}")

    def _on_model_position_changed(self, pos: QPointF) -> None:
        """Handle position change from model."""
        if not self._syncing:
            graphics_pos = self.graphics_item.pos()
            model_x, model_y = pos.x(), pos.y()

            if graphics_pos.x() != model_x or graphics_pos.y() != model_y:
                self.graphics_item.setPos(QPointF(model_x, model_y))
                self.positionChanged.emit(pos)
                self.graphicsUpdated.emit()
                logger.debug(f"Node position updated: ({model_x}, {model_y})")

    def _on_model_selected_changed(self, selected: bool) -> None:
        """Handle selection change from model."""
        if not self._syncing:
            self.graphics_item.setSelected(selected)
            self.selectionChanged.emit(selected)
            self.graphicsUpdated.emit()
            logger.debug(f"Node selection changed: {selected}")

    def _on_model_visible_changed(self, visible: bool) -> None:
        """Handle visibility change from model."""
        if not self._syncing:
            self.graphics_item.setVisible(visible)
            self.graphicsUpdated.emit()
            logger.debug(f"Node visibility changed: {visible}")

    def _on_model_property_changed(self, key: str, value: Any) -> None:
        """Handle custom property change from model."""
        if not self._syncing:
            # Custom property changes can be handled here
            # For now, just emit an update signal
            self.graphicsUpdated.emit()
            logger.debug(f"Node property changed: {key} = {value}")

    @property
    def node_id(self) -> str:
        """Get the node's unique ID."""
        return self.model.id

    @property
    def node_type(self) -> str:
        """Get the node's type identifier."""
        return self.model.node_type

    def set_title(self, title: str) -> None:
        """Set node title through controller or model."""
        if self.controller:
            self.controller.set_node_title(self.model, title)
        else:
            self.model.title = title

    def set_position(self, x: float, y: float) -> None:
        """Set node position through controller or model."""
        if self.controller:
            self.controller.set_node_position(self.model, (x, y))
        else:
            self.model.position = (x, y)

    def set_selected(self, selected: bool) -> None:
        """Set node selection state through controller or model."""
        if self.controller:
            self.controller.set_node_selected(self.model, selected)
        else:
            self.model.selected = selected

    def set_visible(self, visible: bool) -> None:
        """Set node visibility through controller or model."""
        if self.controller:
            self.controller.set_node_visible(self.model, visible)
        else:
            self.model.visible = visible
