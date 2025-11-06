"""
MVC Calculator Main Window

Demonstrates the MVC architecture with a calculator node editor application.
This example shows how to build a proper MVC-based application using the nodeeditor framework.
"""

import os
from qtpy.QtGui import QIcon, QKeySequence
from qtpy.QtWidgets import (
    QMdiArea, QDockWidget, QAction, QMessageBox, QFileDialog, QListWidget, QListWidgetItem
)
from qtpy.QtCore import Qt, QSignalMapper

from nodeeditor.node_editor_window import NodeEditorWindow
from nodeeditor.node_edge import Edge
from nodeeditor.node_edge_validators import (
    edge_validator_debug,
    edge_cannot_connect_two_outputs_or_two_inputs,
    edge_cannot_connect_input_and_output_of_same_node
)
from nodeeditor.utils import loadStylesheets, dumpException, pp

from examples.mvc_calculator.mvc_conf import CALC_NODES
from examples.mvc_calculator.mvc_sub_window import MvcCalculatorSubWindow
from examples.mvc_calculator.mvc_drag_listbox import MvcQDMDragListbox

# Enable edge validators
Edge.registerEdgeValidator(edge_validator_debug)
Edge.registerEdgeValidator(edge_cannot_connect_two_outputs_or_two_inputs)
Edge.registerEdgeValidator(edge_cannot_connect_input_and_output_of_same_node)

DEBUG = False


