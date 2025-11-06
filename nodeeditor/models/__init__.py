"""
MVC Model Layer - Pure data models with Qt signals and property decorators.

This module provides the Model layer for the MVC architecture, containing
pure data classes that represent nodes, edges, sockets, and scenes.

Each model class:
- Stores data with type hints
- Emits Qt signals on data changes
- Uses property decorators for encapsulation
- Supports serialization/deserialization
- Has no direct graphics rendering code

Classes:
    NodeModel: Represents a node with position, title, and properties
    EdgeModel: Represents a connection between two sockets
    SocketModel: Represents an input/output port on a node
    SceneModel: Represents the entire graph/scene
    GroupNodeModel: Represents a visual group container for organizing nodes
    EdgeDraggingModel: Represents the state of an edge being dragged
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from .node_model import NodeModel
from .node_icon_model import NodeIconModel
from .edge_model import EdgeModel
from .socket_model import SocketModel
from .scene_model import SceneModel
from .group_node_model import GroupNodeModel
from .edge_dragging_model import EdgeDraggingModel

__all__ = [
    "NodeModel",
    "NodeIconModel",
    "EdgeModel",
    "SocketModel",
    "SceneModel",
    "GroupNodeModel",
    "EdgeDraggingModel",
]
