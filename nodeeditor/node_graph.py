# -*- coding: utf-8 -*-
"""
Graph algorithms over a NodeEditor :class:`~nodeeditor.node_scene.Scene`.

The data-flow graph of a `Scene` is directed: an
:class:`~nodeeditor.node_edge.Edge` runs from the `Node` owning its start
(output) :class:`~nodeeditor.node_socket.Socket` to the `Node` owning its end
(input) `Socket`. An `Edge` whose endpoints do not form such a pair is
ignored, as is an `Edge` that is not attached to a `Socket` at all.

Every algorithm here is implemented natively, so no third-party graph library
is required. All traversals are iterative and keep a visited set, which means

- a graph containing a cycle terminates instead of exhausting the interpreter's
  recursion limit, and
- a node reachable through several distinct paths is visited once rather than
  once per path.

The graph is derived from the `Scene` on every call, so it always reflects the
current connections. Nothing is cached and nothing has to be invalidated.

Edges internal to a collapsed :class:`~nodeeditor.node_group.Group` are hidden
on screen but still carry data, so they still count here. Groups are visual
containers and never change the shape of the graph.
"""

import heapq

from collections import deque

from typing import (
    TYPE_CHECKING,
    Deque,
    Dict,
    Iterator,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
)


if TYPE_CHECKING:
    from nodeeditor.node_edge import Edge
    from nodeeditor.node_node import Node
    from nodeeditor.node_scene import Scene


#: One step of a path: the `Node` reached and the `Edge` used to reach it.
#: The first step of a path carries ``None`` as its edge, because nothing
#: leads into the first node.
PathStep = Tuple["Node", Optional["Edge"]]

#: An iterator over the ``(neighbour, edge)`` pairs leaving a `Node`.
StepIterator = Iterator[Tuple["Node", "Edge"]]


class GraphCycleError(Exception):
    """Raised when a graph that has to be acyclic contains a cycle.

    :Instance Attributes:

        - **cycles** - the cycles found, each a list of
          :class:`~nodeeditor.node_edge.Edge` in traversal order
    """

    def __init__(self, cycles: List[List["Edge"]]) -> None:
        """
        :param cycles: the cycles found in the graph
        :type cycles: ``list`` of ``list`` of :class:`~nodeeditor.node_edge.Edge`
        """
        self.cycles = cycles
        count = len(cycles)
        super().__init__(
            "graph contains %d cycle%s" % (count, "" if count == 1 else "s"))


# ---------------------------------------------------------------------------
# internal helpers
# ---------------------------------------------------------------------------

def _edge_endpoints(edge: "Edge") -> Tuple[Optional["Node"], Optional["Node"]]:
    """``(source, target)`` of a data-flow `Edge`.

    Returns ``(None, None)`` for an `Edge` that is detached, or whose sockets
    do not form an output-to-input pair.
    """
    start = edge.start_socket
    end = edge.end_socket
    if start is None or end is None:
        return None, None
    if not (start.is_output and end.is_input):
        return None, None
    return start.node, end.node


def _downstream_steps(node: "Node") -> List[Tuple["Node", "Edge"]]:
    """``(neighbour, edge)`` pairs reachable from `node` through its outputs."""
    steps: List[Tuple["Node", "Edge"]] = []
    for socket in getattr(node, "outputs", []):
        for edge in list(getattr(socket, "edges", [])):
            # only follow the edge in the direction data flows
            if edge.start_socket is not socket:
                continue
            target = edge.end_socket
            if target is None:
                continue
            neighbour = target.node
            if neighbour is None:
                continue
            steps.append((neighbour, edge))
    return steps


def _upstream_steps(node: "Node") -> List[Tuple["Node", "Edge"]]:
    """``(neighbour, edge)`` pairs feeding `node` through its inputs."""
    steps: List[Tuple["Node", "Edge"]] = []
    for socket in getattr(node, "inputs", []):
        for edge in list(getattr(socket, "edges", [])):
            if edge.end_socket is not socket:
                continue
            source = edge.start_socket
            if source is None:
                continue
            neighbour = source.node
            if neighbour is None:
                continue
            steps.append((neighbour, edge))
    return steps


def _successor_map(scene: "Scene") -> Dict["Node", List[Tuple["Node", "Edge"]]]:
    """``{node: [(successor, edge), ...]}`` for the data-flow graph."""
    successors: Dict["Node", List[Tuple["Node", "Edge"]]] = {
        node: [] for node in scene.nodes}
    for edge in scene.edges:
        source, target = _edge_endpoints(edge)
        if source is None or target is None:
            continue
        if source not in successors or target not in successors:
            continue
        successors[source].append((target, edge))
    return successors


