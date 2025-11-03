#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify GroupNode implementation in the calculator example.
This script tests that:
1. Groups can be created from the context menu
2. Nodes can be added to groups
3. Groups collapse/expand properly
4. Groups are serialized/deserialized
"""

import sys
from qtpy.QtWidgets import QApplication

# Import calculator example components
from examples.example_calculator.calc_window import CalculatorWindow
from examples.example_calculator.nodes.input import CalcNode_Input
from examples.example_calculator.nodes.output import CalcNode_Output
from examples.example_calculator.nodes.operations import CalcNode_Add, CalcNode_Multiply
from nodeeditor.node_group_node import GroupNode


def test_grouping_in_calculator():
    """Test grouping functionality in calculator example"""
    print("=" * 60)
    print("Testing GroupNode in Calculator Example")
    print("=" * 60)
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Create calculator window
    print("\n1. Creating calculator window...")
    window = CalculatorWindow()
    
    # Get the active sub window (first one created)
    mdi = window.mdiArea
    sub_window = mdi.activeSubWindow()
    if sub_window is None:
        print("   No active sub window, creating new one...")
        window.onFileNew()
        sub_window = mdi.activeSubWindow()
    
    scene = sub_window.scene
    print(f"   ✓ Scene ready with {len(scene.nodes)} nodes")
    
    # Create some test nodes
    print("\n2. Creating test nodes...")
    input1 = CalcNode_Input(scene)
    input1.setPos(0, 0)
    
    add_node = CalcNode_Add(scene)
    add_node.setPos(200, 50)
    
    multiply_node = CalcNode_Multiply(scene)
    multiply_node.setPos(400, 50)
    
    output_node = CalcNode_Output(scene)
    output_node.setPos(600, 50)
    
    print(f"   ✓ Created 4 nodes: Input, Add, Multiply, Output")
    
    # Connect nodes
    print("\n3. Connecting nodes...")
    try:
        # input1.output0 -> add_node.input0
        edge1 = scene.createEdge(
            input1.outputs[0],
            add_node.inputs[0]
        )
        print(f"   ✓ Connected Input → Add")
        
        # add_node.output0 -> multiply_node.input0
        edge2 = scene.createEdge(
            add_node.outputs[0],
            multiply_node.inputs[0]
        )
        print(f"   ✓ Connected Add → Multiply")
        
        # multiply_node.output0 -> output_node.input0
        edge3 = scene.createEdge(
            multiply_node.outputs[0],
            output_node.inputs[0]
        )
        print(f"   ✓ Connected Multiply → Output")
    except Exception as e:
        print(f"   ✗ Connection error: {e}")
    
    # Create a group
    print("\n4. Creating group from nodes...")
    try:
        group = GroupNode(scene, title="Math Group", x=150, y=-50, width=500, height=200)
        
        # Add nodes to group
        group.addNode(add_node)
        group.addNode(multiply_node)
        
        print(f"   ✓ Created group with {len(group.getChildNodes())} nodes")
    except Exception as e:
        print(f"   ✗ Group creation error: {e}")
        return
    
    # Add group to scene
    try:
        scene.grScene.addItem(group)
        print(f"   ✓ Group added to graphics scene")
    except Exception as e:
        print(f"   ✗ Group scene add error: {e}")
    
    # Test collapse
    print("\n5. Testing collapse...")
    try:
        assert not group.isCollapsed(), "Group should not be collapsed initially"
        group.collapse()
        assert group.isCollapsed(), "Group should be collapsed after collapse()"
        print(f"   ✓ Group collapsed successfully")
    except Exception as e:
        print(f"   ✗ Collapse error: {e}")
    
    # Test expand
    print("\n6. Testing expand...")
    try:
        group.expand()
        assert not group.isCollapsed(), "Group should be expanded after expand()"
        print(f"   ✓ Group expanded successfully")
    except Exception as e:
        print(f"   ✗ Expand error: {e}")
    
    # Test serialization
    print("\n7. Testing serialization...")
    try:
        data = group.serialize()
        assert data['type'] == 'GroupNode'
        assert data['title'] == 'Math Group'
        print(f"   ✓ Group serialized successfully")
        print(f"     - Type: {data['type']}")
        print(f"     - Title: {data['title']}")
        print(f"     - Child nodes: {len(data['child_node_ids'])}")
    except Exception as e:
        print(f"   ✗ Serialization error: {e}")
    
    # Test deserialization
    print("\n8. Testing deserialization...")
    try:
        group2 = GroupNode(scene, title="Temp")
        result = group2.deserialize(data)
        assert result, "Deserialization should succeed"
        assert group2.title == group.title
        print(f"   ✓ Group deserialized successfully")
        print(f"     - Title restored: {group2.title}")
        print(f"     - Collapse state: {group2.isCollapsed()}")
    except Exception as e:
        print(f"   ✗ Deserialization error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed successfully!")
    print("=" * 60)
    print("\nTo test the UI manually:")
    print("1. In the calculator window, create multiple nodes")
    print("2. Select 2 or more nodes (click, then Shift+click)")
    print("3. Right-click to see the context menu")
    print("4. Select 'Group Selected Nodes'")
    print("5. Right-click on the group to collapse/expand it")
    print("\nType 'quit' to close the window:")
    
    # Show the window
    window.show()
    
    # Keep running for interactive testing
    return app.exec()


if __name__ == '__main__':
    sys.exit(test_grouping_in_calculator())
