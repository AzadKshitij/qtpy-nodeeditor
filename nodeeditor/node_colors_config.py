# -*- coding: utf-8 -*-
"""
A module for centralized color configuration for the Node Editor.

This module provides a single point to manage and update all colors used in:
- Edge graphics (default, selected, hovered, dragging)
- Socket graphics (background colors per type, highlighting, outlines)
"""

from qtpy.QtGui import QColor
from typing import Dict, List


class BaseColors:
    """Base class for color configurations
    _Parameters:
        - **_default**: Default color
        - **_selected**: Selected color
        - **_hovered**: Hovered color
        - **_dragging**: Dragging color
    """
    def __init__(self):
        """Initialize default colors
        """
        self._default: QColor = QColor("#B08848")
        self._selected: QColor = QColor("#00ff00")
        self._hovered: QColor = QColor("#FF37A6FF")
        self._dragging: QColor = QColor("#333334")

    @property
    def default(self) -> QColor:
        """Get default edge color"""
        return QColor(self._default)

    @default.setter
    def default(self, color):
        """Set default edge color"""
        self._default = self._parse_color(color)

    @property
    def selected(self) -> QColor:
        """Get selected edge color"""
        return QColor(self._selected)

    @selected.setter
    def selected(self, color):
        """Set selected edge color"""
        self._selected = self._parse_color(color)

    @property
    def hovered(self) -> QColor:
        """Get hovered edge color"""
        return QColor(self._hovered)

    @hovered.setter
    def hovered(self, color):
        """Set hovered edge color"""
        self._hovered = self._parse_color(color)

    @staticmethod
    def _parse_color(color) -> QColor:
        """Parse color from various formats to QColor"""
        if isinstance(color, QColor):
            return QColor(color)
        elif isinstance(color, str):
            return QColor(color)
        elif isinstance(color, tuple) and len(color) >= 3:
            # RGB or RGBA tuple
            return QColor(*color)
        else:
            raise ValueError(f"Invalid color format: {color}")


class EdgeColors(BaseColors):
    """Configuration for Edge colors"""

    def __init__(self):
        """Initialize default edge colors"""
        self._default = QColor("#B08848")
        self._selected = QColor("#ff00d0")
        self._hovered = QColor("#FF37A6FF")
        self._dragging = QColor("#333334")

    @property
    def default(self) -> QColor:
        """Get default edge color"""
        return QColor(self._default)

    @default.setter
    def default(self, color):
        """Set default edge color"""
        self._default = self._parse_color(color)

    @property
    def selected(self) -> QColor:
        """Get selected edge color"""
        return QColor(self._selected)

    @selected.setter
    def selected(self, color):
        """Set selected edge color"""
        self._selected = self._parse_color(color)

    @property
    def hovered(self) -> QColor:
        """Get hovered edge color"""
        return QColor(self._hovered)

    @hovered.setter
    def hovered(self, color):
        """Set hovered edge color"""
        self._hovered = self._parse_color(color)

    @property
    def dragging(self) -> QColor:
        """Get dragging edge color"""
        return QColor(self._dragging)

    @dragging.setter
    def dragging(self, color):
        """Set dragging edge color"""
        self._dragging = self._parse_color(color)

    def set_all(self, default=None, selected=None, hovered=None, dragging=None):
        """Set all edge colors at once

        :param default: Default edge color
        :param selected: Selected edge color
        :param hovered: Hovered edge color
        :param dragging: Dragging edge color
        """
        if default is not None:
            self.default = default
        if selected is not None:
            self.selected = selected
        if hovered is not None:
            self.hovered = hovered
        if dragging is not None:
            self.dragging = dragging