# ---------------------------------------------------------------------------
# reachability
# ---------------------------------------------------------------------------

def descendants(scene: "Scene", node: "Node") -> List["Node"]:
    """Every `Node` reachable downstream of `node`, excluding `node` itself.

    The result is ordered breadth-first, so the nearest nodes come first. A
    node reachable through several paths appears once.

    :param scene: the :class:`~nodeeditor.node_scene.Scene` to walk
    :param node: the `Node` to start from
    :return: the downstream `Nodes`
    :rtype: ``list`` of :class:`~nodeeditor.node_node.Node`
    """
    if node is None:
        return []

    members = set(scene.nodes)
    seen: Set["Node"] = {node}
    order: List["Node"] = []
    queue: Deque["Node"] = deque([node])

    while queue:
        current = queue.popleft()
        for neighbour, _edge in _downstream_steps(current):
            if neighbour in seen or neighbour not in members:
                continue
            seen.add(neighbour)
            order.append(neighbour)
            queue.append(neighbour)

    return order


def ancestors(scene: "Scene", node: "Node") -> List["Node"]:
    """Every `Node` feeding `node`, excluding `node` itself.

    The result is ordered breadth-first, so the nearest nodes come first. A
    node feeding through several paths appears once.

    :param scene: the :class:`~nodeeditor.node_scene.Scene` to walk
    :param node: the `Node` to start from
    :return: the upstream `Nodes`
    :rtype: ``list`` of :class:`~nodeeditor.node_node.Node`
    """
    if node is None:
        return []

    members = set(scene.nodes)
    seen: Set["Node"] = {node}
    order: List["Node"] = []
    queue: Deque["Node"] = deque([node])

    while queue:
        current = queue.popleft()
        for neighbour, _edge in _upstream_steps(current):
            if neighbour in seen or neighbour not in members:
                continue
            seen.add(neighbour)
            order.append(neighbour)
            queue.append(neighbour)

    return order


# ---------------------------------------------------------------------------
# components
# ---------------------------------------------------------------------------

def components(scene: "Scene") -> List[List["Node"]]:
    """The disconnected subgraphs of `scene`, the "flocks" of nodes.

    Two `Nodes` belong to the same component when a chain of `Edges` connects
    them, regardless of direction. A `Node` without any connection forms a
    component of its own.

    The components come in scene order, and the `Nodes` inside a component come
    in scene order too, so the result is stable for a given graph.

    :param scene: the :class:`~nodeeditor.node_scene.Scene` to inspect
    :return: one list of `Nodes` per component
    :rtype: ``list`` of ``list`` of :class:`~nodeeditor.node_node.Node`
    """
    nodes = list(scene.nodes)
    order_of = {node: index for index, node in enumerate(nodes)}
    parent = {node: node for node in nodes}

    def find(node: "Node") -> "Node":
        root = node
        while parent[root] is not root:
            root = parent[root]
        # path compression
        while parent[node] is not root:
            parent[node], node = root, parent[node]
        return root

    for edge in scene.edges:
        source, target = _edge_endpoints(edge)
        if source is None or target is None:
            continue
        if source not in parent or target not in parent:
            continue
        root_source = find(source)
        root_target = find(target)
        if root_source is root_target:
            continue
        # keep the earliest node of the component as its root, so the
        # components come out in scene order
        if order_of[root_source] <= order_of[root_target]:
            parent[root_target] = root_source
        else:
            parent[root_source] = root_target

    groups: Dict["Node", List["Node"]] = {}
    for node in nodes:
        groups.setdefault(find(node), []).append(node)

    return list(groups.values())


# ---------------------------------------------------------------------------
# ordering
# ---------------------------------------------------------------------------

