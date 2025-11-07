# -*- coding: utf-8 -*-
"""
Node - MVC-based implementation of a node in the graph.

The Node class wraps NodeModel and NodeController to provide MVC-based
node management while maintaining the existing public API.
"""
from collections import OrderedDict
from qtpy.QtCore import QObject, Signal
from nodeeditor.views.graphics.node_graphics_node import QDMGraphicsNode
from nodeeditor.views.content_widgets.node_content_widget import QDMNodeContentWidget
from nodeeditor.node_serializable import Serializable
from nodeeditor.node_socket import Socket, LEFT_BOTTOM, LEFT_CENTER, LEFT_TOP, RIGHT_BOTTOM, RIGHT_CENTER, RIGHT_TOP
from nodeeditor.utils.utils_no_qt import dumpException

from typing import TYPE_CHECKING, List, Optional, Tuple, Any, Union

if TYPE_CHECKING:
    from nodeeditor.views.graphics.node_graphics_view import QDMGraphicsView
    from nodeeditor.node_edge import Edge
    from nodeeditor.node_socket import Socket
    from nodeeditor.node_scene import Scene
    from nodeeditor.node_group_node import GroupNode

DEBUG = False


class Node(QObject, Serializable):
    """
    Node class representing a node in the graph using MVC architecture.

    The Node wraps NodeModel and NodeController to provide data management
    and operations while maintaining the public API.
    """
    # Signal emitted when node position changes (after user finishes dragging)
    positionChanged = Signal(object)  # Emits the Node object

    GraphicsNode_class = QDMGraphicsNode
    NodeContent_class = QDMNodeContentWidget
    Socket_class = Socket

    def __init__(
        self,
        scene: 'Scene',
        title: str = "Undefined Node",
        inputs: list = [],
        outputs: list = [],
        input_text: list = [],
        output_text: list = []
    ) -> None:
        """
        Initialize a Node with MVC components.

        :param scene: reference to the Scene
        :param title: Node title shown in Scene
        :param inputs: list of socket types for inputs
        :param outputs: list of socket types for outputs
        :param input_text: list of text labels for input sockets
        :param output_text: list of text labels for output sockets
        """
        QObject.__init__(self)
        Serializable.__init__(self)

        # Import here to avoid circular imports
        from nodeeditor.models.node_model import NodeModel
        from nodeeditor.controllers.node_controller import NodeController

        # MVC components
        self.model: NodeModel = NodeModel(title)
        self.controller: NodeController = NodeController(self.model)

        # Reference to scene
        self.scene: 'Scene' = scene

        # Graphics and content
        self.content: QDMNodeContentWidget
        self.grNode: QDMGraphicsNode

        # Initialize graphics and content
        self.initInnerClasses()
        self.initSettings()

        # Evaluation state - MUST be initialized before initSockets as it may be accessed during socket creation
        self._is_dirty = False
        self._is_invalid = False

        # Set title (will update model and graphics)
        self.title = title

        # Add to scene
        self.scene.addNode(self)
        # Only add to graphics scene if not already added
        if self.grNode.scene() is None:
            self.scene.grScene.addItem(self.grNode)

        # Create sockets for inputs and outputs
        self.inputs: List['Socket'] = []
        self.outputs: List['Socket'] = []
        self.initSockets(inputs, outputs, input_text, output_text)

        # Grouping support
        self.parent_group: Optional["GroupNode"] = None

        # Connect model signals to update graphics
        self.model.titleChanged.connect(self._on_title_changed)
        self.model.positionChanged.connect(self._on_position_changed)

    def __str__(self) -> str:
        """String representation of the node."""
        return "<%s:%s %s..%s>" % (
            self.title,
            self.__class__.__name__,
            hex(id(self))[2:5],
            hex(id(self))[-3:]
        )

    # ==================== Signal Handlers ====================

    def _on_title_changed(self, new_title: str) -> None:
        """Handle model title change - update graphics."""
        if self.grNode:
            self.grNode.title = new_title

    def _on_position_changed(self, pos) -> None:
        """Handle model position change - update graphics."""
        # Support both QPointF payloads (from MVC model) and legacy tuple payloads
        if hasattr(pos, "x") and hasattr(pos, "y"):
            x = float(pos.x())
            y = float(pos.y())
        else:
            try:
                x, y = pos  # type: ignore[misc]
                x = float(x)
                y = float(y)
            except (TypeError, ValueError):
                # Fallback: ignore malformed payload
                return

        if self.grNode:
            self.grNode.setPos(x, y)

        # Guard: Only process edges if sockets are actual Socket objects
        # During initialization or edge cases, self.inputs/outputs may contain non-Socket items
        for socket in self.inputs + self.outputs:
            # Type guard: ensure socket is a Socket object with edges attribute
            if not hasattr(socket, "edges"):
                continue
            for edge in socket.edges:
                # Guard against edges being removed during updates
                if edge.grEdge is None:
                    continue
                if edge.grEdge is not None:
                    edge.grEdge.calcPath()
                edge.updatePositions()

        self.positionChanged.emit(
            self
        )  # ==================== Properties (Delegated to Model) ====================

    @property
    def title(self) -> str:
        """
        Title shown in the scene.

        :return: current Node title
        """
        return self.model.title

    @title.setter
    def title(self, value: str) -> None:
        """Set node title."""
        self.model.title = value
        # Also update graphics immediately
        if self.grNode:
            self.grNode.title = value

    @property
    def pos(self):
        """
        Retrieve Node's position in the Scene.

        :return: Node position (QPointF)
        """
        return self.grNode.pos()

    def setPos(self, x: float, y: float) -> None:
        """
        Sets position of the Node.

        :param x: X Scene position
        :param y: Y Scene position
        """
        # Update model first
        self.model.position = (x, y)

        # Update graphics
        self.grNode.setPos(x, y)

        # Update connected edges
        for socket in self.inputs + self.outputs:
            for edge in socket.edges:
                # Guard against edges being removed during updates
                if edge.grEdge is None:
                    continue
                if edge.grEdge is not None:
                    edge.grEdge.calcPath()
                edge.updatePositions()

        # Emit signal
        self.positionChanged.emit(self)

    # ==================== Graphics and Content Initialization ====================

    def initInnerClasses(self) -> None:
        """Sets up graphics Node (PyQt) and Content Widget."""
        node_content_class = self.getNodeContentClass()
        graphics_node_class = self.getGraphicsNodeClass()
        if node_content_class is not None:
            self.content = node_content_class(self)
        if graphics_node_class is not None:
            self.grNode = graphics_node_class(self)

    def getNodeContentClass(self):
        """Returns class representing node content."""
        return self.__class__.NodeContent_class

    def getGraphicsNodeClass(self):
        """Returns class representing graphics node."""
        return self.__class__.GraphicsNode_class

    def initSettings(self) -> None:
        """Initialize socket configuration."""
        self.socket_spacing = 22
        self.input_socket_position = LEFT_BOTTOM
        self.output_socket_position = RIGHT_TOP
        self.input_multi_edged = False
        self.output_multi_edged = True
        self.socket_offsets = {
            LEFT_BOTTOM: -1,
            LEFT_CENTER: -1,
            LEFT_TOP: -1,
            RIGHT_BOTTOM: 1,
            RIGHT_CENTER: 1,
            RIGHT_TOP: 1,
        }

    def initSockets(
        self,
        inputs: list,
        outputs: list,
        input_text: list = [],
        output_text: list = [],
        reset: bool = True
    ) -> None:
        """
        Create sockets for inputs and outputs.

        :param inputs: list of socket types for inputs
        :param outputs: list of socket types for outputs
        :param input_text: list of text labels for input sockets
        :param output_text: list of text labels for output sockets
        :param reset: if True, destroys and removes old sockets
        """
        input_text = input_text or []
        output_text = output_text or []

        if reset:
            # Clear old sockets
            if hasattr(self, 'inputs') and hasattr(self, 'outputs'):
                for socket in (self.inputs + self.outputs):
                    self.scene.grScene.removeItem(socket.grSocket)
                self.inputs = []
                self.outputs = []

        # Create input sockets
        for i, socket_type in enumerate(inputs):
            text = input_text[i] if i < len(input_text) else ""
            socket = self.__class__.Socket_class(
                node=self,
                index=i,
                position=self.input_socket_position,
                socket_type=socket_type,
                multi_edges=self.input_multi_edged,
                count_on_this_node_side=len(inputs),
                is_input=True
            )
            socket.grSocket.setText(text)
            self.inputs.append(socket)

        # Create output sockets
        for i, socket_type in enumerate(outputs):
            text = output_text[i] if i < len(output_text) else ""
            socket = self.__class__.Socket_class(
                node=self,
                index=i,
                position=self.output_socket_position,
                socket_type=socket_type,
                multi_edges=self.output_multi_edged,
                count_on_this_node_side=len(outputs),
                is_input=False
            )
            socket.grSocket.setText(text)
            self.outputs.append(socket)

    def onEdgeConnectionChanged(self, new_edge: 'Edge') -> None:
        """
        Event handling when any connection (Edge) has changed.

        :param new_edge: reference to the changed Edge
        """
        pass

    def onInputChanged(self, socket: 'Socket') -> None:
        """
        Event handling when Node's input Edge has changed.
        Auto-marks this Node and descendants as Dirty.

        :param socket: reference to the changed Socket
        """
        self.markDirty()
        self.markDescendantsDirty()

    def onDeserialized(self, data: dict) -> None:
        """
        Event manually called when this node was deserialized.

        :param data: the deserialized data
        """
        pass

    def onDoubleClicked(self, event) -> None:
        """Event handling double click on Graphics Node in Scene."""
        pass

    def doSelect(self, new_state: bool = True) -> None:
        """
        Shortcut method for selecting/deselecting the Node.

        :param new_state: True to select, False to deselect
        """
        self.grNode.doSelect(new_state)

    def isSelected(self) -> bool:
        """Returns True if current Node is selected."""
        return self.grNode.isSelected()

    def hasConnectedEdge(self, edge: 'Edge') -> bool:
        """Returns True if edge is connected to any Socket of this Node."""
        for socket in (self.inputs + self.outputs):
            if socket.isConnected(edge):
                return True
        return False

    def getSocketPosition(
        self,
        index: int,
        position: int,
        num_out_of: int = 1
    ) -> List[float]:
        """
        Get the relative x, y position of a Socket.

        :param index: Order number of the Socket (0, 1, 2, ...)
        :param position: Socket position constant
        :param num_out_of: Total number of Sockets on this position
        :return: [x, y] position of socket on the node
        """
        x = self.socket_offsets[position] if (position in (
            LEFT_TOP, LEFT_CENTER, LEFT_BOTTOM)) else self.grNode.width + self.socket_offsets[position]

        if position in (LEFT_BOTTOM, RIGHT_BOTTOM):
            y = self.grNode.height - self.grNode.edge_roundness - \
                self.grNode.title_vertical_padding - index * self.socket_spacing
        elif position in (LEFT_CENTER, RIGHT_CENTER):
            num_sockets = num_out_of
            node_height = self.grNode.height
            top_offset = self.grNode.title_height + 2 * \
                self.grNode.title_vertical_padding + self.grNode.edge_padding
            available_height = node_height - top_offset

            total_height_of_all_sockets = num_sockets * self.socket_spacing
            new_top = available_height - total_height_of_all_sockets

            y = top_offset + available_height / 2.0 + (index-0.5)*self.socket_spacing
            if num_sockets > 1:
                y -= self.socket_spacing * (num_sockets-1)/2

        elif position in (LEFT_TOP, RIGHT_TOP):
            y = self.grNode.title_height + self.grNode.title_vertical_padding + \
                self.grNode.edge_roundness + index * self.socket_spacing
        else:
            y = 0

        return [x, y]

    def getSocketScenePosition(self, socket: 'Socket') -> Tuple[float, float]:
        """
        Get absolute Socket position in the Scene.

        :param socket: Socket which position we want to know
        :return: (x, y) Socket's scene position
        """
        nodepos = self.grNode.pos()
        socketpos = self.getSocketPosition(
            socket.index, socket.position, socket.count_on_this_node_side)
        return (nodepos.x() + socketpos[0], nodepos.y() + socketpos[1])

    def updateConnectedEdges(self) -> None:
        """Recalculate positions of all connected Edges."""
        for socket in self.inputs + self.outputs:
            for edge in socket.edges:
                edge.updatePositions()

    def remove(self) -> None:
        """Safely remove this Node."""
        if DEBUG:
            print("> Removing Node", self)

        # Remove all edges from sockets
        if DEBUG:
            print(" - remove all edges from sockets")
        for socket in (self.inputs + self.outputs):
            for edge in socket.edges.copy():
                if DEBUG:
                    print("    - removing from socket:", socket, "edge:", edge)
                edge.remove()

        # Remove graphics node
        if DEBUG:
            print(" - remove grNode")
        self.scene.grScene.removeItem(self.grNode)
        self.grNode = None  # type: ignore

        # Remove node from scene
        if DEBUG:
            print(" - remove node from the scene")
        self.scene.removeNode(self)
        if DEBUG:
            print(" - everything was done.")

    # ==================== Evaluation (Dirty/Invalid State) ====================

    def isDirty(self) -> bool:
        """Is this node marked as Dirty?"""
        return self._is_dirty

    def markDirty(self, new_value: bool = True) -> None:
        """Mark this Node as Dirty."""
        self._is_dirty = new_value
        if self._is_dirty:
            self.onMarkedDirty()

    def onMarkedDirty(self) -> None:
        """Called when this Node has been marked as Dirty. Override this."""
        pass

    def markChildrenDirty(self, new_value: bool = True) -> None:
        """Mark all first level children of this Node to be Dirty."""
        for other_node in self.getChildrenNodes():
            other_node.markDirty(new_value)

    def markDescendantsDirty(self, new_value: bool = True) -> None:
        """Mark all children and descendants of this Node to be Dirty."""
        for other_node in self.getChildrenNodes():
            other_node.markDirty(new_value)
            other_node.markDescendantsDirty(new_value)

    def isInvalid(self) -> bool:
        """Is this node marked as Invalid?"""
        return self._is_invalid

    def markInvalid(self, new_value: bool = True) -> None:
        """Mark this Node as Invalid."""
        self._is_invalid = new_value
        if self._is_invalid:
            self.onMarkedInvalid()

    def onMarkedInvalid(self) -> None:
        """Called when this Node has been marked as Invalid. Override this."""
        pass

    def markChildrenInvalid(self, new_value: bool = True) -> None:
        """Mark all first level children of this Node to be Invalid."""
        for other_node in self.getChildrenNodes():
            other_node.markInvalid(new_value)

    def markDescendantsInvalid(self, new_value: bool = True) -> None:
        """Mark all children and descendants of this Node to be Invalid."""
        for other_node in self.getChildrenNodes():
            other_node.markInvalid(new_value)
            other_node.markDescendantsInvalid(new_value)

    def eval(self, index: int = 0) -> int:
        """Evaluate this Node. Override this method. Returns status code."""
        self.markDirty(False)
        self.markInvalid(False)
        return 0

    def evalChildren(self) -> None:
        """Evaluate all children of this Node."""
        for node in self.getChildrenNodes():
            node.eval()

    # ==================== Graph Traversal ====================

    def getChildrenNodes(self) -> List['Node']:
        """
        Retrieve all first-level children connected to this Node's Outputs.

        :return: list of Nodes connected to this Node from all Outputs
        """
        if self.outputs == []:
            return []
        other_nodes = []
        for ix in range(len(self.outputs)):
            for edge in self.outputs[ix].edges:
                # Guard against malformed edges where getOtherSocket returns None
                other_socket = edge.getOtherSocket(self.outputs[ix])
                if other_socket is not None:
                    other_node = other_socket.node
                    if other_node is not None:
                        other_nodes.append(other_node)
        return other_nodes

    def getInput(self, index: int = 0) -> Optional['Node']:
        """
        Get the first Node connected to the Input specified by index.

        :param index: Order number of the Input Socket
        :return: Node which is connected to the specified Input or None
        """
        try:
            input_socket = self.inputs[index]
            if len(input_socket.edges) == 0:
                return None
            connecting_edge = input_socket.edges[0]
            other_socket = connecting_edge.getOtherSocket(self.inputs[index])
            # Guard against malformed edges
            if other_socket is None:
                return None
            return other_socket.node
        except Exception as e:
            dumpException(e)
            return None

    def getInputWithSocket(
        self,
        index: int = 0
    ) -> Union[Tuple['Node', 'Socket'], Tuple[None, None]]:
        """
        Get the first Node connected to the Input and its Socket.

        :param index: Order number of the Input Socket
        :return: Tuple (Node, Socket) or (None, None)
        """
        try:
            input_socket = self.inputs[index]
            if len(input_socket.edges) == 0:
                return None, None
            connecting_edge = input_socket.edges[0]
            other_socket = connecting_edge.getOtherSocket(self.inputs[index])
            # Guard against malformed edges
            if other_socket is None:
                return None, None
            return other_socket.node, other_socket
        except Exception as e:
            dumpException(e)
            return None, None

    def getInputWithSocketIndex(
        self,
        index: int = 0
    ) -> Union[Tuple['Node', int], Tuple[None, None]]:
        """
        Get the first Node connected to the Input and its Socket index.

        :param index: Order number of the Input Socket
        :return: Tuple (Node, socket_index) or (None, None)
        """
        try:
            edge = self.inputs[index].edges[0]
            socket = edge.getOtherSocket(self.inputs[index])
            # Guard against malformed edges
            if socket is None:
                return None, None
            return socket.node, socket.index
        except IndexError:
            return None, None
        except Exception as e:
            dumpException(e)
            return None, None

    def getInputs(self, index: int = 0) -> List['Node']:
        """
        Get all Nodes connected to the Input specified by index.

        :param index: Order number of the Input Socket
        :return: all Nodes which are connected to the specified Input
        """
        ins = []
        for edge in self.inputs[index].edges:
            other_socket = edge.getOtherSocket(self.inputs[index])
            # Guard against malformed edges
            if other_socket is not None:
                ins.append(other_socket.node)
        return ins

    def getOutputs(self, index: int = 0) -> List['Node']:
        """
        Get all Nodes connected to the Output specified by index.

        :param index: Order number of the Output Socket
        :return: all Nodes which are connected to the specified Output
        """
        outs = []
        for edge in self.outputs[index].edges:
            other_socket = edge.getOtherSocket(self.outputs[index])
            # Guard against malformed edges
            if other_socket is not None:
                outs.append(other_socket.node)
        return outs

    # ==================== Serialization ====================

    def serialize(self) -> OrderedDict:
        """Serialize the node to OrderedDict."""
        inputs, outputs = [], []
        for socket in self.inputs:
            inputs.append(socket.serialize())
        for socket in self.outputs:
            outputs.append(socket.serialize())
        ser_content = self.content.serialize() if isinstance(
            self.content, Serializable) else {}
        return OrderedDict([
            ('id', self.id),
            ('title', self.title),
            ('pos_x', self.grNode.scenePos().x()),
            ('pos_y', self.grNode.scenePos().y()),
            ('inputs', inputs),
            ('outputs', outputs),
            ('content', ser_content),
        ])

    def deserialize(
        self,
        data: dict,
        hashmap: dict = {},
        restore_id: bool = True,
        *args,
        **kwargs
    ) -> bool:
        """Deserialize the node from dict data."""
        try:
            if restore_id:
                self.id = data['id']
            hashmap[data['id']] = self

            self.setPos(data['pos_x'], data['pos_y'])
            self.title = data['title']

            data['inputs'].sort(
                key=lambda socket: socket['index'] + socket['position'] * 10000)
            data['outputs'].sort(
                key=lambda socket: socket['index'] + socket['position'] * 10000)
            num_inputs = len(data['inputs'])
            num_outputs = len(data['outputs'])

            # Reuse existing sockets or create new ones
            for socket_data in data['inputs']:
                found = None
                for socket in self.inputs:
                    if socket.index == socket_data['index']:
                        found = socket
                        break
                if found is None:
                    found = self.__class__.Socket_class(
                        node=self,
                        index=socket_data['index'],
                        position=socket_data['position'],
                        socket_type=socket_data['socket_type'],
                        count_on_this_node_side=num_inputs,
                        is_input=True
                    )
                    self.inputs.append(found)
                found.deserialize(socket_data, hashmap, restore_id)

            for socket_data in data['outputs']:
                found = None
                for socket in self.outputs:
                    if socket.index == socket_data['index']:
                        found = socket
                        break
                if found is None:
                    found = self.__class__.Socket_class(
                        node=self,
                        index=socket_data['index'],
                        position=socket_data['position'],
                        socket_type=socket_data['socket_type'],
                        count_on_this_node_side=num_outputs,
                        is_input=False
                    )
                    self.outputs.append(found)
                found.deserialize(socket_data, hashmap, restore_id)

        except Exception as e:
            dumpException(e)

        # Deserialize the content of the node
        if isinstance(self.content, Serializable):
            res = self.content.deserialize(data['content'], hashmap)
            return res

        return True
