# -*- coding: utf-8 -*-
"""
Scene - MVC-based implementation of the NodeEditor scene.

The Scene class is the main container for all nodes, edges, and groups in the graph.
It uses the MVC architecture:
- SceneModel: Contains all scene data
- SceneController: Handles scene operations
- Scene: Provides the public API
"""
import os
import orjson as json
from orjson import JSONDecodeError, OPT_INDENT_2
from collections import OrderedDict
from qtpy.QtCore import QRectF, Qt, QPoint, QObject
from qtpy.QtWidgets import QGraphicsItem
from nodeeditor.utils_no_qt import dumpException
from nodeeditor.node_serializable import Serializable
from nodeeditor.node_graphics_scene import QDMGraphicsScene
from nodeeditor.node_scene_history import SceneHistory
from nodeeditor.node_scene_clipboard import SceneClipboard

from typing import TYPE_CHECKING, List, Optional, Tuple, Any, Callable, OrderedDict as OrderedDictType, Type

if TYPE_CHECKING:
    from nodeeditor.node_graphics_view import QDMGraphicsView
    from nodeeditor.node_socket import Socket
    from nodeeditor.node_node import Node
    from nodeeditor.node_edge import Edge
    from nodeeditor import NodeModel, EdgeModel

    NodeClassType = Callable[[dict], Type['Node']]

DEBUG_REMOVE_WARNINGS = False


class InvalidFile(Exception):
    pass