def topological_order(scene: "Scene") -> List["Node"]:
    """The `Nodes` of `scene` in dependency order.

    Every `Node` comes after the `Nodes` feeding it, so a `Node` can be
    evaluated once every input it needs has been evaluated. `Nodes` that do
    not depend on each other keep their scene order, which makes the result
    reproducible for a given graph.

    :param scene: the :class:`~nodeeditor.node_scene.Scene` to order
    :return: the `Nodes` in dependency order
    :rtype: ``list`` of :class:`~nodeeditor.node_node.Node`
    :raises :class:`GraphCycleError` if the graph contains a cycle
    """
    nodes = list(scene.nodes)
    order_of = {node: index for index, node in enumerate(nodes)}
    successors: Dict["Node", List["Node"]] = {node: [] for node in nodes}
    indegree: Dict["Node", int] = {node: 0 for node in nodes}

    for edge in scene.edges:
        source, target = _edge_endpoints(edge)
        if source is None or target is None:
            continue
        if source not in successors or target not in successors:
            continue
        successors[source].append(target)
        indegree[target] += 1

    ready = [(order_of[node], node) for node in nodes if indegree[node] == 0]
    heapq.heapify(ready)

    result: List["Node"] = []
    while ready:
        _position, node = heapq.heappop(ready)
        result.append(node)
        for successor in successors[node]:
            indegree[successor] -= 1
            if indegree[successor] == 0:
                heapq.heappush(ready, (order_of[successor], successor))

    if len(result) != len(nodes):
        # whatever is left sits on a cycle
        raise GraphCycleError(cycles(scene))

    return result


# ---------------------------------------------------------------------------
# cycles
# ---------------------------------------------------------------------------

def _strongly_connected_components(
    nodes: Sequence["Node"],
    successors: Dict["Node", List[Tuple["Node", "Edge"]]],
) -> List[List["Node"]]:
    """Kosaraju's algorithm, iterative.

    :return: one list of `Nodes` per strongly connected component
    """
    visited: Set["Node"] = set()
    finish_order: List["Node"] = []

    # first pass: finishing order over the forward graph
    for root in nodes:
        if root in visited:
            continue
        visited.add(root)
        stack: List[Tuple["Node", StepIterator]] = [
            (root, iter(successors.get(root, ())))]
        while stack:
            node, iterator = stack[-1]
            advanced = False
            for successor, _edge in iterator:
                if successor in visited:
                    continue
                visited.add(successor)
                stack.append(
                    (successor, iter(successors.get(successor, ()))))
                advanced = True
                break
            if not advanced:
                stack.pop()
                finish_order.append(node)

    # second pass: components over the reversed graph
    reverse: Dict["Node", List["Node"]] = {node: [] for node in nodes}
    for node, pairs in successors.items():
        for successor, _edge in pairs:
            if successor in reverse:
                reverse[successor].append(node)

    assigned: Set["Node"] = set()
    components_found: List[List["Node"]] = []
    for root in reversed(finish_order):
        if root in assigned:
            continue
        assigned.add(root)
        stack = [root]
        component: List["Node"] = []
        while stack:
            node = stack.pop()
            component.append(node)
            for predecessor in reverse.get(node, ()):
                if predecessor in assigned:
                    continue
                assigned.add(predecessor)
                stack.append(predecessor)
        components_found.append(component)

    return components_found


def _cycle_within(
    component: Sequence["Node"],
    successors: Dict["Node", List[Tuple["Node", "Edge"]]],
) -> List["Edge"]:
    """One cycle inside a strongly connected component, as a list of `Edges`.

    The last `Edge` of the returned list leads back to the node the first
    `Edge` started from. An empty list means the component holds no cycle.
    """
    members = set(component)
    if not component:
        return []

    if len(component) == 1:
        only = component[0]
        for successor, edge in successors.get(only, ()):
            if successor is only:
                return [edge]
        return []

    white, grey, black = 0, 1, 2
    color: Dict["Node", int] = {node: white for node in component}

    root = component[0]
    color[root] = grey
    path_nodes: List["Node"] = [root]
    path_edges: List["Edge"] = []
    stack: List[Tuple["Node", StepIterator]] = [
        (root, iter(successors.get(root, ())))]

    while stack:
        node, iterator = stack[-1]
        advanced = False
        for successor, edge in iterator:
            if successor not in members:
                continue
            state = color.get(successor, white)
            if state == grey:
                # back edge: the cycle closes on a node of the current path
                index = path_nodes.index(successor)
                return path_edges[index:] + [edge]
            if state == white:
                color[successor] = grey
                path_nodes.append(successor)
                path_edges.append(edge)
                stack.append(
                    (successor, iter(successors.get(successor, ()))))
                advanced = True
                break
        if not advanced:
            stack.pop()
            color[node] = black
            if len(path_nodes) > 1:
                path_nodes.pop()
                path_edges.pop()

    return []


