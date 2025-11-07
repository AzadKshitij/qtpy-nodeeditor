"""
MVC Calculator Node Base

Provides base class for all MVC calculator nodes with evaluation support.
Mirrors the legacy CalcNode pattern but using MVC Node architecture.
"""

from nodeeditor.node_node import Node
from nodeeditor.node_socket import LEFT_CENTER, RIGHT_CENTER
from nodeeditor import QDMGraphicsNode
from nodeeditor import QDMNodeContentWidget
from nodeeditor.utils import dumpException


class MvcCalcGraphicsNode(QDMGraphicsNode):
    """Graphics node for calculator nodes."""

    def initSizes(self):
        """Initialize node dimensions and styling."""
        super().initSizes()
        self.width = 120
        self.height = 120
        self.edge_roundness = 6
        self.edge_padding = 0
        self.title_horizontal_padding = 8
        self.title_vertical_padding = 10


class MvcCalcContent(QDMNodeContentWidget):
    """Base content widget for calculator nodes."""

    def initUI(self):
        """Initialize UI - override in subclasses."""
        pass


class MvcCalcNode(Node):
    """
    Base class for MVC calculator nodes.
    
    Provides evaluation logic and common utilities for calculation nodes.
    All calculator nodes should inherit from this.
    """

    icon = ""
    op_code = 0
    op_title = "Undefined"
    content_label = ""
    content_label_objname = "calc_node_bg"

    GraphicsNode_class = MvcCalcGraphicsNode
    NodeContent_class = MvcCalcContent

    def __init__(self, scene, title="Node", inputs=None, outputs=None, input_text=None, output_text=None):
        """
        Initialize an MVC calculator node.

        Args:
            scene: The scene this node belongs to
            title: Node title
            inputs: List of input socket types
            outputs: List of output socket types
            input_text: Labels for input sockets
            output_text: Labels for output sockets
        """
        if inputs is None:
            inputs = [2, 2]
        if outputs is None:
            outputs = [1]
        if input_text is None:
            input_text = []
        if output_text is None:
            output_text = []

        super().__init__(scene, title, inputs, outputs, input_text, output_text)

        self.values = [None] * len(outputs)
        self.markDirty()

    def initSettings(self):
        """Initialize socket configuration."""
        super().initSettings()
        self.input_socket_position = LEFT_CENTER
        self.output_socket_position = RIGHT_CENTER

    def getSocketValue(self, socket_list, target_node):
        """
        Get socket index for a specific target node.

        Args:
            socket_list: List of sockets to search
            target_node: The node to find

        Returns:
            Index of the socket connected to target_node
        """
        socket_index = 0
        for i, socket in enumerate(socket_list):
            if socket.edges:
                for edge in socket.edges:
                    if edge.getOtherSocket(socket).node == target_node:
                        socket_index = i
                        break
        return socket_index

    def handleInputValue(self, val, socket_index=0):
        """
        Extract correct value from input based on socket connection.

        Args:
            val: Value to extract from
            socket_index: Index of the socket

        Returns:
            Extracted value
        """
        if isinstance(val, list):
            if socket_index < len(val):
                value = val[socket_index]
                if isinstance(value, list):
                    value = value[0]
                if isinstance(value, dict):
                    return value.get('value', None)
                return value
        return val

    def evalOperation(self, input1, input2):
        """
        Evaluate the operation - override in subclasses.

        Args:
            input1: First input value
            input2: Second input value

        Returns:
            Result of operation
        """
        return 0

    def evalImplementation(self):
        """
        Evaluate this node - override in subclasses for custom logic.

        Returns:
            List of output values
        """
        return [None] * len(self.outputs)

    def getInput(self, index=0):
        """
        Get the input node at the specified socket index.

        Args:
            index: Socket index (default: 0 for first input)

        Returns:
            The input Node or None if not connected
        """
        if index < len(self.inputs):
            socket = self.inputs[index]
            if socket.hasAnyEdge():
                for edge in socket.edges:
                    other_socket = edge.getOtherSocket(socket)
                    if other_socket is not None:
                        return other_socket.node
        return None

    def evalChildren(self):
        """Recursively evaluate all child nodes (connected to outputs)."""
        for output_socket in self.outputs:
            for edge in output_socket.edges:
                other_socket = edge.getOtherSocket(output_socket)
                if other_socket is not None:
                    child_node = other_socket.node
                    if child_node:
                        child_node.eval()

    def getOutputs(self, index: int = 0) -> list:
        """
        Get all output nodes connected to the specified socket.
        
        Overrides parent to handle cases where getOtherSocket returns None.
        
        Args:
            index: Socket index (default: 0)
            
        Returns:
            List of output nodes
        """
        outputs = []
        if index < len(self.outputs):
            output_socket = self.outputs[index]
            for edge in output_socket.edges:
                other_socket = edge.getOtherSocket(output_socket)
                if other_socket is not None:
                    outputs.append(other_socket.node)
        return outputs

    def eval(self):
        """
        Evaluate this node and return its output values.

        Uses caching to avoid redundant evaluations if node is clean.

        Returns:
            List of output values or None if invalid
        """
        if not self.isDirty() and not self.isInvalid():
            return self.values

        try:
            val = self.evalImplementation()
            if val is not None:
                self.values = val
                self.markDirty(False)
                self.markInvalid(False)
                self.evalChildren()
            return val
        except ValueError as e:
            self.markInvalid()
            self.grNode.setToolTip(str(e))
            self.markDescendantsDirty()
            return None
        except Exception as e:
            self.markInvalid()
            self.grNode.setToolTip(str(e))
            dumpException(e)
            return None

    def onInputChanged(self, socket=None):
        """
        Handle input socket change.

        Args:
            socket: The socket that changed
        """
        self.markDirty()
        self.eval()

    def serialize(self):
        """Serialize the node to a dictionary."""
        res = super().serialize()
        res['op_code'] = self.__class__.op_code
        return res

    def deserialize(self, data, hashmap=None, restore_id=True):
        """Deserialize the node from a dictionary."""
        if hashmap is None:
            hashmap = {}
        res = super().deserialize(data, hashmap, restore_id)
        return res
