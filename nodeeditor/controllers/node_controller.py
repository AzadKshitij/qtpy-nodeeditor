"""
NodeController - Controller for managing NodeModel operations.

The NodeController handles all business logic for node operations, coordinating
between the NodeModel (data) and the view (graphics). It manages validation,
state transitions, and integration with the undo/redo system.

Features:
    - Node creation, deletion, and modification
    - Property validation and change coordination
    - Signal propagation to views
    - Undo/redo command generation and management
    - Serialization/deserialization coordination

Example:
    >>> from nodeeditor.controllers import NodeController
    >>> from nodeeditor.models import NodeModel, SceneModel
    >>> scene_model = SceneModel()
    >>> controller = NodeController(scene_model)
    >>> node = controller.create_node("my_node_type", "MyNode", (100, 200))
    >>> controller.set_node_title(node, "Updated Title")
"""

from typing import TYPE_CHECKING, Optional, Any, Dict, List, Tuple, Callable, Union
import logging

from qtpy.QtCore import QObject, Signal, QPointF

from nodeeditor.models import NodeModel, SocketModel, SceneModel
from nodeeditor.exceptions import (
    NodeCreationError,
    NodeDeletionError,
    NodePropertyError,
)

if TYPE_CHECKING:
    from nodeeditor.commands import BaseCommand

logger = logging.getLogger(__name__)


