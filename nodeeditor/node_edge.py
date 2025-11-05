# -*- coding: utf-8 -*-
"""
Edge - MVC-based implementation of an edge/connection in the graph.

The Edge class wraps EdgeModel and EdgeController to provide MVC-based
edge management while maintaining the existing public API.
"""
from collections import OrderedDict
from nodeeditor.node_graphics_edge import QDMGraphicsEdge
from nodeeditor.node_serializable import Serializable
from nodeeditor.utils_no_qt import dumpException
from qtpy.QtCore import QPointF

from typing import TYPE_CHECKING, List, Optional, Tuple, Any, Callable

if TYPE_CHECKING:
    from nodeeditor.node_graphics_view import QDMGraphicsView
    from nodeeditor.node_socket import Socket
    from nodeeditor.node_scene import Scene

# Edge type constants
EDGE_TYPE_DIRECT = 1
EDGE_TYPE_BEZIER = 2
EDGE_TYPE_SQUARE = 3
EDGE_TYPE_IMPROVED_SHARP = 4
EDGE_TYPE_IMPROVED_BEZIER = 5
EDGE_TYPE_DEFAULT = EDGE_TYPE_IMPROVED_BEZIER

DEBUG = False


class Edge(Serializable):
    """
    Edge class representing a connection between two sockets in the graph using MVC architecture.

    The Edge wraps EdgeModel and EdgeController to provide data management
    and operations while maintaining the public API.
    """

    # Class variable containing list of registered edge validators
    edge_validators: List['function'] = []

    def __init__(
        self,
        scene: 'Scene',
        start_socket: 'Socket' = None,
        end_socket: 'Socket' = None,
        edge_type=EDGE_TYPE_DIRECT
    ) -> None:
        """
        Initialize an Edge with MVC components.

        :param scene: Reference to the Scene
        :param start_socket: Reference to the starting socket
        :param end_socket: Reference to the end socket (or None)
        :param edge_type: Constant determining type of edge
        """
        super().__init__()
        
        # Import here to avoid circular imports
        from nodeeditor.models.edge_model import EdgeModel
        from nodeeditor.controllers.edge_controller import EdgeController
        
        # MVC components
        self.model: EdgeModel = EdgeModel()
        self.controller: EdgeController = EdgeController(self.model)
        
        # Reference to scene
        self.scene: 'Scene' = scene

        # Socket references
        self._start_socket: Optional['Socket'] = None
        self._end_socket: Optional['Socket'] = None

        # Set sockets (this updates model and scene)
        self.start_socket = start_socket
        self.end_socket = end_socket
        
        # Edge type
        self._edge_type = edge_type

        # Create graphics edge instance
        self.grEdge: QDMGraphicsEdge = self.createEdgeClassInstance()

        # Add to scene
        self.scene.addEdge(self)
        
        # Connect model signals
        self.model.typeChanged.connect(self._on_type_changed)

    def __str__(self) -> str:
        """String representation of the edge."""
        return "<Edge %s..%s -- S:%s E:%s>" % (
            hex(id(self))[2:5], hex(id(self))[-3:],
            self.start_socket, self.end_socket
        )

    # ==================== Signal Handlers ====================
    
    def _on_type_changed(self, new_type: int) -> None:
        """Handle model type change - update graphics."""
        if self.grEdge:
            self.grEdge.createEdgePathCalculator()
        if self.start_socket is not None:
            self.updatePositions()

    # ==================== Properties (Delegated to Model) ====================

    @property
    def start_socket(self) -> Optional['Socket']:
        """
        Start socket property.

        :return: Starting Socket or None
        """
        return self._start_socket if self._start_socket else None

    @start_socket.setter
    def start_socket(self, value: 'Socket') -> None:
        """Set the start socket safely."""
        # Remove edge from old socket
        if self._start_socket is not None:
            self._start_socket.removeEdge(self)

        # Assign new start socket
        self._start_socket = value
        
        # Add edge to new socket
        if self.start_socket is not None:
            self.start_socket.addEdge(self)

    @property
    def end_socket(self) -> Optional['Socket']:
        """
        End socket property.

        :return: End Socket or None
        """
        return self._end_socket

    @end_socket.setter
    def end_socket(self, value: Optional['Socket']) -> None:
        """Set the end socket safely."""
        # Remove edge from old socket
        if self._end_socket is not None:
            self._end_socket.removeEdge(self)

        # Assign new end socket
        self._end_socket = value
        
        # Add edge to new socket
        if self.end_socket is not None:
            self.end_socket.addEdge(self)

    @property
    def edge_type(self) -> int:
        """
        Edge type constant.

        :return: Edge type constant
        """
        return self._edge_type

    @edge_type.setter
    def edge_type(self, value: int) -> None:
        """Set edge type and update graphics."""
        self._edge_type = value
        self.model.type = value

        # Update graphics
        if self.grEdge:
            self.grEdge.createEdgePathCalculator()

        if self.start_socket is not None:
            self.updatePositions()

    # ==================== Edge Validation ====================

    @classmethod
    def getEdgeValidators(cls) -> List['function']:
        """Return the list of Edge Validator Callbacks."""
        return cls.edge_validators

    @classmethod
    def registerEdgeValidator(cls, validator_callback: 'function') -> None:
        """
        Register Edge Validator Callback.

        :param validator_callback: A function to validate Edge
        """
        cls.edge_validators.append(validator_callback)

    @classmethod
    def validateEdge(cls, start_socket: 'Socket', end_socket: 'Socket') -> bool:
        """
        Validate Edge against all registered Edge Validator Callbacks.

        :param start_socket: Starting Socket of Edge to check
        :param end_socket: End Socket of Edge to check
        :return: True if the Edge is valid, False otherwise
        """
        for validator in cls.getEdgeValidators():
            if not validator(start_socket, end_socket):
                return False
        return True

    # ==================== Edge Operations ====================

    def reconnect(self, from_socket: 'Socket', to_socket: 'Socket') -> None:
        """
        Helper function which reconnects edge from_socket to to_socket.

        :param from_socket: Current socket
        :param to_socket: New socket
        """
        if self.start_socket == from_socket:
            self.start_socket = to_socket
        elif self.end_socket == from_socket:
            self.end_socket = to_socket

    def getGraphicsEdgeClass(self):
        """Returns the class representing Graphics Edge."""
        return QDMGraphicsEdge

    def createEdgeClassInstance(self) -> QDMGraphicsEdge:
        """
        Create instance of graphics edge class.

        :return: Instance of QDMGraphicsEdge
        """
        self.grEdge = self.getGraphicsEdgeClass()(self)
        self.scene.grScene.addItem(self.grEdge)
        if self.start_socket is not None:
            self.updatePositions()
        return self.grEdge

    def getOtherSocket(self, known_socket: 'Socket') -> Optional['Socket']:
        """
        Returns the opposite socket on this Edge.

        :param known_socket: Provide known Socket to determine the opposite one
        :return: The opposite socket on this Edge or None
        """
        return self.start_socket if known_socket == self.end_socket else self.end_socket

    def doSelect(self, new_state: bool = True) -> None:
        """
        Provide safe selecting/deselecting operation.

        :param new_state: True to select, False to deselect
        """
        self.grEdge.doSelect(new_state)

    def updatePositions(self) -> None:
        """
        Updates the internal Graphics Edge positions according to the sockets.

        This should be called if you update Edge positions.
        """
        if not self.start_socket:
            return

        # For collapsed nodes (width=5), calculate position manually
        if (
            self.start_socket
            and self.start_socket.node
            and self.start_socket.node.grNode
            and hasattr(self.start_socket.node.grNode, "width")
            and self.start_socket.node.grNode.width == 5
        ):
            node_scene_pos = self.start_socket.node.grNode.scenePos()
            source_pos = [node_scene_pos.x() + 2.5, node_scene_pos.y() + 2.5]
        else:
            source_scene_pos = self.start_socket.grSocket.scenePos()
            source_pos = [source_scene_pos.x(), source_scene_pos.y()]

        # Normalize coordinates
        normalized_source = QPointF(source_pos[0], source_pos[1])
        source_pos = [normalized_source.x(), normalized_source.y()]
        self.grEdge.setSource(*source_pos)

        if self.end_socket is not None:
            if (
                self.end_socket.node
                and self.end_socket.node.grNode
                and hasattr(self.end_socket.node.grNode, "width")
                and self.end_socket.node.grNode.width == 5
            ):
                node_scene_pos = self.end_socket.node.grNode.scenePos()
                end_pos = [node_scene_pos.x() + 2.5, node_scene_pos.y() + 2.5]
            else:
                end_scene_pos = self.end_socket.grSocket.scenePos()
                end_pos = [end_scene_pos.x(), end_scene_pos.y()]

            # Normalize coordinates
            normalized_end = QPointF(end_pos[0], end_pos[1])
            end_pos = [normalized_end.x(), normalized_end.y()]
            self.grEdge.setDestination(*end_pos)
        else:
            self.grEdge.setDestination(*source_pos)
        
        self.grEdge.update()

    def remove_from_sockets(self) -> None:
        """
        Helper function which sets start and end Socket to None.
        """
        self.end_socket = None
        self.start_socket = None

    def remove(self, silent_for_socket: 'Socket' = None, silent: bool = False) -> None:
        """
        Safely remove this Edge.

        Removes Graphics Edge from the QGraphicsScene and its references.
        Notifies nodes of this event.

        :param silent_for_socket: Socket of Node which won't be notified
        :param silent: If True, no events should be triggered
        """
        old_sockets = [self.start_socket, self.end_socket]

        # Ugly hack since Qt sometimes doesn't remove grEdge from scene
        if DEBUG:
            print("> Edge::remove", self)

        try:
            self.scene.grScene.removeItem(self.grEdge)
        except:
            pass

        if DEBUG:
            print(" - remove edge from the scene")

        self.scene.removeEdge(self)

        if DEBUG:
            print(" - notify nodes")

        # Notify nodes about edge removal
        for socket in old_sockets:
            if socket:
                if socket.node != silent_for_socket:
                    socket.node.onEdgeConnectionChanged(self)
                    if socket.is_input:
                        socket.node.onInputChanged(socket)

        if self.grEdge:
            self.grEdge = None

        if DEBUG:
            print(" - everything was done.")

    # ==================== Serialization ====================

    def serialize(self) -> OrderedDict:
        """Serialize the edge to OrderedDict."""
        return OrderedDict([
            ('id', self.id),
            ('start', self.start_socket.id if self.start_socket else None),
            ('end', self.end_socket.id if self.end_socket else None),
            ('type', self.edge_type),
        ])

    def deserialize(
        self,
        data: dict,
        hashmap: dict = {},
        restore_id: bool = True,
        *args,
        **kwargs
    ) -> bool:
        """Deserialize the edge from dict data."""
        try:
            if restore_id:
                self.id = data['id']

            hashmap[data['id']] = self

            # Resolve socket references from hashmap
            self.start_socket = hashmap[data['start']]
            self.end_socket = hashmap[data['end']]
            self.edge_type = data['type']

            return True
        except Exception as e:
            if DEBUG:
                dumpException(e)
            return False
