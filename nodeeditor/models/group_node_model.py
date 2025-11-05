"""
GroupNodeModel - MVC Model for GroupNode containers.

A GroupNodeModel represents the state of a visual node grouping container.
It tracks group properties, child nodes, collapse state, and emits signals
when group state changes.

Signals:
    titleChanged: Emitted when group title changes (str)
    collapsedChanged: Emitted when collapse state changes (bool)
    boundariesChanged: Emitted when group boundaries change (QRectF)
    childNodesChanged: Emitted when child nodes list changes (List[int])
    positionChanged: Emitted when position changes (QPointF)
    sizeChanged: Emitted when size changes (QSizeF)
    removed: Emitted when group is removed from scene
"""

from typing import Dict, List, Optional, Tuple, Union
import logging

from qtpy.QtCore import QObject, Signal, QPointF, QSizeF, QRectF
from qtpy.QtGui import QColor

logger = logging.getLogger(__name__)


class GroupNodeModel(QObject):
    """
    Model representing a group node (visual container for grouping nodes).

    A GroupNodeModel tracks the state of a visual container that groups
    nodes together. It is NOT a network node, but a visual organization tool.

    Signals:
        titleChanged(str): Emitted when group title changes
        collapsedChanged(bool): Emitted when collapse state changes
        boundariesChanged(QRectF): Emitted when boundaries change
        childNodesChanged(List[int]): Emitted when child nodes change
        positionChanged(QPointF): Emitted when position changes
        sizeChanged(QSizeF): Emitted when size changes
        removed: Emitted when group is removed

    Attributes:
        id (int): Unique identifier for the group
        title (str): Display title of the group
        x (float): X coordinate of group position
        y (float): Y coordinate of group position
        width (float): Width of group container
        height (float): Height of group container
        is_collapsed (bool): Whether group is collapsed
        child_node_ids (List[int]): IDs of child nodes
    """

    # Qt Signals
    titleChanged = Signal(str)
    collapsedChanged = Signal(bool)
    boundariesChanged = Signal(QRectF)
    childNodesChanged = Signal(list)
    positionChanged = Signal(QPointF)
    sizeChanged = Signal(QSizeF)
    removed = Signal()

    def __init__(self, group_id: Optional[int], title: str = "Group", 
                 x: float = 0, y: float = 0, 
                 width: float = 200, height: float = 150) -> None:
        """
        Initialize a new GroupNodeModel.

        Args:
            group_id: Unique identifier for this group
            title: Display title of the group
            x: X coordinate of group position
            y: Y coordinate of group position
            width: Width of group container
            height: Height of group container
        """
        super().__init__()

        # Legacy support: allow GroupNodeModel("Title") invocation
        if isinstance(group_id, str) and title == "Group":
            title = group_id
            group_id = None

        self.id: int = int(group_id) if isinstance(group_id, int) else id(self)
        self._title: str = title
        self._x: float = x
        self._y: float = y
        self._width: float = width
        self._height: float = height
        self._is_collapsed: bool = False
        self._child_node_ids: List[int] = []
        
        # Visual properties
        self._color: QColor = QColor(100, 100, 100, 200)
        self._title_color: QColor = QColor(255, 255, 255)
        self._border_color: QColor = QColor(50, 50, 50)
        self._border_width: int = 2
        self._corner_radius: int = 5
        self._title_bar_height: int = 30
        
        # Collapse/expand state storage
        self._original_node_states: Dict[int, Dict] = {}

    @property
    def title(self) -> str:
        """Get the group title."""
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        """Set the group title and emit signal."""
        if self._title != value:
            self._title = value
            self.titleChanged.emit(value)

    @property
    def x(self) -> float:
        """Get X coordinate."""
        return self._x

    @x.setter
    def x(self, value: float) -> None:
        """Set X coordinate and emit signal."""
        if self._x != value:
            self._x = value
            self.positionChanged.emit(QPointF(self._x, self._y))

    @property
    def y(self) -> float:
        """Get Y coordinate."""
        return self._y

    @y.setter
    def y(self, value: float) -> None:
        """Set Y coordinate and emit signal."""
        if self._y != value:
            self._y = value
            self.positionChanged.emit(QPointF(self._x, self._y))

    @property
    def width(self) -> float:
        """Get group width."""
        return self._width

    @width.setter
    def width(self, value: float) -> None:
        """Set group width and emit signal."""
        if self._width != value:
            self._width = value
            self.sizeChanged.emit(QSizeF(self._width, self._height))
            self.boundariesChanged.emit(self.rect)

    @property
    def height(self) -> float:
        """Get group height."""
        return self._height

    @height.setter
    def height(self, value: float) -> None:
        """Set group height and emit signal."""
        if self._height != value:
            self._height = value
            self.sizeChanged.emit(QSizeF(self._width, self._height))
            self.boundariesChanged.emit(self.rect)

    @property
    def position(self) -> QPointF:
        """Get position as QPointF."""
        return QPointF(self._x, self._y)

    @position.setter
    def position(self, pos: QPointF) -> None:
        """Set position and emit signal."""
        if self._x != pos.x() or self._y != pos.y():
            self._x = pos.x()
            self._y = pos.y()
            self.positionChanged.emit(pos)

    @property
    def size(self) -> QSizeF:
        """Get size as QSizeF."""
        return QSizeF(self._width, self._height)

    @size.setter
    def size(self, sz: QSizeF) -> None:
        """Set size and emit signal."""
        if self._width != sz.width() or self._height != sz.height():
            self._width = sz.width()
            self._height = sz.height()
            self.sizeChanged.emit(sz)
            self.boundariesChanged.emit(self.rect)

    @property
    def rect(self) -> QRectF:
        """Get bounding rectangle."""
        return QRectF(self._x, self._y, self._width, self._height)

    @property
    def is_collapsed(self) -> bool:
        """Check if group is collapsed."""
        return self._is_collapsed

    @is_collapsed.setter
    def is_collapsed(self, value: bool) -> None:
        """Set collapse state and emit signal."""
        if self._is_collapsed != value:
            self._is_collapsed = value
            self.collapsedChanged.emit(value)

    @property
    def child_node_ids(self) -> List[int]:
        """Get list of child node IDs."""
        return self._child_node_ids.copy()

    def add_child_node(self, node_id: int) -> None:
        """
        Add a child node ID to this group.

        Args:
            node_id: ID of the node to add
        """
        if node_id not in self._child_node_ids:
            self._child_node_ids.append(node_id)
            self.childNodesChanged.emit(self._child_node_ids.copy())

    def remove_child_node(self, node_id: int) -> None:
        """
        Remove a child node ID from this group.

        Args:
            node_id: ID of the node to remove
        """
        if node_id in self._child_node_ids:
            self._child_node_ids.remove(node_id)
            self.childNodesChanged.emit(self._child_node_ids.copy())

    def clear_children(self) -> None:
        """Clear all child nodes."""
        if self._child_node_ids:
            self._child_node_ids.clear()
            self.childNodesChanged.emit([])

    @property
    def color(self) -> QColor:
        """Get the group color."""
        return self._color

    @color.setter
    def color(self, value: QColor) -> None:
        """Set the group color."""
        self._color = value

    @property
    def title_color(self) -> QColor:
        """Get the title text color."""
        return self._title_color

    @title_color.setter
    def title_color(self, value: QColor) -> None:
        """Set the title text color."""
        self._title_color = value

    @property
    def border_color(self) -> QColor:
        """Get the border color."""
        return self._border_color

    @border_color.setter
    def border_color(self, value: QColor) -> None:
        """Set the border color."""
        self._border_color = value

    @property
    def border_width(self) -> int:
        """Get the border width."""
        return self._border_width

    @border_width.setter
    def border_width(self, value: int) -> None:
        """Set the border width."""
        self._border_width = value

    @property
    def corner_radius(self) -> int:
        """Get the corner radius."""
        return self._corner_radius

    @corner_radius.setter
    def corner_radius(self, value: int) -> None:
        """Set the corner radius."""
        self._corner_radius = value

    @property
    def title_bar_height(self) -> int:
        """Get the title bar height."""
        return self._title_bar_height

    @title_bar_height.setter
    def title_bar_height(self, value: int) -> None:
        """Set the title bar height."""
        self._title_bar_height = value

    @property
    def original_node_states(self) -> Dict[int, Dict]:
        """Get the stored original node states for collapse/expand."""
        return self._original_node_states.copy()

    def set_original_node_states(self, states: Dict[int, Dict]) -> None:
        """
        Set the stored original node states for collapse/expand.

        Args:
            states: Dictionary mapping node IDs to their original states
        """
        self._original_node_states = states.copy()

    def set_boundaries(self, x: float, y: float, width: float, height: float) -> None:
        """
        Update position and size in one call.

        Args:
            x: X coordinate
            y: Y coordinate
            width: Width of group
            height: Height of group
        """
        pos_changed = (self._x != x or self._y != y)
        size_changed = (self._width != width or self._height != height)
        
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        
        if pos_changed:
            self.positionChanged.emit(QPointF(self._x, self._y))
        if size_changed:
            self.sizeChanged.emit(QSizeF(self._width, self._height))
        
        self.boundariesChanged.emit(self.rect)

    def serialize(self) -> dict:
        """
        Serialize the group node model to a dictionary.

        Returns:
            Dictionary with all group properties
        """
        return {
            "id": self.id,
            "type": "GroupNode",
            "title": self._title,
            "x": self._x,
            "y": self._y,
            "width": self._width,
            "height": self._height,
            "is_collapsed": self._is_collapsed,
            "child_node_ids": self._child_node_ids.copy(),
            "color": self._color.getRgb(),
            "title_color": self._title_color.getRgb(),
            "border_color": self._border_color.getRgb(),
            "border_width": self._border_width,
            "corner_radius": self._corner_radius,
            "title_bar_height": self._title_bar_height,
            "original_node_states": self._serialize_node_states(),
        }

    def _serialize_node_states(self) -> dict:
        """
        Serialize node states for storage.

        Returns:
            Dictionary with serialized node states
        """
        serialized = {}
        for node_id, state in self._original_node_states.items():
            relative_pos = state.get("relative_position")
            if (
                relative_pos is not None
                and hasattr(relative_pos, "x")
                and hasattr(relative_pos, "y")
            ):
                rel_pos_value = (relative_pos.x(), relative_pos.y())
            else:
                rel_pos_value = relative_pos

            serialized[str(node_id)] = {
                "relative_position": rel_pos_value,
                "width": state.get("width"),
                "height": state.get("height"),
                "scale": state.get("scale", 1.0),
                "was_visible": state.get("was_visible", True),
            }
        return serialized

    def deserialize(self, data: dict, restore_id: bool = True) -> bool:
        """
        Deserialize the group node model from a dictionary.

        Args:
            data: Dictionary with serialized properties
            restore_id: Whether to restore the ID from data

        Returns:
            True if successful, False otherwise
        """
        try:
            if restore_id and 'id' in data:
                self.id = data['id']

            self._title = data.get('title', 'Group')
            self._x = data.get('x', 0)
            self._y = data.get('y', 0)
            self._width = data.get('width', 200)
            self._height = data.get('height', 150)
            self._is_collapsed = data.get('is_collapsed', False)
            self._child_node_ids = data.get('child_node_ids', []).copy()
            self._border_width = data.get('border_width', 2)
            self._corner_radius = data.get('corner_radius', 5)
            self._title_bar_height = data.get('title_bar_height', 30)

            # Restore colors if present
            if 'color' in data and isinstance(data['color'], (list, tuple)):
                self._color = QColor(*data['color'])
            if 'title_color' in data and isinstance(data['title_color'], (list, tuple)):
                self._title_color = QColor(*data['title_color'])
            if 'border_color' in data and isinstance(data['border_color'], (list, tuple)):
                self._border_color = QColor(*data['border_color'])

            # Restore original node states if available
            if "original_node_states" in data:
                self._original_node_states = self._deserialize_node_states(
                    data["original_node_states"]
                )

            return True
        except Exception as e:
            logger.error(f"Failed to deserialize GroupNodeModel: {e}")
            return False

    def _deserialize_node_states(self, serialized: dict) -> Dict[int, Dict]:
        """
        Deserialize node states from storage.

        Args:
            serialized: Dictionary with serialized states

        Returns:
            Dictionary with deserialized states
        """
        states = {}
        for node_id_str, state_data in serialized.items():
            try:
                node_id = int(node_id_str)
                relative_pos = state_data.get("relative_position")
                
                if isinstance(relative_pos, (list, tuple)):
                    relative_pos = QPointF(relative_pos[0], relative_pos[1])

                states[node_id] = {
                    "relative_position": relative_pos,
                    "width": state_data.get("width"),
                    "height": state_data.get("height"),
                    "scale": state_data.get("scale", 1.0),
                    "was_visible": state_data.get("was_visible", True),
                }
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to deserialize node state {node_id_str}: {e}")
                continue
        
        return states
