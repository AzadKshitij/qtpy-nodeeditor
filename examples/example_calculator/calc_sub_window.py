from qtpy.QtGui import QIcon, QPixmap
from qtpy.QtCore import QDataStream, QIODevice, Qt
from qtpy.QtWidgets import QAction, QGraphicsProxyWidget, QMenu

from examples.example_calculator.calc_conf import CALC_NODES, get_class_from_opcode, LISTBOX_MIMETYPE
from nodeeditor.node_editor_widget import NodeEditorWidget
from nodeeditor.node_edge import EDGE_TYPE_DIRECT, EDGE_TYPE_BEZIER, EDGE_TYPE_SQUARE
from nodeeditor.node_graphics_view import MODE_EDGE_DRAG
from nodeeditor.node_graphics_node import QDMGraphicsNode
from nodeeditor.node_group import Group
from nodeeditor.utils import dumpException

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from nodeeditor.node_socket import Socket
    from nodeeditor.node_node import Node

DEBUG = False
DEBUG_CONTEXT = False


class CalculatorSubWindow(NodeEditorWidget):
    def __init__(self):
        super().__init__()
        # self.setAttribute(Qt.WA_DeleteOnClose)

        self.setTitle()

        self.initNewNodeActions()

        self.scene.addHasBeenModifiedListener(self.setTitle)
        self.scene.history.addHistoryRestoredListener(self.onHistoryRestored)
        self.scene.addDragEnterListener(self.onDragEnter)
        self.scene.addDropListener(self.onDrop)
        self.scene.setNodeClassSelector(self.getNodeClassFromData)

        self.scene.grScene.socketClicked.connect(self.onSocketClicked)

        self._close_event_listeners = []

    # Example usage in a class that needs to handle the signal
    def onSocketClicked(self, socket: 'Socket', node: 'Node'):
        """Handle socket clicked signal with index and data"""
        socket_type = "input" if socket.is_input else "output"
        socket_index = socket.index
        node_title = node.title

        # Get socket data/value if available
        if socket.is_input:
            return
        else:
            # socket_data = node.getOutputs(socket_index)  # noqa
            # Get the evaluated value
            value = node.eval()

            # Handle multi-output nodes (like division)
            if isinstance(value, list):
                value = value[socket_index]
                print(
                    "🐍 File: example_calculator/calc_sub_window.py:57 | onSocketClicked ~ value", value)

        print(
            f"Socket clicked: {socket_type} #{socket_index} on node '{node_title}'")
        # print(f"Socket data: {socket_data}")

    def getNodeClassFromData(self, data):
        if 'op_code' not in data:
            return Node
        return get_class_from_opcode(data['op_code'])

    def doEvalOutputs(self):
        # eval all output nodes
        for node in self.scene.nodes:
            if node.__class__.__name__ == "CalcNode_Output":
                node.eval()

    def onHistoryRestored(self):
        self.doEvalOutputs()

    def fileLoad(self, filename):
        if super().fileLoad(filename):
            self.doEvalOutputs()
            return True

        return False

    def initNewNodeActions(self):
        self.node_actions = {}
        keys = list(CALC_NODES.keys())
        keys.sort()
        for key in keys:
            node = CALC_NODES[key]
            self.node_actions[node.op_code] = QAction(
                QIcon(node.icon), node.op_title)
            self.node_actions[node.op_code].setData(node.op_code)

    def initNodesContextMenu(self):
        context_menu = QMenu(self)
        keys = list(CALC_NODES.keys())
        keys.sort()
        for key in keys:
            context_menu.addAction(self.node_actions[key])
        return context_menu

    def getSelectedNodes(self, selected_items: List) -> List["Node"]:
        """Extract Node objects from selected graphics items"""
        nodes = []
        for item in selected_items:
            if isinstance(item, QDMGraphicsNode):
                if hasattr(item, "node"):
                    nodes.append(item.node)
            elif isinstance(item, Group):
                # Don't add groups to the selection, only actual nodes
                pass
        return nodes

    def handleGroupingContextMenu(self, event, nodes_selected: List["Node"]):
        """Handle context menu for grouping selected nodes"""
        if DEBUG_CONTEXT:
            print("CONTEXT: GROUPING")

        context_menu = QMenu(self)
        group_act = context_menu.addAction("Group Selected Nodes")
        try:
            action = context_menu.exec(self.mapToGlobal(event.pos()))
        except Exception:
            action = None

        if action == group_act:
            self.onGroupSelectedNodes(nodes_selected)

    def onGroupSelectedNodes(self, nodes: List["Node"]):
        """Create a group containing the selected nodes"""
        try:
            if len(nodes) < 2:
                return

            # Create group (Group.__init__ already registers with scene+grScene)
            group = Group(self.scene, title=f"Group ({len(nodes)} nodes)")

            # Add nodes to group
            for node in nodes:
                group.addNode(node)

            # Auto-fit to children
            group.updateBounds()

            # Store in history
            self.scene.history.storeHistory(f"Created group with {len(nodes)} nodes", setModified=True)

            if DEBUG_CONTEXT:
                print(f"Created group with {len(nodes)} nodes")

        except Exception as e:
            dumpException(e)

    def setTitle(self):
        self.setWindowTitle(self.getUserFriendlyFilename())

    def addCloseEventListener(self, callback):
        self._close_event_listeners.append(callback)

    def closeEvent(self, event):
        for callback in self._close_event_listeners:
            callback(self, event)

    def onDragEnter(self, event):
        if event.mimeData().hasFormat(LISTBOX_MIMETYPE):
            event.acceptProposedAction()
        else:
            # print(" ... denied drag enter event")
            event.setAccepted(False)

    def onDrop(self, event):
        if event.mimeData().hasFormat(LISTBOX_MIMETYPE):
            eventData = event.mimeData().data(LISTBOX_MIMETYPE)
            dataStream = QDataStream(eventData, QIODevice.ReadOnly)
            pixmap = QPixmap()
            dataStream >> pixmap
            op_code = dataStream.readInt()
            text = dataStream.readQString()

            mouse_position = event.pos()
            scene_position = self.scene.grScene.views()[
                0].mapToScene(mouse_position)

            if DEBUG:
                print("GOT DROP: [%d] '%s'" % (op_code, text),
                      "mouse:", mouse_position, "scene:", scene_position)

            try:
                node = get_class_from_opcode(op_code)(self.scene)
                node.setPos(scene_position.x(), scene_position.y())
                self.scene.history.storeHistory(
                    "Created node %s" % node.__class__.__name__)
            except Exception as e:
                dumpException(e)

            event.setDropAction(Qt.MoveAction)
            event.accept()
        else:
            # print(" ... drop ignored, not requested format '%s'" % LISTBOX_MIMETYPE)
            event.ignore()

    def contextMenuEvent(self, event):
        try:
            item = self.scene.getItemAt(event.pos())
            if DEBUG_CONTEXT:
                print(item)

            if type(item) == QGraphicsProxyWidget:
                item = item.widget()

            if hasattr(item, 'node') or hasattr(item, 'socket'):
                self.handleNodeContextMenu(event)
            elif hasattr(item, 'edge'):
                self.handleEdgeContextMenu(event)
            else:
                print("Context menu for empty space")
                # Check if we have selected nodes for grouping
                selected_items = self.scene.getSelectedItems()
                selected_nodes = self.getSelectedNodes(selected_items)
                print(
                    "🐍 File: example_calculator/calc_sub_window.py | Line: 224 | contextMenuEvent ~ selected_nodes",
                    selected_nodes,
                )

                if len(selected_nodes) > 1:
                    # Show grouping context menu for multiple selected nodes
                    self.handleGroupingContextMenu(event, selected_nodes)
                else:
                    # Show default new node context menu for empty space
                    self.handleNewNodeContextMenu(event)

            return super().contextMenuEvent(event)
        except Exception as e:
            dumpException(e)

    def onDetachNodeFromGroup(self, node: "Node"):
        """Detach `node` from its parent group so it moves freely."""
        try:
            grp = getattr(node, 'parent_group', None)
            if grp is None:
                return
            grp.removeNode(node)
            self.scene.history.storeHistory("Detached node from group", setModified=True)
        except Exception as e:
            dumpException(e)

    def handleNodeContextMenu(self, event):
        if DEBUG_CONTEXT:
            print("CONTEXT: NODE")
        # Resolve the right-clicked node BEFORE building the menu so entries
        # can be gated on actual state.
        selected = None
        item = self.scene.getItemAt(event.pos())
        if type(item) == QGraphicsProxyWidget:
            item = item.widget()

        if hasattr(item, 'node'):
            selected = item.node
        if hasattr(item, 'socket'):
            selected = item.socket.node

        # Nodes available for grouping = current selection (+ clicked node,
        # in case right-click hasn't selected it yet).
        nodes_for_grouping = list(self.scene.getSelectedNodes())
        if selected is not None and selected not in nodes_for_grouping:
            nodes_for_grouping.append(selected)

        context_menu = QMenu(self)
        markDirtyAct = context_menu.addAction("Mark Dirty")
        markDirtyDescendantsAct = context_menu.addAction(
            "Mark Descendant Dirty")
        markInvalidAct = context_menu.addAction("Mark Invalid")
        unmarkInvalidAct = context_menu.addAction("Unmark Invalid")
        # Only offer grouping when it can actually do something (>1 node).
        group_nodes = None
        if len(nodes_for_grouping) > 1:
            group_nodes = context_menu.addAction("Group Selected Nodes")
        # Only offer detach when the clicked node actually lives in a group.
        detach_act = None
        if selected is not None and getattr(selected, 'parent_group', None) is not None:
            detach_act = context_menu.addAction("Detach from Group")
        evalAct = context_menu.addAction("Eval")
        try:
            action = context_menu.exec(self.mapToGlobal(event.pos()))
        except Exception:
            action = None

        if DEBUG_CONTEXT:
            print("got item:", selected)
        if selected and action == markDirtyAct:
            selected.markDirty()
        if selected and action == markDirtyDescendantsAct:
            selected.markDescendantsDirty()
        if selected and action == markInvalidAct:
            selected.markInvalid()
        if selected and action == unmarkInvalidAct:
            selected.markInvalid(False)
        if group_nodes is not None and selected and action == group_nodes:
            print("Context menu for empty space")
            # Check if we have selected nodes for grouping
            nodes_selected = self.scene.getSelectedNodes()
            if selected not in nodes_selected:
                nodes_selected.append(selected)
            print(
                "🐍 File: example_calculator/calc_sub_window.py | Line: 277 | handleNodeContextMenu ~ nodes_selected",
                nodes_selected,
            )

            if len(nodes_selected) > 1:
                # Show grouping context menu for multiple selected nodes
                self.onGroupSelectedNodes(nodes_selected)
        if detach_act is not None and selected and action == detach_act:
            self.onDetachNodeFromGroup(selected)
        if selected and action == evalAct:
            val = selected.eval()
            if DEBUG_CONTEXT:
                print("EVALUATED:", val)

    def handleEdgeContextMenu(self, event):
        if DEBUG_CONTEXT:
            print("CONTEXT: EDGE")
        context_menu = QMenu(self)
        bezierAct = context_menu.addAction("Bezier Edge")
        directAct = context_menu.addAction("Direct Edge")
        squareAct = context_menu.addAction("Square Edge")
        try:
            action = context_menu.exec(self.mapToGlobal(event.pos()))
        except Exception:
            action = None

        selected = None
        item = self.scene.getItemAt(event.pos())
        if hasattr(item, 'edge'):
            selected = item.edge

        if selected and action == bezierAct:
            selected.edge_type = EDGE_TYPE_BEZIER
        if selected and action == directAct:
            selected.edge_type = EDGE_TYPE_DIRECT
        if selected and action == squareAct:
            selected.edge_type = EDGE_TYPE_SQUARE

    # helper functions
    def determine_target_socket_of_node(self, was_dragged_flag, new_calc_node):
        target_socket = None
        if was_dragged_flag:
            if len(new_calc_node.inputs) > 0:
                target_socket = new_calc_node.inputs[0]
        else:
            if len(new_calc_node.outputs) > 0:
                target_socket = new_calc_node.outputs[0]
        return target_socket

    def finish_new_node_state(self, new_calc_node):
        self.scene.doDeselectItems()
        new_calc_node.grNode.doSelect(True)
        new_calc_node.grNode.onSelected()

    def handleNewNodeContextMenu(self, event):

        if DEBUG_CONTEXT:
            print("CONTEXT: EMPTY SPACE")
        context_menu = self.initNodesContextMenu()
        try:
            action = context_menu.exec(self.mapToGlobal(event.pos()))
        except Exception:
            action = None

        if action is not None:
            new_calc_node = get_class_from_opcode(action.data())(self.scene)
            scene_pos = self.scene.getView().mapToScene(event.pos())
            new_calc_node.setPos(scene_pos.x(), scene_pos.y())
            if DEBUG_CONTEXT:
                print("Selected node:", new_calc_node)

            if self.scene.getView().mode == MODE_EDGE_DRAG:
                # if we were dragging an edge...
                target_socket = self.determine_target_socket_of_node(
                    self.scene.getView().dragging.drag_start_socket.is_output, new_calc_node)
                if target_socket is not None:
                    self.scene.getView().dragging.edgeDragEnd(target_socket.grSocket)
                    self.finish_new_node_state(new_calc_node)

            else:
                self.scene.history.storeHistory(
                    "Created %s" % new_calc_node.__class__.__name__)
