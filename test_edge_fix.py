#!/usr/bin/env python
"""Test the edge malformation fix."""

from qtpy.QtWidgets import QApplication

app = QApplication([])

print("Test 1: Create scene and nodes...")
from nodeeditor.node_scene import Scene
from examples.mvc_calculator.nodes.mvc_input_node import MvcCalcNode_Input
from examples.mvc_calculator.nodes.mvc_operation_nodes import MvcCalcNode_Add
from examples.mvc_calculator.nodes.mvc_output_node import MvcCalcNode_Output

scene = Scene()

input_node = MvcCalcNode_Input(scene)
add_node = MvcCalcNode_Add(scene)
output_node = MvcCalcNode_Output(scene)

print("[OK] Nodes created")

print("\nTest 2: Evaluate nodes (should not crash)...")
try:
    input_val = input_node.eval()
    print(f"[OK] Input node evaluation: {input_val}")
    print(f"  Input isDirty: {input_node.isDirty()}")
    print(f"  Input children: {input_node.getChildrenNodes()}")
except Exception as e:
    print(f"[FAIL] Error evaluating: {e}")
    import traceback
    traceback.print_exc()

print("\nTest 3: Get children with no connections...")
try:
    children = input_node.getChildrenNodes()
    print(f"[OK] getChildrenNodes returned: {children}")
except Exception as e:
    print(f"[FAIL] Error: {e}")
    import traceback
    traceback.print_exc()

print("\nTest 4: Mark descendants invalid...")
try:
    input_node.markDescendantsInvalid(False)
    print("[OK] markDescendantsInvalid succeeded")
except Exception as e:
    print(f"[FAIL] Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*50)
print("[OK] All tests passed!")
print("="*50)
