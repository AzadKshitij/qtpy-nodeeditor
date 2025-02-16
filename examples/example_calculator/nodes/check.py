from qtpy.QtWidgets import QLineEdit, QVBoxLayout, QLabel
from qtpy.QtCore import Qt
from qtpy.QtGui import QPixmap, QImage
from examples.example_calculator.calc_conf import register_node, OP_NODE_CHECK
from examples.example_calculator.calc_node_base import CalcNode, CalcGraphicsNode
from nodeeditor.node_content_widget import QDMNodeContentWidget
from nodeeditor.node_icon_content_widget import QDMNodeIconContentWidget
from nodeeditor.utils import dumpException


# class CalcCheckContent(QDMNodeContentWidget):
class CalcCheckContent(QDMNodeIconContentWidget):

    # def initUI(self):
    # super().initUI()
    #     self.edit = QLineEdit("1", self)
    #     self.edit.setAlignment(Qt.AlignRight)
    #     self.edit.setObjectName(self.node.content_label_objname)

    def initUI(self):
        """Sets up layouts and widgets to be rendered in :py:class:`~nodeeditor.node_graphics_node.QDMGraphicsNode` class."""
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # Add icon in the center
        self.icon_label = QLabel(self)

        # image = QImage("icons/in.png")
        # if not image.isNull():
        pixmap = QPixmap("examples/example_calculator/icons/File Output.png")
        self.icon_label.setPixmap(pixmap)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.icon_label)

    def serialize(self):
        res = super().serialize()
        # res['value'] = self.edit.text()
        return res

    def deserialize(self, data, hashmap={}):
        res = super().deserialize(data, hashmap)
        try:
            # value = data['value']
            # self.edit.setText(value)
            return True & res
        except Exception as e:
            dumpException(e)
        return res


@register_node(OP_NODE_CHECK)
class CalcCheck_Input(CalcNode):
    icon = "icons/in.png"
    op_code = OP_NODE_CHECK
    op_title = "Check"
    content_label_objname = "calc_node_check"

    def __init__(self, scene):
        super().__init__(scene, inputs=[], outputs=[1, 1, 1, 1])
        self.picon = QImage("icons/in.png")
        self.eval()

    def initInnerClasses(self):
        self.content = CalcCheckContent(self)
        self.grNode = CalcGraphicsNode(self)
        # self.content.edit.textChanged.connect(self.onInputChanged)

    def evalImplementation(self):
        # u_value = self.content.edit.text()
        u_value = 0
        s_value = int(u_value)
        self.value = s_value
        self.markDirty(False)
        self.markInvalid(False)

        self.markDescendantsInvalid(False)
        self.markDescendantsDirty()

        self.grNode.setToolTip("")

        self.evalChildren()

        return self.value
