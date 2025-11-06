"""
SceneController - Controller for managing SceneModel operations.

The SceneController is the top-level controller that manages the entire scene
graph. It coordinates between the SceneModel (data), NodeController, EdgeController,
and views. It handles scene-level operations like serialization, history management,
and global state changes.

Features:
    - Scene initialization and management
    - Node and edge creation/deletion delegation
    - Undo/redo stack management
    - Scene serialization and deserialization
    - Global scene state queries
    - Signal coordination

Example:
    >>> from nodeeditor.controllers import SceneController
    >>> from nodeeditor.models import SceneModel
    >>> from qtpy.QtGui import QUndoStack
    >>> undo_stack = QUndoStack()
    >>> controller = SceneController(SceneModel(), undo_stack)
    >>> node = controller.create_node("node_type", "Start", (0, 0))
    >>> edge = controller.create_edge(node.input_socket, node.output_socket)
"""

from typing import TYPE_CHECKING, Optional, Any, Dict, List, Tuple
import logging
import json

from qtpy.QtCore import QObject, Signal
from qtpy.QtGui import QUndoStack

from nodeeditor.models import NodeModel, EdgeModel, SocketModel, SceneModel
from nodeeditor.controllers.node_controller import NodeController
from nodeeditor.controllers.edge_controller import EdgeController
from nodeeditor.exceptions import (
    NodeCreationError,
    NodeDeletionError,
    NodeEditorException,
)

if TYPE_CHECKING:
    from nodeeditor.commands import BaseCommand
    from nodeeditor.node_node import Node
    from nodeeditor.node_edge import Edge

logger = logging.getLogger(__name__)


