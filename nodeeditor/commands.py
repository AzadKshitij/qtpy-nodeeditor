# -*- coding: utf-8 -*-
"""
Command pattern implementation for undo/redo functionality.

This module provides QUndoCommand subclasses that follow the Command design pattern
to handle all scene modifications in a way that supports undo/redo operations.

All commands follow the standard QUndoCommand interface with undo() and redo() methods,
allowing them to be managed by Qt's QUndoStack and QUndoView.

Example:
    .. code-block:: python

        from qtpy.QtGui import QUndoStack
        from nodeeditor.commands import NodeCreatedCmd, NodeMovedCmd

        undo_stack = QUndoStack()

        # Create a node
        cmd = NodeCreatedCmd(scene, node_data)
        undo_stack.push(cmd)

        # Move a node
        cmd = NodeMovedCmd(node, old_pos, new_pos)
        undo_stack.push(cmd)
"""

from qtpy.QtWidgets import QUndoCommand
# from PyQt6.QtGui import QUndoCommand
from qtpy.QtCore import QPointF
from typing import TYPE_CHECKING, Optional, List, Dict, Any
import json

if TYPE_CHECKING:
    from nodeeditor.node_scene import Scene
    from nodeeditor.node_node import Node
    from nodeeditor.node_edge import Edge
    from nodeeditor.node_socket import Socket


class BaseCommand(QUndoCommand):
    """
    Base class for all NodeEditor commands.
    
    Provides common functionality for all undo/redo commands including
    automatic text formatting and error handling.
    """
    
    def __init__(self, text: str = ""):
        """
        Initialize the command.
        
        Args:
            text (str): Description of the command for display in undo/redo menus.
        """
        super().__init__(text)
    
    def undo(self):
        """Undo the command. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement undo()")
    
    def redo(self):
        """Redo the command. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement redo()")


# ======================== Node Commands ========================

class NodeCreatedCmd(BaseCommand):
    """
    Command for creating a new node.
    
    This command stores all necessary data to recreate a node and handles
    both the creation (redo) and destruction (undo) of the node.
    """
    
    def __init__(self, scene: 'Scene', node_data: Dict[str, Any]):
        """
        Initialize the node creation command.
        
        Args:
            scene (Scene): The scene where the node will be created.
            node_data (dict): Serialized node data including position, type, etc.
        """
        super().__init__(f"Create Node")
        self.scene = scene
        self.node_data = node_data
        self.node = None
    
    def undo(self):
        """Remove the created node from the scene."""
        if self.node and self.node in self.scene.nodes:
            self.scene.removeNode(self.node)
    
    def redo(self):
        """Create and add the node to the scene."""
        if self.node is None:
            self.node = self.scene.deserialize_node(self.node_data)
        else:
            self.scene.addNode(self.node)


class NodeDeletedCmd(BaseCommand):
    """
    Command for deleting a node.
    
    Stores all node data to allow recreation on undo.
    """
    
    def __init__(self, scene: 'Scene', node: 'Node'):
        """
        Initialize the node deletion command.
        
        Args:
            scene (Scene): The scene containing the node.
            node (Node): The node to be deleted.
        """
        super().__init__(f"Delete Node '{node.title}'")
        self.scene = scene
        self.node = node
        self.node_data = node.serialize()
    
    def undo(self):
        """Recreate the deleted node."""
        self.node = self.scene.deserialize_node(self.node_data)
    
    def redo(self):
        """Remove the node from the scene."""
        if self.node in self.scene.nodes:
            self.scene.removeNode(self.node)


class NodeMovedCmd(BaseCommand):
    """
    Command for moving a node.
    
    Stores the node's old and new positions to support undo/redo of moves.
    """
    
    def __init__(self, node: 'Node', old_pos: QPointF, new_pos: QPointF):
        """
        Initialize the node move command.
        
        Args:
            node (Node): The node being moved.
            old_pos (QPointF): The node's previous position.
            new_pos (QPointF): The node's new position.
        """
        super().__init__(f"Move Node '{node.title}'")
        self.node = node
        self.old_pos = old_pos
        self.new_pos = new_pos
    
    def undo(self):
        """Move the node back to its original position."""
        self.node.setPos(*self.old_pos)
    
    def redo(self):
        """Move the node to the new position."""
        self.node.setPos(*self.new_pos)


class NodeRenamedCmd(BaseCommand):
    """
    Command for renaming a node.
    
    Stores the node's old and new titles.
    """
    
    def __init__(self, node: 'Node', old_title: str, new_title: str):
        """
        Initialize the node rename command.
        
        Args:
            node (Node): The node being renamed.
            old_title (str): The node's previous title.
            new_title (str): The node's new title.
        """
        super().__init__(f"Rename Node to '{new_title}'")
        self.node = node
        self.old_title = old_title
        self.new_title = new_title
    
    def undo(self):
        """Restore the node's original title."""
        self.node.title = self.old_title
    
    def redo(self):
        """Set the node to the new title."""
        self.node.title = self.new_title


