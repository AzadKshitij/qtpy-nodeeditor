# -*- coding: utf-8 -*-
"""
Constants and enumerations for the NodeEditor library.

This module contains all constant values, configuration defaults, and enumerations
used throughout the NodeEditor framework, organized by category.

Example:
    .. code-block:: python

        from nodeeditor.constants import SocketType, NodeZValue

        input_socket = Node.Socket_class(SocketType.INPUT)
        node.grNode.setZValue(NodeZValue.NODE)
"""

from enum import Enum
from qtpy.QtWidgets import QGraphicsItem
from qtpy.QtGui import QColor


# ======================== Graphics Z-Order ========================

class NodeZValue:
    """Z-order values for stacking graphics items in the scene."""
    BACKGROUND = -100
    GRID = -50
    PIPE = -1
    NODE = 1
    PORT = 2
    NODE_WIDGET = 3
    SELECTION = 10
    OVERLAY = 100


# ======================== Socket Types ========================

class SocketType(Enum):
    """Enumeration for socket/port types."""
    INPUT = 1
    OUTPUT = 2


# ======================== Socket Position ========================

class SocketPosition(Enum):
    """Enumeration for socket positions on nodes."""
    LEFT_TOP = 1
    LEFT_CENTER = 2
    LEFT_BOTTOM = 3
    RIGHT_TOP = 4
    RIGHT_CENTER = 5
    RIGHT_BOTTOM = 6


# ======================== Edge Types ========================

class EdgeType(Enum):
    """Enumeration for edge drawing styles."""
    DIRECT = 1
    BEZIER = 2
    SQUARE = 3
    IMPROVED_SHARP = 4
    IMPROVED_BEZIER = 5


# ======================== Cache Mode ========================

class CacheMode(Enum):
    """Enumeration for QGraphicsItem cache modes."""
    NO_CACHE = QGraphicsItem.CacheMode.NoCache
    DEVICE_CACHE = QGraphicsItem.CacheMode.DeviceCoordinateCache
    ITEM_CACHE = QGraphicsItem.CacheMode.ItemCoordinateCache


# ======================== Colors ========================

class NodeColors:
    """Default color values for nodes and UI elements."""
    # Background colors
    BACKGROUND = QColor("#14171a")
    GRID_LIGHT = QColor("#1d2225")
    GRID_DARK = QColor("#1d2225")
    
    # Node colors
    NODE_DEFAULT = QColor("#3d3d3d")
    NODE_SELECTED = QColor("#4a90e2")
    NODE_HOVERED = QColor("#5a5a5a")
    
    # Text colors
    TEXT_DEFAULT = QColor("#ffffff")
    TEXT_DISABLED = QColor("#888888")
    
    # Socket colors
    SOCKET_DEFAULT = QColor("#ffaa00")
    SOCKET_SELECTED = QColor("#ffff00")
    
    # Edge colors
    EDGE_DEFAULT = QColor("#aaaaaa")
    EDGE_SELECTED = QColor("#ffff00")


# ======================== Grid Settings ========================

class GridSettings:
    """Default grid display settings."""
    SIZE = 20
    SQUARES = 5
    SHOW_GRID = True


# ======================== Node Layout ========================

class LayoutDirection(Enum):
    """Enumeration for node layout directions."""
    HORIZONTAL = 0  # Left to right
    VERTICAL = 1    # Top to bottom


# ======================== Node Type Constants ========================

class NodeTypeConstants:
    """Constants for node type classification."""
    TYPE_BASE = "nodeeditor.nodes.base"
    TYPE_GROUP = "nodeeditor.nodes.group"
    TYPE_BACKDROP = "nodeeditor.nodes.backdrop"


# ======================== Serialization ========================

class SerializationKeys:
    """Dictionary keys used in node and scene serialization."""
    # Scene keys
    SCENE_NODES = "nodes"
    SCENE_EDGES = "edges"
    SCENE_GROUPS = "groups"
    SCENE_VERSION = "version"
    SCENE_METADATA = "metadata"
    
    # Node keys
    NODE_ID = "id"
    NODE_TYPE = "type"
    NODE_TITLE = "title"
    NODE_POS = "pos"
    NODE_INPUTS = "inputs"
    NODE_OUTPUTS = "outputs"
    NODE_PROPERTIES = "properties"
    NODE_VISIBLE = "visible"
    
    # Socket keys
    SOCKET_ID = "id"
    SOCKET_NAME = "name"
    SOCKET_TYPE = "type"
    SOCKET_MULTI_CONNECTION = "multi_connection"
    
    # Edge keys
    EDGE_ID = "id"
    EDGE_SOURCE = "source"
    EDGE_TARGET = "target"
    EDGE_TYPE = "type"


# ======================== File I/O ========================

class FileExtensions:
    """Supported file extensions."""
    SCENE = ".json"
    SCENE_BACKUP = ".json.bak"
    CLIPBOARD = ".clip"


# ======================== UI Dimensions ========================

class UIDimensions:
    """Default UI dimension values."""
    # Node dimensions
    NODE_MIN_WIDTH = 100
    NODE_MIN_HEIGHT = 100
    
    # Socket dimensions
    SOCKET_SIZE = 8
    SOCKET_RADIUS = SOCKET_SIZE // 2
    
    # Port dimensions
    PORT_SIZE = 12
    PORT_SPACING = 22
    
    # Grid dimensions
    GRID_SIZE = 20
    GRID_SPACING = 20


# ======================== Timing & Performance ========================

class TimingSettings:
    """Timing and performance-related settings."""
    DRAG_EDGE_THRESHOLD = 50  # pixels
    EDGE_SNAPPING_RADIUS = 24  # pixels
    SELECTION_TIMEOUT = 200  # milliseconds
    ZOOM_STEP = 1.25  # zoom factor


# ======================== Interaction Modes ========================

class InteractionMode(Enum):
    """Enumeration for view interaction modes."""
    NORMAL = 0
    EDGE_DRAG = 1
    EDGE_CUT = 2
    NODE_DRAG = 3
    SELECTION = 4


# ======================== Document Constants ========================

class DocumentConstants:
    """Constants for document/scene management."""
    DEFAULT_SCENE_WIDTH = 64000
    DEFAULT_SCENE_HEIGHT = 64000
    MAX_SCENE_WIDTH = 128000
    MAX_SCENE_HEIGHT = 128000
    MIN_SCENE_WIDTH = 8000
    MIN_SCENE_HEIGHT = 8000


# ======================== Signal/Event Constants ========================

class EventTypes:
    """Constants for different event types."""
    NODE_CREATED = "node_created"
    NODE_DELETED = "node_deleted"
    NODE_MOVED = "node_moved"
    NODE_SELECTED = "node_selected"
    NODE_PROPERTY_CHANGED = "node_property_changed"
    
    EDGE_CREATED = "edge_created"
    EDGE_DELETED = "edge_deleted"
    
    SOCKET_CONNECTED = "socket_connected"
    SOCKET_DISCONNECTED = "socket_disconnected"
    
    SCENE_CHANGED = "scene_changed"
    SCENE_MODIFIED = "scene_modified"
    
    HISTORY_CHANGED = "history_changed"
