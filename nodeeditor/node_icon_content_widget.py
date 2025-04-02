# -*- coding: utf-8 -*-
"""A module containing the base class for the Node's content graphical representation. It also contains an example of
an overridden Text Widget, which can pass a notification to it's parent about being modified."""
from collections import OrderedDict
from nodeeditor.node_content_widget import QDMNodeContentWidget
from nodeeditor.node_serializable import Serializable
from qtpy.QtWidgets import QWidget, QLabel, QVBoxLayout, QTextEdit
from qtpy.QtGui import QPixmap, QImage, QFocusEvent
from qtpy.QtCore import Qt

from typing import TYPE_CHECKING, List, Optional, Tuple, Any, Callable


if TYPE_CHECKING:
    from nodeeditor.node_graphics_view import QDMGraphicsView
    from nodeeditor.node_socket import Socket
    from nodeeditor.node_scene import Scene
    from nodeeditor.node_node import Node


class QDMNodeIconContentWidget(QWidget, Serializable):
    """Base class for representation of the Node's graphics content. This class also provides layout
    for other widgets inside of a :py:class:`~nodeeditor.node_node.Node`"""

    def __init__(self, node: 'Node', parent: QWidget = None):
        """
        :param node: reference to the :py:class:`~nodeeditor.node_node.Node`
        :type node: :py:class:`~nodeeditor.node_node.Node`
        :param parent: parent widget
        :type parent: QWidget

        :Instance Attributes:
            - **node** - reference to the :class:`~nodeeditor.node_node.Node`
            - **layout** - ``QLayout`` container
        """
        self.node = node
        super().__init__(parent)
        self.icon: QPixmap

        self.initUI()

    def initUI(self, icon: QPixmap = None):
        """Sets up layouts and widgets to be rendered in :py:class:`~nodeeditor.node_graphics_node.QDMGraphicsNode` class.
        """

        self.v_layout = QVBoxLayout()
        self.v_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.v_layout)

        # Add icon in the center
        self.icon_label = QLabel(self)

        # image = QImage("icons/in.png")
        # if not image.isNull():
        print("icon: ", icon)
        print(type(icon))
        if icon:
            pixmap = icon
            self.icon_label.setPixmap(pixmap)
            self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.v_layout.addWidget(self.icon_label)

        # self.layout = QVBoxLayout()
        # self.layout.setContentsMargins(0, 0, 0, 0)
        # self.setLayout(self.layout)

        # self.wdg_label = QLabel("Some Title")
        # self.layout.addWidget(self.wdg_label)
        # self.layout.addWidget(QDMTextEdit("foo"))

        # Add icon in the center
        # self.icon_label = QLabel(self)
        # if hasattr(self.node, 'picon') and isinstance(self.node.picon, QImage):
        #     image = self.node.picon
        #     print(image.isNull())
        #     # image = QImage(self.node.picon)
        #     if not image.isNull():
        #         pixmap = QPixmap.fromImage(image)
        #         self.icon_label.setPixmap(pixmap)
        #         self.icon_label.setAlignment(Qt.AlignCenter)
        #         self.layout.addWidget(self.icon_label)
        #     else:
        #         print(f"Failed to load image from path: {self.node.picon}")
        # else:
        #     print("Node does not have a valid 'picon' attribute or it is not a QImage")

        # Assuming node has an icon_path attribute
        # image = QImage(self.node.picon)
        # image = self.node.picon
        # pixmap = QPixmap.fromImage(image)
        # self.icon_label.setPixmap(pixmap)
        # self.icon_label.setAlignment(Qt.AlignCenter)
        # self.layout.addWidget(self.icon_label)

    def setEditingFlag(self, value: bool):
        """
        .. note::

            If you are handling keyPress events by default Qt Window's shortcuts and ``QActions``, you will not
             need to use this method.

        Helper function which sets editingFlag inside :py:class:`~nodeeditor.node_graphics_view.QDMGraphicsView` class.

        This is a helper function to handle keys inside nodes with ``QLineEdits`` or ``QTextEdits`` (you can
        use overridden :py:class:`QDMTextEdit` class) and with QGraphicsView class method ``keyPressEvent``.

        :param value: new value for editing flag
        """
        self.node.scene.getView().editingFlag = value

    def serialize(self) -> OrderedDict:
        return OrderedDict([
        ])

    def deserialize(self, data: dict, hashmap: dict = {}, restore_id: bool = True) -> bool:
        return True


class QDMTextEdit(QTextEdit):
    """
        .. note::

            This class is an example of a ``QTextEdit`` modification that handles the `Delete` key event with an overridden
            Qt's ``keyPressEvent`` (when not using ``QActions`` in menu or toolbar)

        Overridden ``QTextEdit`` which sends a notification about being edited to its parent's container :py:class:`QDMNodeContentWidget`
    """

    def focusInEvent(self, event: QFocusEvent | None):
        """Example of an overridden focusInEvent to mark the start of editing

        :param event: Qt's focus event
        :type event: QFocusEvent
        """
        parent = self.parentWidget()
        if isinstance(parent, QDMNodeContentWidget):
            parent.setEditingFlag(True)

        super().focusInEvent(event)

    def focusOutEvent(self, event: QFocusEvent | None):
        """Example of an overridden focusOutEvent to mark the end of editing

        :param event: Qt's focus event
        :type event: QFocusEvent
        """
        parent = self.parentWidget()
        if isinstance(parent, QDMNodeContentWidget):
            parent.setEditingFlag(False)

        super().focusOutEvent(event)
