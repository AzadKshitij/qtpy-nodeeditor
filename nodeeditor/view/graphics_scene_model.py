"""
QDMGraphicsSceneModel - View coordinator for SceneModel and QDMGraphicsScene.

This class orchestrates the integration between the scene model, controllers,
and the graphics scene. It manages synchronization of all graphics items
with their corresponding models.

Features:
    - Coordinates scene-level graphics updates
    - Manages node/edge graphics creation and deletion
    - Synchronizes graphics scene with model state
    - Handles undo/redo coordination
    - Manages model-to-graphics wrapper lifecycle

Example:
    >>> scene_model = SceneModel()
    >>> graphics_scene = QGraphicsScene()
    >>> coordinator = QDMGraphicsSceneModel(scene_model, graphics_scene)
    >>> # Creating nodes/edges updates both model and graphics automatically
"""

from typing import TYPE_CHECKING, Dict, Optional, Any, List
import logging

from qtpy.QtCore import QObject, Signal
from qtpy.QtWidgets import QGraphicsScene

from nodeeditor.models import NodeModel, EdgeModel, SceneModel
from nodeeditor.view.graphics_node_model import QDMGraphicsNodeModel
from nodeeditor.view.graphics_edge_model import QDMGraphicsEdgeModel
from nodeeditor.view.graphics_socket_model import QDMGraphicsSocketModel

if TYPE_CHECKING:
    from nodeeditor.views.graphics.node_graphics_scene import QDMGraphicsScene
    from nodeeditor.controllers import SceneController, NodeController, EdgeController

logger = logging.getLogger(__name__)


