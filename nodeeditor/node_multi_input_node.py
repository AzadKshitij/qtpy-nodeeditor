# -*- coding: utf-8 -*-
"""
A module containing the ``MultiInputNode`` class: a :class:`~nodeeditor.node_node.Node`
whose input :class:`~nodeeditor.node_socket.Socket` accepts any number of
:class:`~nodeeditor.node_edge.Edge` (s) and reads them in an explicit,
persisted order.
"""
from nodeeditor.node_node import Node
from nodeeditor.utils_no_qt import dumpException

import re
from typing import TYPE_CHECKING, Any, List, Optional, Tuple


if TYPE_CHECKING:
    from nodeeditor.node_edge import Edge
    from nodeeditor.node_scene import Scene
    from nodeeditor.node_socket import Socket


class MultiInputNode(Node):
    """
    Base class for nodes reading an arbitrary number of inputs **in order**.

    Subclass it, declare the sockets you need and read them with
    :meth:`getOrderedSources` / :meth:`getOrderedValues`::

        class Sum(MultiInputNode, CalcNode):
            def evalImplementation(self):
                return [sum(self.getOrderedValues())]

    By default *every* input socket accepts multiple `Edges`
    (:attr:`multi_input_all_inputs`). Set :attr:`multi_input_socket` and
    :attr:`multi_input_all_inputs = False` to make only one socket do so.

    The order is, by default, the order the `Edges` were connected in. It can
    be changed at any time from code (:meth:`setEdgeOrder`, :meth:`moveEdgeTo`,
    :meth:`swapEdges`) and is saved to / loaded from the graph file.

    This class deliberately does not define ``__init__``, so it can be mixed
    into an existing node hierarchy without changing its constructor chain.

    :Instance Attributes:

        - **multi_input_socket** - index of the input `Socket` which accepts
          many `Edges` when :attr:`multi_input_all_inputs` is ``False``
        - **multi_input_all_inputs** - ``True`` to let every input `Socket`
          accept multiple `Edges`
    """

    #: index of the input socket accepting many `Edges` (see multi_input_all_inputs)
    multi_input_socket: int = 0

    #: when ``True`` every input socket of this node accepts multiple ``Edges``
    multi_input_all_inputs: bool = True

    #: when ``True`` every `Edge` on the ordered input is labeled ``#1``,
    #: ``#2``, ... (1-based display of its read position) and the labels are
    #: kept in sync on reorder/removal. Labels are cleared when an `Edge`
    #: detaches, but only when they still match the ``#N`` pattern, so a
    #: custom label you set yourself is never overwritten on disconnect.
    show_input_order_labels: bool = True

    def initSettings(self) -> None:
        """Initialize properties and socket information"""
        super().initSettings()
        if self.multi_input_all_inputs:
            self.input_multi_edged = True

    def initSockets(self, inputs: list, outputs: list,
                    input_text: list = [], output_text: list = [],
                    reset: bool = True) -> None:
        """Create sockets for inputs and outputs, keeping only
        :attr:`multi_input_socket` multi-edged if :attr:`multi_input_all_inputs`
        is ``False``"""
        super().initSockets(inputs, outputs, input_text, output_text, reset)
        if self.multi_input_all_inputs:
            return
        for index, socket in enumerate(self.inputs):
            socket.is_multi_edges = index == self.multi_input_socket

    # socket access

    def getMultiSocket(self, index: Optional[int] = None) -> Optional['Socket']:
        """
        Get the input :class:`~nodeeditor.node_socket.Socket` which accepts many `Edges`.

        :param index: index of the input `Socket` or ``None`` to use
            :attr:`multi_input_socket`
        :type index: ``int`` or ``None``
        :return: the ordered input `Socket` or ``None`` if the node has no such socket
        :rtype: :class:`~nodeeditor.node_socket.Socket` or ``None``
        """
        if index is None:
            index = self.multi_input_socket
        try:
            return self.inputs[index]
        except IndexError:
            return None

    def compactEdgeOrder(self, index: Optional[int] = None) -> bool:
        """
        Renumber the input `Edges` to a gap free ``0..n-1`` sequence.

        Called automatically on every connection change, so it is only needed
        after assigning :attr:`~nodeeditor.node_edge.Edge.input_index` directly.

        :param index: index of the input `Socket` or ``None`` to use
            :attr:`multi_input_socket`
        :type index: ``int`` or ``None``
        :return: ``True`` if anything actually changed
        :rtype: ``bool``
        """
        socket = self.getMultiSocket(index)
        if socket is None:
            return False
        return socket.compactEdgeOrder()

    # reading

    def getOrderedEdges(self, index: Optional[int] = None) -> List['Edge']:
        """
        Get the connected `Edges` of the ordered input `Socket` in read order.

        :param index: index of the input `Socket` or ``None`` to use
            :attr:`multi_input_socket`
        :type index: ``int`` or ``None``
        :return: `Edges` ordered by :attr:`~nodeeditor.node_edge.Edge.input_index`
        :rtype: List[:class:`~nodeeditor.node_edge.Edge`]
        """
        socket = self.getMultiSocket(index)
        if socket is None:
            return []
        return socket.orderedEdges()

    def getOrderedSources(self, index: Optional[int] = None) -> List[Tuple['Node', 'Socket']]:
        """
        Get the ``(node, socket)`` pairs feeding the ordered input `Socket`.

        One entry per connected `Edge`, in read order, so a source connected
        twice appears twice.

        :param index: index of the input `Socket` or ``None`` to use
            :attr:`multi_input_socket`
        :type index: ``int`` or ``None``
        :return: source `Node` and its `Socket` per read position
        :rtype: List[Tuple[:class:`~nodeeditor.node_node.Node`, :class:`~nodeeditor.node_socket.Socket`]]
        """
        socket = self.getMultiSocket(index)
        if socket is None:
            return []
        sources = []
        for edge in socket.orderedEdges():
            other_socket = edge.getOtherSocket(socket)
            sources.append(
                (other_socket.node, other_socket) if other_socket is not None else (None, None)
            )
        return sources

    def getOrderedValues(self, index: Optional[int] = None) -> List[Any]:
        """
        Evaluate every source of the ordered input `Socket` in read order.

        The returned list always has one entry per connected `Edge`; a source
        which fails to evaluate contributes ``None`` instead of raising, so
        ``len(getOrderedValues())`` always equals the number of connections.

        :param index: index of the input `Socket` or ``None`` to use
            :attr:`multi_input_socket`
        :type index: ``int`` or ``None``
        :return: evaluated value per read position
        :rtype: ``list``
        """
        values: List[Any] = []
        for node, _socket in self.getOrderedSources(index):
            if node is None:
                values.append(None)
                continue
            try:
                values.append(node.eval())
            except Exception as e:
                dumpException(e)
                values.append(None)
        return values

    def getOrderedNodes(self, index: Optional[int] = None) -> List['Node']:
        """
        Get the source :class:`~nodeeditor.node_node.Node` (s) of the ordered
        input `Socket` in read order.

        :param index: index of the input `Socket` or ``None`` to use
            :attr:`multi_input_socket`
        :type index: ``int`` or ``None``
        :return: source `Nodes`, one per read position
        :rtype: List[:class:`~nodeeditor.node_node.Node`]
        """
        return [node for node, _socket in self.getOrderedSources(index)]

    def describeInputOrder(self, index: Optional[int] = None) -> str:
        """
        Human readable one-line-per-position description of the input order.

        Handy for tooltips and for logging what the node currently sees::

            0: Input
            1: Add

        :param index: index of the input `Socket` or ``None`` to use
            :attr:`multi_input_socket`
        :type index: ``int`` or ``None``
        :return: description of the current read order
        :rtype: ``str``
        """
        lines = []
        for position, (node, socket) in enumerate(self.getOrderedSources(index)):
            title = node.title if node is not None else "?"
            suffix = "" if socket is None else " [out %d]" % socket.index
            lines.append("%d: %s%s" % (position, title, suffix))
        return "\n".join(lines)

    # edge order labels

    @staticmethod
    def orderLabel(position: int) -> str:
        """
        Display label for read position ``position`` (0-based).

        :param position: 0-based read position
        :type position: ``int``
        :return: ``"#1"`` for position 0, ``"#2"`` for position 1, and so on
        :rtype: ``str``
        """
        return "#%d" % (position + 1)

    def updateInputOrderLabels(self, index: Optional[int] = None) -> None:
        """
        Write :meth:`orderLabel` onto every `Edge` of the ordered input
        `Socket`. No-op when :attr:`show_input_order_labels` is ``False``.

        Called automatically after every connection change and reorder, so
        you only need it when toggling :attr:`show_input_order_labels` on
        for a node that already has connections.

        :param index: index of the input `Socket` or ``None`` to use
            :attr:`multi_input_socket`
        :type index: ``int`` or ``None``
        """
        if not self.show_input_order_labels:
            return
        socket = self.getMultiSocket(index)
        if socket is None:
            return
        for position, edge in enumerate(socket.orderedEdges()):
            try:
                if edge.getLabel() != self.orderLabel(position):
                    edge.setLabel(self.orderLabel(position))
            except Exception:
                continue

    def _clearDetachedOrderLabel(self, edge: 'Edge') -> None:
        """Clear a ``#N`` label from an `Edge` that just detached from us.

        Only labels still matching the managed pattern are cleared, so a
        custom label set from code is never destroyed on disconnect.
        """
        if not self.show_input_order_labels or edge is None:
            return
        try:
            label = edge.getLabel()
        except Exception:
            return
        if not label:
            return
        if re.fullmatch(r"#\d+", label.strip()):
            try:
                edge.setLabel("")
            except Exception:
                pass

    # manual ordering

    def setEdgeOrder(self, edges: List['Edge'], index: Optional[int] = None) -> bool:
        """
        Set the read order of the connected `Edges` of the ordered input `Socket`.

        ``edges`` may be a partial list; edges missing from it are appended
        afterwards keeping their relative order.

        :param edges: `Edges` of this node's ordered input `Socket`, first read
            position first
        :type edges: List[:class:`~nodeeditor.node_edge.Edge`]
        :param index: index of the input `Socket` or ``None`` to use
            :attr:`multi_input_socket`
        :type index: ``int`` or ``None``
        :return: ``True`` if the order changed
        :rtype: ``bool``
        """
        socket = self.getMultiSocket(index)
        if socket is None:
            return False
        if not socket.setEdgeOrder(edges):
            return False
        self.updateInputOrderLabels(index)
        self.markDirty()
        self.markDescendantsDirty()
        return True

    def setEdgeOrderByNodes(self, nodes: List['Node'], index: Optional[int] = None) -> bool:
        """
        Set the read order from a list of source :class:`~nodeeditor.node_node.Node` (s).

        Each node moves to the first read position that is not already taken by
        an earlier entry, so listing the same node twice moves it to position 0
        and pushes the rest down.

        :param nodes: source `Nodes`, first read position first
        :type nodes: List[:class:`~nodeeditor.node_node.Node`]
        :param index: index of the input `Socket` or ``None`` to use
            :attr:`multi_input_socket`
        :type index: ``int`` or ``None``
        :return: ``True`` if the order changed
        :rtype: ``bool``
        """
        socket = self.getMultiSocket(index)
        if socket is None:
            return False

        ordered = socket.orderedEdges()
        taken: List['Edge'] = []
        for node in nodes or []:
            for edge in ordered:
                if edge in taken:
                    continue
                other_socket = edge.getOtherSocket(socket)
                if other_socket is not None and other_socket.node is node:
                    taken.append(edge)
                    break
        return self.setEdgeOrder(taken, index)

    def moveEdgeTo(self, edge: 'Edge', position: int, index: Optional[int] = None) -> bool:
        """
        Move a connected `Edge` to read position ``position``.

        :param edge: :class:`~nodeeditor.node_edge.Edge` connected to this node
        :type edge: :class:`~nodeeditor.node_edge.Edge`
        :param position: target read position
        :type position: ``int``
        :param index: index of the input `Socket` or ``None`` to use
            :attr:`multi_input_socket`
        :type index: ``int`` or ``None``
        :return: ``True`` if the order changed
        :rtype: ``bool``
        """
        socket = self.getMultiSocket(index)
        if socket is None:
            return False
        if not socket.moveEdgeTo(edge, position):
            return False
        self.updateInputOrderLabels(index)
        self.markDirty()
        self.markDescendantsDirty()
        return True

    def moveEdgeBy(self, edge: 'Edge', offset: int, index: Optional[int] = None) -> bool:
        """
        Shift a connected `Edge` by ``offset`` read positions.

        Clamped at both ends, so ``offset=-1`` on the first input is a no-op.

        :param edge: :class:`~nodeeditor.node_edge.Edge` connected to this node
        :type edge: :class:`~nodeeditor.node_edge.Edge`
        :param offset: how many positions to move, negative moves earlier
        :type offset: ``int``
        :param index: index of the input `Socket` or ``None`` to use
            :attr:`multi_input_socket`
        :type index: ``int`` or ``None``
        :return: ``True`` if the order changed
        :rtype: ``bool``
        """
        socket = self.getMultiSocket(index)
        if socket is None:
            return False
        return self.moveEdgeTo(edge, socket.edgeIndex(edge) + offset, index)

    def swapEdges(self, edge_a: 'Edge', edge_b: 'Edge', index: Optional[int] = None) -> bool:
        """
        Swap the read positions of two `Edges` connected to this node.

        :param edge_a: first :class:`~nodeeditor.node_edge.Edge` to swap
        :type edge_a: :class:`~nodeeditor.node_edge.Edge`
        :param edge_b: second :class:`~nodeeditor.node_edge.Edge` to swap
        :type edge_b: :class:`~nodeeditor.node_edge.Edge`
        :param index: index of the input `Socket` or ``None`` to use
            :attr:`multi_input_socket`
        :type index: ``int`` or ``None``
        :return: ``True`` if the order changed
        :rtype: ``bool``
        """
        socket = self.getMultiSocket(index)
        if socket is None:
            return False
        if not socket.swapEdges(edge_a, edge_b):
            return False
        self.updateInputOrderLabels(index)
        self.markDirty()
        self.markDescendantsDirty()
        return True

    def reverseEdgeOrder(self, index: Optional[int] = None) -> bool:
        """
        Reverse the read order of the connected `Edges`.

        :param index: index of the input `Socket` or ``None`` to use
            :attr:`multi_input_socket`
        :type index: ``int`` or ``None``
        :return: ``True`` if the order changed
        :rtype: ``bool``
        """
        socket = self.getMultiSocket(index)
        if socket is None:
            return False
        return self.setEdgeOrder(list(reversed(socket.orderedEdges())), index)

    # events

    def onEdgeConnectionChanged(self, new_edge: 'Edge') -> None:
        """
        Keep the read order gap free after any connection change.

        This is the single hook every connection path already goes through
        (``EdgeDragging``, ``EdgeRerouting``, ``Edge.remove``), so
        :attr:`~nodeeditor.node_edge.Edge.input_index` stays a contiguous
        ``0..n-1`` sequence and the ``#N`` labels (see
        :attr:`show_input_order_labels`) stay in sync. An `Edge` that just
        detached from our ordered socket gets its managed ``#N`` label
        cleared. ``onInputChanged`` is intentionally not overridden
        so existing subclass chains keep working.
        """
        self.compactEdgeOrder()
        if (new_edge is not None
                and new_edge.start_socket is None
                and new_edge.end_socket is None):
            # fully detached (Edge.remove): forget a managed #N label, but
            # only when it still matches the pattern, so a custom label set
            # from code is never destroyed. Edges that are still connected
            # anywhere (e.g. our outputs, or rerouted elsewhere) are left
            # alone; their current owner labels them through its own hook.
            self._clearDetachedOrderLabel(new_edge)
        self.updateInputOrderLabels()
        super().onEdgeConnectionChanged(new_edge)
