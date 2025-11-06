"""
MVC Calculator Output Node

Demonstrates output node implementation in the MVC architecture.
"""

from qtpy.QtWidgets import QLabel
from qtpy.QtCore import Qt

from nodeeditor.node_content_widget import QDMNodeContentWidget
from examples.mvc_calculator.mvc_calc_node_base import MvcCalcNode, MvcCalcGraphicsNode

from examples.mvc_calculator.mvc_conf import register_node, OP_NODE_OUTPUT


class MvcCalcOutputContent(QDMNodeContentWidget):
    """Content widget for output nodes displaying computed values."""

    def initUI(self):
        """Initialize the UI with a label for displaying values."""
        self.lbl = QLabel("42", self)
        self.lbl.setAlignment(Qt.AlignLeft)
        self.lbl.setObjectName("mvc_calc_output")


@register_node(OP_NODE_OUTPUT)
class MvcCalcNode_Output(MvcCalcNode):
    """
    Output node for calculator in MVC architecture.

    Displays the result of computations from connected nodes.
    """

    icon = "icons/out.png"
    op_code = OP_NODE_OUTPUT
    op_title = "Output"

    GraphicsNode_class = MvcCalcGraphicsNode
    NodeContent_class = MvcCalcOutputContent

    def __init__(self, scene):
        """
        Initialize an output node.

        Args:
            scene: The scene this node belongs to
        """
        super().__init__(scene, "Output", inputs=[1], outputs=[])

    def initInnerClasses(self):
        """Initialize the content and graphics components."""
        self.content = MvcCalcOutputContent(self)
        self.grNode = MvcCalcGraphicsNode(self)

    def evalImplementation(self):
        """
        Evaluate the output node.

        Gets the value from the connected input and displays it.
        """
        input_node = self.getInput(0)
        if not input_node:
            self.grNode.setToolTip("Input is not connected")
            self.markInvalid()
            return None

        val = input_node.eval()
        if val is None:
            self.grNode.setToolTip("Input is NaN")
            self.markInvalid()
            return None

        # Extract the value from the result
        display_val = val[0] if isinstance(val, list) and val else val

        # Update the label to display the value
        self.content.lbl.setText(str(display_val))
        self.markDirty(False)
        self.markInvalid(False)
        self.grNode.setToolTip("")

        return [display_val]
