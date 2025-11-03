# -*- coding: utf-8 -*-
"""
Utilities for node grouping operations
"""
from nodeeditor.node_group_node import GroupNode
from nodeeditor.utils_no_qt import dumpException

from typing import TYPE_CHECKING, Optional, List

if TYPE_CHECKING:
    from nodeeditor.node_scene import Scene
    from nodeeditor.node_node import Node


class GroupNodeFactory:
    """Factory for creating and managing group nodes"""
    
    @staticmethod
    def createGroup(scene: 'Scene', title: str = "Group", nodes: Optional[List['Node']] = None) -> Optional[GroupNode]:
        """
        Create a new group node
        
        :param scene: the scene to add the group to
        :param title: title of the group
        :param nodes: optional list of nodes to add to the group
        :return: the created GroupNode or None on failure
        """
        try:
            group = GroupNode(scene, title=title)
            
            if nodes:
                for node in nodes:
                    group.addNode(node)
            
            return group
        except Exception as e:
            dumpException(e)
            return None
    
    @staticmethod
    def groupSelectedNodes(scene: 'Scene', title: str = "Group") -> Optional[GroupNode]:
        """
        Create a group from selected nodes
        
        :param scene: the scene
        :param title: title of the group
        :return: the created GroupNode or None if no nodes selected
        """
        try:
            selected_items = scene.getSelectedItems()
            if not selected_items:
                return None
            
            # Filter to get only nodes
            nodes = []
            for item in selected_items:
                if hasattr(item, 'node') and not isinstance(item.node, GroupNode):
                    nodes.append(item.node)
            
            if len(nodes) < 2:
                return None
            
            return GroupNodeFactory.createGroup(scene, title, nodes)
        except Exception as e:
            dumpException(e)
            return None
    
    @staticmethod
    def ungroupNodes(group: GroupNode) -> None:
        """
        Ungroup nodes from a group
        
        :param group: the group to ungroup
        """
        try:
            nodes_to_ungroup = group.getChildNodes()
            for node in nodes_to_ungroup:
                group.removeNode(node)
        except Exception as e:
            dumpException(e)
    
    @staticmethod
    def deleteGroup(group: GroupNode, delete_children: bool = False) -> None:
        """
        Delete a group
        
        :param group: the group to delete
        :param delete_children: if True, delete child nodes as well
        """
        try:
            if delete_children:
                # Delete all child nodes
                nodes_to_delete = group.getChildNodes()
                for node in nodes_to_delete:
                    group.scene.removeNode(node)
            else:
                # Ungroup first
                GroupNodeFactory.ungroupNodes(group)
            
            # Delete the group itself
            group.scene.removeNode(group)
        except Exception as e:
            dumpException(e)


class GroupNodeManager:
    """Manager for advanced group operations"""
    
    @staticmethod
    def checkAndUpdateGroupBoundaries(node: 'Node') -> None:
        """
        Check and update parent group boundaries after node movement
        
        :param node: the node that was moved
        """
        try:
            if node.parent_group:
                node.parent_group.checkNodeBoundaries()
                node.parent_group.updateGroupBoundaries()
        except Exception as e:
            dumpException(e)
    
    @staticmethod
    def getAllNodesInGroup(group: GroupNode, recursive: bool = True) -> List['Node']:
        """
        Get all nodes in a group
        
        :param group: the group
        :param recursive: if True, include nodes in nested groups
        :return: list of all nodes
        """
        try:
            nodes = []
            
            for node in group.getChildNodes():
                nodes.append(node)
                
                if recursive and isinstance(node, GroupNode):
                    nodes.extend(GroupNodeManager.getAllNodesInGroup(node, recursive=True))
            
            return nodes
        except Exception as e:
            dumpException(e)
            return []
    
    @staticmethod
    def getGroupHierarchy(node: 'Node') -> List[GroupNode]:
        """
        Get the hierarchy of parent groups for a node
        
        :param node: the node
        :return: list of parent groups from immediate parent to root
        """
        try:
            hierarchy = []
            current = node
            
            while current.parent_group is not None:
                hierarchy.append(current.parent_group)
                current = current.parent_group
            
            return hierarchy
        except Exception as e:
            dumpException(e)
            return []
    
    @staticmethod
    def isNodeInNestedGroup(node: 'Node', group: GroupNode) -> bool:
        """
        Check if a node is in a nested group
        
        :param node: the node to check
        :param group: the group to check in
        :return: True if node is in group or any child group
        """
        try:
            if node in group.getChildNodes():
                return True
            
            for child in group.getChildNodes():
                if isinstance(child, GroupNode):
                    if GroupNodeManager.isNodeInNestedGroup(node, child):
                        return True
            
            return False
        except Exception as e:
            dumpException(e)
            return False
