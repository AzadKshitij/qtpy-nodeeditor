"""
MVC Calculator Sub-window

Represents a single calculator editor document in the MDI interface.
Handles node creation, graph management, and file I/O using MVC pattern.
"""

from typing import TYPE_CHECKING
from qtpy.QtGui import QIcon
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QAction, QMenu
from qtpy.QtCore import QDataStream, QIODevice
from qtpy.QtGui import QPixmap

from nodeeditor.views import NodeEditorWidget
from nodeeditor.node_edge import EDGE_TYPE_DIRECT
from nodeeditor.node_node import Node
from nodeeditor.utils import dumpException

from examples.mvc_calculator.mvc_conf import CALC_NODES, get_class_from_opcode, LISTBOX_MIMETYPE

if TYPE_CHECKING:
    from nodeeditor.node_socket import Socket

DEBUG = False


class MvcCalculatorSubWindow(NodeEditorWidget):
    """
    A sub-window for editing calculator node graphs.

    Extends NodeEditorWidget to provide calculator-specific functionality
    including node creation from menus and automatic output evaluation.
    """

    def __init__(self):
        """Initialize the calculator sub-window."""
        super().__init__()

        self.setTitle()

        # Initialize node creation actions
        self.initNewNodeActions()

        # Connect scene signals
        self.scene.addHasBeenModifiedListener(self.setTitle)
        self.scene.history.addHistoryRestoredListener(self.onHistoryRestored)
        self.scene.addDragEnterListener(self.onDragEnter)
        self.scene.addDropListener(self.onDrop)
        self.scene.setNodeClassSelector(self.getNodeClassFromData)

        # Connect graphics signals
        self.scene.grScene.socketClicked.connect(self.onSocketClicked)

        self._close_event_listeners = []

    def setTitle(self) -> None:
        """Update window title based on the current filename."""
        self.setWindowTitle(self.getUserFriendlyFilename())

    def onSocketClicked(self, socket: 'Socket', node: 'Node'):
        """
        Handle socket click events.

        Args:
            socket: The socket that was clicked
            node: The node containing the socket
        """
        socket_type = "input" if socket.is_input else "output"
        socket_index = socket.index
        node_title = node.title

        if not socket.is_input:
            value = node.eval()
            # Handle multi-output nodes (like division)
            if isinstance(value, list):
                value = value[socket_index]

            if DEBUG:
                print(f"Socket clicked: {socket_type} #{socket_index} on node '{node_title}'")
                print(f"Value: {value}")

    def getNodeClassFromData(self, data):
        """
        Get the node class for deserialization.

        Args:
            data: Serialized node data

        Returns:
            The appropriate Node class
        """
        if 'op_code' not in data:
            return Node
        return get_class_from_opcode(data['op_code'])

    def doEvalOutputs(self):
        """Evaluate all output nodes in the scene."""
        for node in self.scene.nodes:
            if node.__class__.__name__ == "MvcCalcNode_Output":
                node.eval()

    def onHistoryRestored(self):
        """Handle history restoration."""
        self.doEvalOutputs()

    def onDragEnter(self, event):
        """Handle drag enter events."""
        if event.mimeData().hasFormat(LISTBOX_MIMETYPE):
            event.acceptProposedAction()
        else:
            event.setAccepted(False)

    def onDrop(self, event):
        """Handle drop events for node creation from drag-and-drop."""
        if event.mimeData().hasFormat(LISTBOX_MIMETYPE):
            eventData = event.mimeData().data(LISTBOX_MIMETYPE)
            dataStream = QDataStream(eventData, QIODevice.ReadOnly)
            pixmap = QPixmap()
            dataStream >> pixmap
            op_code = dataStream.readInt()
            text = dataStream.readQString()

            mouse_position = event.pos()
            scene_position = self.scene.grScene.views()[0].mapToScene(mouse_position)

            if DEBUG:
                print(f"GOT DROP: [{op_code}] '{text}' mouse: {mouse_position} scene: {scene_position}")

            try:
                node = get_class_from_opcode(op_code)(self.scene)
                node.setPos(scene_position.x(), scene_position.y())
                self.scene.history.storeHistory(f"Created node {node.__class__.__name__}")
            except Exception as e:
                dumpException(e)

            event.setDropAction(Qt.DropAction.MoveAction)
            event.accept()
        else:
            event.ignore()

    def fileLoad(self, filename):
        """
        Load a graph from file.

        Args:
            filename: Path to the file

        Returns:
            True if successful, False otherwise
        """
        if super().fileLoad(filename):
            self.doEvalOutputs()
            return True
        return False

    def initNewNodeActions(self):
        """Initialize actions for creating each node type."""
        self.node_actions = {}
        keys = sorted(CALC_NODES.keys())
        for key in keys:
            node_class = CALC_NODES[key]
            self.node_actions[node_class.op_code] = QAction(
                QIcon(node_class.icon),
                node_class.op_title
            )
            self.node_actions[node_class.op_code].setData(node_class.op_code)

    def initNodesContextMenu(self):
        """Initialize the right-click context menu for creating nodes."""
        context_menu = QMenu(self)
        keys = sorted(CALC_NODES.keys())
        for key in keys:
            node_class = CALC_NODES[key]
            action = context_menu.addAction(
                QIcon(node_class.icon),
                node_class.op_title
            )
            action.setData(node_class.op_code)
            action.triggered.connect(lambda checked, op_code=node_class.op_code: self.onNodeCreationAction(op_code))

        return context_menu

    def onNodeCreationAction(self, op_code):
        """
        Create a new node when a context menu action is triggered.

        Args:
            op_code: The operation code of the node to create
        """
        try:
            node_class = get_class_from_opcode(op_code)
            node = node_class(self.scene)
            self.scene.history.storeHistory(f"Created {node.title}")
        except Exception as e:
            dumpException(e)

    def contextMenuEvent(self, event):
        """Handle right-click context menu."""
        try:
            context_menu = self.initNodesContextMenu()
            context_menu.exec_(event.globalPos())
        except Exception as e:
            dumpException(e)

    def addCloseEventListener(self, callback):
        """
        Add a callback for close events.

        Args:
            callback: Function to call on close
        """
        self._close_event_listeners.append(callback)

    def closeEvent(self, event):
        """Handle close event."""
        for callback in self._close_event_listeners:
            callback(self, event)
        super().closeEvent(event)
