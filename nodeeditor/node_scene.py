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

    def clear(self) -> None:
        """Remove all `Nodes` from this `Scene`. This causes also to remove all `Edges`"""
        while len(self.nodes) > 0:
            self.nodes[0].remove()

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
                option=json.OPT_INDENT_2  # Use orjson's built-in indentation option
            ).decode('utf-8')
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
                if sys.version_info >= (3, 9):
                    data = json.loads(raw_data)
                else:
                    data = json.loads(raw_data, encoding='utf-8')
                self.filename = filename
                self.deserialize(data)
                self.has_been_modified = False
            except json.JSONDecodeError:
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
        return Node if self.node_class_selector is None else self.node_class_selector(data)

    def serialize(self) -> OrderedDict:
        nodes: List[dict] = []
        edges: List[dict] = []
        for node in self.nodes:
            new_node = node.serialize()
            if not any(new_node['id'] == a['id'] for a in nodes):
                nodes.append(new_node)
        for edge in self.edges:
            new_edge = edge.serialize()
            if not any(new_edge['id'] == a['id'] for a in edges):
                edges.append(new_edge)
        return OrderedDict([
            ('id', self.id),
            ('scene_width', self.scene_width),
            ('scene_height', self.scene_height),
            ('nodes', nodes),
            ('edges', edges),
        ])

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
                new_edge = self.getEdgeClass()(self).deserialize(
                    edge_data, hashmap, restore_id, *args, **kwargs)
                # print("New edge for", edge_data)
            else:
                found_edge.deserialize(edge_data, hashmap,
                                       restore_id, *args, **kwargs)
                all_edges.remove(found_edge)

        # remove nodes which are left in the scene and were NOT in the serialized data!
        # that means they were not in the graph before...
        while all_edges != []:
            edge = all_edges.pop()
            edge.remove()

        return True
