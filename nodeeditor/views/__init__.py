"""
Views Layer - Graphics and UI Components

This module contains all view-related components:
- Graphics items for rendering (in graphics/)
- Custom content widgets (in content_widgets/)
- Icon management system (in icons/)
"""

# Import all graphics components
from .graphics import (
    QDMGraphicsEdge,
    GraphicsEdgePathBezier,
    GraphicsEdgePathDirect,
    GraphicsEdgePathSquare,
    GraphicsEdgePathImprovedSharp,
    GraphicsEdgePathImprovedBezier,
    QDMGraphicsNode,
    QDMGraphicsSocket,
    QDMGraphicsView,
    QDMGraphicsScene,
    QDMCutLine,
    QDMGraphicsGroupNode,
    NodeEditorWidget,
    NodeEditorWindow,
)

# Import content widgets
from .content_widgets import (
    QDMNodeContentWidget,
    QDMNodeIconContentWidget,
)

# Import icon registry
from .icons import (
    IconRegistry,
    get_icon_registry,
    set_icon_registry,
)

# Import debug widget
from .debug_dock_widget import (
    DebugDockWidget,
)

__all__ = [
    # Graphics
    "QDMGraphicsEdge",
    "GraphicsEdgePathBezier",
    "GraphicsEdgePathDirect",
    "GraphicsEdgePathSquare",
    "GraphicsEdgePathImprovedSharp",
    "GraphicsEdgePathImprovedBezier",
    "QDMGraphicsNode",
    "QDMGraphicsSocket",
    "QDMGraphicsView",
    "QDMGraphicsScene",
    "QDMCutLine",
    "QDMGraphicsGroupNode",
    "NodeEditorWidget",
    "NodeEditorWindow",
    # Content Widgets
    "QDMNodeContentWidget",
    "QDMNodeIconContentWidget",
    # Icons
    "IconRegistry",
    "get_icon_registry",
    "set_icon_registry",
    # Debug
    "DebugDockWidget",
]
