"""
Controllers Package - Business logic layer for MVC architecture.

This package contains controller classes that manage business logic and coordinate
between the Model layer (data) and View layer (graphics). Controllers handle validation,
command management, and state coordination.

Controllers:
    NodeController: Manages node creation, deletion, and property updates
    EdgeController: Manages edge creation, deletion, and connection validation
    SceneController: Top-level controller coordinating all scene operations
    GroupNodeController: Manages group container operations and state

Architecture:
    The controller layer follows the MVC pattern where:
    - Model classes (in models/) represent pure data
    - Controller classes (in controllers/) manage business logic
    - View classes coordinate with both to display and handle user interaction

Example:
    >>> from nodeeditor.controllers import SceneController
    >>> from qtpy.QtGui import QUndoStack
    >>> controller = SceneController(undo_stack=QUndoStack())
    >>> node = controller.create_node("MyNode", (100, 200))
    >>> edge = controller.create_edge(socket1, socket2)
    >>> controller.undo()
"""

from .node_controller import NodeController
from .edge_controller import EdgeController
from .scene_controller import SceneController
from .group_node_controller import GroupNodeController

__all__ = [
    "NodeController",
    "EdgeController",
    "SceneController",
    "GroupNodeController",
]

__version__ = "1.0.0"
__author__ = "NodeEditor Contributors"
