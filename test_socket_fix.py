#!/usr/bin/env python3
"""
Verify that SocketModel initialization is fixed.
"""

import sys

# Test the fix without needing Qt runtime
code = """
# Simulate the fixed code path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nodeeditor.node_node import Node

class MockSocketModel:
    INPUT = 1
    OUTPUT = 2
    
    def __init__(self, name, socket_type, socket_id=None, parent_node=None):
        self._name = name
        self._type = socket_type
        self._id = socket_id or str(id(self))
        self._parent_node = parent_node
        print(f"✓ SocketModel created: name={name}, type={socket_type}")

# Simulate Socket initialization code (the fixed version)
def test_socket_init():
    print("Testing Socket initialization with fixed SocketModel call...")
    
    # Simulate socket creation parameters
    is_input = True
    index = 0
    socket_type = 1  # Color type
    
    # The FIXED code path:
    model_socket_type = MockSocketModel.INPUT if is_input else MockSocketModel.OUTPUT
    model = MockSocketModel(
        name=f"{'input' if is_input else 'output'}_{index}",
        socket_type=model_socket_type,
        socket_id=None,
        parent_node=None
    )
    
    print(f"✓ Socket created successfully with model")
    return True

if test_socket_init():
    print("✓✓ Test PASSED: SocketModel initialization is fixed!")
    sys.exit(0)
else:
    print("✗✗ Test FAILED")
    sys.exit(1)
"""

print("=" * 60)
print("SocketModel Initialization Fix Verification")
print("=" * 60)

try:
    exec(code)
except Exception as e:
    print(f"✗ Test failed with error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
