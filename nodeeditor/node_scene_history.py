# -*- coding: utf-8 -*-
"""
A module containing all code for working with History (Undo/Redo)
"""
from nodeeditor.utils import dumpException

from contextlib import contextmanager
from typing import (
    TYPE_CHECKING,
    List,
    Optional,
    Tuple,
    Any,
    Callable,
    Iterator,
    TypedDict,
    Union,
)

if TYPE_CHECKING:
    from nodeeditor.node_graphics_view import QDMGraphicsView
    from nodeeditor.node_socket import Socket
    from nodeeditor.node_scene import Scene

DEBUG = False
DEBUG_SELECTION = False


class SelectionDict(TypedDict, total=False):
    """Define the TypedDict for selection objects"""
    nodes: List[str]  # list of node IDs
    edges: List[str]  # list of edge IDs
    groups: List[str]  # list of group IDs


class SceneHistory():
    """Class contains all the code for undo/redo operations

    Two guards control re-entrancy:

    - **restore depth** - incremented by :meth:`restoring`. Any history store
      attempted while the depth is non-zero is ignored, so restoring a stamp
      can never push a new entry onto the stack.
    - **merge key** - an optional grouping token supplied to
      :meth:`storeHistory`. Consecutive stores sharing a key are coalesced
      into a single entry, which is how bursts of keystrokes collapse into
      one undo step.
    """

    def __init__(
        self,
        scene: 'Scene',
        history_limit: Optional[int] = None,
    ) -> None:
        """
        :param scene: Reference to the :class:`~nodeeditor.node_scene.Scene`
        :type scene: :class:`~nodeeditor.node_scene.Scene`
        :param history_limit: Maximum number of stamps to keep. ``None``
            (the default) means unlimited.
        :type history_limit: ``int`` or ``None``

        :Instance Attributes:

        - **scene** - reference to the :class:`~nodeeditor.node_scene.Scene`
        - **history_limit** - number of history steps that can be stored
        """
        self.scene = scene

        self.clear()
        self.history_limit = history_limit

        self.undo_selection_has_changed = False
        self.if_undo = False
        self._restore_depth = 0

        # listeners
        self._history_modified_listeners: List[Callable[[], None]] = []
        self._history_stored_listeners: List[Callable[[], None]] = []
        self._history_restored_listeners: List[Callable[[], None]] = []

    def clear(self) -> None:
        """Reset the history stack"""
        self.history_stack = []
        self.history_current_step = -1

    def storeInitialHistoryStamp(self) -> None:
        """Helper function usually used when new or open file requested"""
        self.storeHistory("Initial History Stamp")

    # ------------------------------------------------------------------
    # Re-entrancy guard
    # ------------------------------------------------------------------

    @property
    def is_restoring_history(self) -> bool:
        """``True`` while a history stamp is being restored.

        Retained as a property for backward compatibility: legacy callers
        assign to it directly instead of using :meth:`restoring`.
        """
        return self._restore_depth > 0

    @is_restoring_history.setter
    def is_restoring_history(self, value: bool) -> None:
        if value:
            self._restore_depth = max(self._restore_depth, 1)
        else:
            self._restore_depth = 0

    @property
    def is_restoring(self) -> bool:
        """Alias of :attr:`is_restoring_history` for new call sites."""
        return self._restore_depth > 0

    @contextmanager
    def restoring(self, is_undo: bool = False) -> Iterator['SceneHistory']:
        """Context manager guarding a history restore.

        Nestable: the depth counter only reaches zero when the outermost
        block exits, so an inner callback cannot re-enable history storage
        for the remainder of an outer restore.

        :param is_undo: ``True`` when the restore is an undo, which is the
            flag legacy ``history_stamp_callback`` implementations read to
            decide which side of a diff to apply.
        """
        self._restore_depth += 1
        previous_if_undo = self.if_undo
        self.if_undo = is_undo
        try:
            yield self
        finally:
            self.if_undo = previous_if_undo
            self._restore_depth = max(0, self._restore_depth - 1)

    # ------------------------------------------------------------------
    # Listeners
    # ------------------------------------------------------------------

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

    def removeHistoryModifiedListener(self, callback: Callable[[], None]) -> None:
        """
        Remove registered callback for `HistoryModified` event

        :param callback: callback function
        """
        if callback in self._history_modified_listeners:
            self._history_modified_listeners.remove(callback)

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

    # ------------------------------------------------------------------
    # Stack state
    # ------------------------------------------------------------------

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

    def currentText(self) -> str:
        """Description of the stamp the next undo would revert."""
        if not self.canUndo():
            return ""
        return self.history_stack[self.history_current_step].get('desc', '')

    def nextText(self) -> str:
        """Description of the stamp the next redo would reapply."""
        if not self.canRedo():
            return ""
        return self.history_stack[self.history_current_step + 1].get('desc', '')

    def undo(self) -> None:
        """Undo operation (restore previous snapshot)."""
        if DEBUG:
            print("UNDO")

        if self.canUndo():
            self.history_current_step -= 1
            with self.restoring(is_undo=True):
                self.restoreHistory()
            self.scene.has_been_modified = True

    def redo(self) -> None:
        """Redo operation"""
        if DEBUG:
            print("REDO")
        if self.canRedo():
            self.history_current_step += 1
            with self.restoring(is_undo=False):
                self.restoreHistory()
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

        history_stamp = self.history_stack[self.history_current_step]
        self.restoreHistoryStamp(history_stamp)
        self._dispatch_stamp_data(history_stamp)

        for callback in self._history_modified_listeners:
            callback()
        for callback in self._history_restored_listeners:
            callback()

    def _dispatch_stamp_data(self, history_stamp: dict) -> None:
        """Hand the stamp's side-channel payload back to its content widget.

        The owning content is resolved defensively: a stamp may carry a
        payload for a node that has since been deleted, or for a content
        class that never implemented ``history_stamp_callback``. Neither is
        an error, and neither may abort the restore.
        """
        data = history_stamp.get('data', None)
        if not data:
            return

        node = data.get('node') if isinstance(data, dict) else None
        content = getattr(node, 'content', None)
        callback = getattr(content, 'history_stamp_callback', None)
        if not callable(callback):
            if DEBUG:
                print("No history_stamp_callback for stamp:", history_stamp.get('desc'))
            return

        try:
            callback(data, self.if_undo)
        except Exception as e:
            dumpException(e)

    def storeHistory(
        self,
        desc: str,
        setModified: bool = False,
        data: dict = None,
        callback: 'function' = None,
        merge_key: Optional[str] = None,
        merge: Optional[Callable[[Optional[dict], Optional[dict]], Optional[dict]]] = None,
    ) -> bool:
        """
        Store History Stamp into History Stack

        :param desc: Description of current History Stamp
        :type desc: ``str``
        :param setModified: if ``True`` marks :class:`~nodeeditor.node_scene.Scene` with `has_been_modified`
        :type setModified: ``bool``
        :param data: Additional data to store with History Stamp
        :type data: ``dict``
        :param callback: Callback function to call after storing the History Stamp
        :type callback: ``function``
        :param merge_key: Grouping token. When it matches the key of the
            current top-of-stack stamp, that stamp is updated in place
            instead of a new one being appended, so a burst of related
            changes collapses into a single undo step.
        :type merge_key: ``str`` or ``None``
        :param merge: Combines the existing payload with the incoming one
            when a merge happens. Receives ``(existing_data, new_data)`` and
            returns the payload to store. Defaults to replacing the payload
            outright, which is correct when the payload is a self-contained
            snapshot of the post-change state. Use it to preserve the
            *original* side of a diff so undo still returns to where the
            burst began.
        :type merge: ``callable`` or ``None``
        :return: ``True`` if a new stamp was pushed, ``False`` if the store
            was skipped (restore in progress) or coalesced into the top stamp.
        :rtype: ``bool``

        Triggers:

        - `HistoryModified`
        - `History Stored`
        """

        if self.is_restoring_history:
            return False

        if setModified:
            self.scene.has_been_modified = True

        if DEBUG:
            print("Storing history", '"%s"' % desc,
                  ".... current_step: @%d" % self.history_current_step,
                  "(%d)" % len(self.history_stack))

        if self._coalesce(desc, data, merge_key, merge):
            return False

        # if the pointer (history_current_step) is not at the end of history_stack
        if self.history_current_step+1 < len(self.history_stack):
            self.history_stack = self.history_stack[0:self.history_current_step+1]

        # history is outside of the limits
        if (
            self.history_limit is not None
            and self.history_current_step+1 >= self.history_limit
        ):
            self.history_stack = self.history_stack[1:]
            self.history_current_step -= 1

        hs = self.createHistoryStamp(desc, data=data, merge_key=merge_key)

        self.history_stack.append(hs)
        self.history_current_step += 1
        if DEBUG:
            print("  -- setting step to:", self.history_current_step)

        # always trigger history modified (for i.e. updateEditMenu)
        for callback in self._history_modified_listeners:
            callback()
        for callback in self._history_stored_listeners:
            callback()

        return True

    def _coalesce(
        self,
        desc: str,
        data: Optional[dict],
        merge_key: Optional[str],
        merge: Optional[Callable[[Optional[dict], Optional[dict]], Optional[dict]]],
    ) -> bool:
        """Fold this store into the current top stamp when keys match.

        Only merges when the stack is already at its tip - after an undo
        there is a redo tail, and folding into a stamp the user has stepped
        back from would rewrite history they are about to redo.
        """
        if merge_key is None or not self.history_stack:
            return False
        if self.history_current_step != len(self.history_stack) - 1:
            return False

        top = self.history_stack[-1]
        if top.get('merge_key') != merge_key:
            return False

        existing_data = top.get('data', None)
        if merge is not None:
            try:
                data = merge(existing_data, data)
            except Exception as e:
                dumpException(e)
                return False

        hs = self.createHistoryStamp(desc, data=data, merge_key=merge_key)
        self.history_stack[-1] = hs
        # current step is unchanged: the entry was folded, not added

        for callback in self._history_modified_listeners:
            callback()
        for callback in self._history_stored_listeners:
            callback()
        return True

    def captureCurrentSelection(self) -> SelectionDict:
        """
        Create dictionary with a list of selected nodes and a list of selected edges
        :return: ``dict`` 'nodes' - list of selected nodes, 'edges' - list of selected edges
        :rtype: ``dict``
        """
        sel_obj: SelectionDict = {
            'nodes': [],
            'edges': [],
            'groups': [],
        }
        for item in self.scene.grScene.selectedItems():
            try:
                # Groups are QGraphicsRectItem without .node/.edge; check first
                groups = getattr(self.scene, 'groups', [])
                if groups and item in groups:
                    sel_obj['groups'].append(item.id)
                    continue
            except Exception:
                pass
            if hasattr(item, 'node'):
                sel_obj['nodes'].append(item.node.id)
            elif hasattr(item, 'edge'):
                sel_obj['edges'].append(item.edge.id)
        return sel_obj

    def createHistoryStamp(
        self,
        desc: str,
        data: Optional[dict] = None,
        merge_key: Optional[str] = None,
    ) -> dict:
        """
        Create History Stamp. Internally serialize whole scene and the current selection

        :param desc: Descriptive label for the History Stamp
        :param data: Optional side-channel payload replayed to the owning content
        :param merge_key: Optional grouping token recorded alongside the stamp
        :return: History stamp serializing state of `Scene` and current selection
        :rtype: ``dict``
        """
        history_stamp = {
            'desc': desc,
            'snapshot': self.scene.serialize(),
            'selection': self.captureCurrentSelection(),
            'merge_key': merge_key,
        }

        if data is not None:
            history_stamp['data'] = data

        return history_stamp

    def restoreHistoryStamp(self, history_stamp: dict) -> None:
        """
        Restore History Stamp to current `Scene` with selection of items included

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

            self.scene.deserialize(history_stamp['snapshot'])

            # restore selection

            # first clear all selection on edges
            for edge in self.scene.edges:
                try:
                    if getattr(edge, 'grEdge', None) is not None:
                        edge.grEdge.setSelected(False)
                except Exception:
                    pass
            # now restore selected edges from history_stamp
            for edge_id in history_stamp['selection'].get('edges', []):
                for edge in self.scene.edges:
                    if edge.id == edge_id:
                        try:
                            edge.grEdge.setSelected(True)
                        except Exception:
                            pass
                        break

            # first clear all selection on nodes
            for node in self.scene.nodes:
                try:
                    if getattr(node, 'grNode', None) is not None:
                        node.grNode.setSelected(False)
                except Exception:
                    pass
            # now restore selected nodes from history_stamp
            for node_id in history_stamp['selection'].get('nodes', []):
                for node in self.scene.nodes:
                    if node.id == node_id:
                        try:
                            node.grNode.setSelected(True)
                        except Exception:
                            pass
                        break

            # groups (new; old stamps may lack the key)
            try:
                for grp in list(getattr(self.scene, 'groups', [])):
                    try:
                        grp.setSelected(False)
                    except Exception:
                        pass
                for gid in history_stamp['selection'].get('groups', []):
                    for grp in list(getattr(self.scene, 'groups', [])):
                        if getattr(grp, 'id', None) == gid:
                            try:
                                grp.setSelected(True)
                            except Exception:
                                pass
                            break
            except Exception:
                pass

            current_selection = self.captureCurrentSelection()
            if DEBUG_SELECTION:
                print("selected nodes after restore:",
                      current_selection['nodes'])

            # reset the last_selected_items - since we're comparing change to the last_selected state
            self.scene._last_selected_items = self.scene.getSelectedItems()

            # if the selection of nodes differ before and after restoration, set flag
            if current_selection.get('nodes') != previous_selection.get('nodes') or current_selection.get('edges') != previous_selection.get('edges') or current_selection.get('groups') != previous_selection.get('groups'):
                if DEBUG_SELECTION:
                    print("\nSCENE: Selection has changed")
                self.undo_selection_has_changed = True

        except Exception as e:
            dumpException(e)
