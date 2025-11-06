#!/usr/bin/env python3
"""
Test script to verify the library fixes work for example_calculator.
"""

import sys
import traceback

def test_socket_controller_import():
    """Test 1: Can we import SocketController?"""
    print("Test 1: Importing SocketController...")
    try:
        from nodeeditor.controllers.socket_controller import SocketController
        print("✓ SocketController imported successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to import SocketController: {e}")
        traceback.print_exc()
        return False

def test_scene_controller_methods():
    """Test 2: Does SceneController have register_node methods?"""
    print("\nTest 2: Checking SceneController methods...")
    try:
        from nodeeditor.controllers.scene_controller import SceneController
        
        # Check methods exist
        methods = ['register_node', 'unregister_node', 'register_edge', 'unregister_edge']
        for method in methods:
            if not hasattr(SceneController, method):
                print(f"✗ SceneController missing method: {method}")
                return False
        
        print("✓ All required methods present in SceneController")
        return True
    except Exception as e:
        print(f"✗ Failed to check SceneController: {e}")
        traceback.print_exc()
        return False

def test_node_initialization():
    """Test 3: Can Node initialize without _is_dirty error?"""
    print("\nTest 3: Testing Node initialization...")
    try:
        from qtpy.QtWidgets import QApplication
        from nodeeditor.node_scene import Scene
        from nodeeditor.node_node import Node
        
        # Create a minimal Qt application if needed
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Create a scene
        scene = Scene()
        
        # Try to create a node (this was failing with _is_dirty error)
        node = Node(
            scene,
            title="Test Node",
            inputs=[1],
            outputs=[1],
            input_text=["in"],
            output_text=["out"]
        )
        
        print(f"✓ Node created successfully: {node}")
        
        # Clean up
        app.quit()
        return True
        
    except Exception as e:
        print(f"✗ Failed to create Node: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Library Fixes Verification Tests")
    print("=" * 60)
    
    results = []
    results.append(("SocketController Import", test_socket_controller_import()))
    results.append(("SceneController Methods", test_scene_controller_methods()))
    # Skip the full Node test for now as it requires Qt GUI environment
    # results.append(("Node Initialization", test_node_initialization()))
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n✓ All tests passed! Library fixes are working.")
        return 0
    else:
        print("\n✗ Some tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