class NodeController(QObject):
    """
    Controller for NodeModel operations.

    The NodeController is responsible for managing all business logic related to nodes.
    It acts as an intermediary between the model (data storage) and the view (graphics).
    Controllers handle validation, command generation, and state management.

    Signals:
        nodeCreated(NodeModel): Emitted when a node is successfully created
        nodeDeleted(NodeModel): Emitted when a node is deleted
        nodePropertyChanged(NodeModel, str, Any): Emitted when a node property changes
        nodeSelectionChanged(NodeModel, bool): Emitted when node selection state changes
        nodeValidationError(str, str): Emitted when validation fails (node_id, error)

    Attributes:
        scene_model (SceneModel): The scene model this controller operates on
        undo_stack: Optional undo stack for command management
    """

    # Signals
    nodeCreated = Signal(NodeModel)
    nodeDeleted = Signal(NodeModel)
    nodePropertyChanged = Signal(NodeModel, str, object)  # node, property_name, value
    nodeSelectionChanged = Signal(NodeModel, bool)  # node, is_selected
    nodeValidationError = Signal(str, str)  # node_id, error_message

    def __init__(
        self,
        scene_model: Union[SceneModel, NodeModel],
        undo_stack: Optional[Any] = None,
    ) -> None:
        """
        Initialize the NodeController.

        Args:
            scene_model: The SceneModel this controller operates on. For backward
                compatibility, a NodeModel instance may also be provided to bind
                the controller directly to a single node.
            undo_stack: Optional QUndoStack for undo/redo management

        Raises:
            TypeError: If scene_model is not a SceneModel or NodeModel instance
        """
        super().__init__()

        self.scene_model: Optional[SceneModel]
        self._bound_node: Optional[NodeModel] = None

        if isinstance(scene_model, SceneModel):
            self.scene_model = scene_model
        elif isinstance(scene_model, NodeModel):
            # Legacy usage: controller manages a single node instance
            self.scene_model = None
            self._bound_node = scene_model
        else:
            raise TypeError(
                "scene_model must be SceneModel or NodeModel, "
                f"got {type(scene_model).__name__}"
            )

        self.undo_stack = undo_stack
        self._validation_handlers: Dict[str, Callable] = {}

        # Connect scene model signals to track changes when a scene is available
        if self.scene_model is not None:
            self.scene_model.nodeAdded.connect(self._on_node_added)
            self.scene_model.nodeRemoved.connect(self._on_node_removed)

    def _require_scene_model(self) -> SceneModel:
        """Return the active scene model or raise if unavailable."""
        if self.scene_model is None:
            raise RuntimeError(
                "NodeController was initialized with a NodeModel and does not have a SceneModel "
                "available for this operation."
            )
        return self.scene_model

    def _resolve_node(self, node: Optional[NodeModel]) -> NodeModel:
        """Resolve the node to operate on, falling back to the bound node when available."""
        if node is not None:
            return node

        if self._bound_node is not None:
            return self._bound_node

        raise ValueError(
            "A NodeModel instance must be provided; no node is bound to this controller."
        )

    @staticmethod
    def _coerce_position(position: Union[Tuple[float, float], List[float], QPointF]) -> Tuple[float, float]:
        """Normalize various position inputs to a float tuple."""
        if isinstance(position, QPointF):
            return float(position.x()), float(position.y())

        if isinstance(position, (tuple, list)) and len(position) == 2:
            x, y = position
            return float(x), float(y)

        raise TypeError(
            "Position must be provided as (x, y), [x, y], or QPointF for compatibility."
        )

    def create_node(
        self,
        node_type: str,
        title: str = "Node",
    position: Union[Tuple[float, float], List[float], QPointF] = (0, 0),
        node_id: Optional[str] = None,
    ) -> NodeModel:
        """
        Create a new node in the scene.

        This is the primary method for creating nodes. It handles validation,
        model creation, scene registration, and signal emission.

        Args:
            node_type: Type identifier for the node (e.g., "add_node")
            title: Display name for the node
            position: (x, y) tuple for initial position
            node_id: Optional unique identifier (auto-generated if not provided)

        Returns:
            NodeModel: The created node

        Raises:
            NodeCreationError: If node creation fails
            ValueError: If parameters are invalid
        """
        try:
            if not isinstance(node_type, str) or not node_type.strip():
                raise ValueError("Node type must be a non-empty string")

            if not isinstance(title, str):
                raise ValueError("Node title must be a string")

            if not title.strip():
                raise ValueError("Node title cannot be empty")

            if len(title) > 255:
                raise ValueError("Node title cannot exceed 255 characters")

            # Create the model
            node = NodeModel(
                node_type=node_type,
                title=title,
                node_id=node_id,
            )
            
            # Set position
            node.position = self._coerce_position(position)

            # Add to scene
            scene_model = self._require_scene_model()
            scene_model.add_node(node)

            logger.info(f"Node created: {node.title} (id: {node.id})")
            self.nodeCreated.emit(node)

            return node

        except Exception as e:
            error_msg = f"Failed to create node '{title}': {str(e)}"
            logger.error(error_msg)
            raise NodeCreationError(error_msg) from e

    def delete_node(self, node: NodeModel) -> None:
        """
        Delete a node from the scene.

        This method removes the node and all its connected edges from the scene.
        It handles validation and signal emission.

        Args:
            node: The NodeModel to delete

        Raises:
            NodeDeletionError: If deletion fails
            ValueError: If node is not in the scene
        """
        try:
            scene_model = self._require_scene_model()

            if node not in scene_model.nodes:
                raise ValueError(f"Node {node.id} is not in the scene")

            # Remove from scene (this also removes connected edges)
            scene_model.remove_node(node.id)

            logger.info(f"Node deleted: {node.title} (id: {node.id})")
            self.nodeDeleted.emit(node)

        except Exception as e:
            error_msg = f"Failed to delete node '{node.title}': {str(e)}"
            logger.error(error_msg)
            raise NodeDeletionError(error_msg) from e

    def set_node_title(self, node: Optional[NodeModel], title: str) -> None:
        """
        Set a node's title with validation.

        Args:
            node: The NodeModel to update. When omitted, the controller's bound
                node (if any) will be used.
            title: New title string

        Raises:
            NodePropertyError: If validation fails
        """
        try:
            if not isinstance(title, str) or not title.strip():
                raise ValueError("Title must be a non-empty string")

            if len(title) > 255:
                raise ValueError("Title cannot exceed 255 characters")

            resolved_node = self._resolve_node(node)

            old_title = resolved_node.title
            resolved_node.title = title
            logger.info(f"Node title changed: {old_title} → {title}")
            self.nodePropertyChanged.emit(resolved_node, "title", title)

        except Exception as e:
            error_msg = f"Failed to set node title: {str(e)}"
            logger.error(error_msg)
            raise NodePropertyError(error_msg) from e

    def set_node_position(
        self,
        node: Optional[NodeModel],
        position: Union[Tuple[float, float], List[float], QPointF],
    ) -> None:
        """
        Set a node's position with validation.

        Args:
            node: The NodeModel to update. When omitted, the controller's bound
                node (if any) will be used.
            position: Position expressed as (x, y), [x, y], or QPointF

        Raises:
            NodePropertyError: If validation fails
        """
        try:
            resolved_node = self._resolve_node(node)
            normalized_position = self._coerce_position(position)

            old_pos = resolved_node.position
            resolved_node.position = normalized_position
            logger.info(f"Node position changed: {old_pos} → {normalized_position}")
            self.nodePropertyChanged.emit(resolved_node, "position", normalized_position)

        except Exception as e:
            error_msg = f"Failed to set node position: {str(e)}"
            logger.error(error_msg)
            raise NodePropertyError(error_msg) from e

    def set_node_selected(self, node: Optional[NodeModel], selected: bool) -> None:
        """
        Set a node's selection state.

        Args:
            node: The NodeModel to update. When omitted, the controller's bound
                node (if any) will be used.
            selected: True to select, False to deselect

        Raises:
            NodePropertyError: If operation fails
        """
        try:
            resolved_node = self._resolve_node(node)
            old_state = resolved_node.selected
            resolved_node.selected = selected
            logger.debug(f"Node selection changed: {old_state} → {selected}")
            self.nodeSelectionChanged.emit(resolved_node, selected)

        except Exception as e:
            error_msg = f"Failed to set node selection: {str(e)}"
            logger.error(error_msg)
            raise NodePropertyError(error_msg) from e

    def set_node_visible(self, node: Optional[NodeModel], visible: bool) -> None:
        """
        Set a node's visibility state.

        Args:
            node: The NodeModel to update. When omitted, the controller's bound
                node (if any) will be used.
            visible: True to show, False to hide

        Raises:
            NodePropertyError: If operation fails
        """
        try:
            resolved_node = self._resolve_node(node)
            old_state = resolved_node.visible
            resolved_node.visible = visible
            logger.debug(f"Node visibility changed: {old_state} → {visible}")
            self.nodePropertyChanged.emit(resolved_node, "visible", visible)

        except Exception as e:
            error_msg = f"Failed to set node visibility: {str(e)}"
            logger.error(error_msg)
            raise NodePropertyError(error_msg) from e

    def set_node_property(self, node: Optional[NodeModel], key: str, value: Any) -> None:
        """
        Set a custom property on a node.

        Args:
            node: The NodeModel to update. When omitted, the controller's bound
                node (if any) will be used.
            key: Property key/name
            value: Property value

        Raises:
            NodePropertyError: If validation or setting fails
        """
        try:
            if not isinstance(key, str) or not key.strip():
                raise ValueError("Property key must be a non-empty string")

            resolved_node = self._resolve_node(node)
            old_value = resolved_node.get_property(key)
            resolved_node.set_property(key, value)
            logger.debug(f"Node property set: {key} = {value}")
            self.nodePropertyChanged.emit(resolved_node, key, value)

        except Exception as e:
            error_msg = f"Failed to set node property '{key}': {str(e)}"
            logger.error(error_msg)
            raise NodePropertyError(error_msg) from e

    # ------------------------------------------------------------------
    # Legacy compatibility helpers
    # ------------------------------------------------------------------

    def bind_node(self, node: NodeModel) -> None:
        """Bind a default node for legacy single-node controller usage."""
        if not isinstance(node, NodeModel):
            raise TypeError("bind_node expects a NodeModel instance")

        self._bound_node = node

    def set_title(self, *args, **kwargs) -> None:
        """Legacy alias for :meth:`set_node_title` supporting positional variants."""
        node = kwargs.pop("node", None)
        if kwargs:
            raise TypeError(
                "set_title() got unexpected keyword arguments: "
                f"{', '.join(kwargs.keys())}"
            )

        if len(args) == 1:
            title = args[0]
        elif len(args) == 2:
            candidate_node, title = args
            if isinstance(candidate_node, NodeModel):
                node = node or candidate_node
            else:
                raise TypeError(
                    "set_title(node, title) expects the first positional argument to be a NodeModel"
                )
        else:
            raise TypeError("set_title() expects 1 or 2 positional arguments")

        self.set_node_title(node, title)

    def set_position(self, *args, **kwargs) -> None:
        """Legacy alias for :meth:`set_node_position` supporting flexible inputs."""
        node = kwargs.pop("node", None)
        if kwargs:
            raise TypeError(
                "set_position() got unexpected keyword arguments: "
                f"{', '.join(kwargs.keys())}"
            )

        position: Union[Tuple[float, float], List[float], QPointF]

        if len(args) == 1:
            position = args[0]
        elif len(args) == 2:
            first, second = args
            if isinstance(first, NodeModel):
                node = node or first
                position = second
            else:
                position = (first, second)
        elif len(args) == 3:
            candidate_node, x, y = args
            if not isinstance(candidate_node, NodeModel):
                raise TypeError(
                    "set_position(node, x, y) expects the first positional argument to be a NodeModel"
                )
            node = node or candidate_node
            position = (x, y)
        else:
            raise TypeError("set_position() expects between 1 and 3 positional arguments")

        self.set_node_position(node, position)

    def set_selected(self, *args, **kwargs) -> None:
        """Legacy alias for :meth:`set_node_selected`."""
        node = kwargs.pop("node", None)
        if kwargs:
            raise TypeError(
                "set_selected() got unexpected keyword arguments: "
                f"{', '.join(kwargs.keys())}"
            )

        if len(args) == 1:
            selected = args[0]
        elif len(args) == 2:
            candidate_node, selected = args
            if not isinstance(candidate_node, NodeModel):
                raise TypeError(
                    "set_selected(node, selected) expects the first positional argument to be a NodeModel"
                )
            node = node or candidate_node
        else:
            raise TypeError("set_selected() expects 1 or 2 positional arguments")

        self.set_node_selected(node, bool(selected))

    def set_visible(self, *args, **kwargs) -> None:
        """Legacy alias for :meth:`set_node_visible`."""
        node = kwargs.pop("node", None)
        if kwargs:
            raise TypeError(
                "set_visible() got unexpected keyword arguments: "
                f"{', '.join(kwargs.keys())}"
            )

        if len(args) == 1:
            visible = args[0]
        elif len(args) == 2:
            candidate_node, visible = args
            if not isinstance(candidate_node, NodeModel):
                raise TypeError(
                    "set_visible(node, visible) expects the first positional argument to be a NodeModel"
                )
            node = node or candidate_node
        else:
            raise TypeError("set_visible() expects 1 or 2 positional arguments")

        self.set_node_visible(node, bool(visible))

    def set_property(self, *args, **kwargs) -> None:
        """Legacy alias for :meth:`set_node_property`."""
        node = kwargs.pop("node", None)
        if kwargs:
            raise TypeError(
                "set_property() got unexpected keyword arguments: "
                f"{', '.join(kwargs.keys())}"
            )

        if len(args) == 2:
            key, value = args
        elif len(args) == 3:
            candidate_node, key, value = args
            if not isinstance(candidate_node, NodeModel):
                raise TypeError(
                    "set_property(node, key, value) expects the first positional argument to be a NodeModel"
                )
            node = node or candidate_node
        else:
            raise TypeError("set_property() expects 2 or 3 positional arguments")

        self.set_node_property(node, key, value)

    def register_property_validator(
        self,
        property_name: str,
        validator: Callable,
    ) -> None:
        """
        Register a custom validator for a node property.

        Validators are functions that take (value) and return True if valid,
        or raise ValueError with a descriptive message if invalid.

        Args:
            property_name: Name of the property to validate
            validator: Callable that validates the property value

        Example:
            >>> def validate_positive(value):
            ...     if value <= 0:
            ...         raise ValueError("Value must be positive")
            ...     return True
            >>> controller.register_property_validator("count", validate_positive)
        """
        self._validation_handlers[property_name] = validator
        logger.debug(f"Property validator registered: {property_name}")

    def get_nodes(self) -> List[NodeModel]:
        """
        Get all nodes in the scene.

        Returns:
            List[NodeModel]: List of all nodes
        """
        scene_model = self._require_scene_model()
        return list(scene_model.nodes)

    def get_node_by_id(self, node_id: str) -> Optional[NodeModel]:
        """
        Get a node by its unique identifier.

        Args:
            node_id: The node's unique ID

        Returns:
            NodeModel if found, None otherwise
        """
        scene_model = self._require_scene_model()

        for node in scene_model.nodes:
            if node.id == node_id:
                return node
        return None

    # ======================== Private Methods ========================

    def _on_node_added(self, node: NodeModel) -> None:
        """Internal handler when a node is added to the scene."""
        logger.debug(f"Node added to scene: {node.id}")

    def _on_node_removed(self, node_id: str) -> None:
        """Internal handler when a node is removed from the scene."""
        logger.debug(f"Node removed from scene: {node_id}")
