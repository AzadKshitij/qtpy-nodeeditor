"""
SceneModel - MVC Model for representing the entire graph/scene.

A SceneModel represents the complete state of a node graph including all nodes,
edges, and metadata. It coordinates between multiple node/edge models and
emits signals when the graph structure changes.

Signals:
    nodeAdded: Emitted when a node is added (NodeModel)
    nodeRemoved: Emitted when a node is removed (str - node_id)
    edgeAdded: Emitted when an edge is added (EdgeModel)
    edgeRemoved: Emitted when an edge is removed (str - edge_id)
    modifiedChanged: Emitted when modification state changes (bool)
    cleared: Emitted when scene is completely cleared
"""

from typing import Dict, List, Optional
import logging

from qtpy.QtCore import QObject, Signal

from .node_model import NodeModel
from .edge_model import EdgeModel

logger = logging.getLogger(__name__)


class SceneModel(QObject):
    """
    Model representing an entire scene/graph.

    A SceneModel is a container for all nodes and edges in a graph. It tracks
    the complete state of the scene and emits signals when nodes or edges are
    added/removed.

    Signals:
        nodeAdded(NodeModel): Emitted when node is added
        nodeRemoved(str): Emitted when node is removed (emits node_id)
        edgeAdded(EdgeModel): Emitted when edge is added
        edgeRemoved(str): Emitted when edge is removed (emits edge_id)
        modifiedChanged(bool): Emitted when modification state changes
        cleared: Emitted when scene is cleared

    Example:
        >>> scene = SceneModel()
        >>> scene.nodeAdded.connect(lambda node: print(f"Added: {node}"))
        >>> node = NodeModel("add_node", "Add")
        >>> scene.add_node(node)
        Added: add_node: Add
    """

    # Qt Signals
    nodeAdded = Signal(object)      # Emits NodeModel
    nodeRemoved = Signal(int)       # Emits node_id
    edgeAdded = Signal(object)      # Emits EdgeModel
    edgeRemoved = Signal(int)       # Emits edge_id
    modifiedChanged = Signal(bool)  # Emits True/False
    cleared = Signal()              # Emitted when scene is cleared

    def __init__(self) -> None:
        """Initialize a new SceneModel."""
        super().__init__()
        self._nodes: Dict[int, NodeModel] = {}
        self._edges: Dict[int, EdgeModel] = {}
        self._modified: bool = False
        self._filename: Optional[str] = None
        self.groups: List = []

    @property
    def nodes(self) -> List[NodeModel]:
        """
        Get all nodes in the scene.

        Returns a snapshot (shallow copy) of current nodes.

        Returns:
            List of NodeModel objects
        """
        return list(self._nodes.values())

    @property
    def node_count(self) -> int:
        """
        Get the number of nodes in the scene.

        Returns:
            Number of nodes
        """
        return len(self._nodes)

    @property
    def edges(self) -> List[EdgeModel]:
        """
        Get all edges in the scene.

        Returns a snapshot (shallow copy) of current edges.

        Returns:
            List of EdgeModel objects
        """
        return list(self._edges.values())

    @property
    def edge_count(self) -> int:
        """
        Get the number of edges in the scene.

        Returns:
            Number of edges
        """
        return len(self._edges)

    @property
    def modified(self) -> bool:
        """
        Get whether the scene has been modified.

        Useful for determining if the scene needs to be saved.

        Returns:
            True if modified, False otherwise
        """
        return self._modified

    @modified.setter
    def modified(self, value: bool) -> None:
        """
        Set the modification state of the scene.

        Emits modifiedChanged signal if state changed.

        Args:
            value: True if modified, False otherwise

        Raises:
            TypeError: If value is not boolean
        """
        if not isinstance(value, bool):
            raise TypeError(f"modified must be bool, got {type(value).__name__}")

        if self._modified != value:
            self._modified = value
            self.modifiedChanged.emit(value)

    @property
    def filename(self) -> Optional[str]:
        """
        Get the filename this scene was loaded from/saved to.

        Returns:
            Filename string or None if not yet saved
        """
        return self._filename

    @filename.setter
    def filename(self, value: Optional[str]) -> None:
        """
        Set the filename for this scene.

        Args:
            value: Filename string or None
        """
        self._filename = value

    def add_node(self, node: NodeModel) -> bool:
        """
        Add a node to the scene.

        Emits nodeAdded signal if node was successfully added.

        Args:
            node: NodeModel to add

        Returns:
            True if node was added, False if already exists

        Raises:
            TypeError: If node is not a NodeModel
        """
        if not isinstance(node, NodeModel):
            raise TypeError(f"node must be NodeModel, got {type(node).__name__}")

        if node.id in self._nodes:
            logger.warning(f"Node {node.id} already exists in scene")
            return False

        self._nodes[node.id] = node
        self.nodeAdded.emit(node)
        self.modified = True
        return True

    def remove_node(self, node_id: int) -> bool:
        """
        Remove a node from the scene.

        Also removes all edges connected to this node. Emits nodeRemoved signal
        if node was successfully removed.

        Args:
            node_id: ID of node to remove

        Returns:
            True if node was removed, False if not found

        Raises:
            TypeError: If node_id is not a string
        """
        if not isinstance(node_id, int):
            raise TypeError(f"node_id must be int, got {type(node_id).__name__}")

        if node_id not in self._nodes:
            logger.warning(f"Node {node_id} not found in scene")
            return False

        # Remove all edges connected to this node
        edges_to_remove = [
            edge_id for edge_id, edge in self._edges.items()
            if (edge.start_socket and edge.start_socket.parent_node and 
                edge.start_socket.parent_node.id == node_id)
               or (edge.end_socket and edge.end_socket.parent_node and 
                   edge.end_socket.parent_node.id == node_id)
        ]
        for edge_id in edges_to_remove:
            self.remove_edge(edge_id)

        del self._nodes[node_id]
        self.nodeRemoved.emit(node_id)
        self.modified = True
        return True

    def get_node(self, node_id: str) -> Optional[NodeModel]:
        """
        Get a node by ID.

        Args:
            node_id: ID of node to retrieve

        Returns:
            NodeModel or None if not found

        Raises:
            TypeError: If node_id is not a string
        """
        if not isinstance(node_id, int):
            raise TypeError(f"node_id must be int, got {type(node_id).__name__}")

        return self._nodes.get(node_id)

    def has_node(self, node_id: int) -> bool:
        """
        Check if a node exists in the scene.

        Args:
            node_id: ID of node to check

        Returns:
            True if node exists, False otherwise
        """
        return node_id in self._nodes

    def add_edge(self, edge: EdgeModel) -> bool:
        """
        Add an edge to the scene.

        Emits edgeAdded signal if edge was successfully added.

        Args:
            edge: EdgeModel to add

        Returns:
            True if edge was added, False if already exists

        Raises:
            TypeError: If edge is not an EdgeModel
        """
        if not isinstance(edge, EdgeModel):
            raise TypeError(f"edge must be EdgeModel, got {type(edge).__name__}")

        if edge.id in self._edges:
            logger.warning(f"Edge {edge.id} already exists in scene")
            return False

        # Validate edge
        is_valid, error = edge.validate_connection()
        if not is_valid:
            logger.warning(f"Invalid edge connection: {error}")
            return False

        self._edges[edge.id] = edge
        self.edgeAdded.emit(edge)
        self.modified = True
        return True

    def remove_edge(self, edge_id: int) -> bool:
        """
        Remove an edge from the scene.

        Emits edgeRemoved signal if edge was successfully removed.

        Args:
            edge_id: ID of edge to remove

        Returns:
            True if edge was removed, False if not found

        Raises:
            TypeError: If edge_id is not a string
        """
        if not isinstance(edge_id, int):
            raise TypeError(f"edge_id must be int, got {type(edge_id).__name__}")

        if edge_id not in self._edges:
            logger.warning(f"Edge {edge_id} not found in scene")
            return False

        edge = self._edges[edge_id]

        # Disconnect from sockets
        if edge.start_socket:
            edge.start_socket.remove_edge(edge)
        if edge.end_socket:
            edge.end_socket.remove_edge(edge)

        del self._edges[edge_id]
        self.edgeRemoved.emit(edge_id)
        self.modified = True
        return True

    def get_edge(self, edge_id: str) -> Optional[EdgeModel]:
        """
        Get an edge by ID.

        Args:
            edge_id: ID of edge to retrieve

        Returns:
            EdgeModel or None if not found

        Raises:
            TypeError: If edge_id is not a string
        """
        if not isinstance(edge_id, str):
            raise TypeError(f"edge_id must be str, got {type(edge_id).__name__}")

        return self._edges.get(edge_id)

    def has_edge(self, edge_id: str) -> bool:
        """
        Check if an edge exists in the scene.

        Args:
            edge_id: ID of edge to check

        Returns:
            True if edge exists, False otherwise
        """
        return edge_id in self._edges

    def get_selected_nodes(self) -> List[NodeModel]:
        """
        Get all selected nodes in the scene.

        Returns:
            List of selected NodeModel objects
        """
        return [node for node in self._nodes.values() if node.selected]

    def select_all_nodes(self) -> int:
        """
        Select all nodes in the scene.

        Returns:
            Number of nodes selected
        """
        count = 0
        for node in self._nodes.values():
            if not node.selected:
                node.selected = True
                count += 1
        return count

    def deselect_all_nodes(self) -> int:
        """
        Deselect all nodes in the scene.

        Returns:
            Number of nodes deselected
        """
        count = 0
        for node in self._nodes.values():
            if node.selected:
                node.selected = False
                count += 1
        return count

    def delete_selected_nodes(self) -> int:
        """
        Delete all selected nodes from the scene.

        Also removes connected edges. Returns number deleted.

        Returns:
            Number of nodes deleted
        """
        selected_ids = [n.id for n in self.get_selected_nodes()]
        count = 0
        for node_id in selected_ids:
            if self.remove_node(node_id):
                count += 1
        return count

    def clear(self) -> None:
        """
        Clear all nodes and edges from the scene.

        Emits cleared signal and sets modified to True.
        """
        self._nodes.clear()
        self._edges.clear()
        self.cleared.emit()
        self.modified = True

    def serialize(self) -> dict:
        """
        Serialize the entire scene to a dictionary.

        Can be converted to JSON for saving to file.

        Returns:
            Dictionary containing complete scene data
        """
        return {
            'nodes': [node.serialize() for node in self._nodes.values()],
            'edges': [edge.serialize() for edge in self._edges.values()],
            'metadata': {
                'node_count': len(self._nodes),
                'edge_count': len(self._edges),
            },
        }

    @classmethod
    def deserialize(cls, data: dict) -> 'SceneModel':
        """
        Deserialize a scene from a dictionary.

        Restores all nodes and edges from serialized data.

        Args:
            data: Dictionary containing scene data

        Returns:
            New SceneModel instance with all nodes and edges

        Raises:
            KeyError: If required keys are missing
            ValueError: If data is invalid
        """
        if not isinstance(data, dict):
            raise TypeError(f"data must be dict, got {type(data).__name__}")

        try:
            scene = cls()

            # Deserialize nodes
            node_map = {}  # Map of node_id to NodeModel
            for node_data in data.get('nodes', []):
                node = NodeModel.deserialize(node_data)
                scene.add_node(node)
                node_map[node.id] = node

            # Deserialize edges
            for edge_data in data.get('edges', []):
                edge = EdgeModel.deserialize(edge_data)

                # Reconnect to sockets (would need socket mapping in real implementation)
                # For now, edges are created but not connected
                scene.add_edge(edge)

            scene.modified = False
            return scene
        except (KeyError, ValueError) as e:
            raise ValueError(f"Failed to deserialize scene: {e}") from e

    def __repr__(self) -> str:
        """Return string representation of the scene model."""
        return f"SceneModel(nodes={len(self._nodes)}, edges={len(self._edges)}, modified={self._modified})"

    def __str__(self) -> str:
        """Return human-readable string of the scene model."""
        return f"Scene with {len(self._nodes)} nodes and {len(self._edges)} edges"

    def __len__(self) -> int:
        """Return total number of elements (nodes + edges)."""
        return len(self._nodes) + len(self._edges)

    @property
    def is_modified(self) -> bool:
        """Get whether the scene has been modified."""
        return self.modified
    
    @is_modified.setter
    def is_modified(self, value: bool) -> None:
        """Set the modification state of the scene."""
        self.modified = value