class Scene(QObject, Serializable):
    """
    MVC-based Scene using Models and Controllers.

    This is a wrapper around SceneModel and SceneController that provides
    the public API while delegating all operations to the MVC layer.
    """

    historyClass = SceneHistory
    clipboardClass = SceneClipboard

    def __init__(self) -> None:
        """Initialize Scene with MVC components."""
        QObject.__init__(self)
        Serializable.__init__(self)

        # Import models and controllers here to avoid circular imports
        from nodeeditor.models.scene_model import SceneModel
        from nodeeditor.controllers.scene_controller import SceneController

        # MVC components
        self.model: SceneModel = SceneModel()
        self.controller: SceneController = SceneController(self.model)

        # Legacy-compatible registries for node and edge wrappers
        self._nodes: List["Node"] = []
        self._edges: List["Edge"] = []

        # current filename assigned to this scene
        self.filename: Optional[str] = None

        self.scene_width: int = 64000
        self.scene_height: int = 64000

        # custom flag used to suppress triggering onItemSelected which does a bunch of stuff
        self._silent_selection_events: bool = False

        self._last_selected_items: Optional[List[QGraphicsItem]] = None
        self._last_selected_socket: Optional["Socket"] = None
        self._last_selected_edges: Optional[List["Edge"]] = None

        # initialize all listeners
        self._has_been_modified_listeners: List[Callable[[], None]] = []
        self._item_selected_listeners: List[Callable[[], None]] = []
        self._items_deselected_listeners: List[Callable[[], None]] = []

        # here we can store callback for retrieving the class for Nodes
        self.node_class_selector: Optional['NodeClassType'] = None

        self.initUI()

        # Connect MVC signals
        self.model.modifiedChanged.connect(self._on_modified_changed)

        self.history = self.historyClass(self)
        self.clipboard = self.clipboardClass(self)

        self.grScene.itemSelected.connect(self.onItemSelected)
        self.grScene.itemsDeselected.connect(self.onItemsDeselected)

    # ==================== MVC Signal Handlers ====================

    def _on_modified_changed(self, is_modified: bool) -> None:
        """Handle model modification state change."""
        for callback in self._has_been_modified_listeners:
            callback()

    # ==================== Properties (Delegated to MVC) ====================

    @property
    def nodes(self) -> List["Node"]:
        """Return legacy Node wrapper instances registered with the scene."""
        return self._nodes

    @property
    def edges(self) -> List["Edge"]:
        """Return legacy Edge wrapper instances registered with the scene."""
        return self._edges

    @property
    def node_models(self) -> List["NodeModel"]:
        """Return underlying NodeModel instances tracked by the SceneModel."""
        return self.model.nodes

    @property
    def edge_models(self) -> List["EdgeModel"]:
        """Return underlying EdgeModel instances tracked by the SceneModel."""
        return self.model.edges

    @property
    def groups(self) -> List:
        """Get all groups."""
        return self.model.groups

    @property
    def _has_been_modified(self) -> bool:
        """Internal property for backward compatibility."""
        return self.model.is_modified

    @_has_been_modified.setter
    def _has_been_modified(self, value: bool) -> None:
        """Internal property for backward compatibility."""
        self.model.is_modified = value

    @property
    def has_been_modified(self) -> bool:
        """
        Has this `Scene` been modified?

        :getter: ``True`` if the `Scene` has been modified
        :setter: set new state. Triggers `Has Been Modified` event
        :type: ``bool``
        """
        return self.model.is_modified

    @has_been_modified.setter
    def has_been_modified(self, value: bool) -> None:
        """Set modified state."""
        self.model.is_modified = value

    # ==================== UI Initialization ====================

    def initUI(self) -> None:
        """Set up Graphics Scene Instance."""
        self.grScene = QDMGraphicsScene(self)
        self.grScene.setGrScene(self.scene_width, self.scene_height)

    # ==================== Node/Edge Management (Delegated) ====================

    def getNodeByID(self, node_id: int) -> Optional["Node"]:
        """Find node in the scene by ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def setSilentSelectionEvents(self, value: bool = True) -> None:
        """Suppress onItemSelected events. Useful when working with clipboard."""
        self._silent_selection_events = value

    # ==================== Selection Management ====================

    def onItemSelected(self, silent: bool = False) -> None:
        """Handle Item selection and trigger event `Item Selected`."""
        if self._silent_selection_events:
            return

        current_selected_items = self.getSelectedItems()
        if current_selected_items != self._last_selected_items:
            self._last_selected_items = current_selected_items
            if not silent:
                for callback in self._item_selected_listeners:
                    callback()
                # store history as a last step always
                self.history.storeHistory("Selection Changed")

    def onItemsDeselected(self, silent: bool = False) -> None:
        """Handle Items deselection and trigger event `Items Deselected`."""
        # double check if the selection has actually changed
        current_selected_items = self.getSelectedItems()
        if current_selected_items == self._last_selected_items:
            return

        self.resetLastSelectedStates()
        if current_selected_items == []:
            self._last_selected_items = []
            if not silent:
                self.history.storeHistory("Deselected Everything")
                for callback in self._items_deselected_listeners:
                    callback()

    def isModified(self) -> bool:
        """Is this `Scene` dirty aka `has been modified`?"""
        return self.has_been_modified

    def getSelectedItems(self) -> list:
        """Returns currently selected Graphics Items."""
        return self.grScene.selectedItems()

    def getSelectedNodes(self) -> list:
        """Returns currently selected Nodes."""
        return [item.node for item in self.getSelectedItems() if hasattr(item, "node")]

    def doDeselectItems(self, silent: bool = False) -> None:
        """Deselects everything in scene."""
        for item in self.getSelectedItems():
            item.setSelected(False)
        if not silent:
            self.onItemsDeselected()

    # ==================== Event Listeners ====================

    def addHasBeenModifiedListener(self, callback: Callable[[], None]) -> None:
        """Register callback for `Has Been Modified` event."""
        self._has_been_modified_listeners.append(callback)

    def addItemSelectedListener(self, callback: Callable[[], None]) -> None:
        """Register callback for `Item Selected` event."""
        self._item_selected_listeners.append(callback)

    def addItemsDeselectedListener(self, callback: Callable[[], None]) -> None:
        """Register callback for `Items Deselected` event."""
        self._items_deselected_listeners.append(callback)

    def addDragEnterListener(self, callback: Callable[[], None]) -> None:
        """Register callback for `Drag Enter` event."""
        self.getView().addDragEnterListener(callback)

    def addDropListener(self, callback: Callable[[], None]) -> None:
        """Register callback for `Drop` event."""
        self.getView().addDropListener(callback)

    # ==================== Selection State Management ====================

    def resetLastSelectedStates(self) -> None:
        """Resets internal `selected flags` in all `Nodes` and `Edges` in the `Scene`."""
        for node in self.nodes:
            node.grNode._last_selected_state = False
        for edge in self.edges:
            edge.grEdge._last_selected_state = False

    # ==================== View/Graphics Access ====================

    def getView(self) -> 'QDMGraphicsView':
        """Shortcut for returning `Scene` ``QGraphicsView``."""
        return self.grScene.views()[0]

    def getItemAt(self, pos: 'QPoint') -> Optional['QGraphicsItem']:
        """Shortcut for retrieving item at provided `Scene` position."""
        return self.getView().itemAt(pos)

    # ==================== Node/Edge Operations (Delegated to Controller) ====================

    def addNode(self, node: "Node") -> None:
        """Add Node to this Scene (delegates to controller)."""
        if node not in self._nodes:
            self._nodes.append(node)
        self.controller.register_node(node)

    def addEdge(self, edge: "Edge") -> None:
        """Add Edge to this Scene (delegates to controller)."""
        if edge not in self._edges:
            self._edges.append(edge)
        self.controller.register_edge(edge)

    def removeNode(self, node: "Node") -> None:
        """Remove Node from this Scene."""
        if node in self._nodes:
            self._nodes.remove(node)
        self.controller.unregister_node(node)

    def removeEdge(self, edge: "Edge") -> None:
        """Remove Edge from this Scene."""
        if edge in self._edges:
            self._edges.remove(edge)
        self.controller.unregister_edge(edge)

    def addGroup(self, group: Any) -> None:
        """Add GroupNode to this Scene."""
        self.model.groups.append(group)

    def removeGroup(self, group: Any) -> None:
        """Remove GroupNode from this Scene."""
        if group in self.model.groups:
            self.model.groups.remove(group)
        else:
            if DEBUG_REMOVE_WARNINGS:
                print(f"Warning: Group {group} not found in scene groups")

    # ==================== Scene Operations ====================

    def clear(self) -> None:
        """Remove all Nodes from this Scene. This causes also to remove all Edges."""
        while len(self.nodes) > 0:
            self.nodes[0].remove()
        self.has_been_modified = False

    # ==================== File Operations ====================

    def saveToFile(self, filename: str) -> None:
        """Save this Scene to the file on disk."""
        with open(filename, "w") as file:
            json_str = json.dumps(
                self.serialize(),
                option=OPT_INDENT_2,
            ).decode("utf-8")
            file.write(json_str)

            self.has_been_modified = False
            self.filename = filename

    def loadFromFile(self, filename: str) -> None:
        """Load Scene from a file on disk."""
        with open(filename, "r") as file:
            raw_data = file.read()
            try:
                data = json.loads(raw_data)
                self.filename = filename
                self.deserialize(data)
                self.has_been_modified = False
            except JSONDecodeError:
                raise InvalidFile(
                    f"{os.path.basename(filename)} is not a valid JSON file"
                )
            except Exception as e:
                dumpException(e)

    # ==================== Node Class Selection ====================

    def getEdgeClass(self):
        """Return the class representing Edge. Override me if needed."""
        from nodeeditor.node_edge import Edge

        return Edge

    def setNodeClassSelector(self, class_selecting_function: "NodeClassType") -> None:
        """Set the function which decides what Node class to instantiate when deserializing Scene."""
        self.node_class_selector = class_selecting_function

    def getNodeClassFromData(self, data: dict) -> Type['Node']:
        """Determines which Node Class to instantiate according the serialized Node data."""
        # Check if this is a GroupNode
        if data.get("type") == "GroupNode":
            from nodeeditor.node_group_node import GroupNode

            return GroupNode

        from nodeeditor.node_node import Node

        return Node if self.node_class_selector is None else self.node_class_selector(data)

    # ==================== Serialization ====================

    def serialize(self) -> OrderedDict:
        """Serialize the scene to OrderedDict."""
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
        """Deserialize the scene from dict data."""
        hashmap = hashmap or {}

        if restore_id:
            self.id = data['id']

        # -- deserialize NODES
        all_nodes = self.nodes.copy()

        for node_data in data['nodes']:
            found_node: Optional["Node"] = None
            for node in all_nodes:
                if node.id == node_data['id']:
                    found_node = node
                    break

            if not found_node:
                try:
                    new_node = self.getNodeClassFromData(node_data)(self)
                    new_node.deserialize(
                        node_data, hashmap, restore_id, *args, **kwargs
                    )
                    new_node.onDeserialized(node_data)
                except:
                    dumpException()
            else:
                try:
                    found_node.deserialize(
                        node_data, hashmap, restore_id, *args, **kwargs
                    )
                    found_node.onDeserialized(node_data)
                    all_nodes.remove(found_node)
                except:
                    dumpException()

        while all_nodes != []:
            node = all_nodes.pop()
            node.remove()

        # -- deserialize EDGES
        all_edges = self.edges.copy()

        for edge_data in data['edges']:
            found_edge: Optional["Edge"] = None
            for edge in all_edges:
                if edge.id == edge_data['id']:
                    found_edge = edge
                    break

            if not found_edge:
                try:
                    new_edge = self.getEdgeClass()(self).deserialize(
                        edge_data, hashmap, restore_id, *args, **kwargs
                    )
                except:
                    dumpException()
            else:
                try:
                    found_edge.deserialize(
                        edge_data, hashmap, restore_id, *args, **kwargs
                    )
                    all_edges.remove(found_edge)
                except:
                    dumpException()

        while all_edges != []:
            edge = all_edges.pop()
            edge.remove()

        # -- deserialize GROUPS
        all_groups = self.groups.copy()

        for group_data in data.get("groups", []):
            found_group = None
            for group in all_groups:
                if group.id == group_data["id"]:
                    found_group = group
                    break

            if not found_group:
                try:
                    from nodeeditor.node_group_node import GroupNode

                    new_group = GroupNode(self)
                    new_group.deserialize(
                        group_data, hashmap, restore_id, *args, **kwargs
                    )
                    self.groups.append(new_group)
                except:
                    dumpException()
            else:
                try:
                    found_group.deserialize(
                        group_data, hashmap, restore_id, *args, **kwargs
                    )
                    all_groups.remove(found_group)
                except:
                    dumpException()

        while all_groups != []:
            group = all_groups.pop()
            if hasattr(group, "remove"):
                group.remove()

        # -- restore child node relationships for groups
        for group_data in data.get("groups", []):
            group = None
            for g in self.groups:
                if g.id == group_data["id"]:
                    group = g
                    break

            if group and "child_node_ids" in group_data:
                group.child_nodes.clear()

                for child_id in group_data["child_node_ids"]:
                    for node in self.nodes:
                        if node.id == child_id:
                            group.addNode(node)
                            break

                if group._is_collapsed:
                    group.applyCollapsedStateFromDeserialization()

        return True
