# -*- coding: utf-8 -*-
"""Graph inspector panel for the calculator example.

The buttons run the algorithms of :mod:`nodeeditor.node_graph` on the active
graph and list the result. Clicking a row selects the matching node on the
canvas and centres the view on it, so the listed order can be followed in the
graph itself.
"""

from typing import TYPE_CHECKING, Callable, List, Optional

from qtpy.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from nodeeditor.node_graph import GraphCycleError

if TYPE_CHECKING:
    from nodeeditor.node_edge import Edge
    from nodeeditor.node_node import Node
    from nodeeditor.node_scene import Scene


#: ``Qt.ItemDataRole.UserRole`` written as a number, because the scoped enum
#: name differs between PyQt5 and PyQt6.
NODE_ROLE = 0x0100


def describeNode(node: "Node") -> str:
    """The text a row shows for `node`.

    :param node: the node to describe
    :type node: :class:`~nodeeditor.node_node.Node`
    :return: the node's title
    :rtype: ``str``
    """
    return node.title


class GraphInspectorPanel(QWidget):
    """Buttons for the graph algorithms and a tree showing their result."""

    def __init__(self, get_scene: Callable[[], Optional["Scene"]],
                 parent: Optional[QWidget] = None) -> None:
        """
        :param get_scene: returns the `Scene` of the active tab, or ``None``
          when no graph is open
        :type get_scene: ``callable``
        :param parent: the parent widget
        :type parent: ``QWidget`` or ``None``
        """
        super().__init__(parent)
        self._get_scene = get_scene
        #: the algorithm :meth:`refresh` runs again, set by every ``show*`` method
        self._reload: Callable[[], None] = self.showTopologicalOrder

        self.resultTree = QTreeWidget()
        self.resultTree.setColumnCount(2)
        self.resultTree.setHeaderLabels(["Step", "Node"])
        self.resultTree.setRootIsDecorated(True)
        self.resultTree.setAlternatingRowColors(True)
        self.resultTree.setColumnWidth(0, 70)
        self.resultTree.itemClicked.connect(self.onItemClicked)

        self.statusLabel = QLabel("Open or create a graph to inspect it.")
        self.statusLabel.setWordWrap(True)

        buttons = QHBoxLayout()
        buttons.addWidget(self._makeButton(
            "Topological Order",
            "List every node so it comes after the nodes feeding it",
            self.showTopologicalOrder))
        buttons.addWidget(self._makeButton(
            "Flocks",
            "Split the graph into its disconnected subgraphs",
            self.showComponents))
        buttons.addWidget(self._makeButton(
            "Cycles",
            "Find the loops in the graph",
            self.showCycles))
        buttons.addWidget(self._makeButton(
            "Selected Path",
            "Shortest chain between the two selected nodes",
            self.showSelectedPath))
        buttons.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(buttons)
        layout.addWidget(self.resultTree)
        layout.addWidget(self.statusLabel)

    def _makeButton(self, text: str, tooltip: str, slot: Callable[[], None]) -> QPushButton:
        button = QPushButton(text)
        button.setToolTip(tooltip)
        button.clicked.connect(lambda *args: slot())
        return button

    # ------------------------------------------------------------------
    # algorithms
    # ------------------------------------------------------------------

    def showTopologicalOrder(self) -> None:
        """List the nodes so every node comes after the nodes feeding it."""
        self._reload = self.showTopologicalOrder
        scene = self._get_scene()
        if scene is None:
            self.clearResults("Open or create a graph to inspect it.")
            return
        if not scene.nodes:
            self.clearResults("The graph is empty.")
            return

        try:
            order = scene.topological_order()
        except GraphCycleError as error:
            self.clearResults()
            self._fillCycles(error.cycles)
            self.statusLabel.setText(
                "No dependency order: the graph has %d cycle%s." % (
                    len(error.cycles), "" if len(error.cycles) == 1 else "s"))
            return

        self.clearResults()
        for step, node in enumerate(order, start=1):
            self.addNodeRow(str(step), node)
        self.statusLabel.setText(
            "%d node%s in dependency order. Click a row to select the node."
            % (len(order), "" if len(order) == 1 else "s"))

    def showComponents(self) -> None:
        """List the disconnected subgraphs, each in dependency order."""
        self._reload = self.showComponents
        scene = self._get_scene()
        if scene is None:
            self.clearResults("Open or create a graph to inspect it.")
            return
        if not scene.nodes:
            self.clearResults("The graph is empty.")
            return

        flocks = scene.components()
        # Order every flock the way it has to be evaluated. A cycle leaves no
        # such order, so the flocks keep the scene order components() returns.
        try:
            position = {node: index for index, node in
                        enumerate(scene.topological_order())}
        except GraphCycleError:
            position = None

        self.clearResults()
        for number, flock in enumerate(flocks, start=1):
            if position is not None:
                flock = sorted(flock, key=position.__getitem__)
            parent = self.addTextRow(
                "", "Flock %d (%d node%s)" % (
                    number, len(flock), "" if len(flock) == 1 else "s"))
            for step, node in enumerate(flock, start=1):
                self.addNodeRow(str(step), node, parent)
        self.resultTree.expandAll()
        self.statusLabel.setText(
            "%d disconnected subgraph%s. Click a row to select the node."
            % (len(flocks), "" if len(flocks) == 1 else "s"))

    def showCycles(self) -> None:
        """List the loops of the graph."""
        self._reload = self.showCycles
        scene = self._get_scene()
        if scene is None:
            self.clearResults("Open or create a graph to inspect it.")
            return

        found = scene.cycles()
        self.clearResults()
        if not found:
            self.statusLabel.setText("No cycles: the graph is acyclic.")
            return
        self._fillCycles(found)
        self.statusLabel.setText(
            "%d cycle%s. Click a row to select the node."
            % (len(found), "" if len(found) == 1 else "s"))

    def showSelectedPath(self) -> None:
        """List the shortest chain between the two selected nodes."""
        self._reload = self.showSelectedPath
        scene = self._get_scene()
        if scene is None:
            self.clearResults("Open or create a graph to inspect it.")
            return

        selected = scene.getSelectedNodes()
        if len(selected) != 2:
            self.clearResults(
                "Select exactly two nodes to find the path between them.")
            return

        first, second = selected[0], selected[1]
        path = scene.shortest_path(first, second)
        if path is None:
            path = scene.shortest_path(second, first)
            if path is not None:
                first, second = second, first
        if path is None:
            self.clearResults(
                "No path between %s and %s." % (first.title, second.title))
            return

        self.clearResults()
        for step, (node, _edge) in enumerate(path, start=1):
            self.addNodeRow(str(step), node)
        self.statusLabel.setText(
            "%s -> %s, %d edge%s. Click a row to select the node."
            % (describeNode(first), describeNode(second), len(path) - 1,
               "" if len(path) == 2 else "s"))

    def refresh(self) -> None:
        """Run the last used algorithm again, e.g. for another tab."""
        self._reload()

    # ------------------------------------------------------------------
    # result rows
    # ------------------------------------------------------------------

    def clearResults(self, message: str = "") -> None:
        """Empty the list and show `message` in the status line."""
        self.resultTree.clear()
        self.statusLabel.setText(message)

    def addNodeRow(self, step: str, node: "Node",
                   parent: Optional[QTreeWidgetItem] = None) -> QTreeWidgetItem:
        """Add a row that selects `node` when clicked."""
        item = QTreeWidgetItem([step, describeNode(node)])
        item.setData(0, NODE_ROLE, node)
        item.setToolTip(1, "Click to select this node on the canvas")
        self._attach(item, parent)
        return item

    def addTextRow(self, step: str, text: str,
                   parent: Optional[QTreeWidgetItem] = None) -> QTreeWidgetItem:
        """Add a row that does not belong to a node, such as a flock header."""
        item = QTreeWidgetItem([step, text])
        self._attach(item, parent)
        return item

    def _attach(self, item: QTreeWidgetItem,
                parent: Optional[QTreeWidgetItem]) -> None:
        if parent is None:
            self.resultTree.addTopLevelItem(item)
        else:
            parent.addChild(item)

    def _fillCycles(self, found: List[List["Edge"]]) -> None:
        for number, cycle in enumerate(found, start=1):
            parent = self.addTextRow(
                "", "Cycle %d (%d edge%s)" % (
                    number, len(cycle), "" if len(cycle) == 1 else "s"))
            for step, edge in enumerate(cycle, start=1):
                self.addNodeRow(str(step), edge.start_socket.node, parent)
            self.addTextRow("", "back to %s" % describeNode(
                cycle[0].start_socket.node), parent)
        self.resultTree.expandAll()

    # ------------------------------------------------------------------
    # canvas feedback
    # ------------------------------------------------------------------

    def onItemClicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Select the node of the clicked row and centre the view on it."""
        node = item.data(0, NODE_ROLE)
        if node is None:
            return
        self.focusNode(node)

    def focusNode(self, node: "Node") -> None:
        """Select `node` on the canvas and scroll it into view."""
        scene = self._get_scene()
        graphics_node = getattr(node, "grNode", None)
        if scene is None or graphics_node is None:
            return
        scene.doDeselectItems()
        graphics_node.doSelect(True)
        view = scene.getView()
        if view is not None:
            view.centerOn(graphics_node)
