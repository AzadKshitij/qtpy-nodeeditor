# -*- coding: utf-8 -*-
"""
SceneHistory - MVC Refactored
A module containing all code for working with History (Undo/Redo)

Refactored for MVC architecture - uses model signals and controller methods.
"""
from nodeeditor.utils.utils import dumpException

from typing import TYPE_CHECKING, List, Optional, Tuple, Any, Callable, TypedDict


if TYPE_CHECKING:
    from nodeeditor.views.graphics.node_graphics_view import QDMGraphicsView
    from nodeeditor.node_socket import Socket
    from nodeeditor.node_scene import Scene

DEBUG = False
DEBUG_SELECTION = False


class SelectionDict(TypedDict):
    """Define the TypedDict for selection objects"""
    nodes: List[str]  # list of node IDs
    edges: List[str]  # list of edge IDs


class SceneHistory:
    """
    Class contains all the code for undo/redo operations.
    
    Refactored for MVC: Uses model state instead of graphics state,
    connects to model signals for automatic history tracking.
    """

    def __init__(self, scene: 'Scene') -> None:
        """
        :param scene: Reference to the :class:`~nodeeditor.node_scene.Scene`
        :type scene: :class:`~nodeeditor.node_scene.Scene`

        :Instance Attributes:

        - **scene** - reference to the :class:`~nodeeditor.node_scene.Scene`
        - **history_limit** - number of history steps that can be stored
        """
        self.scene = scene

        self.clear()
        self.history_limit = 32

        self.undo_selection_has_changed = False
        self.is_restoring_history = False
        self.if_undo = False

        # listeners
        self._history_modified_listeners: List[Callable[[], None]] = []
        self._history_stored_listeners: List[Callable[[], None]] = []
        self._history_restored_listeners: List[Callable[[], None]] = []

        # Connect to model signals for automatic history tracking
        self._connect_model_signals()

    def _connect_model_signals(self) -> None:
        """Connect to scene model signals for automatic history tracking."""
        if hasattr(self.scene, 'model'):
            # Track when nodes/edges are modifiedc
            nodes_changed_signal = getattr(self.scene.model, "nodesChanged", None)
            if nodes_changed_signal is not None:
                try:
                    nodes_changed_signal.connect(self._on_scene_changed)
                except (AttributeError, TypeError):
                    pass

            edges_changed_signal = getattr(self.scene.model, "edgesChanged", None)
            if edges_changed_signal is not None:
                try:
                    edges_changed_signal.connect(self._on_scene_changed)
                except (AttributeError, TypeError):
                    pass

    def _on_scene_changed(self, *args) -> None:
        """Handle scene changes - store history if enabled."""
        # This is called automatically when model signals are emitted
        # Actual history storage happens through storeHistory() calls
        pass

    def clear(self) -> None:
        """Reset the history stack"""
        self.history_stack = []
        self.history_current_step = -1

    def storeInitialHistoryStamp(self) -> None:
        """Helper function usually used when new or open file requested"""
        self.storeHistory("Initial History Stamp")

    def addHistoryModifiedListener(self, callback: Callable[[], None]) -> None:
        """
        Register callback for `HistoryModified` event

        :param callback: callback function
        """
        self._history_modified_listeners.append(callback)

    def addHistoryStoredListener(self, callback: Callable[[], None]) -> None:
        """
        Register callback for `HistoryStored` event

        :param callback: callback function
        """
        self._history_stored_listeners.append(callback)

    def addHistoryRestoredListener(self, callback: Callable[[], None]) -> None:
        """
        Register callback for `HistoryRestored` event

        :param callback: callback function
        """
        self._history_restored_listeners.append(callback)

    def removeHistoryStoredListener(self, callback: Callable[[], None]) -> None:
        """
        Remove registered callback for `HistoryStored` event

        :param callback: callback function
        """
        if callback in self._history_stored_listeners:
            self._history_stored_listeners.remove(callback)

    def removeHistoryRestoredListener(self, callback: Callable[[], None]) -> None:
        """
        Remove registered callback for `HistoryRestored` event

        :param callback: callback function
        """
        if callback in self._history_restored_listeners:
            self._history_restored_listeners.remove(callback)

    def canUndo(self) -> bool:
        """Return ``True`` if Undo is available for current `History Stack`

        :rtype: ``bool``
        """
        return self.history_current_step > 0

    def canRedo(self) -> bool:
        """
        Return ``True`` if Redo is available for current `History Stack`

        :rtype: ``bool``
        """
        return self.history_current_step + 1 < len(self.history_stack)

    def undo(self) -> None:
        """Undo operation"""
        if DEBUG:
            print("UNDO")

        if self.canUndo():
            self.if_undo = True
            self.restoreHistory()
            self.history_current_step -= 1
            # Use model property instead of graphics attribute
            if hasattr(self.scene, 'model'):
                self.scene.model.is_modified = True
            elif hasattr(self.scene, 'has_been_modified'):
                self.scene.has_been_modified = True

    def redo(self) -> None:
        """Redo operation"""
        if DEBUG:
            print("REDO")
        if self.canRedo():
            self.if_undo = False
            self.history_current_step += 1
            self.restoreHistory()
            # Use model property instead of graphics attribute
            if hasattr(self.scene, 'model'):
                self.scene.model.is_modified = True
            elif hasattr(self.scene, 'has_been_modified'):
                self.scene.has_been_modified = True

    def restoreHistory(self) -> None:
        """
        Restore `History Stamp` from `History stack`.

        Triggers:

        - `History Modified` event
        - `History Restored` event
        """
        if DEBUG:
            print("Restoring history",
                  ".... current_step: @%d" % self.history_current_step,
                  "(%d)" % len(self.history_stack))

        # Prevent storing history during restoration
        self.is_restoring_history = True
        history_stamp = self.history_stack[self.history_current_step]
        self.restoreHistoryStamp(history_stamp)

        if history_stamp.get('data', None):
            history_stamp['data']['node'].content.history_stamp_callback(
                history_stamp['data'], self.if_undo)

        self.is_restoring_history = False  # Re-enable history storage

        for callback in self._history_modified_listeners:
            callback()
        for callback in self._history_restored_listeners:
            callback()

    def storeHistory(
        self,
        desc: str,
        setModified: bool = False,
        data: Optional[dict] = None,
        callback: Optional[Callable] = None,
    ) -> None:
        """
        Store History Stamp into History Stack

        :param desc: Description of current History Stamp
        :type desc: ``str``
        :param setModified: if ``True`` marks Scene with `is_modified`
        :type setModified: ``bool``
        :param data: Additional data to store with History Stamp
        :type data: ``dict``
        :param callback: Callback function to call after storing the History Stamp
        :type callback: ``function``

        Triggers:

        - `History Modified`
        - `History Stored`
        """

        if self.is_restoring_history:
            return

        if setModified:
            # Use model property instead of graphics attribute
            if hasattr(self.scene, 'model'):
                self.scene.model.is_modified = True
            elif hasattr(self.scene, 'has_been_modified'):
                self.scene.has_been_modified = True

        if DEBUG:
            print("Storing history", '"%s"' % desc,
                  ".... current_step: @%d" % self.history_current_step,
                  "(%d)" % len(self.history_stack))

        # if the pointer (history_current_step) is not at the end of history_stack
        if self.history_current_step+1 < len(self.history_stack):
            self.history_stack = self.history_stack[0:self.history_current_step+1]

        # history is outside of the limits
        if self.history_current_step+1 >= self.history_limit:
            self.history_stack = self.history_stack[1:]
            self.history_current_step -= 1

        hs = self.createHistoryStamp(desc)

        self.history_stack.append(hs)
        self.history_current_step += 1
        if DEBUG:
            print("  -- setting step to:", self.history_current_step)

        # always trigger history modified (for i.e. updateEditMenu)
        for callback in self._history_modified_listeners:
            callback()
        for callback in self._history_stored_listeners:
            callback()

    def captureCurrentSelection(self) -> SelectionDict:
        """
        Create dictionary with a list of selected nodes and a list of selected edges
        MVC: Use model selection instead of graphics selection
        
        :return: ``dict`` 'nodes' - list of selected nodes, 'edges' - list of selected edges
        :rtype: ``dict``
        """
        sel_obj: SelectionDict = {
            'nodes': [],
            'edges': [],
        }

        # Try model-based selection first (MVC)
        if hasattr(self.scene, 'model'):
            for node in getattr(self.scene.model, 'nodes', []):
                if getattr(node, 'selected', False):
                    sel_obj['nodes'].append(node.id)
            for edge in getattr(self.scene.model, 'edges', []):
                if getattr(edge, 'selected', False):
                    sel_obj['edges'].append(edge.id)

        # Fallback to graphics-based selection (backward compatibility)
        if not sel_obj['nodes'] and not sel_obj['edges'] and hasattr(self.scene, 'grScene'):
            # Import graphics classes locally to avoid circular imports
            from nodeeditor.views.graphics.node_graphics_node import QDMGraphicsNode
            from nodeeditor.views.graphics.node_graphics_edge import QDMGraphicsEdge

            for item in self.scene.grScene.selectedItems():
                if (
                    isinstance(item, QDMGraphicsNode)
                    and hasattr(item, "node")
                    and item.node is not None
                ):
                    sel_obj['nodes'].append(item.node.id)
                elif (
                    isinstance(item, QDMGraphicsEdge)
                    and hasattr(item, "edge")
                    and item.edge is not None
                ):
                    sel_obj['edges'].append(item.edge.id)

        return sel_obj

    def createHistoryStamp(self, desc: str) -> dict:
        """
        Create History Stamp. Internally serialize whole scene and the current selection
        MVC: Store model state, not graphics state

        :param desc: Descriptive label for the History Stamp
        :return: History stamp serializing state of `Scene` and current selection
        :rtype: ``dict``
        """
        history_stamp = {
            'desc': desc,
            'snapshot': self.scene.serialize(),
            'selection': self.captureCurrentSelection(),
        }

        return history_stamp

    def restoreHistoryStamp(self, history_stamp: dict) -> None:
        """
        Restore History Stamp to current `Scene` with selection of items included
        MVC: Restores model state first, graphics follow via signals

        :param history_stamp: History Stamp to restore
        :type history_stamp: ``dict``
        """
        if DEBUG:
            print("RHS: ", history_stamp['desc'])

        try:
            self.undo_selection_has_changed = False
            previous_selection = self.captureCurrentSelection()
            if DEBUG_SELECTION:
                print("selected nodes before restore:",
                      previous_selection['nodes'])

            # Deserialize restores model state, graphics follow via signals
            self.scene.deserialize(history_stamp['snapshot'])

            # restore selection

            # first clear all selection on edges
            for edge in self.scene.edges:
                if hasattr(edge, "grEdge") and edge.grEdge is not None:
                    edge.grEdge.setSelected(False)
            # now restore selected edges from history_stamp
            for edge_id in history_stamp['selection']['edges']:
                for edge in self.scene.edges:
                    if (
                        edge.id == edge_id
                        and hasattr(edge, "grEdge")
                        and edge.grEdge is not None
                    ):
                        edge.grEdge.setSelected(True)
                        break

            # first clear all selection on nodes
            for node in self.scene.nodes:
                node.grNode.setSelected(False)
            # now restore selected nodes from history_stamp
            for node_id in history_stamp['selection']['nodes']:
                for node in self.scene.nodes:
                    if node.id == node_id:
                        node.grNode.setSelected(True)
                        break

            current_selection = self.captureCurrentSelection()
            if DEBUG_SELECTION:
                print("selected nodes after restore:",
                      current_selection['nodes'])

            # reset the last_selected_items - since we're comparing change to the last_selected state
            self.scene._last_selected_items = self.scene.getSelectedItems()

            # if the selection of nodes differ before and after restoration, set flag
            if current_selection['nodes'] != previous_selection['nodes'] or current_selection['edges'] != previous_selection['edges']:
                if DEBUG_SELECTION:
                    print("\nSCENE: Selection has changed")
                self.undo_selection_has_changed = True

        except Exception as e:
            dumpException(e)