def cycles(scene: "Scene") -> List[List["Edge"]]:
    """The cycles of `scene`.

    One representative cycle is returned per cyclic region, so a graph with
    two separate loops yields two cycles. Within a cycle, the `Edges` are
    listed in traversal order and the last one leads back to the node the
    first one started from.

    :param scene: the :class:`~nodeeditor.node_scene.Scene` to inspect
    :return: the cycles, each a list of :class:`~nodeeditor.node_edge.Edge`
    :rtype: ``list`` of ``list`` of :class:`~nodeeditor.node_edge.Edge`
    """
    nodes = list(scene.nodes)
    successors = _successor_map(scene)

    found: List[List["Edge"]] = []
    for component in _strongly_connected_components(nodes, successors):
        cycle = _cycle_within(component, successors)
        if cycle:
            found.append(cycle)

    return found


# ---------------------------------------------------------------------------
# paths
# ---------------------------------------------------------------------------

def paths(scene: "Scene", source: "Node", target: "Node") -> List[List[PathStep]]:
    """Every simple path from `source` to `target`.

    A path is a list of ``(node, edge)`` steps. The `edge` of a step is the
    `Edge` that led into its `Node`; the first step carries ``None`` because
    nothing leads into the first node. Two `Edges` between the same pair of
    `Nodes` yield two different paths, because each `Edge` is its own thing.

    :param scene: the :class:`~nodeeditor.node_scene.Scene` to search
    :param source: the `Node` to start from
    :param target: the `Node` to reach
    :return: the paths found
    :rtype: ``list`` of ``list`` of ``(Node, Edge)``
    """
    if source is None or target is None:
        return []
    if source is target:
        return [[(source, None)]]

    successors = _successor_map(scene)
    members = set(scene.nodes)
    if source not in members or target not in members:
        return []

    results: List[List[PathStep]] = []
    visited: Set["Node"] = {source}
    path_nodes: List["Node"] = [source]
    path_edges: List[Optional["Edge"]] = [None]
    stack: List[StepIterator] = [iter(successors.get(source, ()))]

    while stack:
        iterator = stack[-1]
        advanced = False
        for successor, edge in iterator:
            if successor in visited:
                continue
            visited.add(successor)
            path_nodes.append(successor)
            path_edges.append(edge)
            if successor is target:
                results.append(list(zip(path_nodes, path_edges)))
                visited.discard(successor)
                path_nodes.pop()
                path_edges.pop()
                continue
            stack.append(iter(successors.get(successor, ())))
            advanced = True
            break
        if not advanced:
            stack.pop()
            if len(path_nodes) > 1:
                visited.discard(path_nodes.pop())
                path_edges.pop()

    return results


def shortest_path(
    scene: "Scene", source: "Node", target: "Node") -> Optional[List[PathStep]]:
    """The shortest path from `source` to `target`, counted in `Edges`.

    The path is a list of ``(node, edge)`` steps, the same shape
    :func:`paths` returns. When several shortest paths exist, the one found
    first is returned, which makes the result reproducible.

    :param scene: the :class:`~nodeeditor.node_scene.Scene` to search
    :param source: the `Node` to start from
    :param target: the `Node` to reach
    :return: the shortest path, or ``None`` when `target` is unreachable
    :rtype: ``list`` of ``(Node, Edge)`` or ``None``
    """
    if source is None or target is None:
        return None
    if source is target:
        return [(source, None)]

    successors = _successor_map(scene)
    members = set(scene.nodes)
    if source not in members or target not in members:
        return None

    previous: Dict["Node", Tuple["Node", "Edge"]] = {}
    visited: Set["Node"] = {source}
    queue: Deque["Node"] = deque([source])

    while queue:
        node = queue.popleft()
        for successor, edge in successors.get(node, ()):
            if successor in visited:
                continue
            visited.add(successor)
            previous[successor] = (node, edge)
            if successor is target:
                return _rebuild_path(previous, source, target)
            queue.append(successor)

    return None


def _rebuild_path(
    previous: Dict["Node", Tuple["Node", "Edge"]],
    source: "Node",
    target: "Node",
) -> List[PathStep]:
    """Turn a BFS predecessor map into a list of ``(node, edge)`` steps."""
    steps: List[PathStep] = []
    node = target
    while node is not source:
        predecessor, edge = previous[node]
        steps.append((node, edge))
        node = predecessor
    steps.append((source, None))
    steps.reverse()
    return steps
