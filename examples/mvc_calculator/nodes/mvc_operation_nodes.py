"""
MVC Calculator Operation Nodes

Demonstrates operation nodes (Add, Sub, Mul, Div) implementation in the MVC architecture.
"""

from nodeeditor.node_node import Node
from nodeeditor.node_content_widget import QDMNodeContentWidget
from qtpy.QtWidgets import QLabel
from qtpy.QtCore import Qt

from examples.mvc_calculator.nodes.mvc_input_node import MvcCalcGraphicsNode
from examples.mvc_calculator.mvc_conf import (
    register_node,
    OP_NODE_ADD,
    OP_NODE_SUB,
    OP_NODE_MUL,
    OP_NODE_DIV,
)


class MvcCalcOperationContent(QDMNodeContentWidget):
    """Content widget for operation nodes displaying the operation symbol."""

    def initUI(self):
        """Initialize with a label showing the operation."""
        self.lbl = QLabel("+", self)
        self.lbl.setAlignment(Qt.AlignCenter)
        self.lbl.setObjectName("mvc_calc_operation")


class MvcCalcOperationNode(Node):
    """
    Base class for binary operation nodes (two inputs, one output).

    Subclasses should define `evalOperation` method.
    """

    GraphicsNode_class = MvcCalcGraphicsNode
    NodeContent_class = MvcCalcOperationContent

    def __init__(self, scene, op_title="Operation"):
        """
        Initialize an operation node.

        Args:
            scene: The scene this node belongs to
            op_title: Display title for the node
        """
        super().__init__(scene, op_title, inputs=[2, 2], outputs=[1])

    def initInnerClasses(self):
        """Initialize the content and graphics components."""
        self.content = MvcCalcOperationContent(self)
        self.grNode = MvcCalcGraphicsNode(self)
        # Set the operation symbol in the label
        if hasattr(self, 'op_symbol'):
            self.content.lbl.setText(self.op_symbol)

    def evalImplementation(self):
        """
        Evaluate the operation node.

        Gets input values, performs operation, and returns result.
        """
        input1 = self.getInput(0)
        input2 = self.getInput(1)

        if not input1 or not input2:
            self.grNode.setToolTip("Both inputs must be connected")
            self.markInvalid()
            return None

        val1 = input1.eval()
        val2 = input2.eval()

        if val1 is None or val2 is None:
            self.grNode.setToolTip("One or both inputs are NaN")
            self.markInvalid()
            return None

        # Extract values from list format
        v1 = val1[0] if isinstance(val1, list) and val1 else val1
        v2 = val2[0] if isinstance(val2, list) and val2 else val2

        try:
            result = self.evalOperation(v1, v2)
            self.values = [result]
            self.markDirty(False)
            self.markInvalid(False)
            self.grNode.setToolTip("")
            self.evalChildren()
            return self.values
        except Exception as e:
            self.markInvalid(True)
            self.grNode.setToolTip(f"Error: {str(e)}")
            return None

    def evalOperation(self, input1, input2):
        """
        Perform the operation (to be implemented by subclasses).

        Args:
            input1: First input value
            input2: Second input value

        Returns:
            Result of the operation
        """
        raise NotImplementedError("Subclasses must implement evalOperation")


@register_node(OP_NODE_ADD)
class MvcCalcNode_Add(MvcCalcOperationNode):
    """Addition operation node."""

    icon = "icons/add.png"
    op_code = OP_NODE_ADD
    op_title = "Add"
    op_symbol = "+"

    def evalOperation(self, input1, input2):
        """Add two values."""
        return input1 + input2


@register_node(OP_NODE_SUB)
class MvcCalcNode_Sub(MvcCalcOperationNode):
    """Subtraction operation node."""

    icon = "icons/sub.png"
    op_code = OP_NODE_SUB
    op_title = "Subtract"
    op_symbol = "-"

    def evalOperation(self, input1, input2):
        """Subtract input2 from input1."""
        return input1 - input2


@register_node(OP_NODE_MUL)
class MvcCalcNode_Mul(MvcCalcOperationNode):
    """Multiplication operation node."""

    icon = "icons/mul.png"
    op_code = OP_NODE_MUL
    op_title = "Multiply"
    op_symbol = "*"

    def evalOperation(self, input1, input2):
        """Multiply two values."""
        return input1 * input2


@register_node(OP_NODE_DIV)
class MvcCalcNode_Div(MvcCalcOperationNode):
    """Division operation node with integer division and modulo."""

    icon = "icons/divide.png"
    op_code = OP_NODE_DIV
    op_title = "Divide"
    op_symbol = "/"

    def __init__(self, scene):
        """
        Initialize a division node.

        Two outputs: quotient and remainder.

        Args:
            scene: The scene this node belongs to
        """
        super().__init__(scene, "Divide")
        # Override to have two outputs
        self.outputs = [1, 1]  # Two outputs

    def evalImplementation(self):
        """
        Evaluate division with two outputs (quotient and remainder).

        Returns list with two values: [quotient, remainder]
        """
        input1 = self.getInput(0)
        input2 = self.getInput(1)

        if not input1 or not input2:
            self.grNode.setToolTip("Both inputs must be connected")
            self.markInvalid()
            return None

        val1 = input1.eval()
        val2 = input2.eval()

        if val1 is None or val2 is None:
            self.grNode.setToolTip("One or both inputs are NaN")
            self.markInvalid()
            return None

        # Extract values
        v1 = val1[0] if isinstance(val1, list) and val1 else val1
        v2 = val2[0] if isinstance(val2, list) and val2 else val2

        try:
            if v2 == 0:
                raise ValueError("Division by zero")

            quotient = v1 // v2
            remainder = v1 % v2
            self.values = [quotient, remainder]
            self.markDirty(False)
            self.markInvalid(False)
            self.grNode.setToolTip("")
            self.evalChildren()
            return self.values
        except Exception as e:
            self.markInvalid(True)
            self.grNode.setToolTip(f"Error: {str(e)}")
            return None
