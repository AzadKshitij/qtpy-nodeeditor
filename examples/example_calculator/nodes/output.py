from qtpy.QtWidgets import QLabel
from qtpy.QtCore import Qt
from examples.example_calculator.calc_conf import register_node, OP_NODE_OUTPUT
from examples.example_calculator.calc_node_base import CalcNode, CalcGraphicsNode
from nodeeditor.node_content_widget import QDMNodeContentWidget


class CalcOutputContent(QDMNodeContentWidget):
    def initUI(self):
        self.lbl = QLabel("42", self)
        self.lbl.setAlignment(Qt.AlignLeft)
        self.lbl.setObjectName(self.node.content_label_objname)


@register_node(OP_NODE_OUTPUT)
class CalcNode_Output(CalcNode):
    icon = "icons/out.png"
    op_code = OP_NODE_OUTPUT
    op_title = "Output"
    content_label_objname = "calc_node_output"

    def __init__(self, scene):
        super().__init__(scene, inputs=[1], outputs=[])

    def initInnerClasses(self):
        self.content = CalcOutputContent(self)
        self.grNode = CalcGraphicsNode(self)

    def evalImplementation(self):
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

        # Get value based on socket connection
        socket_index = self.getSocketValue(input_node.outputs, self)
        display_val = self.handleInputValue(val, socket_index)

        # Get additional info if available
        if isinstance(display_val, dict):
            tooltip = f"Type: {display_val.get('type', 'unknown')}"
            display_val = display_val.get('value', None)
            self.grNode.setToolTip(tooltip)
        else:
            self.grNode.setToolTip("")

        # Update display
        self.content.lbl.setText(str(display_val))
        self.markInvalid(False)
        self.markDirty(False)

        return display_val

    # def evalImplementation(self):
    #     input_node = self.getInput(0)
    #     if not input_node:
    #         self.grNode.setToolTip("Input is not connected")
    #         self.markInvalid()
    #         return None

    #     val = input_node.eval()

    #     if val is None:
    #         self.grNode.setToolTip("Input is NaN")
    #         self.markInvalid()
    #         return None

    #     # Get value based on socket connection
    #     socket_index = self.getSocketValue(input_node.outputs, self)
    #     display_val = self.handleInputValue(val, socket_index)

    #     # Update display
    #     self.content.lbl.setText(str(display_val))
    #     self.markInvalid(False)
    #     self.markDirty(False)
    #     self.grNode.setToolTip("")

    #     return display_val
