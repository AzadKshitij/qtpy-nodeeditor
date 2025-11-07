"""
MVC Calculator Input Node

Demonstrates input node implementation in the MVC architecture.
"""

from qtpy.QtWidgets import QLineEdit
from qtpy.QtCore import Qt

from nodeeditor import QDMNodeContentWidget
from nodeeditor.utils import dumpException

from examples.mvc_calculator.mvc_calc_node_base import MvcCalcNode, MvcCalcGraphicsNode
from examples.mvc_calculator.mvc_conf import register_node, OP_NODE_INPUT


class MvcCalcInputContent(QDMNodeContentWidget):
    """Content widget for input nodes with editable text field."""

    def initUI(self):
        """Initialize the UI with a line edit widget."""
        self.edit = QLineEdit("1", self)
        self.edit.setAlignment(Qt.AlignRight)
        self.edit.setObjectName("mvc_calc_input")

    def serialize(self):
        """Serialize the node content to a dictionary."""
        res = super().serialize()
        res['value'] = self.edit.text()
        return res

    def deserialize(self, data, hashmap=None):
        """Deserialize the node content from a dictionary."""
        if hashmap is None:
            hashmap = {}
        res = super().deserialize(data, hashmap)
        try:
            value = data.get('value', '1')
            self.edit.setText(str(value))
            return True and res
        except Exception as e:
            dumpException(e)
        return res


@register_node(OP_NODE_INPUT)
class MvcCalcNode_Input(MvcCalcNode):
    """
    Input node for calculator in MVC architecture.

    Allows users to enter numeric values that feed into operation nodes.
    """

    icon = "icons/in.png"
    op_code = OP_NODE_INPUT
    op_title = "Input"

    GraphicsNode_class = MvcCalcGraphicsNode
    NodeContent_class = MvcCalcInputContent

    def __init__(self, scene):
        """
        Initialize an input node.

        Args:
            scene: The scene this node belongs to
        """
        super().__init__(scene, "Input", inputs=[], outputs=[1], output_text=["value"])
        self.eval()

    def initInnerClasses(self):
        """Initialize the content and graphics components."""
        self.content = MvcCalcInputContent(self)
        self.grNode = MvcCalcGraphicsNode(self)
        self.content.edit.textChanged.connect(self.onInputChanged)

    def evalImplementation(self):
        """
        Evaluate the input node.

        Returns the user-entered value or marks as invalid if not a number.
        """
        u_value = self.content.edit.text()
        try:
            s_value = int(u_value)
            self.values = [s_value]
            self.markDirty(False)
            self.markInvalid(False)
            self.markDescendantsInvalid(False)
            self.markDescendantsDirty()
            self.grNode.setToolTip("")
            self.evalChildren()
            return self.values
        except ValueError:
            self.markInvalid(True)
            self.grNode.setToolTip("Please enter a valid integer")
            return None