class SceneController(QObject):
    """
    Top-level controller for the scene graph.

    The SceneController orchestrates all scene operations, delegating to
    NodeController and EdgeController as appropriate. It manages the undo/redo
    system and provides high-level scene manipulation methods.

    Signals:
        sceneModified: Emitted when the scene state changes
        sceneClear: Emitted when the scene is cleared
        sceneLoaded: Emitted when a scene is loaded from file/data
        nodeCountChanged(int): Emitted when number of nodes changes
        edgeCountChanged(int): Emitted when number of edges changes
        error(str): Emitted when an operation fails

    Attributes:
        model (SceneModel): The underlying scene model
        node_controller (NodeController): Controller for node operations
        edge_controller (EdgeController): Controller for edge operations
        undo_stack (QUndoStack): Stack for undo/redo operations
    """

    # Signals
    sceneModified = Signal()
    sceneClear = Signal()
    sceneLoaded = Signal()
    nodeCountChanged = Signal(int)  # new_count
    edgeCountChanged = Signal(int)  # new_count
    error = Signal(str)  # error_message

    def __init__(self, scene_model: Optional[SceneModel] = None, undo_stack: Optional[QUndoStack] = None) -> None:
        """
        Initialize the SceneController.

        Args:
            scene_model: Optional SceneModel instance (creates new if not provided)
            undo_stack: Optional QUndoStack (creates new if not provided)

        Raises:
            TypeError: If scene_model is provided but not a SceneModel instance
        """
        super().__init__()

        # Create or validate scene model
        if scene_model is None:
            self.model = SceneModel()
        elif isinstance(scene_model, SceneModel):
            self.model = scene_model
        else:
            raise TypeError(f"scene_model must be SceneModel, got {type(scene_model).__name__}")

        # Create or use provided undo stack
        self.undo_stack = undo_stack or QUndoStack()

        # Create sub-controllers
        self.node_controller = NodeController(self.model, self.undo_stack)
        self.edge_controller = EdgeController(self.model, self.undo_stack)

        # Track state
        self._previous_node_count = len(self.model.nodes)
        self._previous_edge_count = len(self.model.edges)

        # Connect model signals
        self.model.nodeAdded.connect(self._on_node_count_changed)
        self.model.nodeRemoved.connect(self._on_node_count_changed)
        self.model.edgeAdded.connect(self._on_edge_count_changed)
        self.model.edgeRemoved.connect(self._on_edge_count_changed)
        self.model.modifiedChanged.connect(self.sceneModified.emit)

        # Connect controller signals
        self.node_controller.nodeCreated.connect(self._on_scene_changed)
        self.node_controller.nodeDeleted.connect(self._on_scene_changed)
        self.edge_controller.edgeCreated.connect(self._on_scene_changed)
        self.edge_controller.edgeDeleted.connect(self._on_scene_changed)

        logger.info("SceneController initialized")

    # ======================== Node Operations ========================

    def create_node(
        self,
        node_type: str,
        title: str = "Node",
        position: Tuple[float, float] = (0, 0),
        node_id: Optional[str] = None,
    ) -> NodeModel:
        """
        Create a new node in the scene.

        Delegates to NodeController.

        Args:
            node_type: Type identifier for the node
            title: Display name for the node
            position: (x, y) tuple for initial position
            node_id: Optional unique identifier

        Returns:
            NodeModel: The created node

        Raises:
            NodeCreationError: If creation fails
        """
        try:
            return self.node_controller.create_node(node_type, title, position, node_id)
        except Exception as e:
            error_msg = f"Failed to create node: {str(e)}"
            self.error.emit(error_msg)
            raise

    def delete_node(self, node: NodeModel) -> None:
        """
        Delete a node from the scene.

        Delegates to NodeController. Also removes all connected edges.

        Args:
            node: The NodeModel to delete

        Raises:
            NodeDeletionError: If deletion fails
        """
        try:
            # Delete the node (this handles removal of connected edges in the model)
            self.node_controller.delete_node(node)

        except Exception as e:
            error_msg = f"Failed to delete node: {str(e)}"
            self.error.emit(error_msg)
            raise

    def set_node_title(self, node: NodeModel, title: str) -> None:
        """
        Set a node's title.

        Delegates to NodeController.

        Args:
            node: The NodeModel to update
            title: New title

        Raises:
            NodePropertyError: If operation fails
        """
        try:
            self.node_controller.set_node_title(node, title)
        except Exception as e:
            error_msg = f"Failed to set node title: {str(e)}"
            self.error.emit(error_msg)
            raise

    def set_node_position(self, node: NodeModel, position: Tuple[float, float]) -> None:
        """
        Set a node's position.

        Delegates to NodeController.

        Args:
            node: The NodeModel to update
            position: (x, y) tuple

        Raises:
            NodePropertyError: If operation fails
        """
        try:
            self.node_controller.set_node_position(node, position)
        except Exception as e:
            error_msg = f"Failed to set node position: {str(e)}"
            self.error.emit(error_msg)
            raise

    # ======================== Legacy Compatibility Methods ========================

    def register_node(self, node: "Node") -> None:
        """
        Register a legacy Node object with the scene.

        This is a compatibility method for the old Node API. It handles both
        legacy Node objects and new NodeModel objects.

        Args:
            node: The Node object to register
        """
        try:
            # Check if this is a legacy Node object (has both model and controller)
            if hasattr(node, "model") and hasattr(node, "controller"):
                # It's already an MVC node, just ensure it's in the model
                added = self.model.add_node(node.model)
                if added:
                    logger.debug(f"Registered MVC node {node.model.id} with scene")
            else:
                # Treat as legacy node - just add it to tracking if needed
                logger.debug(f"Registered legacy node {node} with scene")
        except Exception as e:
            error_msg = f"Failed to register node: {str(e)}"
            self.error.emit(error_msg)
            logger.error(error_msg, exc_info=True)

    def unregister_node(self, node: "Node") -> None:
        """
        Unregister a legacy Node object from the scene.

        This is a compatibility method for the old Node API.

        Args:
            node: The Node object to unregister
        """
        try:
            # Check if this is an MVC node with a model
            if hasattr(node, "model"):
                removed = self.model.remove_node(node.model.id)
                if removed:
                    logger.debug(f"Unregistered MVC node {node.model.id} from scene")
            else:
                logger.debug(f"Unregistered legacy node {node} from scene")
        except Exception as e:
            error_msg = f"Failed to unregister node: {str(e)}"
            self.error.emit(error_msg)
            logger.error(error_msg, exc_info=True)

    def register_edge(self, edge: "Edge") -> None:
        """
        Register a legacy Edge object with the scene.

        This is a compatibility method for the old Edge API.

        Args:
            edge: The Edge object to register
        """
        try:
            # Check if this is an MVC edge with a model
            if hasattr(edge, "model") and hasattr(edge, "controller"):
                added = self.model.add_edge(edge.model)
                if added:
                    logger.debug(f"Registered MVC edge {edge.model.id} with scene")
            else:
                logger.debug(f"Registered legacy edge {edge} with scene")
        except Exception as e:
            error_msg = f"Failed to register edge: {str(e)}"
            self.error.emit(error_msg)
            logger.error(error_msg, exc_info=True)

    def unregister_edge(self, edge: "Edge") -> None:
        """
        Unregister a legacy Edge object from the scene.

        This is a compatibility method for the old Edge API.

        Args:
            edge: The Edge object to unregister
        """
        try:
            # Check if this is an MVC edge with a model
            if hasattr(edge, "model"):
                removed = self.model.remove_edge(edge.model.id)
                if removed:
                    logger.debug(f"Unregistered MVC edge {edge.model.id} from scene")
            else:
                logger.debug(f"Unregistered legacy edge {edge} from scene")
        except Exception as e:
            error_msg = f"Failed to unregister edge: {str(e)}"
            self.error.emit(error_msg)
            logger.error(error_msg, exc_info=True)

    # ======================== Edge Operations ========================

    def create_edge(
        self,
        start_socket: SocketModel,
        end_socket: SocketModel,
        edge_id: Optional[str] = None,
        edge_type: int = EdgeModel.BEZIER,
    ) -> EdgeModel:
        """
        Create an edge connecting two sockets.

        Delegates to EdgeController.

        Args:
            start_socket: Source socket
            end_socket: Destination socket
            edge_id: Optional unique identifier
            edge_type: Type of edge

        Returns:
            EdgeModel: The created edge

        Raises:
            SocketConnectionError: If connection fails
        """
        try:
            return self.edge_controller.create_edge(start_socket, end_socket, edge_id, edge_type)
        except Exception as e:
            error_msg = f"Failed to create edge: {str(e)}"
            self.error.emit(error_msg)
            raise

    def delete_edge(self, edge: EdgeModel) -> None:
        """
        Delete an edge from the scene.

        Delegates to EdgeController.

        Args:
            edge: The EdgeModel to delete

        Raises:
            SocketDisconnectionError: If deletion fails
        """
        try:
            self.edge_controller.delete_edge(edge)
        except Exception as e:
            error_msg = f"Failed to delete edge: {str(e)}"
            self.error.emit(error_msg)
            raise

    def set_edge_type(self, edge: EdgeModel, edge_type: int) -> None:
        """
        Set an edge's type.

        Delegates to EdgeController.

        Args:
            edge: The EdgeModel to update
            edge_type: New type

        Raises:
            ValueError: If type is invalid
        """
        try:
            self.edge_controller.set_edge_type(edge, edge_type)
        except Exception as e:
            error_msg = f"Failed to set edge type: {str(e)}"
            self.error.emit(error_msg)
            raise

    # ======================== Scene Operations ========================

    def clear_scene(self) -> None:
        """
        Clear all nodes and edges from the scene.

        Raises:
            NodeEditorException: If clearing fails
        """
        try:
            self.model.clear()
            logger.info("Scene cleared")
            self.sceneClear.emit()
            self.sceneModified.emit()

        except Exception as e:
            error_msg = f"Failed to clear scene: {str(e)}"
            logger.error(error_msg)
            self.error.emit(error_msg)
            raise NodeEditorException(error_msg) from e

    def undo(self) -> None:
        """Undo the last operation."""
        if self.undo_stack.canUndo():
            self.undo_stack.undo()
            logger.debug("Undo executed")
        else:
            logger.debug("Nothing to undo")

    def redo(self) -> None:
        """Redo the last undone operation."""
        if self.undo_stack.canRedo():
            self.undo_stack.redo()
            logger.debug("Redo executed")
        else:
            logger.debug("Nothing to redo")

    def can_undo(self) -> bool:
        """Check if undo is available."""
        return self.undo_stack.canUndo()

    def can_redo(self) -> bool:
        """Check if redo is available."""
        return self.undo_stack.canRedo()

    # ======================== Query Operations ========================

    def get_nodes(self) -> List[NodeModel]:
        """
        Get all nodes in the scene.

        Returns:
            List[NodeModel]: List of all nodes
        """
        return self.node_controller.get_nodes()

    def get_edges(self) -> List[EdgeModel]:
        """
        Get all edges in the scene.

        Returns:
            List[EdgeModel]: List of all edges
        """
        return self.edge_controller.get_edges()

    def get_node_by_id(self, node_id: str) -> Optional[NodeModel]:
        """
        Get a node by ID.

        Args:
            node_id: The node's ID

        Returns:
            NodeModel if found, None otherwise
        """
        return self.node_controller.get_node_by_id(node_id)

    def get_edge_by_id(self, edge_id: str) -> Optional[EdgeModel]:
        """
        Get an edge by ID.

        Args:
            edge_id: The edge's ID

        Returns:
            EdgeModel if found, None otherwise
        """
        return self.edge_controller.get_edge_by_id(edge_id)

    def get_node_count(self) -> int:
        """Get the number of nodes in the scene."""
        return len(self.model.nodes)

    def get_edge_count(self) -> int:
        """Get the number of edges in the scene."""
        return len(self.model.edges)

    def is_modified(self) -> bool:
        """Check if the scene has unsaved changes."""
        return self.model.modified

    # ======================== Serialization ========================

    def serialize(self) -> Dict[str, Any]:
        """
        Serialize the entire scene to a dictionary.

        Returns:
            Dict containing the scene data
        """
        return self.model.serialize()

    def deserialize(self, data: Dict[str, Any]) -> None:
        """
        Load a scene from serialized data.

        Args:
            data: Dictionary containing the scene data

        Raises:
            ValueError: If data is invalid
        """
        try:
            self.clear_scene()
            self.model.deserialize(data)
            logger.info("Scene deserialized successfully")
            self.sceneLoaded.emit()
            self.sceneModified.emit()

        except Exception as e:
            error_msg = f"Failed to deserialize scene: {str(e)}"
            logger.error(error_msg)
            self.error.emit(error_msg)
            raise ValueError(error_msg) from e

    def save_to_file(self, filepath: str) -> None:
        """
        Save the scene to a JSON file.

        Args:
            filepath: Path to save the file

        Raises:
            IOError: If file write fails
        """
        try:
            data = self.serialize()
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Scene saved to {filepath}")

        except Exception as e:
            error_msg = f"Failed to save scene to {filepath}: {str(e)}"
            logger.error(error_msg)
            self.error.emit(error_msg)
            raise IOError(error_msg) from e

    def load_from_file(self, filepath: str) -> None:
        """
        Load a scene from a JSON file.

        Args:
            filepath: Path to load the file

        Raises:
            IOError: If file read fails
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            self.deserialize(data)
            logger.info(f"Scene loaded from {filepath}")

        except Exception as e:
            error_msg = f"Failed to load scene from {filepath}: {str(e)}"
            logger.error(error_msg)
            self.error.emit(error_msg)
            raise IOError(error_msg) from e

    # ======================== Private Methods ========================

    def _on_scene_changed(self, *args) -> None:
        """Internal handler for any scene change."""
        self.model.modified = True
        self.sceneModified.emit()

    def _on_node_count_changed(self) -> None:
        """Internal handler when node count changes."""
        current_count = len(self.model.nodes)
        if current_count != self._previous_node_count:
            self._previous_node_count = current_count
            self.nodeCountChanged.emit(current_count)
            self.sceneModified.emit()

    def _on_edge_count_changed(self) -> None:
        """Internal handler when edge count changes."""
        current_count = len(self.model.edges)
        if current_count != self._previous_edge_count:
            self._previous_edge_count = current_count
            self.edgeCountChanged.emit(current_count)
            self.sceneModified.emit()
