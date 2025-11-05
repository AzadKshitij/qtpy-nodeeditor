"""
EdgeController - Controller for managing EdgeModel operations.

The EdgeController handles all business logic for edge (connection) operations,
coordinating between the EdgeModel (data) and the view (graphics). It manages
connection validation, type selection, and integration with the undo/redo system.

Features:
    - Edge creation and deletion
    - Socket connection management
    - Connection validation and conflict detection
    - Edge type/style management
    - Undo/redo command generation

Example:
    >>> from nodeeditor.controllers import EdgeController
    >>> from nodeeditor.models import SceneModel
    >>> scene_model = SceneModel()
    >>> controller = EdgeController(scene_model)
    >>> edge = controller.create_edge(start_socket, end_socket)
    >>> controller.set_edge_type(edge, EdgeModel.BEZIER)
"""

from typing import TYPE_CHECKING, Optional, Any, List, Callable
import logging

from qtpy.QtCore import QObject, Signal

from nodeeditor.models import EdgeModel, SocketModel, NodeModel, SceneModel
from nodeeditor.exceptions import (
    SocketConnectionError,
    SocketDisconnectionError,
    NodeEditorException,
    EdgeCreationError,
    EdgeDeletionError
)

if TYPE_CHECKING:
    from nodeeditor.commands import BaseCommand

logger = logging.getLogger(__name__)


