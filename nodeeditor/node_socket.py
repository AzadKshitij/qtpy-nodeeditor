# -*- coding: utf-8 -*-
"""
A module containing NodeEditor's class for representing Socket and Socket Position Constants.
"""
from collections import OrderedDict
from qtpy.QtCore import QObject

from nodeeditor.node_serializable import Serializable
from nodeeditor.node_graphics_socket import QDMGraphicsSocket


from typing import TYPE_CHECKING, List, Optional, Tuple, Any, Callable, TypedDict


if TYPE_CHECKING:
    from nodeeditor.node_graphics_view import QDMGraphicsView
    from nodeeditor.node_scene import Scene
    from nodeeditor.node_edge import Edge
    from nodeeditor.node_node import Node


LEFT_TOP = 1        #:
LEFT_CENTER = 2      #:
LEFT_BOTTOM = 3     #:
RIGHT_TOP = 4       #:
RIGHT_CENTER = 5    #:
RIGHT_BOTTOM = 6    #:


DEBUG = False
DEBUG_REMOVE_WARNINGS = False


class Socket(QObject, Serializable):
    Socket_GR_Class = QDMGraphicsSocket

    """Class representing Socket."""

    def __init__(self, node: 'Node', index: int = 0, position: int = LEFT_TOP, socket_type: int = 1, multi_edges: bool = True,
                 count_on_this_node_side: int = 1, is_input: bool = False) -> None:
        """
        :param node: reference to the :class:`~nodeeditor.node_node.Node` containing this `Socket`
        :type node: :class:`~nodeeditor.node_node.Node`
        :param index: Current index of this socket in the position
        :type index: ``int``
        :param position: Socket position. See :ref:`socket-position-constants`
        :param socket_type: Constant defining type(color) of this socket
        :param multi_edges: Can this socket have multiple `Edges` connected?
        :type multi_edges: ``bool``
        :param count_on_this_node_side: number of total sockets on this position
        :type count_on_this_node_side: ``int``
        :param is_input: Is this an input `Socket`?
        :type is_input: ``bool``

        :Instance Attributes:

            - **node** - reference to the :class:`~nodeeditor.node_node.Node` containing this `Socket`
            - **edges** - list of `Edges` connected to this `Socket`
            - **grSocket** - reference to the :class:`~nodeeditor.node_graphics_socket.QDMGraphicsSocket`
            - **position** - Socket position. See :ref:`socket-position-constants`
            - **index** - Current index of this socket in the position
            - **socket_type** - Constant defining type(color) of this socket
            - **count_on_this_node_side** - number of sockets on this position
            - **is_multi_edges** - ``True`` if `Socket` can contain multiple `Edges`
            - **is_input** - ``True`` if this socket serves for Input
            - **is_output** - ``True`` if this socket serves for Output
        """
        super().__init__()  # Initialize QObject
        super(Serializable).__init__()  # Initialize Serializable

        self.node = node
        self.position = position
        self.index = index
        self.socket_type = socket_type
        self.count_on_this_node_side = count_on_this_node_side
        self.is_multi_edges = multi_edges
        self.is_input = is_input
        self.is_output = not self.is_input

        if DEBUG:
            print("Socket -- creating with", self.index,
                  self.position, "for nodeeditor", self.node)

        self.grSocket = self.__class__.Socket_GR_Class(self)

        self.setSocketPosition()

        self.edges: List['Edge'] = []

    def __str__(self) -> str:
        return "<Socket #%d %s %s..%s>" % (
            self.index, "ME" if self.is_multi_edges else "SE", hex(id(self))[
                2:5], hex(id(self))[-3:]
        )

    def delete(self) -> None:
        """Delete this `Socket` from graphics scene for sure"""
        self.grSocket.setParentItem(None)
        self.node.scene.grScene.removeItem(self.grSocket)
        del self.grSocket

    def changeSocketType(self, new_socket_type: int) -> bool:
        """
        Change the Socket Type

        :param new_socket_type: new socket type
        :type new_socket_type: ``int``
        :return: Returns ``True`` if the socket type was actually changed
        :rtype: ``bool``
        """
        if self.socket_type != new_socket_type:
            self.socket_type = new_socket_type
            self.grSocket.changeSocketType()
            return True
        return False

    def setSocketPosition(self) -> None:
        """Helper function to set `Graphics Socket` position. Exact socket position is calculated
        inside :class:`~nodeeditor.node_node.Node`."""
        self.grSocket.setPos(*self.node.getSocketPosition(self.index,
                             self.position, self.count_on_this_node_side))

    def getSocketPosition(self):
        """
        :return: Returns this `Socket` position according to the implementation stored in
            :class:`~nodeeditor.node_node.Node`
        :rtype: ``x, y`` position
        """
        if DEBUG:
            print("  GSP: ", self.index, self.position, "nodeeditor:", self.node)
        res = self.node.getSocketPosition(
            self.index, self.position, self.count_on_this_node_side)
        if DEBUG:
            print("  res", res)
        return res

    def hasAnyEdge(self) -> bool:
        """
        Returns ``True`` if any :class:`~nodeeditor.node_edge.Edge` is connected to this socket

        :return: ``True`` if any :class:`~nodeeditor.node_edge.Edge` is connected to this socket
        :rtype: ``bool``
        """
        return len(self.edges) > 0

    def isConnected(self, edge: 'Edge') -> bool:
        """
        Returns ``True`` if :class:`~nodeeditor.node_edge.Edge` is connected to this `Socket`

        :param edge: :class:`~nodeeditor.node_edge.Edge` to check if it is connected to this `Socket`
        :type edge: :class:`~nodeeditor.node_edge.Edge`
        :return: ``True`` if `Edge` is connected to this socket
        :rtype: ``bool``
        """
        return edge in self.edges

    def addEdge(self, edge: 'Edge', index: Optional[int] = None) -> None:
        """
        Append an Edge to the list of connected Edges

        On an **input** socket the `Edge` also gets a *read position* (see
        :attr:`~nodeeditor.node_edge.Edge.input_index`). Pass ``index`` to
        place it at a specific slot; when ``index`` is ``None`` a value
        already set on the `Edge` (``Edge(..., input_index=n)`` or
        deserialization) is used, and otherwise the `Edge` is appended, i.e.
        it is read last. Output sockets are not ordered and ignore ``index``.

        :param edge: :class:`~nodeeditor.node_edge.Edge` to connect to this `Socket`
        :type edge: :class:`~nodeeditor.node_edge.Edge`
        :param index: 0-based read position on an input socket or ``None`` to
            append at the end (default: order of connection)
        :type index: ``int`` or ``None``
        """
        if edge in self.edges:
            return

        if not self.is_input:
            # output sockets keep plain connection order
            self.edges.append(edge)
            return

        if index is None:
            index = getattr(edge, "input_index", -1)

        try:
            index = int(index)
        except (TypeError, ValueError):
            index = -1

        if 0 <= index <= len(self.edges):
            self.edges.insert(index, edge)
        else:
            self.edges.append(edge)
        self._reindexEdges()

    def removeEdge(self, edge: 'Edge') -> None:
        """
        Disconnect passed :class:`~nodeeditor.node_edge.Edge` from this `Socket`
        :param edge: :class:`~nodeeditor.node_edge.Edge` to disconnect
        :type edge: :class:`~nodeeditor.node_edge.Edge`
        """
        if edge in self.edges:
            self.edges.remove(edge)
            if self.is_input:
                # close the gap the removed edge left behind
                self._reindexEdges()
        else:
            if DEBUG_REMOVE_WARNINGS:
                print("!W:", "Socket::removeEdge", "wanna remove edge", edge,
                      "from self.edges but it's not in the list!")

    def removeAllEdges(self, silent: bool = False) -> None:
        """Disconnect all `Edges` from this `Socket`"""
        while self.edges:
            edge = self.edges.pop(0)
            if silent:
                edge.remove(silent_for_socket=self)
            else:
                edge.remove()       # just remove all with notifications
        if self.is_input:
            self._reindexEdges()

    # ordered input helpers

    def _reindexEdges(self) -> None:
        """
        Compact the read order of this **input** `Socket`.

        Writes ``0..len(edges)-1`` back onto every connected `Edge` so read
        positions are always gap free. No-op for output sockets, whose `Edges`
        carry no meaningful :attr:`~nodeeditor.node_edge.Edge.input_index`.
        """
        if not self.is_input:
            return
        for position, edge in enumerate(self.edges):
            edge.input_index = position

    def orderedEdges(self) -> List['Edge']:
        """
        Connected `Edges` in read order.

        On an input `Socket` this is the connection order maintained by
        :meth:`addEdge`; on an output `Socket` it is the plain connection list.

        :return: `Edges` connected to this `Socket`, first read position first
        :rtype: List[:class:`~nodeeditor.node_edge.Edge`]
        """
        if not self.is_input:
            return list(self.edges)
        # stable sort: edges sharing an input_index keep their relative order
        return sorted(self.edges, key=lambda edge: edge.input_index)

    def edgeIndex(self, edge: 'Edge') -> int:
        """
        Read position of ``edge`` on this input `Socket`.

        :param edge: :class:`~nodeeditor.node_edge.Edge` to look up
        :type edge: :class:`~nodeeditor.node_edge.Edge`
        :return: 0-based read position or ``-1`` if not connected to this `Socket`
        :rtype: ``int``
        """
        if edge not in self.edges:
            return -1
        return self.orderedEdges().index(edge)

    def compactEdgeOrder(self) -> bool:
        """
        Re-sort and renumber this input `Socket`'s `Edges` to a gap free
        ``0..n-1`` sequence. Useful after assigning
        :attr:`~nodeeditor.node_edge.Edge.input_index` directly from code.

        :return: ``True`` if anything actually changed
        :rtype: ``bool``
        """
        if not self.is_input:
            return False
        ordered = self.orderedEdges()
        changed = ordered != self.edges
        self.edges[:] = ordered
        for position, edge in enumerate(ordered):
            if edge.input_index != position:
                changed = True
            edge.input_index = position
        return changed

    def setEdgeOrder(self, edges: List['Edge']) -> bool:
        """
        Set the read order of the `Edges` connected to this input `Socket`.

        ``edges`` may be a partial list; connected `Edges` missing from it are
        appended afterwards keeping their current relative order. Duplicates
        and `Edges` of other sockets are ignored, so passing a stale or
        reordered reference is safe.

        :param edges: `Edges` of this socket, first read position first
        :type edges: List[:class:`~nodeeditor.node_edge.Edge`]
        :return: ``True`` if the order changed
        :rtype: ``bool``
        """
        if not self.is_input:
            return False

        ordered: List['Edge'] = []
        for edge in edges or []:
            # skip foreign edges and duplicates instead of failing, so a stale
            # reference to a disconnected edge cannot corrupt the order
            if edge in self.edges and edge not in ordered:
                ordered.append(edge)
        ordered += [edge for edge in self.orderedEdges() if edge not in ordered]

        if ordered == self.orderedEdges():
            return False
        self.edges[:] = ordered
        self._reindexEdges()
        return True

    def moveEdgeTo(self, edge: 'Edge', position: int) -> bool:
        """
        Move ``edge`` to read position ``position`` on this input `Socket`.

        :param edge: :class:`~nodeeditor.node_edge.Edge` to move
        :type edge: :class:`~nodeeditor.node_edge.Edge`
        :param position: target read position
        :type position: ``int``
        :return: ``True`` if the order changed
        :rtype: ``bool``
        """
        if not self.is_input or edge not in self.edges:
            return False
        try:
            position = int(position)
        except (TypeError, ValueError):
            return False

        ordered = self.orderedEdges()
        if not 0 <= position < len(ordered):
            return False
        ordered.remove(edge)
        ordered.insert(position, edge)
        self.edges[:] = ordered
        self._reindexEdges()
        return True

    def swapEdges(self, edge_a: 'Edge', edge_b: 'Edge') -> bool:
        """
        Swap the read positions of two `Edges` of this input `Socket`.

        :param edge_a: first :class:`~nodeeditor.node_edge.Edge` to swap
        :type edge_a: :class:`~nodeeditor.node_edge.Edge`
        :param edge_b: second :class:`~nodeeditor.node_edge.Edge` to swap
        :type edge_b: :class:`~nodeeditor.node_edge.Edge`
        :return: ``True`` if the order changed
        :rtype: ``bool``
        """
        if not self.is_input or edge_a not in self.edges or edge_b not in self.edges:
            return False
        ordered = self.orderedEdges()
        first, second = ordered.index(edge_a), ordered.index(edge_b)
        if first == second:
            return False
        ordered[first], ordered[second] = ordered[second], ordered[first]
        self.edges[:] = ordered
        self._reindexEdges()
        return True

    def determineMultiEdges(self, data: dict) -> bool:
        """
        Deserialization helper function. In our tutorials we created a new version of graph data format.
        This function is here to help solve the issue of opening older files in the newer format.
        If the 'multi_edges' param is missing in the dictionary, we determine if this `Socket`
        should support multiple `Edges`.

        :param data: `Socket` data in ``dict`` format for deserialization
        :type data: ``dict``
        :return: ``True`` if this `Socket` should support multi_edges
        """
        if 'multi_edges' in data:
            return data['multi_edges']
        else:
            # probably older version of file, make RIGHT socket multiedged by default
            return data['position'] in (RIGHT_BOTTOM, RIGHT_TOP)

    def serialize(self) -> OrderedDict:
        return OrderedDict([
            ('id', self.id),
            ('index', self.index),
            ('multi_edges', self.is_multi_edges),
            ('position', self.position),
            ('socket_type', self.socket_type),
        ])

    def deserialize(self, data: dict, hashmap: dict = {}, restore_id: bool = True) -> bool:
        if restore_id:
            self.id = data['id']
        self.is_multi_edges = self.determineMultiEdges(data)
        self.changeSocketType(data['socket_type'])
        hashmap[data['id']] = self
        return True