class SocketColors(BaseColors):
    """Configuration for Socket colors"""

    def __init__(self):
        """Initialize default socket colors"""
        self._socket_type_colors = [
            QColor("#FFFF7700"),  # Orange
            QColor("#FF52e220"),  # Green
            QColor("#FF0056a6"),  # Blue
            QColor("#FFa86db1"),  # Purple
            QColor("#FFb54747"),  # Red
            QColor("#FFdbe220"),  # Yellow
            QColor("#FF888888"),  # Gray
            QColor("#FFFF7700"),  # Orange (duplicate)
            QColor("#FF52e220"),  # Green (duplicate)
            QColor("#FF0056a6"),  # Blue (duplicate)
            QColor("#FFa86db1"),  # Purple (duplicate)
            QColor("#FFb54747"),  # Red (duplicate)
            QColor("#FFdbe220"),  # Yellow (duplicate)
            QColor("#FF888888"),  # Gray (duplicate)
        ]
        self._outline = QColor("#FF000000")
        self._highlight = QColor("#FF37A6FF")

    @property
    def outline(self) -> QColor:
        """Get socket outline color"""
        return QColor(self._outline)

    @outline.setter
    def outline(self, color):
        """Set socket outline color"""
        self._outline = self._parse_color(color)

    @property
    def highlight(self) -> QColor:
        """Get socket highlight color"""
        return QColor(self._highlight)

    @highlight.setter
    def highlight(self, color):
        """Set socket highlight color"""
        self._highlight = self._parse_color(color)

    def get_type_color(self, socket_type: int) -> QColor:
        """Get color for a specific socket type

        :param socket_type: Socket type index
        :return: QColor for the socket type
        """
        if isinstance(socket_type, int):
            return QColor(self._socket_type_colors[socket_type % len(self._socket_type_colors)])
        elif isinstance(socket_type, str):
            return QColor(socket_type)
        return QColor(0, 0, 0, 0)

    def set_type_color(self, socket_type: int, color):
        """Set color for a specific socket type

        :param socket_type: Socket type index
        :param color: Color to set
        """
        self._socket_type_colors[socket_type] = self._parse_color(color)

    def set_type_colors(self, colors: List) -> None:
        """Set all socket type colors at once

        :param colors: List of colors
        """
        self._socket_type_colors = [self._parse_color(c) for c in colors]

    def get_all_type_colors(self) -> List[QColor]:
        """Get all socket type colors

        :return: List of QColor objects
        """
        return [QColor(c) for c in self._socket_type_colors]

    def set_all(self, outline=None, highlight=None, type_colors=None):
        """Set all socket colors at once

        :param outline: Socket outline color
        :param highlight: Socket highlight color
        :param type_colors: List of socket type colors
        """
        if outline is not None:
            self.outline = outline
        if highlight is not None:
            self.highlight = highlight
        if type_colors is not None:
            self.set_type_colors(type_colors)

class NodesColors(BaseColors):
    """Configuration for Node colors

    This class reuses the EdgeColors structure to define colors for nodes.
    """

    def __init__(self):
        """Initialize default node colors"""
        super().__init__()


class NodeEditorColorScheme:
    """Global color scheme configuration for Node Editor

    This class provides a centralized way to manage and update all colors
    used in the node editor, including edge colors and socket colors.

    Example:
        >>> scheme = NodeEditorColorScheme()
        >>> scheme.edges.default = "#FF0000"  # Red edges
        >>> scheme.sockets.highlight = "#00FF00"  # Green highlights
    """

    _instance = None

    def __new__(cls):
        """Singleton pattern - ensure only one instance exists"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize color scheme (only once)"""
        if self._initialized:
            return

        self.edges = EdgeColors()
        self.sockets = SocketColors()
        self.nodes = NodesColors()  # Reusing EdgeColors for node colors
        self._initialized = True

    @classmethod
    def get_instance(cls) -> 'NodeEditorColorScheme':
        """Get the singleton instance of the color scheme

        :return: NodeEditorColorScheme instance
        """
        return cls()

    def reset_to_defaults(self):
        """Reset all colors to their default values"""
        self.edges = EdgeColors()
        self.sockets = SocketColors()
        self.nodes = NodesColors()

    def to_dict(self) -> Dict:
        """Export current color scheme to dictionary

        :return: Dictionary representation of the color scheme
        """
        return {
            'edges': {
                'default': self.edges.default.name(),
                'selected': self.edges.selected.name(),
                'hovered': self.edges.hovered.name(),
                'dragging': self.edges.dragging.name(),
            },
            'sockets': {
                'outline': self.sockets.outline.name(),
                'highlight': self.sockets.highlight.name(),
                'type_colors': [c.name() for c in self.sockets.get_all_type_colors()],
            }
        }

    def from_dict(self, config: Dict):
        """Import color scheme from dictionary

        :param config: Dictionary with color configuration
        """
        if 'edges' in config:
            edge_config = config['edges']
            self.edges.set_all(
                default=edge_config.get('default'),
                selected=edge_config.get('selected'),
                hovered=edge_config.get('hovered'),
                dragging=edge_config.get('dragging')
            )

        if 'sockets' in config:
            socket_config = config['sockets']
            self.sockets.set_all(
                outline=socket_config.get('outline'),
                highlight=socket_config.get('highlight'),
                type_colors=socket_config.get('type_colors')
            )

# Global singleton instance
_global_scheme = None


def get_color_scheme() -> NodeEditorColorScheme:
    """Get the global color scheme instance

    :return: NodeEditorColorScheme instance
    """
    global _global_scheme
    if _global_scheme is None:
        _global_scheme = NodeEditorColorScheme()
    return _global_scheme