class EdgeController(QObject):
    """
    Controller for EdgeModel operations.

    The EdgeController is responsible for managing all business logic related to edges
    (connections between sockets). It validates connections, manages edge lifecycle,
    and coordinates with the model and views.

    Signals:
        edgeCreated(EdgeModel): Emitted when an edge is successfully created
        edgeDeleted(EdgeModel): Emitted when an edge is deleted
        edgeConnected(EdgeModel, SocketModel, SocketModel): Emitted when sockets are connected
        edgeDisconnected(EdgeModel): Emitted when edge connection is broken
        edgeTypeChanged(EdgeModel, int): Emitted when edge type changes
        connectionFailed(str): Emitted when connection fails (error message)

    Attributes:
        scene_model (SceneModel): The scene model this controller operates on
        undo_stack: Optional undo stack for command management
    """

    # Signals
    edgeCreated = Signal(EdgeModel)
    edgeDeleted = Signal(EdgeModel)
    edgeConnected = Signal(EdgeModel, SocketModel, SocketModel)  # edge, start_socket, end_socket
    edgeDisconnected = Signal(EdgeModel)
    edgeTypeChanged = Signal(EdgeModel, int)  # edge, new_type
    connectionFailed = Signal(str)  # error_message

    # Connection type constants
    SINGLE_CONNECTION = 1  # Only one edge per socket
    MULTI_CONNECTION = 2   # Multiple edges per socket

    def __init__(self, scene_model: SceneModel, undo_stack: Optional[Any] = None) -> None:
        """
        Initialize the EdgeController.

        Args:
            scene_model: The SceneModel this controller operates on
            undo_stack: Optional QUndoStack for undo/redo management

        Raises:
            TypeError: If scene_model is not a SceneModel instance
        """
        super().__init__()

        if not isinstance(scene_model, SceneModel):
            raise TypeError(f"scene_model must be SceneModel, got {type(scene_model).__name__}")

        self.scene_model = scene_model
        self.undo_stack = undo_stack
        self._connection_mode = self.MULTI_CONNECTION
        self._connection_validators: List[Callable] = []

        # Connect scene model signals
        self.scene_model.edgeAdded.connect(self._on_edge_added)
        self.scene_model.edgeRemoved.connect(self._on_edge_removed)

    def create_edge(
        self,
        start_socket: SocketModel,
        end_socket: SocketModel,
        edge_id: Optional[str] = None,
        edge_type: int = EdgeModel.BEZIER,
    ) -> EdgeModel:
        """
        Create an edge connecting two sockets.

        This is the primary method for creating edges. It validates the connection,
        creates the model, registers it with the scene, and emits signals.

        Args:
            start_socket: The source socket
            end_socket: The destination socket
            edge_id: Optional unique identifier (auto-generated if not provided)
            edge_type: Type of edge (STRAIGHT, BEZIER, POLYLINE)

        Returns:
            EdgeModel: The created edge

        Raises:
            SocketConnectionError: If connection validation fails
        """
        try:
            # Validate connection
            self._validate_connection(start_socket, end_socket)

            # Create the model
            edge = EdgeModel(edge_id=edge_id)
            edge.edge_type = edge_type
            edge.start_socket = start_socket
            edge.end_socket = end_socket

            # Register sockets
            if edge not in start_socket.edges:
                start_socket._edges.append(edge)
            if edge not in end_socket.edges:
                end_socket._edges.append(edge)

            # Add to scene
            self.scene_model.add_edge(edge)

            logger.info(f"Edge created: {start_socket.id} → {end_socket.id} (id: {edge.id})")
            self.edgeCreated.emit(edge)
            self.edgeConnected.emit(edge, start_socket, end_socket)

            return edge

        except Exception as e:
            error_msg = f"Failed to create edge: {str(e)}"
            logger.error(error_msg)
            self.connectionFailed.emit(error_msg)
            raise SocketConnectionError(error_msg) from e

    def delete_edge(self, edge: EdgeModel) -> None:
        """
        Delete an edge from the scene.

        This method removes the edge and disconnects its sockets.

        Args:
            edge: The EdgeModel to delete

        Raises:
            SocketDisconnectionError: If deletion fails
        """
        try:
            if edge not in self.scene_model.edges:
                raise ValueError(f"Edge {edge.id} is not in the scene")

            # Disconnect sockets
            if edge.start_socket:
                if edge in edge.start_socket.edges:
                    edge.start_socket._edges.remove(edge)
            if edge.end_socket:
                if edge in edge.end_socket.edges:
                    edge.end_socket._edges.remove(edge)

            # Remove from scene
            self.scene_model.remove_edge(edge.id)

            logger.info(f"Edge deleted: {edge.id}")
            self.edgeDisconnected.emit(edge)
            self.edgeDeleted.emit(edge)

        except Exception as e:
            error_msg = f"Failed to delete edge: {str(e)}"
            logger.error(error_msg)
            raise SocketDisconnectionError(error_msg) from e

    def disconnect_edge(self, edge: EdgeModel) -> None:
        """
        Disconnect an edge without deleting it.

        This clears the start and end sockets while preserving the edge object.

        Args:
            edge: The EdgeModel to disconnect

        Raises:
            SocketDisconnectionError: If disconnection fails
        """
        try:
            if edge not in self.scene_model.edges:
                raise ValueError(f"Edge {edge.id} is not in the scene")

            start_socket = edge.start_socket
            end_socket = edge.end_socket

            # Clear socket references
            edge.start_socket = None
            edge.end_socket = None

            # Remove from sockets
            if start_socket and edge in start_socket.edges:
                start_socket._edges.remove(edge)
            if end_socket and edge in end_socket.edges:
                end_socket._edges.remove(edge)

            logger.info(f"Edge disconnected: {edge.id}")
            self.edgeDisconnected.emit(edge)

        except Exception as e:
            error_msg = f"Failed to disconnect edge: {str(e)}"
            logger.error(error_msg)
            raise SocketDisconnectionError(error_msg) from e

    def set_edge_type(self, edge: EdgeModel, edge_type: int) -> None:
        """
        Set the edge type/style.

        Args:
            edge: The EdgeModel to update
            edge_type: Type constant (STRAIGHT, BEZIER, POLYLINE)

        Raises:
            ValueError: If edge_type is invalid
        """
        try:
            if edge_type not in (EdgeModel.STRAIGHT, EdgeModel.BEZIER, EdgeModel.POLYLINE):
                raise ValueError(f"Invalid edge type: {edge_type}")

            old_type = edge.edge_type
            edge.edge_type = edge_type
            logger.debug(f"Edge type changed: {old_type} → {edge_type}")
            self.edgeTypeChanged.emit(edge, edge_type)

        except Exception as e:
            error_msg = f"Failed to set edge type: {str(e)}"
            logger.error(error_msg)
            raise NodeEditorException(error_msg) from e

    def set_connection_mode(self, mode: int) -> None:
        """
        Set whether sockets can have multiple connections.

        Args:
            mode: SINGLE_CONNECTION or MULTI_CONNECTION
        """
        if mode not in (self.SINGLE_CONNECTION, self.MULTI_CONNECTION):
            raise ValueError(f"Invalid connection mode: {mode}")
        self._connection_mode = mode
        logger.debug(f"Connection mode set to: {mode}")

    def register_connection_validator(self, validator: Callable) -> None:
        """
        Register a custom validator for connections.

        Validators are called before allowing a connection and should raise
        SocketConnectionError if the connection is invalid.

        Args:
            validator: Callable(start_socket, end_socket) that validates the connection

        Example:
            >>> def validate_same_node(start, end):
            ...     if start.parent_node == end.parent_node:
            ...         raise SocketConnectionError("Cannot connect sockets on same node")
            >>> controller.register_connection_validator(validate_same_node)
        """
        self._connection_validators.append(validator)
        logger.debug("Connection validator registered")

    def get_edges(self) -> List[EdgeModel]:
        """
        Get all edges in the scene.

        Returns:
            List[EdgeModel]: List of all edges
        """
        return list(self.scene_model.edges)

    def get_edge_by_id(self, edge_id: str) -> Optional[EdgeModel]:
        """
        Get an edge by its unique identifier.

        Args:
            edge_id: The edge's unique ID

        Returns:
            EdgeModel if found, None otherwise
        """
        for edge in self.scene_model.edges:
            if edge.id == edge_id:
                return edge
        return None

    def get_edges_for_socket(self, socket: SocketModel) -> List[EdgeModel]:
        """
        Get all edges connected to a socket.

        Args:
            socket: The SocketModel to query

        Returns:
            List[EdgeModel]: List of edges connected to the socket
        """
        return list(socket.edges)

    # ======================== Private Methods ========================

    def _validate_connection(self, start_socket: SocketModel, end_socket: SocketModel) -> None:
        """
        Validate a proposed connection.

        This method runs all registered validators and applies connection rules.

        Args:
            start_socket: The source socket
            end_socket: The destination socket

        Raises:
            SocketConnectionError: If validation fails
        """
        if not isinstance(start_socket, SocketModel):
            raise SocketConnectionError("start_socket must be a SocketModel")

        if not isinstance(end_socket, SocketModel):
            raise SocketConnectionError("end_socket must be a SocketModel")

        if start_socket == end_socket:
            raise SocketConnectionError("Cannot connect a socket to itself")

        # Check socket types (shouldn't connect input-to-input or output-to-output)
        if start_socket.socket_type == end_socket.socket_type:
            raise SocketConnectionError(
                f"Cannot connect {start_socket.socket_type} to {end_socket.socket_type}"
            )

        # Check connection mode
        if self._connection_mode == self.SINGLE_CONNECTION:
            if len(start_socket.edges) > 0:
                raise SocketConnectionError(
                    f"Socket {start_socket.id} already has a connection"
                )
            if len(end_socket.edges) > 0:
                raise SocketConnectionError(
                    f"Socket {end_socket.id} already has a connection"
                )

        # Check if already connected
        for edge in start_socket.edges:
            if edge.end_socket == end_socket:
                raise SocketConnectionError(
                    f"Sockets already connected: {start_socket.id} → {end_socket.id}"
                )

        # Run registered validators
        for validator in self._connection_validators:
            try:
                validator(start_socket, end_socket)
            except SocketConnectionError:
                raise
            except Exception as e:
                raise SocketConnectionError(f"Validation failed: {str(e)}") from e

    def _on_edge_added(self, edge: EdgeModel) -> None:
        """Internal handler when an edge is added to the scene."""
        logger.debug(f"Edge added to scene: {edge.id}")

    def _on_edge_removed(self, edge_id: str) -> None:
        """Internal handler when an edge is removed from the scene."""
        logger.debug(f"Edge removed from scene: {edge_id}")
