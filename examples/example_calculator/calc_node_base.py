from qtpy.QtGui import QImage, QPixmap
from qtpy.QtCore import QRectF
from qtpy.QtWidgets import QLabel

from nodeeditor.node_node import Node
from nodeeditor.node_content_widget import QDMNodeContentWidget
from nodeeditor.node_graphics_node import QDMGraphicsNode

from nodeeditor.node_icon_content_widget import QDMNodeIconContentWidget
from nodeeditor.node_icon_graphics_node import QDMIconGraphicsNode

from nodeeditor.node_socket import LEFT_CENTER, RIGHT_CENTER
from nodeeditor.utils import dumpException


class CalcGraphicsNode(QDMIconGraphicsNode):
    def initSizes(self):
        super().initSizes()
        self.width = 120
        self.height = 120
        self.edge_roundness = 6
        self.edge_padding = 0
        self.title_horizontal_padding = 8
        self.title_vertical_padding = 10

    def initAssets(self):
        super().initAssets()
        # self.icons = QImage("icons/status_icons.png")
        self.icons = QImage(
            "examples/example_calculator/icons/status_icons.png")

    def paint(self, painter, QStyleOptionGraphicsItem, widget=None):
        super().paint(painter, QStyleOptionGraphicsItem, widget)

        offset = 24.0
        if self.node.isDirty():
            offset = 0.0
        if self.node.isInvalid():
            offset = 48.0

        # Calculate the position for bottom center
        icon_width = 24.0
        icon_x = (self.width - icon_width) / 2
        icon_y = self.height - 12  # 5 pixels padding from the bottom

        # print(icon_x, icon_y, icon_width, icon_height)
        # painter.drawImage(
        #     QRectF(icon_x, icon_y, icon_width, icon_height),
        #     self.icons,
        #     QRectF(offset, 0, icon_width, icon_height)
        # )

        painter.drawImage(
            QRectF(icon_x, icon_y, 24.0, 24.0),
            self.icons,
            QRectF(offset, 0, 24.0, 24.0)
        )


class CalcContent(QDMNodeIconContentWidget):
    def initUI(self):
        lbl = QLabel(self.node.content_label, self)
        lbl.setObjectName(self.node.content_label_objname)


class CalcNode(Node):
    icon = ""
    op_code = 0
    op_title = "Undefined"
    content_label = ""
    content_label_objname = "calc_node_bg"

    GraphicsNode_class = CalcGraphicsNode
    NodeContent_class = CalcContent

    def __init__(self, scene, inputs=[2, 2], outputs=[1], input_text=[], output_text=[]):
        super().__init__(scene, self.__class__.op_title, inputs,
                         outputs, input_text=input_text, output_text=output_text)

        self.values = [None] * len(outputs)

        # it's really important to mark all nodes Dirty by default
        self.markDirty()

    def initSettings(self):
        super().initSettings()
        self.input_socket_position = LEFT_CENTER
        self.output_socket_position = RIGHT_CENTER

    def getSocketValue(self, socket_list, target_node):
        """Get value based on socket connection"""
        socket_index = 0
        for i, socket in enumerate(socket_list):
            if socket.edges:
                for edge in socket.edges:
                    if edge.getOtherSocket(socket).node == target_node:
                        socket_index = i
                        break
        return socket_index

    def handleInputValue(self, val, socket_index=0):
        """Extract correct value from input based on socket connection"""
        if isinstance(val, list):
            if socket_index < len(val):
                value = val[socket_index]
                if isinstance(value, list):
                    value = value[0]
                # Handle dictionary value
                if isinstance(value, dict):
                    return value.get('value', None)
                return value
        return val

    def evalOperation(self, input1, input2):
        return 123

    def evalImplementation(self):
        print(" _> evaluating %s" % self.__class__.__name__)
        i1 = self.getInput(0)
        i2 = self.getInput(1)

        if i1 is None or i2 is None:
            self.markInvalid()
            self.markDescendantsDirty()
            self.grNode.setToolTip("Connect all inputs")
            return [None] * len(self.outputs)

        val1 = i1.eval()
        val2 = i2.eval()

        # Handle None values from input evaluations
        if val1 is None or val2 is None:
            self.markInvalid()
            self.markDescendantsDirty()
            self.grNode.setToolTip("Invalid input values")
            return [None] * len(self.outputs)

        # Extract first value from lists if necessary
        input1 = val1[0] if isinstance(val1, list) else val1
        input2 = val2[0] if isinstance(val2, list) else val2

        try:
            val = self.evalOperation(input1, input2)

            # Handle multiple outputs
            if isinstance(val, list):
                if len(val) == len(self.outputs):
                    # Wrap each value in a list
                    self.values = [[v] for v in val]
                else:
                    # If lengths don't match, fill with None
                    self.values = [[None]] * len(self.outputs)
            else:
                # Single value case - all outputs get the same value
                self.values = [[val]] * len(self.outputs)

            self.markDirty(False)
            self.markInvalid(False)
            self.grNode.setToolTip("")

            self.markDescendantsDirty()
            self.evalChildren()

            return self.values

        except Exception as e:
            self.markInvalid()
            self.grNode.setToolTip(str(e))
            self.markDescendantsDirty()
            return [None] * len(self.outputs)

    def eval(self):
        if not self.isDirty() and not self.isInvalid():
            print(" _> returning cached %s value:" %
                  self.__class__.__name__, self.values)
            return self.values

        try:
            val = self.evalImplementation()
            return val
        except ValueError as e:
            self.markInvalid()
            self.grNode.setToolTip(str(e))
            self.markDescendantsDirty()
        except Exception as e:
            self.markInvalid()
            self.grNode.setToolTip(str(e))
            dumpException(e)

    def onInputChanged(self, socket=None):
        print("%s::__onInputChanged" % self.__class__.__name__)
        self.markDirty()
        self.eval()

    def serialize(self):
        res = super().serialize()
        res['op_code'] = self.__class__.op_code
        return res

    def deserialize(self, data, hashmap={}, restore_id=True):
        res = super().deserialize(data, hashmap, restore_id)
        print("Deserialized CalcNode '%s'" %
              self.__class__.__name__, "res:", res)
        return res
