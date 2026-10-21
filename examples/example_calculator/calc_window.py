import examples.example_calculator.qss.nodeeditor_dark_resources
import os
from qtpy.QtGui import QIcon, QKeySequence
from qtpy.QtWidgets import QMdiArea, QWidget, QDockWidget, QAction, QMessageBox, QFileDialog
from qtpy.QtCore import Qt, QSignalMapper

from nodeeditor.node_editor_widget import NodeEditorWidget
from nodeeditor.utils import loadStylesheets
from nodeeditor.node_editor_window import NodeEditorWindow
from examples.example_calculator.calc_sub_window import CalculatorSubWindow
from examples.example_calculator.calc_drag_listbox import QDMDragListbox
from examples.example_calculator.calc_graph_inspector import GraphInspectorPanel
from nodeeditor.utils import dumpException, pp
from examples.example_calculator.calc_conf import CALC_NODES

# Enabling edge validators
from nodeeditor.node_edge import Edge
from nodeeditor.node_edge_validators import (
    edge_validator_debug,
    edge_cannot_connect_two_outputs_or_two_inputs,
    edge_cannot_connect_input_and_output_of_same_node
)
Edge.registerEdgeValidator(edge_validator_debug)
Edge.registerEdgeValidator(edge_cannot_connect_two_outputs_or_two_inputs)
Edge.registerEdgeValidator(edge_cannot_connect_input_and_output_of_same_node)


# images for the dark skin


DEBUG = False


