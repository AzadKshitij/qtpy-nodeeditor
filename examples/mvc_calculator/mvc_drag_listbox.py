"""
MVC Calculator Drag Listbox

Provides a draggable list of calculator node types for drag-and-drop node creation.
"""

from qtpy.QtGui import QPixmap, QIcon, QDrag
from qtpy.QtCore import QSize, Qt, QByteArray, QDataStream, QMimeData, QIODevice, QPoint
from qtpy.QtWidgets import QListWidget, QAbstractItemView, QListWidgetItem

from examples.mvc_calculator.mvc_conf import CALC_NODES, get_class_from_opcode, LISTBOX_MIMETYPE
from nodeeditor.utils import dumpException


class MvcQDMDragListbox(QListWidget):
    """
    Draggable list widget for MVC calculator nodes.
    
    Allows users to drag node types from the list onto the graph canvas
    to create new nodes.
    """

    def __init__(self, parent=None):
        """Initialize the drag listbox."""
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        """Initialize the list widget with drag-and-drop settings."""
        self.setIconSize(QSize(32, 32))
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setDragEnabled(True)
        self.addMyItems()

    def addMyItems(self):
        """Add all registered calculator node types to the list."""
        keys = list(CALC_NODES.keys())
        keys.sort()
        for key in keys:
            node_class = get_class_from_opcode(key)
            self.addMyItem(node_class.op_title, node_class.icon, node_class.op_code)

    def addMyItem(self, name, icon=None, op_code=0):
        """
        Add a single item to the list.
        
        Args:
            name: Display name of the node
            icon: Path to icon file
            op_code: Operation code identifying the node type
        """
        item = QListWidgetItem(name, self)
        pixmap = QPixmap(icon if icon is not None else ".")
        item.setIcon(QIcon(pixmap))
        item.setSizeHint(QSize(32, 32))

        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled)

        # Store metadata for drag-and-drop
        item.setData(Qt.UserRole, pixmap)
        item.setData(Qt.UserRole + 1, op_code)

    def startDrag(self, *args, **kwargs):
        """
        Start a drag operation with the selected node.
        
        Serializes node metadata into MIME data for drop handling.
        """
        try:
            item = self.currentItem()
            op_code = item.data(Qt.UserRole + 1)
            pixmap = QPixmap(item.data(Qt.UserRole))

            itemData = QByteArray()
            dataStream = QDataStream(itemData, QIODevice.WriteOnly)
            dataStream << pixmap
            dataStream.writeInt(op_code)
            dataStream.writeQString(item.text())

            mimeData = QMimeData()
            mimeData.setData(LISTBOX_MIMETYPE, itemData)

            drag = QDrag(self)
            drag.setMimeData(mimeData)
            drag.setHotSpot(QPoint(pixmap.width() // 2, pixmap.height() // 2))
            drag.setPixmap(pixmap)

            drag.exec_(Qt.DropAction.MoveAction)

        except Exception as e:
            dumpException(e)