class QDMGraphicsSceneModel(QObject):
    """
    Coordinator for synchronizing SceneModel with QDMGraphicsScene.

    This class manages the integration between the data layer (models),
    business logic layer (controllers), and graphics layer (QGraphicsScene).
    It creates and maintains wrapper objects that bridge each graphics item
    with its corresponding model.

    Signals:
        sceneUpdated: Emitted when scene needs redraw
        nodeCreated(str): Emitted when a node is created (passes node_id)
        nodeDeleted(str): Emitted when a node is deleted (passes node_id)
        edgeCreated(str): Emitted when an edge is created (passes edge_id)
        edgeDeleted(str): Emitted when an edge is deleted (passes edge_id)

    Attributes:
        scene_model (SceneModel): The underlying scene model
        graphics_scene (QDMGraphicsScene): The graphics scene
        scene_controller (SceneController): Optional scene controller
        node_wrappers (dict): Maps node_id to QDMGraphicsNodeModel
        edge_wrappers (dict): Maps edge_id to QDMGraphicsEdgeModel
        socket_wrappers (dict): Maps socket_id to QDMGraphicsSocketModel
    """

    # Signals
    sceneUpdated = Signal()
    nodeCreated = Signal(str)  # node_id
    nodeDeleted = Signal(str)  # node_id
    edgeCreated = Signal(str)  # edge_id
    edgeDeleted = Signal(str)  # edge_id

    def __init__(
        self,
        scene_model: SceneModel,
        graphics_scene: 'QDMGraphicsScene',
        scene_controller: Optional['SceneController'] = None,
    ) -> None:
        """
        Initialize the graphics scene coordinator.

        Args:
            scene_model: The SceneModel to coordinate
            graphics_scene: The QDMGraphicsScene to synchronize with
            scene_controller: Optional SceneController for operations

        Raises:
            TypeError: If scene_model is not a SceneModel
        """
        super().__init__()

        if not isinstance(scene_model, SceneModel):
            raise TypeError(f"scene_model must be SceneModel, got {type(scene_model).__name__}")

        self.scene_model = scene_model
        self.graphics_scene = graphics_scene
        self.scene_controller = scene_controller

        # Wrapper caches
        self.node_wrappers: Dict[str, QDMGraphicsNodeModel] = {}
        self.edge_wrappers: Dict[str, QDMGraphicsEdgeModel] = {}
        self.socket_wrappers: Dict[str, QDMGraphicsSocketModel] = {}

        # Graphics item caches (for reverse lookup)
        self.graphics_items_to_models: Dict[int, NodeModel | EdgeModel] = {}

        # Connect model signals
        self._connect_model_signals()

        logger.info("QDMGraphicsSceneModel initialized")

    def _connect_model_signals(self) -> None:
        """Connect scene model signals to coordinator methods."""
        self.scene_model.nodeAdded.connect(self._on_node_added)
        self.scene_model.nodeRemoved.connect(self._on_node_removed)
        self.scene_model.edgeAdded.connect(self._on_edge_added)
        self.scene_model.edgeRemoved.connect(self._on_edge_removed)
        self.scene_model.cleared.connect(self._on_scene_cleared)

    # ======================== Node Management ========================

    def register_node_graphics(
        self,
        model: NodeModel,
        graphics_item: Any,
        node_controller: Optional['NodeController'] = None,
    ) -> QDMGraphicsNodeModel:
        """
        Register a graphics node with its model.

        This creates a wrapper that coordinates updates between the model
        and graphics representation.

        Args:
            model: The NodeModel
            graphics_item: The QDMGraphicsNode graphics item
            node_controller: Optional NodeController for operations

        Returns:
            QDMGraphicsNodeModel: The created wrapper

        Raises:
            ValueError: If node is already registered
        """
        if model.id in self.node_wrappers:
            raise ValueError(f"Node {model.id} already registered")

        wrapper = QDMGraphicsNodeModel(model, graphics_item, node_controller)

        # Cache the wrapper
        self.node_wrappers[model.id] = wrapper
        self.graphics_items_to_models[id(graphics_item)] = model

        # Connect wrapper signals
        wrapper.graphicsUpdated.connect(self.sceneUpdated.emit)

        logger.debug(f"Registered graphics for node: {model.id}")
        return wrapper

    def unregister_node_graphics(self, node_id: str) -> None:
        """
        Unregister a graphics node wrapper.

        Args:
            node_id: The node's ID
        """
        if node_id in self.node_wrappers:
            del self.node_wrappers[node_id]
            logger.debug(f"Unregistered graphics for node: {node_id}")

    def get_node_wrapper(self, node_id: str) -> Optional[QDMGraphicsNodeModel]:
        """
        Get the graphics wrapper for a node.

        Args:
            node_id: The node's ID

        Returns:
            QDMGraphicsNodeModel if found, None otherwise
        """
        return self.node_wrappers.get(node_id)

    # ======================== Edge Management ========================

    def register_edge_graphics(
        self,
        model: EdgeModel,
        graphics_item: Any,
        edge_controller: Optional['EdgeController'] = None,
    ) -> QDMGraphicsEdgeModel:
        """
        Register a graphics edge with its model.

        This creates a wrapper that coordinates updates between the model
        and graphics representation.

        Args:
            model: The EdgeModel
            graphics_item: The QDMGraphicsEdge graphics item
            edge_controller: Optional EdgeController for operations

        Returns:
            QDMGraphicsEdgeModel: The created wrapper

        Raises:
            ValueError: If edge is already registered
        """
        if model.id in self.edge_wrappers:
            raise ValueError(f"Edge {model.id} already registered")

        wrapper = QDMGraphicsEdgeModel(model, graphics_item, edge_controller)

        # Cache the wrapper
        self.edge_wrappers[model.id] = wrapper
        self.graphics_items_to_models[id(graphics_item)] = model

        # Connect wrapper signals
        wrapper.graphicsUpdated.connect(self.sceneUpdated.emit)

        logger.debug(f"Registered graphics for edge: {model.id}")
        return wrapper

    def unregister_edge_graphics(self, edge_id: str) -> None:
        """
        Unregister a graphics edge wrapper.

        Args:
            edge_id: The edge's ID
        """
        if edge_id in self.edge_wrappers:
            del self.edge_wrappers[edge_id]
            logger.debug(f"Unregistered graphics for edge: {edge_id}")

    def get_edge_wrapper(self, edge_id: str) -> Optional[QDMGraphicsEdgeModel]:
        """
        Get the graphics wrapper for an edge.

        Args:
            edge_id: The edge's ID

        Returns:
            QDMGraphicsEdgeModel if found, None otherwise
        """
        return self.edge_wrappers.get(edge_id)

    # ======================== Socket Management ========================

    def register_socket_graphics(
        self,
        model: Any,  # SocketModel
        graphics_item: Any,
    ) -> QDMGraphicsSocketModel:
        """
        Register a graphics socket with its model.

        Args:
            model: The SocketModel
            graphics_item: The QDMGraphicsSocket graphics item

        Returns:
            QDMGraphicsSocketModel: The created wrapper

        Raises:
            ValueError: If socket is already registered
        """
        if model.id in self.socket_wrappers:
            raise ValueError(f"Socket {model.id} already registered")

        wrapper = QDMGraphicsSocketModel(model, graphics_item)

        # Cache the wrapper
        self.socket_wrappers[model.id] = wrapper

        # Connect wrapper signals
        wrapper.graphicsUpdated.connect(self.sceneUpdated.emit)

        logger.debug(f"Registered graphics for socket: {model.id}")
        return wrapper

    def get_socket_wrapper(self, socket_id: str) -> Optional[QDMGraphicsSocketModel]:
        """
        Get the graphics wrapper for a socket.

        Args:
            socket_id: The socket's ID

        Returns:
            QDMGraphicsSocketModel if found, None otherwise
        """
        return self.socket_wrappers.get(socket_id)

    # ======================== Model Signal Handlers ========================

    def _on_node_added(self, node: NodeModel) -> None:
        """Handle node addition to model."""
        logger.debug(f"Node added to model: {node.id}")
        self.nodeCreated.emit(node.id)
        self.sceneUpdated.emit()

    def _on_node_removed(self, node_id: str) -> None:
        """Handle node removal from model."""
        self.unregister_node_graphics(node_id)
        logger.debug(f"Node removed from model: {node_id}")
        self.nodeDeleted.emit(node_id)
        self.sceneUpdated.emit()

    def _on_edge_added(self, edge: EdgeModel) -> None:
        """Handle edge addition to model."""
        logger.debug(f"Edge added to model: {edge.id}")
        self.edgeCreated.emit(edge.id)
        self.sceneUpdated.emit()

    def _on_edge_removed(self, edge_id: str) -> None:
        """Handle edge removal from model."""
        self.unregister_edge_graphics(edge_id)
        logger.debug(f"Edge removed from model: {edge_id}")
        self.edgeDeleted.emit(edge_id)
        self.sceneUpdated.emit()

    def _on_scene_cleared(self) -> None:
        """Handle scene clear."""
        # Clear all wrappers
        self.node_wrappers.clear()
        self.edge_wrappers.clear()
        self.socket_wrappers.clear()
        self.graphics_items_to_models.clear()

        logger.debug("Scene cleared - all wrappers removed")
        self.sceneUpdated.emit()

    # ======================== Query Methods ========================

    def get_all_node_wrappers(self) -> List[QDMGraphicsNodeModel]:
        """Get all node wrappers."""
        return list(self.node_wrappers.values())

    def get_all_edge_wrappers(self) -> List[QDMGraphicsEdgeModel]:
        """Get all edge wrappers."""
        return list(self.edge_wrappers.values())

    def get_all_socket_wrappers(self) -> List[QDMGraphicsSocketModel]:
        """Get all socket wrappers."""
        return list(self.socket_wrappers.values())

    def node_count(self) -> int:
        """Get the number of registered nodes."""
        return len(self.node_wrappers)

    def edge_count(self) -> int:
        """Get the number of registered edges."""
        return len(self.edge_wrappers)

    def socket_count(self) -> int:
        """Get the number of registered sockets."""
        return len(self.socket_wrappers)
