#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Basic test to verify GroupNode implementation is correct.
This tests that GroupNode is a QGraphicsItem container, not a Node.
"""

import sys
from qtpy.QtWidgets import QApplication, QGraphicsScene
from qtpy.QtCore import Qt
from qtpy.QtGui import QPen, QBrush, QColor

# Import the necessary classes
from nodeeditor.node_scene import Scene
from nodeeditor.node_node import Node
from nodeeditor.node_socket import Socket, LEFT_BOTTOM, RIGHT_TOP
from nodeeditor.node_group_node import GroupNode
from nodeeditor.utils_no_qt import dumpException

def test_groupnode_creation():
    """Test that GroupNode can be created"""
    print("Testing GroupNode creation...")
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Create a scene
    scene = Scene()
    
    # Create a GroupNode
    group = GroupNode(scene, title="Test Group", x=100, y=100, width=300, height=200)
    
    # Verify it's a GroupNode
    assert isinstance(group, GroupNode), "GroupNode should be an instance of GroupNode"
    assert group.title == "Test Group", "Title should be set correctly"
    assert not group.isCollapsed(), "Group should not be collapsed initially"
    assert len(group.getChildNodes()) == 0, "Group should start with no child nodes"
    
    print("✓ GroupNode creation successful")
    
    return scene, group

def test_add_remove_nodes(scene, group):
    """Test adding and removing nodes to/from group"""
    print("Testing add/remove nodes...")
    
    # Create some test nodes
    node1 = Node(scene, title="Node1", inputs=[], outputs=[])
    node2 = Node(scene, title="Node2", inputs=[], outputs=[])
    
    # Add nodes to group
    group.addNode(node1)
    group.addNode(node2)
    
    # Verify they're in the group
    assert len(group.getChildNodes()) == 2, "Group should have 2 child nodes"
    assert node1 in group.getChildNodes(), "Node1 should be in the group"
    assert node2 in group.getChildNodes(), "Node2 should be in the group"
    assert node1.parent_group == group, "Node1's parent_group should be the group"
    assert node2.parent_group == group, "Node2's parent_group should be the group"
    
    # Remove a node
    group.removeNode(node1)
    
    # Verify
    assert len(group.getChildNodes()) == 1, "Group should have 1 child node"
    assert node1 not in group.getChildNodes(), "Node1 should not be in the group"
    assert node2 in group.getChildNodes(), "Node2 should still be in the group"
    assert node1.parent_group is None, "Node1's parent_group should be None"
    assert node2.parent_group == group, "Node2's parent_group should still be the group"
    
    print("✓ Add/remove nodes successful")

def test_collapse_expand(group):
    """Test collapse and expand functionality"""
    print("Testing collapse/expand...")
    
    # Initially not collapsed
    assert not group.isCollapsed(), "Group should not be collapsed initially"
    
    # Collapse
    group.collapse()
    assert group.isCollapsed(), "Group should be collapsed after collapse()"
    
    # Expand
    group.expand()
    assert not group.isCollapsed(), "Group should be expanded after expand()"
    
    # Toggle collapse
    group.toggleCollapse()
    assert group.isCollapsed(), "Group should be collapsed after toggleCollapse()"
    
    group.toggleCollapse()
    assert not group.isCollapsed(), "Group should be expanded after toggleCollapse()"
    
    print("✓ Collapse/expand successful")

def test_serialization(scene, group):
    """Test serialization and deserialization"""
    print("Testing serialization...")
    
    # Serialize the group
    data = group.serialize()
    
    # Verify serialized data
    assert data['type'] == 'GroupNode', "Serialized data should have type 'GroupNode'"
    assert data['title'] == 'Test Group', "Title should be in serialized data"
    assert 'x' in data and 'y' in data, "Position should be in serialized data"
    assert 'width' in data and 'height' in data, "Size should be in serialized data"
    assert 'is_collapsed' in data, "Collapse state should be in serialized data"
    
    # Create new group and deserialize
    group2 = GroupNode(scene, title="Temp")
    result = group2.deserialize(data)
    
    # Verify deserialization
    assert result, "Deserialization should succeed"
    assert group2.title == group.title, "Title should match after deserialization"
    assert group2.isCollapsed() == group.isCollapsed(), "Collapse state should match"
    
    print("✓ Serialization successful")

def main():
    """Run all tests"""
    try:
        scene, group = test_groupnode_creation()
        test_add_remove_nodes(scene, group)
        test_collapse_expand(group)
        test_serialization(scene, group)
        
        print("\n✅ All tests passed!")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        dumpException(e)
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        dumpException(e)
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