class CalculatorWindow(NodeEditorWindow):

    def initUI(self):
        self.name_company = 'Blenderfreak'
        self.name_product = 'Calculator NodeEditor'
        self.windowMapper = QSignalMapper(self)

        self.stylesheet_filename = os.path.join(
            os.path.dirname(__file__), "qss/nodeeditor.qss")
        loadStylesheets(
            # os.path.join(os.path.dirname(__file__), "qss/nodeeditor-dark.qss"),
            self.stylesheet_filename
        )

        self.empty_icon = QIcon(".")

        if DEBUG:
            print("Registered nodes:")
            pp(CALC_NODES)

        self.mdiArea = QMdiArea()
        self.mdiArea.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.mdiArea.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.mdiArea.setViewMode(QMdiArea.ViewMode.TabbedView)
        self.mdiArea.setDocumentMode(True)
        self.mdiArea.setTabsClosable(True)
        self.mdiArea.setTabsMovable(True)
        self.setCentralWidget(self.mdiArea)

        self.mdiArea.subWindowActivated.connect(self.updateMenus)

        self.createNodesDock()
        self.createGraphInspectorDock()

        self.createActions()
        self.createMenus()
        self.createToolBars()
        self.createStatusBar()
        self.updateMenus()

        self.readSettings()

        self.setWindowTitle("Calculator NodeEditor Example")

    def closeEvent(self, event):
        self.mdiArea.closeAllSubWindows()
        if self.mdiArea.currentSubWindow():
            event.ignore()
        else:
            self.writeSettings()
            event.accept()
            # hacky fix for PyQt 5.14.x
            import sys
            sys.exit(0)

    def createActions(self):
        super().createActions()

        self.actClose = QAction("Cl&ose", self, statusTip="Close the active window",
                                triggered=self.mdiArea.closeActiveSubWindow)
        self.actCloseAll = QAction(
            "Close &All", self, statusTip="Close all the windows", triggered=self.mdiArea.closeAllSubWindows)
        self.actTile = QAction(
            "&Tile", self, statusTip="Tile the windows", triggered=self.mdiArea.tileSubWindows)
        self.actCascade = QAction(
            "&Cascade", self, statusTip="Cascade the windows", triggered=self.mdiArea.cascadeSubWindows)
        self.actNext = QAction("Ne&xt", self, shortcut=QKeySequence.NextChild,
                               statusTip="Move the focus to the next window", triggered=self.mdiArea.activateNextSubWindow)
        self.actPrevious = QAction("Pre&vious", self, shortcut=QKeySequence.PreviousChild,
                                   statusTip="Move the focus to the previous window", triggered=self.mdiArea.activatePreviousSubWindow)

        self.actSeparator = QAction(self)
        self.actSeparator.setSeparator(True)

        self.actAbout = QAction(
            "&About", self, statusTip="Show the application's About box", triggered=self.about)

        self.createGraphActions()

    def createGraphActions(self):
        self.actTopologicalOrder = QAction(
            "&Topological Order", self,
            statusTip="List every node so it comes after the nodes feeding it",
            triggered=self.showTopologicalOrder)
        self.actTopologicalOrder.setShortcut(QKeySequence("Ctrl+Shift+T"))

        self.actComponents = QAction(
            "&Flocks (disconnected subgraphs)", self,
            statusTip="Split the graph into its disconnected subgraphs",
            triggered=self.showComponents)

        self.actCycles = QAction(
            "&Cycles", self,
            statusTip="Find the loops in the graph",
            triggered=self.showCycles)

        self.actShortestPath = QAction(
            "&Shortest Path Between Two Selected Nodes", self,
            statusTip="Find the shortest chain between the two selected nodes",
            triggered=self.showSelectedPath)
        self.actShortestPath.setShortcut(QKeySequence("Ctrl+Shift+P"))

    def getCurrentScene(self):
        """Shortcut for the `Scene` of the active tab, or ``None``."""
        active = self.getCurrentNodeEditorWidget()
        return active.scene if active is not None else None

    def onActiveSceneChanged(self, *args):
        """Show the last algorithm again when another graph becomes active."""
        if self.mdiArea.activeSubWindow() is None and self.mdiArea.subWindowList():
            # focus moved to a dock, the graph is still open
            return
        self.graphInspector.refresh()

    def showTopologicalOrder(self):
        self.showGraphInspector()
        self.graphInspector.showTopologicalOrder()

    def showComponents(self):
        self.showGraphInspector()
        self.graphInspector.showComponents()

    def showCycles(self):
        self.showGraphInspector()
        self.graphInspector.showCycles()

    def showSelectedPath(self):
        self.showGraphInspector()
        self.graphInspector.showSelectedPath()

    def showGraphInspector(self):
        self.graphDock.show()
        self.graphDock.raise_()

    def getCurrentNodeEditorWidget(self):
        """ we're returning NodeEditorWidget here... """
        activeSubWindow = self.mdiArea.activeSubWindow()
        if activeSubWindow:
            return activeSubWindow.widget()
        return None

    def onFileNew(self):
        try:
            subwnd = self.createMdiChild()
            subwnd.widget().fileNew()
            subwnd.show()
        except Exception as e:
            dumpException(e)

    def onFileOpen(self):
        fnames, filter = QFileDialog.getOpenFileNames(
            self, 'Open graph from file', self.getFileDialogDirectory(), self.getFileDialogFilter())

        try:
            for fname in fnames:
                if fname:
                    existing = self.findMdiChild(fname)
                    if existing:
                        self.mdiArea.setActiveSubWindow(existing)
                    else:
                        # we need to create new subWindow and open the file
                        nodeeditor = CalculatorSubWindow()
                        if nodeeditor.fileLoad(fname):
                            self.statusBar().showMessage("File %s loaded" % fname, 5000)
                            nodeeditor.setTitle()
                            subwnd = self.createMdiChild(nodeeditor)
                            subwnd.show()
                        else:
                            nodeeditor.close()
        except Exception as e:
            dumpException(e)

    def about(self):
        QMessageBox.about(self, "About Calculator NodeEditor Example",
                          "The <b>Calculator NodeEditor</b> example demonstrates how to write multiple "
                          "document interface applications using PyQt5 and NodeEditor. For more information visit: "
                          "<a href='https://www.blenderfreak.com/'>www.BlenderFreak.com</a>")

    def createMenus(self):
        super().createMenus()

        self.graphMenu = self.menuBar().addMenu("&Graph")
        self.graphMenu.addAction(self.actTopologicalOrder)
        self.graphMenu.addAction(self.actComponents)
        self.graphMenu.addAction(self.actCycles)
        self.graphMenu.addAction(self.actShortestPath)

        self.viewMenu = self.menuBar().addMenu("&View")
        self.updateViewMenu()
        self.viewMenu.aboutToShow.connect(self.updateViewMenu)

        self.menuBar().addSeparator()

        self.windowMenu = self.menuBar().addMenu("&Window")
        self.updateWindowMenu()
        self.windowMenu.aboutToShow.connect(self.updateWindowMenu)

        self.menuBar().addSeparator()

        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.actAbout)

        self.editMenu.aboutToShow.connect(self.updateEditMenu)

    def updateMenus(self):
        # print("update Menus")
        active = self.getCurrentNodeEditorWidget()
        hasMdiChild = (active is not None)

        self.actSave.setEnabled(hasMdiChild)
        self.actSaveAs.setEnabled(hasMdiChild)
        self.actClose.setEnabled(hasMdiChild)
        self.actCloseAll.setEnabled(hasMdiChild)
        self.actTile.setEnabled(hasMdiChild)
        self.actCascade.setEnabled(hasMdiChild)
        self.actNext.setEnabled(hasMdiChild)
        self.actPrevious.setEnabled(hasMdiChild)
        self.actSeparator.setVisible(hasMdiChild)
        self.actTopologicalOrder.setEnabled(hasMdiChild)
        self.actComponents.setEnabled(hasMdiChild)
        self.actCycles.setEnabled(hasMdiChild)
        self.actShortestPath.setEnabled(hasMdiChild)

        self.updateEditMenu()

    def updateEditMenu(self):
        try:
            # print("update Edit Menu")
            active = self.getCurrentNodeEditorWidget()
            hasMdiChild = (active is not None)

            self.actPaste.setEnabled(hasMdiChild)

            self.actCut.setEnabled(hasMdiChild and active.hasSelectedItems())
            self.actCopy.setEnabled(hasMdiChild and active.hasSelectedItems())
            self.actDelete.setEnabled(
                hasMdiChild and active.hasSelectedItems())

            self.actUndo.setEnabled(hasMdiChild and active.canUndo())
            self.actRedo.setEnabled(hasMdiChild and active.canRedo())
        except Exception as e:
            dumpException(e)

    def updateViewMenu(self) -> None:
        self.viewMenu.clear()

        # option to show grids.
        gridAct = self.viewMenu.addAction("Show &Grid")
        gridAct.setCheckable(True)

        active: 'NodeEditorWidget' = self.getCurrentNodeEditorWidget()
        if active:
            gridAct.setChecked(active.scene.grScene.showGrid)
            gridAct.triggered.connect(self.onShowGrid)
        # gridAct.setChecked(self.scene.grScene.showGrid)
        # gridAct.triggered.connect(self.onShowGrid)

    def onShowGrid(self, checked: bool) -> None:
        """
        Toggle the grid visibility for all subwindows

        Args:
            checked: True to show grid, False to hide
        """
        # Apply to all subwindows
        for window in self.mdiArea.subWindowList():
            if window and window.widget():
                window.widget().scene.grScene.showGrid = checked

    def updateWindowMenu(self):
        self.windowMenu.clear()

        toolbar_nodes = self.windowMenu.addAction("Nodes Toolbar")
        toolbar_nodes.setCheckable(True)
        toolbar_nodes.triggered.connect(self.onWindowNodesToolbar)
        toolbar_nodes.setChecked(self.nodesDock.isVisible())

        graph_inspector = self.windowMenu.addAction("Graph Inspector")
        graph_inspector.setCheckable(True)
        graph_inspector.triggered.connect(self.onWindowGraphInspector)
        graph_inspector.setChecked(self.graphDock.isVisible())

        self.windowMenu.addSeparator()

        self.windowMenu.addAction(self.actClose)
        self.windowMenu.addAction(self.actCloseAll)
        self.windowMenu.addSeparator()
        self.windowMenu.addAction(self.actTile)
        self.windowMenu.addAction(self.actCascade)
        self.windowMenu.addSeparator()
        self.windowMenu.addAction(self.actNext)
        self.windowMenu.addAction(self.actPrevious)
        self.windowMenu.addAction(self.actSeparator)

        windows = self.mdiArea.subWindowList()
        self.actSeparator.setVisible(len(windows) != 0)

        for i, window in enumerate(windows):
            child = window.widget()

            text = "%d %s" % (i + 1, child.getUserFriendlyFilename())
            if i < 9:
                text = '&' + text

            action = self.windowMenu.addAction(text)
            action.setCheckable(True)
            action.setChecked(child is self.getCurrentNodeEditorWidget())
            action.triggered.connect(self.windowMapper.map)
            self.windowMapper.setMapping(action, window)

    def onWindowNodesToolbar(self):
        if self.nodesDock.isVisible():
            self.nodesDock.hide()
        else:
            self.nodesDock.show()

    def onWindowGraphInspector(self):
        if self.graphDock.isVisible():
            self.graphDock.hide()
        else:
            self.graphDock.show()

    def createToolBars(self):
        pass

    def createNodesDock(self):
        self.nodesListWidget = QDMDragListbox()

        self.nodesDock = QDockWidget("Nodes")
        self.nodesDock.setWidget(self.nodesListWidget)
        self.nodesDock.setFloating(False)

        self.addDockWidget(Qt.RightDockWidgetArea, self.nodesDock)

    def createGraphInspectorDock(self):
        self.graphInspector = GraphInspectorPanel(self.getCurrentScene)

        self.graphDock = QDockWidget("Graph Inspector")
        self.graphDock.setWidget(self.graphInspector)
        self.graphDock.setFloating(False)

        self.addDockWidget(Qt.BottomDockWidgetArea, self.graphDock)

        self.mdiArea.subWindowActivated.connect(self.onActiveSceneChanged)

    def createStatusBar(self):
        self.statusBar().showMessage("Ready")

    def createMdiChild(self, child_widget=None):
        nodeeditor = child_widget if child_widget is not None else CalculatorSubWindow()
        subwnd = self.mdiArea.addSubWindow(nodeeditor)
        subwnd.setWindowIcon(self.empty_icon)
        # nodeeditor.scene.addItemSelectedListener(self.updateEditMenu)
        # nodeeditor.scene.addItemsDeselectedListener(self.updateEditMenu)
        nodeeditor.scene.history.addHistoryModifiedListener(
            self.updateEditMenu)
        nodeeditor.addCloseEventListener(self.onSubWndClose)
        return subwnd

    def onSubWndClose(self, widget, event):
        existing = self.findMdiChild(widget.filename)
        self.mdiArea.setActiveSubWindow(existing)

        if self.maybeSave():
            event.accept()
        else:
            event.ignore()

    def findMdiChild(self, filename):
        for window in self.mdiArea.subWindowList():
            if window.widget().filename == filename:
                return window
        return None
