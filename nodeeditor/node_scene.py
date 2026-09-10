# -*- coding: utf-8 -*-
"""
A module containing the representation of the NodeEditor's Scene
"""
import os
import sys
import orjson as json
from orjson import JSONDecodeError, OPT_INDENT_2
from collections import OrderedDict
from qtpy.QtCore import QRectF, Qt, QPoint
from qtpy.QtWidgets import QGraphicsItem
from nodeeditor.utils_no_qt import dumpException, pp
from nodeeditor.node_serializable import Serializable
from nodeeditor.node_graphics_scene import QDMGraphicsScene
from nodeeditor.node_node import Node
from nodeeditor.node_edge import Edge
from nodeeditor.node_scene_history import SceneHistory
from nodeeditor.node_scene_clipboard import SceneClipboard

from typing import TYPE_CHECKING, List, Optional, Tuple, Any, Callable, OrderedDict as OrderedDictType, Type


if TYPE_CHECKING:
    from nodeeditor.node_graphics_view import QDMGraphicsView
    from nodeeditor.node_socket import Socket
    NodeClassType = Callable[[dict], Type['Node']]


DEBUG_REMOVE_WARNINGS = False


class InvalidFile(Exception):
    pass


class Scene(Serializable):
    """Class representing NodeEditor's `Scene`"""
    historyClass = SceneHistory
    clipboardClass = SceneClipboard

    def __init__(self) -> None:
        """
        :Instance Attributes:

            - **nodes** - list of `Nodes` in this `Scene`
            - **edges** - list of `Edges` in this `Scene`
            - **history** - Instance of :class:`~nodeeditor.node_scene_history.SceneHistory`
            - **clipboard** - Instance of :class:`~nodeeditor.node_scene_clipboard.SceneClipboard`
            - **scene_width** - width of this `Scene` in pixels
            - **scene_height** - height of this `Scene` in pixels
        """
        super().__init__()
        self.nodes: List[Node] = []
        self.edges: List[Edge] = []
        self.groups: List = []  # List of GroupNode instances

        # current filename assigned to this scene
        self.filename: Optional[str] = None

        self.scene_width: int = 64000
        self.scene_height: int = 64000

        # custom flag used to suppress triggering onItemSelected which does a bunch of stuff
        self._silent_selection_events: bool = False

        self._has_been_modified: bool = False
        self._last_selected_items: Optional[List[QGraphicsItem]] = None
        self._last_selected_socket: Optional[Socket] = None
        self._last_selected_edges: Optional[List[Edge]] = None

        # initialize all listeners
        self._has_been_modified_listeners: List[Callable[[], None]] = []
        self._item_selected_listeners: List[Callable[[], None]] = []
        self._items_deselected_listeners: List[Callable[[], None]] = []

        # here we can store callback for retrieving the class for Nodes
        self.node_class_selector: Optional['NodeClassType'] = None

        self.initUI()
        self.history = self.historyClass(self)
        self.clipboard = self.clipboardClass(self)

        self.grScene.itemSelected.connect(self.onItemSelected)
        self.grScene.itemsDeselected.connect(self.onItemsDeselected)

    @property
    def has_been_modified(self):
        """
        Has this `Scene` been modified?

        :getter: ``True`` if the `Scene` has been modified
        :setter: set new state. Triggers `Has Been Modified` event
        :type: ``bool``
        """
        return self._has_been_modified

    @has_been_modified.setter
    def has_been_modified(self, value) -> None:
        if not self._has_been_modified and value:
            # set it now, because we will be reading it soon
            self._has_been_modified = value

            # call all registered listeners
            for callback in self._has_been_modified_listeners:
                callback()

        self._has_been_modified = value

    def initUI(self) -> None:
        """Set up Graphics Scene Instance"""
        self.grScene = QDMGraphicsScene(self)
        self.grScene.setGrScene(self.scene_width, self.scene_height)

    def getNodeByID(self, node_id: int):
        """
        Find node in the scene according to provided `node_id`

        :param node_id: ID of the node we are looking for
        :type node_id: ``int``
        :return: Found ``Node`` or ``None``
        """
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def setSilentSelectionEvents(self, value: bool = True) -> None:
        """Calling this can suppress onItemSelected events to be triggered. This is useful when working with clipboard"""
        self._silent_selection_events = value

    def onItemSelected(self, silent: bool = False) -> None:
        """
        Handle Item selection and trigger event `Item Selected`

        :param silent: If ``True`` scene's onItemSelected won't be called and history stamp not stored
        :type silent: ``bool``
        """
        if self._silent_selection_events:
            return

        current_selected_items = self.getSelectedItems()
        if current_selected_items != self._last_selected_items:
            self._last_selected_items = current_selected_items
            if not silent:
                # we could create some kind of UI which could be serialized,
                # therefore first run all callbacks...
                for callback in self._item_selected_listeners:
                    callback()
                # and store history as a last step always
                self.history.storeHistory("Selection Changed")

    def onItemsDeselected(self, silent: bool = False) -> None:
        """
        Handle Items deselection and trigger event `Items Deselected`

        :param silent: If ``True`` scene's onItemsDeselected won't be called and history stamp not stored
        :type silent: ``bool``
        """
        # somehow this event is being triggered when we start dragging file outside of our application
        # or we just loose focus on our app? -- which does not mean we've deselected item in the scene!
        # double check if the selection has actually changed, since
        current_selected_items = self.getSelectedItems()
        if current_selected_items == self._last_selected_items:
            # print("Qt itemsDeselected Invalid Event! Ignoring")
            return

        self.resetLastSelectedStates()
        if current_selected_items == []:
            self._last_selected_items = []
            if not silent:
                self.history.storeHistory("Deselected Everything")
                for callback in self._items_deselected_listeners:
                    callback()

    def isModified(self) -> bool:
        """Is this `Scene` dirty aka `has been modified` ?

        :return: ``True`` if `Scene` has been modified
        :rtype: ``bool``
        """
        return self.has_been_modified

    def getSelectedItems(self) -> list:
        """
        Returns currently selected Graphics Items

        :return: list of ``QGraphicsItems``
        :rtype: list[QGraphicsItem]
        """
        return self.grScene.selectedItems()

    def getSelectedNodes(self) -> list:
        """
        Returns currently selected Nodes

        :return: list of ``Node``
        :rtype: list[Node]
        """
        return [item.node for item in self.getSelectedItems() if hasattr(item, "node")]

    def doDeselectItems(self, silent: bool = False) -> None:
        """
        Deselects everything in scene

        :param silent: If ``True`` scene's onItemsDeselected won't be called
        :type silent: ``bool``
        """
        for item in self.getSelectedItems():
            item.setSelected(False)
        if not silent:
            self.onItemsDeselected()

    # our helper listener functions
    def addHasBeenModifiedListener(self, callback: Callable[[], None]) -> None:
        """
        Register callback for `Has Been Modified` event

        :param callback: callback function
        """
        self._has_been_modified_listeners.append(callback)

    def addItemSelectedListener(self, callback: Callable[[], None]) -> None:
        """
        Register callback for `Item Selected` event

        :param callback: callback function
        """
        self._item_selected_listeners.append(callback)

    def addItemsDeselectedListener(self, callback: Callable[[], None]) -> None:
        """
        Register callback for `Items Deselected` event

        :param callback: callback function
        """
        self._items_deselected_listeners.append(callback)

    def addDragEnterListener(self, callback: Callable[[], None]) -> None:
        """
        Register callback for `Drag Enter` event

        :param callback: callback function
        """
        self.getView().addDragEnterListener(callback)

    def addDropListener(self, callback: Callable[[], None]) -> None:
        """
        Register callback for `Drop` event

        :param callback: callback function
        """
        self.getView().addDropListener(callback)

    # custom flag to detect node or edge has been selected....
    def resetLastSelectedStates(self) -> None:
        """Resets internal `selected flags` in all `Nodes` and `Edges` in the `Scene`"""
        for node in self.nodes:
            node.grNode._last_selected_state = False
        for edge in self.edges:
            edge.grEdge._last_selected_state = False

    def getView(self) -> 'QDMGraphicsView':
        """Shortcut for returning `Scene` ``QGraphicsView``

        :return: ``QGraphicsView`` attached to the `Scene`
        :rtype: ``QGraphicsView``
        """
        return self.grScene.views()[0]

    def getItemAt(self, pos: 'QPoint') -> Optional['QGraphicsItem']:
        """Shortcut for retrieving item at provided `Scene` position

        :param pos: scene position
        :type pos: ``QPointF``
        :return: Qt Graphics Item at scene position
        :rtype: ``QGraphicsItem``
        """
        return self.getView().itemAt(pos)

    def addNode(self, node: Node) -> None:
        """Add :class:`~nodeeditor.node_node.Node` to this `Scene`

        :param node: :class:`~nodeeditor.node_node.Node` to be added to this `Scene`
        :type node: :class:`~nodeeditor.node_node.Node`
        """
        self.nodes.append(node)

    def addEdge(self, edge: Edge) -> None:
        """Add :class:`~nodeeditor.node_edge.Edge` to this `Scene`

        :param edge: :class:`~nodeeditor.node_edge.Edge` to be added to this `Scene`
        :return: :class:`~nodeeditor.node_edge.Edge`
        """
        self.edges.append(edge)

    def removeNode(self, node: Node) -> None:
        """Remove :class:`~nodeeditor.node_node.Node` from this `Scene`

        :param node: :class:`~nodeeditor.node_node.Node` to be removed from this `Scene`
        :type node: :class:`~nodeeditor.node_node.Node`
        """
        if node in self.nodes:
            self.nodes.remove(node)
        else:
            if DEBUG_REMOVE_WARNINGS:
                print("!W:", "Scene::removeNode", "wanna remove nodeeditor", node,
                      "from self.nodes but it's not in the list!")

    def removeEdge(self, edge: Edge) -> None:
        """Remove :class:`~nodeeditor.node_edge.Edge` from this `Scene`

        :param edge: :class:`~nodeeditor.node_edge.Edge` to be remove from this `Scene`
        :return: :class:`~nodeeditor.node_edge.Edge`
        """
        if edge in self.edges:
            self.edges.remove(edge)
        else:
            if DEBUG_REMOVE_WARNINGS:
                print("!W:", "Scene::removeEdge", "wanna remove edge", edge,
                      "from self.edges but it's not in the list!")

    def addGroup(self, group) -> None:
        """Add Group to this `Scene`

        :param group: Group to be added to this `Scene`
        """
        if group not in self.groups:
            self.groups.append(group)

    def removeGroup(self, group) -> None:
        """Remove Group from this `Scene`

        :param group: Group to be removed from this `Scene`
        """
        if group in self.groups:
            self.groups.remove(group)
        else:
            if DEBUG_REMOVE_WARNINGS:
                print(
                    "!W:",
                    "Scene::removeGroup",
                    "wanna remove group",
                    group,
                    "from self.groups but it's not in the list!",
                )

    def getGroupById(self, group_id: int):
        for group in self.groups:
            if getattr(group, 'id', None) == group_id:
                return group
        return None

    def findCollapsedGroupForNode(self, node):
        """Return collapsed Group containing `node`, or None."""
        try:
            grp = getattr(node, 'parent_group', None)
            if grp is not None and grp in self.groups and getattr(grp, '_collapsed', False):
                return grp
        except Exception:
            pass
        return None

    def findGroupForDrop(self, scenepos, exclude_nodes=None):
        """Topmost smallest group whose *bounding* rect contains `scenepos`.

        Uses boundingRect (not header-only shape) so drops onto the body work.
        Returns None if no candidate. `exclude_nodes` skips groups that already
        contain all dragged nodes (avoids redundant history stamps).
        """
        try:
            from qtpy.QtCore import QPointF
            if not isinstance(scenepos, QPointF):
                try:
                    scenepos = QPointF(scenepos.x(), scenepos.y())
                except Exception:
                    return None
            best = None
            best_area = None
            exclude_ids = set()
            try:
                for n in list(exclude_nodes or []):
                    nid = getattr(n, 'id', None)
                    exclude_ids.add(nid if nid is not None else id(n))
            except Exception:
                pass
            for grp in list(getattr(self, 'groups', [])):
                try:
                    gr = grp
                    # map scene pos into group local coords, test full rect
                    try:
                        lp = gr.mapFromScene(scenepos)
                    except Exception:
                        continue
                    if not gr.rect().contains(lp):
                        continue
                    if exclude_ids:
                        try:
                            members = set()
                            for n in list(getattr(grp, 'child_nodes', [])):
                                nid = getattr(n, 'id', None)
                                members.add(nid if nid is not None else id(n))
                            if members and members.issuperset(exclude_ids):
                                # all dragged nodes already inside; still allow
                                # highlight? No - skip to avoid noop stamps.
                                all_inside = True
                                for n in list(exclude_nodes or []):
                                    if n not in list(getattr(grp, 'child_nodes', [])):
                                        all_inside = False
                                        break
                                if all_inside:
                                    continue
                        except Exception:
                            pass
                    try:
                        area = gr.rect().width() * gr.rect().height()
                    except Exception:
                        area = float('inf')
                    if best is None or area < best_area:
                        best, best_area = grp, area
                except Exception:
                    continue
            return best
        except Exception:
            return None

    def dropNodesIntoGroup(self, nodes, scenepos) -> bool:
        """Move `nodes` into group under `scenepos`. Returns True if changed."""
        try:
            grp = self.findGroupForDrop(scenepos, exclude_nodes=nodes)
            if grp is None:
                return False
            changed = False
            for node in list(nodes or []):
                try:
                    if node is None or getattr(node, 'grNode', None) is None:
                        continue
                    if getattr(node, 'parent_group', None) is grp:
                        continue
                    grp.addNode(node)
                    changed = True
                except Exception:
                    continue
            if changed:
                try:
                    if getattr(grp, '_collapsed', False):
                        grp._updateCollapsedSize()
                        grp.refreshExternalEdges()
                    else:
                        grp.updateBounds()
                except Exception:
                    pass
                try:
                    self.has_been_modified = True
                except Exception:
                    pass
            return changed
        except Exception:
            return False

    def clear(self) -> None:
        """Remove all `Nodes`, `Edges` and `Groups` from this `Scene`"""
        while len(self.nodes) > 0:
            try:
                self.nodes[0].remove()
            except Exception:
                # ensure progress even if a node is broken
                try:
                    self.nodes.pop(0)
                except Exception:
                    break
        # nodes detach from groups on remove; drop any remaining group graphics
        for group in list(self.groups):
            try:
                try:
                    if self.grScene is not None and group in self.grScene.items():
                        self.grScene.removeItem(group)
                except Exception:
                    pass
            except Exception:
                pass
        self.groups.clear()

        self.has_been_modified = False

    def saveToFile(self, filename: str) -> None:
        """
        Save this `Scene` to the file on disk.

        :param filename: where to save this scene
        :type filename: ``str``
        """
        # orjson returns bytes, so we need to decode to str before writing
        with open(filename, "w") as file:
            json_str = json.dumps(
                self.serialize(),
                option=OPT_INDENT_2,  # Use orjson's built-in indentation option
            ).decode("utf-8")
            file.write(json_str)
            # print("saving to", filename, "was successfull.")

            self.has_been_modified = False
            self.filename = filename

    def loadFromFile(self, filename: str):
        """
        Load `Scene` from a file on disk

        :param filename: from what file to load the `Scene`
        :type filename: ``str``
        :raises: :class:`~nodeeditor.node_scene.InvalidFile` if there was an error decoding JSON file
        """

        with open(filename, "r") as file:
            raw_data = file.read()
            try:
                data = json.loads(raw_data)
                self.filename = filename
                self.deserialize(data)
                self.has_been_modified = False
            except JSONDecodeError:
                raise InvalidFile("%s is not a valid JSON file" %
                                  os.path.basename(filename))
            except Exception as e:
                dumpException(e)

    def getEdgeClass(self):
        """Return the class representing Edge. Override me if needed"""
        return Edge

    def setNodeClassSelector(self, class_selecting_function: 'NodeClassType') -> None:  # noqa
        """
        Set the function which decides what `Node` class to instantiate when deserializing `Scene`.
        If not set, we will always instantiate :class:`~nodeeditor.node_node.Node` for each `Node` in the `Scene`

        :param class_selecting_function: function which returns `Node` class type (not instance) from `Node` serialized ``dict`` data
        :type class_selecting_function: ``function``
        :return: Class Type of `Node` to be instantiated during deserialization
        :rtype: `Node` class type
        """
        self.node_class_selector = class_selecting_function

    def getNodeClassFromData(self, data: dict) -> Type['Node']:
        """
        Takes `Node` serialized data and determines which `Node Class` to instantiate according the description
        in the serialized Node

        :param data: serialized `Node` object data
        :type data: ``dict``
        :return: Instance of `Node` class to be used in this Scene
        :rtype: `Node` class instance
        """
        # Groups are first-class (Scene.groups), never created via node path.
        # Keep a guard so group payloads accidentally routed here don't crash.
        if data.get("type") in ("Group", "GroupNode"):
            from nodeeditor.node_group import Group

            return Group  # type: ignore[return-value]

        return Node if self.node_class_selector is None else self.node_class_selector(data)

    def serialize(self) -> OrderedDict:
        nodes: List[dict] = []
        edges: List[dict] = []
        groups: List[dict] = []
        for node in self.nodes:
            new_node = node.serialize()
            if not any(new_node['id'] == a['id'] for a in nodes):
                nodes.append(new_node)
        for edge in self.edges:
            new_edge = edge.serialize()
            if not any(new_edge['id'] == a['id'] for a in edges):
                edges.append(new_edge)
        for group in self.groups:
            new_group = group.serialize()
            if not any(new_group["id"] == a["id"] for a in groups):
                groups.append(new_group)
        return OrderedDict(
            [
                ("id", self.id),
                ("scene_width", self.scene_width),
                ("scene_height", self.scene_height),
                ("nodes", nodes),
                ("edges", edges),
                ("groups", groups),
            ]
        )

    def deserialize(self, data: dict, hashmap: Optional[dict] = None, restore_id: bool = True, *args: Any, **kwargs: Any) -> bool:
        hashmap = hashmap or {}

        if restore_id:
            self.id = data['id']

        # -- deserialize NODES

        # Instead of recreating all the nodes, reuse existing ones...
        # get list of all current nodes:
        all_nodes = self.nodes.copy()

        # go through deserialized nodes:
        for node_data in data['nodes']:
            # can we find this node in the scene?
            found_node: Optional[Node] = None
            for node in all_nodes:
                if node.id == node_data['id']:
                    found_node = node
                    break

            if not found_node:
                try:
                    new_node = self.getNodeClassFromData(node_data)(self)
                    new_node.deserialize(
                        node_data, hashmap, restore_id, *args, **kwargs)
                    new_node.onDeserialized(node_data)
                    # print("New node for", node_data['title'])
                except:
                    dumpException()
            else:
                try:
                    found_node.deserialize(node_data, hashmap,
                                           restore_id, *args, **kwargs)
                    found_node.onDeserialized(node_data)
                    all_nodes.remove(found_node)
                    # print("Reused", node_data['title'])
                except:
                    dumpException()

        # remove nodes which are left in the scene and were NOT in the serialized data!
        # that means they were not in the graph before...
        while all_nodes != []:
            node = all_nodes.pop()
            node.remove()

        # -- deserialize EDGES

        # Instead of recreating all the edges, reuse existing ones...
        # get list of all current edges:
        all_edges = self.edges.copy()

        # go through deserialized edges:
        for edge_data in data['edges']:
            # can we find this node in the scene?
            found_edge: Optional[Edge] = None
            for edge in all_edges:
                if edge.id == edge_data['id']:
                    found_edge = edge
                    break

            if not found_edge:
                new_edge = None
                try:
                    new_edge = self.getEdgeClass()(self)
                    ok = new_edge.deserialize(
                        edge_data, hashmap, restore_id, *args, **kwargs)
                    if not ok:
                        # clean up half-created edge so groups phase still runs
                        try:
                            try:
                                if getattr(new_edge, 'grEdge', None) is not None:
                                    self.grScene.removeItem(new_edge.grEdge)
                            except Exception:
                                pass
                            if new_edge in self.edges:
                                self.edges.remove(new_edge)
                        except Exception:
                            pass
                except Exception:
                    try:
                        dumpException()
                    except Exception:
                        pass
                    try:
                        if new_edge is not None:
                            try:
                                if getattr(new_edge, 'grEdge', None) is not None:
                                    self.grScene.removeItem(new_edge.grEdge)
                            except Exception:
                                pass
                            if new_edge in self.edges:
                                self.edges.remove(new_edge)
                    except Exception:
                        pass
                # print("New edge for", edge_data)
            else:
                try:
                    found_edge.deserialize(edge_data, hashmap,
                                           restore_id, *args, **kwargs)
                except Exception:
                    try:
                        dumpException()
                    except Exception:
                        pass
                all_edges.remove(found_edge)

        # remove nodes which are left in the scene and were NOT in the serialized data!
        # that means they were not in the graph before...
        while all_edges != []:
            edge = all_edges.pop()
            edge.remove()

        # -- deserialize GROUPS (v2 clean break, best-effort old load as expanded)
        all_groups = self.groups.copy()

        for group_data in data.get("groups", []):
            found_group = None
            try:
                gid = group_data.get("id", None)
            except Exception:
                gid = None
            for group in all_groups:
                if getattr(group, 'id', None) == gid:
                    found_group = group
                    break

            if not found_group:
                try:
                    from nodeeditor.node_group import Group

                    new_group = Group(self)
                    new_group.deserialize(
                        group_data, hashmap, restore_id, *args, **kwargs
                    )
                    # Group.__init__ already added itself; guard double-add
                    if new_group not in self.groups:
                        self.groups.append(new_group)
                except Exception:
                    dumpException()
            else:
                try:
                    found_group.deserialize(
                        group_data, hashmap, restore_id, *args, **kwargs
                    )
                    all_groups.remove(found_group)
                except Exception:
                    dumpException()

        while all_groups != []:
            group = all_groups.pop()
            try:
                # dispose graphics + list entry (no child deletion on undo/load)
                # clear dangling parent_group pointers first
                try:
                    for n in list(getattr(group, 'child_nodes', [])):
                        try:
                            if getattr(n, 'parent_group', None) is group:
                                n.parent_group = None
                        except Exception:
                            pass
                    try:
                        group.child_nodes.clear()
                    except Exception:
                        pass
                except Exception:
                    pass
                try:
                    if self.grScene is not None and group in self.grScene.items():
                        self.grScene.removeItem(group)
                except Exception:
                    pass
                if group in self.groups:
                    self.groups.remove(group)
            except Exception:
                pass

        # -- restore child node relationships for groups
        # detach all first to handle moves between groups reliably
        try:
            for grp in list(self.groups):
                try:
                    for n in list(getattr(grp, 'child_nodes', [])):
                        try:
                            if getattr(n, 'parent_group', None) is grp:
                                n.parent_group = None
                        except Exception:
                            pass
                    grp.child_nodes.clear()
                except Exception:
                    continue
        except Exception:
            pass

        for group_data in data.get("groups", []):
            group = None
            try:
                gid = group_data.get("id", None)
            except Exception:
                gid = None
            for g in self.groups:
                if getattr(g, 'id', None) == gid:
                    group = g
                    break
            if group is None:
                continue
            # v2 key "children", old key "child_node_ids" (clean break: old loads expanded)
            child_ids = group_data.get("children", group_data.get("child_node_ids", []))
            try:
                node_by_id = {getattr(n, 'id', None): n for n in self.nodes}
                for child_id in list(child_ids or []):
                    node = node_by_id.get(child_id, None)
                    if node is not None:
                        group.addNode(node)
            except Exception:
                pass
            try:
                if getattr(group, '_collapsed', False):
                    group.applyCollapsedAfterLoad()
                else:
                    # mirror expand() visuals so internal edges don't stay hidden
                    # after undo/redo from collapsed -> expanded
                    try:
                        group.restoreExpandedVisuals()
                    except Exception:
                        pass
            except Exception:
                pass

        # final pass: collapsed proxy positions need real socket scenePos; refresh
        try:
            for grp in list(self.groups):
                try:
                    if getattr(grp, '_collapsed', False):
                        grp.refreshExternalEdges()
                except Exception:
                    continue
        except Exception:
            pass

        return True