class MvcCalculatorWindow(NodeEditorWindow):
    """
    Main application window for the MVC Calculator example.

    Demonstrates MVC architecture with:
    - Models: CalcNodeModel classes representing node data
    - Controllers: CalcNodeController managing business logic
    - Views: Graphics nodes and editor widgets for visualization
    """

    def initUI(self):
        """Initialize the user interface."""
        self.name_company = 'NodeEditor Community'
        self.name_product = 'MVC Calculator NodeEditor'
        self.windowMapper = QSignalMapper(self)

        # Load stylesheet
        self.stylesheet_filename = os.path.join(
            os.path.dirname(__file__), "qss/nodeeditor.qss"
        )
        loadStylesheets(self.stylesheet_filename)

        self.empty_icon = QIcon(".")

        if DEBUG:
            print("Registered nodes:")
            pp(CALC_NODES)

        # Create MDI area for multiple documents
        self.mdiArea = QMdiArea()
        self.mdiArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.mdiArea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.mdiArea.setViewMode(QMdiArea.ViewMode.TabbedView)
        self.mdiArea.setDocumentMode(True)
        self.mdiArea.setTabsClosable(True)
        self.mdiArea.setTabsMovable(True)
        self.setCentralWidget(self.mdiArea)

        self.mdiArea.subWindowActivated.connect(self.updateMenus)

        # Create nodes dock
        self.createNodesDock()

        # Create UI elements
        self.createActions()
        self.createMenus()
        self.createStatusBar()
        self.updateMenus()

        self.readSettings()

        self.setWindowTitle("MVC Calculator NodeEditor Example")

    def closeEvent(self, event):
        """Handle window close event."""
        self.mdiArea.closeAllSubWindows()
        if self.mdiArea.currentSubWindow():
            event.ignore()
        else:
            self.writeSettings()
            event.accept()
            import sys
            sys.exit(0)

    def createActions(self):
        """Create application actions."""
        super().createActions()

        self.actClose = QAction(
            "Cl&ose",
            self,
            statusTip="Close the active window",
            triggered=self.mdiArea.closeActiveSubWindow
        )
        self.actCloseAll = QAction(
            "Close &All",
            self,
            statusTip="Close all windows",
            triggered=self.mdiArea.closeAllSubWindows
        )
        self.actTile = QAction(
            "&Tile",
            self,
            statusTip="Tile the windows",
            triggered=self.mdiArea.tileSubWindows
        )
        self.actCascade = QAction(
            "&Cascade",
            self,
            statusTip="Cascade the windows",
            triggered=self.mdiArea.cascadeSubWindows
        )
        self.actNext = QAction(
            "Ne&xt",
            self,
            shortcut=QKeySequence.NextChild,
            statusTip="Move to next window",
            triggered=self.mdiArea.activateNextSubWindow
        )
        self.actPrevious = QAction(
            "Pre&vious",
            self,
            shortcut=QKeySequence.PreviousChild,
            statusTip="Move to previous window",
            triggered=self.mdiArea.activatePreviousSubWindow
        )

        self.actSeparator = QAction(self)
        self.actSeparator.setSeparator(True)

        self.actAbout = QAction(
            "&About",
            self,
            statusTip="About this application",
            triggered=self.about
        )

    def getCurrentNodeEditorWidget(self):
        """Get the currently active node editor widget."""
        activeSubWindow = self.mdiArea.activeSubWindow()
        if activeSubWindow:
            return activeSubWindow.widget()
        return None

    def onFileNew(self):
        """Create a new file."""
        try:
            subwnd = self.createMdiChild()
            subwnd.widget().fileNew()
            subwnd.show()
        except Exception as e:
            dumpException(e)

    def onFileOpen(self):
        """Open an existing file."""
        fnames, filter = QFileDialog.getOpenFileNames(
            self,
            'Open graph from file',
            self.getFileDialogDirectory(),
            self.getFileDialogFilter()
        )

        try:
            for fname in fnames:
                if fname:
                    existing = self.findMdiChild(fname)
                    if existing:
                        self.mdiArea.setActiveSubWindow(existing)
                    else:
                        nodeeditor = MvcCalculatorSubWindow()
                        if nodeeditor.fileLoad(fname):
                            self.statusBar().showMessage(f"File {fname} loaded", 5000)
                            nodeeditor.setTitle()
                            subwnd = self.createMdiChild(nodeeditor)
                            subwnd.show()
                        else:
                            nodeeditor.close()
        except Exception as e:
            dumpException(e)

    def about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About MVC Calculator NodeEditor Example",
            "The <b>MVC Calculator NodeEditor</b> example demonstrates how to build "
            "applications using the Model-View-Controller architecture with the NodeEditor "
            "framework. It includes Input nodes, Output nodes, and Operation nodes "
            "(Add, Subtract, Multiply, Divide)."
        )

    def createMenus(self):
        """Create application menus."""
        super().createMenus()

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
        """Update menu states based on current editor state."""
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

        self.updateEditMenu()

    def updateEditMenu(self):
        """Update edit menu state."""
        try:
            active = self.getCurrentNodeEditorWidget()
            hasMdiChild = (active is not None)

            self.actPaste.setEnabled(hasMdiChild)
            self.actCut.setEnabled(hasMdiChild and active.hasSelectedItems())
            self.actCopy.setEnabled(hasMdiChild and active.hasSelectedItems())
            self.actDelete.setEnabled(hasMdiChild and active.hasSelectedItems())

            self.actUndo.setEnabled(hasMdiChild and active.canUndo())
            self.actRedo.setEnabled(hasMdiChild and active.canRedo())
        except Exception as e:
            dumpException(e)

    def updateViewMenu(self) -> None:
        """Update view menu."""
        self.viewMenu.clear()

        gridAct = self.viewMenu.addAction("Show &Grid")
        gridAct.setCheckable(True)

        active = self.getCurrentNodeEditorWidget()
        if active:
            gridAct.setChecked(active.scene.grScene.showGrid)
            gridAct.triggered.connect(self.onShowGrid)

    def onShowGrid(self, checked: bool) -> None:
        """Toggle grid visibility."""
        for window in self.mdiArea.subWindowList():
            if window and window.widget():
                window.widget().scene.grScene.showGrid = checked

    def updateWindowMenu(self):
        """Update window menu."""
        self.windowMenu.clear()

        toolbar_nodes = self.windowMenu.addAction("Nodes Toolbar")
        toolbar_nodes.setCheckable(True)
        toolbar_nodes.triggered.connect(self.onWindowNodesToolbar)
        toolbar_nodes.setChecked(self.nodesDock.isVisible())

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
        """Toggle nodes toolbar visibility."""
        if self.nodesDock.isVisible():
            self.nodesDock.hide()
        else:
            self.nodesDock.show()

    def createNodesDock(self):
        """Create the nodes dock with available node types."""
        self.nodesListWidget = MvcQDMDragListbox()
        self.nodesListWidget.setObjectName("nodesListWidget")

        self.nodesDock = QDockWidget("Nodes")
        self.nodesDock.setWidget(self.nodesListWidget)
        self.nodesDock.setFloating(False)

        self.addDockWidget(Qt.RightDockWidgetArea, self.nodesDock)

    def createStatusBar(self):
        """Create the status bar."""
        self.statusBar().showMessage("Ready")

    def createMdiChild(self, child_widget=None):
        """Create a new MDI child window."""
        nodeeditor = child_widget if child_widget is not None else MvcCalculatorSubWindow()
        subwnd = self.mdiArea.addSubWindow(nodeeditor)
        subwnd.setWindowIcon(self.empty_icon)
        nodeeditor.scene.history.addHistoryModifiedListener(self.updateEditMenu)
        nodeeditor.addCloseEventListener(self.onSubWndClose)
        return subwnd

    def onSubWndClose(self, widget, event):
        """Handle sub-window close event."""
        existing = self.findMdiChild(widget.filename)
        self.mdiArea.setActiveSubWindow(existing)

        if self.maybeSave():
            event.accept()
        else:
            event.ignore()

    def findMdiChild(self, filename):
        """Find an MDI child by filename."""
        for window in self.mdiArea.subWindowList():
            if window.widget().filename == filename:
                return window
        return None