class NodePropertyChangedCmd(BaseCommand):
    """
    Command for changing a node's property.
    
    Stores the property name and its old and new values.
    """
    
    def __init__(self, node: 'Node', property_name: str, 
                 old_value: Any, new_value: Any):
        """
        Initialize the node property change command.
        
        Args:
            node (Node): The node whose property is changing.
            property_name (str): Name of the property being changed.
            old_value: The property's previous value.
            new_value: The property's new value.
        """
        super().__init__(f"Change {property_name}")
        self.node = node
        self.property_name = property_name
        self.old_value = old_value
        self.new_value = new_value
    
    def undo(self):
        """Restore the property to its old value."""
        setattr(self.node, self.property_name, self.old_value)
    
    def redo(self):
        """Set the property to its new value."""
        setattr(self.node, self.property_name, self.new_value)


# ======================== Edge Commands ========================

class EdgeCreatedCmd(BaseCommand):
    """
    Command for creating a new edge/connection.
    
    Stores the source and target sockets to allow recreation on undo.
    """
    
    def __init__(self, edge: 'Edge'):
        """
        Initialize the edge creation command.
        
        Args:
            edge (Edge): The edge being created.
        """
        start_node = edge.start_socket.node.title if edge.start_socket else "Unknown"
        end_node = edge.end_socket.node.title if edge.end_socket else "Unknown"
        super().__init__(f"Connect '{start_node}' to '{end_node}'")
        self.edge = edge
        self.scene = edge.scene
    
    def undo(self):
        """Remove the edge from the scene."""
        if self.edge in self.scene.edges:
            self.scene.removeEdge(self.edge)
    
    def redo(self):
        """Recreate the edge connection."""
        if self.edge not in self.scene.edges:
            self.scene.addEdge(self.edge)


class EdgeDeletedCmd(BaseCommand):
    """
    Command for deleting an edge/connection.
    
    Stores all edge data to allow recreation on undo.
    """
    
    def __init__(self, edge: 'Edge'):
        """
        Initialize the edge deletion command.
        
        Args:
            edge (Edge): The edge being deleted.
        """
        start_node = edge.start_socket.node.title if edge.start_socket else "Unknown"
        end_node = edge.end_socket.node.title if edge.end_socket else "Unknown"
        super().__init__(f"Disconnect '{start_node}' from '{end_node}'")
        self.edge = edge
        self.scene = edge.scene
        self.edge_data = edge.serialize()
    
    def undo(self):
        """Recreate the deleted edge."""
        self.edge = self.scene.deserialize_edge(self.edge_data)
    
    def redo(self):
        """Remove the edge from the scene."""
        if self.edge in self.scene.edges:
            self.scene.removeEdge(self.edge)


# ======================== Multi-Object Commands ========================

class NodesMovedCmd(BaseCommand):
    """
    Command for moving multiple nodes at once.
    
    More efficient than creating individual NodeMovedCmd for each node.
    """
    
    def __init__(self, nodes: List['Node'], old_positions: List[QPointF], 
                 new_positions: List[QPointF]):
        """
        Initialize the multi-node move command.
        
        Args:
            nodes (list): List of nodes being moved.
            old_positions (list): List of previous positions.
            new_positions (list): List of new positions.
        """
        super().__init__(f"Move {len(nodes)} nodes")
        self.nodes = nodes
        self.old_positions = old_positions
        self.new_positions = new_positions
    
    def undo(self):
        """Move all nodes back to their original positions."""
        for node, pos in zip(self.nodes, self.old_positions):
            node.setPos(*pos)
    
    def redo(self):
        """Move all nodes to their new positions."""
        for node, pos in zip(self.nodes, self.new_positions):
            node.setPos(*pos)


class NodesDeletedCmd(BaseCommand):
    """
    Command for deleting multiple nodes at once.
    
    Also removes all edges connected to the deleted nodes.
    """
    
    def __init__(self, scene: 'Scene', nodes: List['Node']):
        """
        Initialize the multi-node deletion command.
        
        Args:
            scene (Scene): The scene containing the nodes.
            nodes (list): List of nodes to delete.
        """
        super().__init__(f"Delete {len(nodes)} nodes")
        self.scene = scene
        self.nodes = nodes
        self.nodes_data = [node.serialize() for node in nodes]
        # Also store edges connected to these nodes
        self.edges_data = []
        for node in nodes:
            for socket in node.inputs + node.outputs:
                for edge in socket.edges:
                    self.edges_data.append(edge.serialize())
    
    def undo(self):
        """Recreate the deleted nodes and edges."""
        for node_data in self.nodes_data:
            self.scene.deserialize_node(node_data)
        for edge_data in self.edges_data:
            self.scene.deserialize_edge(edge_data)
    
    def redo(self):
        """Remove all the nodes and their connected edges."""
        for node in self.nodes:
            if node in self.scene.nodes:
                self.scene.removeNode(node)


class SceneClearedCmd(BaseCommand):
    """
    Command for clearing all nodes and edges from a scene.
    
    Stores all data to allow complete scene restoration on undo.
    """
    
    def __init__(self, scene: 'Scene'):
        """
        Initialize the scene clear command.
        
        Args:
            scene (Scene): The scene to clear.
        """
        super().__init__("Clear Scene")
        self.scene = scene
        self.scene_data = scene.serialize()
    
    def undo(self):
        """Restore the entire scene."""
        self.scene.deserialize(self.scene_data)
    
    def redo(self):
        """Clear all nodes and edges from the scene."""
        self.scene.clear()
