# -*- coding: utf-8 -*-
"""
A module containing all code for working with Clipboard
"""
from collections import OrderedDict
from nodeeditor.node_graphics_edge import QDMGraphicsEdge
from nodeeditor.node_edge import Edge

from typing import TYPE_CHECKING, List, Optional, Tuple, Any, Callable


if TYPE_CHECKING:
    from nodeeditor.node_graphics_view import QDMGraphicsView
    from nodeeditor.node_socket import Socket
    from nodeeditor.node_scene import Scene
    from nodeeditor.node_node import Node


DEBUG = False
DEBUG_PASTING = False


class SceneClipboard():
    """
    Class contains all the code for serialization/deserialization from Clipboard
    """

    def __init__(self, scene: 'Scene') -> None:
        """
        :param scene: Reference to the :class:`~nodeeditor.node_scene.Scene`
        :type scene: :class:`~nodeeditor.node_scene.Scene`

        :Instance Attributes:

        - **scene** - reference to the :class:`~nodeeditor.node_scene.Scene`
        """
        self.scene = scene

    def serializeSelected(self, delete: bool = False) -> OrderedDict:
        """
        Serializes selected items in the Scene into ``OrderedDict``

        :param delete: True if you want to delete selected items after serialization. Useful for Cut operation
        :type delete: ``bool``
        :return: Serialized data of current selection in NodeEditor :class:`~nodeeditor.node_scene.Scene`
        """
        if DEBUG:
            print("-- COPY TO CLIPBOARD ---")

        sel_nodes, sel_edges, sel_sockets = [], [], {}

        # sort edges and nodes
        for item in self.scene.grScene.selectedItems():
            if hasattr(item, 'node'):
                sel_nodes.append(item.node.serialize())
                for socket in (item.node.inputs + item.node.outputs):
                    sel_sockets[socket.id] = socket
            elif isinstance(item, QDMGraphicsEdge):
                sel_edges.append(item.edge)

        # debug
        if DEBUG:
            print("  NODES\n      ", sel_nodes)
            print("  EDGES\n      ", sel_edges)
            print("  SOCKETS\n     ", sel_sockets)

        # remove all edges which are not connected to a nodeeditor in our list
        edges_to_remove = []
        for edge in sel_edges:
            if edge.start_socket.id in sel_sockets and edge.end_socket.id in sel_sockets:
                # if DEBUG: print(" edge is ok, connected with both sides")
                pass
            else:
                if DEBUG:
                    print("edge", edge, "is not connected with both sides")
                edges_to_remove.append(edge)
        for edge in edges_to_remove:
            sel_edges.remove(edge)

        # make final list of edges
        edges_final = []
        for edge in sel_edges:
            edges_final.append(edge.serialize())

        if DEBUG:
            print("our final edge list:", edges_final)

        data = OrderedDict([
            ('nodes', sel_nodes),
            ('edges', edges_final),
        ])

        # if CUT (aka delete) remove selected items
        if delete:
            self.scene.getView().deleteSelected()
            # store our history
            self.scene.history.storeHistory(
                "Cut out elements from scene", setModified=True)

        return data

    def deserializeFromClipboard(self, data: dict, *args, **kwargs) -> List['Node']:
        """
        Deserializes data from Clipboard.

        :param data: ``dict`` data for deserialization to the :class:`nodeeditor.node_scene.Scene`.
        :type data: ``dict``
        """

        hashmap: dict = {}

        # calculate mouse pointer - scene position
        view = self.scene.getView()
        mouse_scene_pos = view.last_scene_mouse_position

        # calculate selected objects bbox and center
        minx, max_x, min_y, max_y = 10000000, -10000000, 10000000, -10000000
        for node_data in data['nodes']:
            if 'pos_x' in node_data and 'pos_y' in node_data:
                x, y = node_data['pos_x'], node_data['pos_y']
            else:
                # added support if node pos serializes into `pos` instead of `pos_x` and `pos_y`
                x, y = node_data['pos']
            if x < minx:
                minx = x
            if x > max_x:
                max_x = x
            if y < min_y:
                min_y = y
            if y > max_y:
                max_y = y

        # add width and height of a node
        max_x -= 180
        max_y += 100

        relbboxcenterx = (minx + max_x) / 2 - minx
        relbboxcentery = (min_y + max_y) / 2 - min_y

        if DEBUG_PASTING:
            print(" *** PASTA:")
            print("Copied boudaries:\n\tX:", minx,
                  max_x, "   Y:", min_y, max_y)
            print("\tbbox_center:", relbboxcenterx, relbboxcentery)

        # calculate the offset of the newly creating nodes
        mouse_x, mouse_y = mouse_scene_pos.x(), mouse_scene_pos.y()

        # create each node
        created_nodes: List['Node'] = []

        self.scene.setSilentSelectionEvents()

        self.scene.doDeselectItems()

        for node_data in data['nodes']:
            new_node = self.scene.getNodeClassFromData(node_data)(self.scene)
            new_node.deserialize(node_data, hashmap, False, *args, **kwargs)
            created_nodes.append(new_node)

            # readjust the new nodeeditor's position

            # new node's current position
            pos_x, pos_y = new_node.pos.x(), new_node.pos.y()
            new_x, new_y = mouse_x + pos_x - minx, mouse_y + pos_y - min_y

            new_node.setPos(new_x, new_y)

            new_node.doSelect()

            if DEBUG_PASTING:
                print("** PASTA SUM:")
                print("\tMouse pos:", mouse_x, mouse_y)
                print("\tnew node pos:", pos_x, pos_y)
                print("\tFINAL:", new_x, new_y)

        # create each edge
        if 'edges' in data:
            for edge_data in data['edges']:
                new_edge = Edge(self.scene)
                # kwargs_copy = kwargs.copy()
                # if 'restore_id' in kwargs_copy:
                #     del kwargs_copy['restore_id']
                new_edge.deserialize(edge_data, hashmap,
                                     False, *args, **kwargs)

        self.scene.setSilentSelectionEvents(False)

        # store history
        self.scene.history.storeHistory(
            "Pasted elements in scene", setModified=True)

        return created_nodes
