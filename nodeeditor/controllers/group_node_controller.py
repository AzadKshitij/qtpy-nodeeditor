"""
GroupNodeController - MVC Controller for managing GroupNode operations.

The GroupNodeController coordinates operations on GroupNodeModel and handles
business logic for group management including collapse/expand, node management,
and boundary updates.
"""

from typing import TYPE_CHECKING, List, Optional
import logging

from qtpy.QtCore import QObject, QPointF, QSizeF, QRectF, Signal

from nodeeditor.models.group_node_model import GroupNodeModel

if TYPE_CHECKING:
    from nodeeditor.models.node_model import NodeModel
    from nodeeditor.models.scene_model import SceneModel

logger = logging.getLogger(__name__)


class GroupNodeController(QObject):
    """
    Controller for managing GroupNode operations.

    Coordinates between GroupNodeModel and the view, handles collapse/expand
    logic, child node management, and boundary calculations.

    Attributes:
        model: The GroupNodeModel this controller manages
        scene_model: Reference to the SceneModel for node lookups
    """

    def __init__(self, model: GroupNodeModel, scene_model: Optional['SceneModel'] = None) -> None:
        """
        Initialize the GroupNodeController.

        Args:
            model: The GroupNodeModel to manage
            scene_model: Reference to SceneModel for node resolution
        """
        super().__init__(model)
        self.model: GroupNodeModel = model
        self.scene_model: Optional['SceneModel'] = scene_model

    def add_node(self, node_model: 'NodeModel') -> None:
        """
        Add a node to the group.

        Args:
            node_model: The NodeModel to add
        """
        if node_model and hasattr(node_model, 'id'):
            self.model.add_child_node(node_model.id)
    
    def add_node_by_id(self, id: int):
        """
        Add node by ID

        Args:
            id (int): id for the node to add
        """
        self.model.add_child_node(id)

    def remove_node(self, node_model: 'NodeModel') -> None:
        """
        Remove a node from the group.

        Args:
            node_model: The NodeModel to remove
        """
        if node_model and hasattr(node_model, 'id'):
            self.model.remove_child_node(node_model.id)

    def set_title(self, title: str) -> None:
        """
        Set the group title.

        Args:
            title: New title for the group
        """
        self.model.title = title

    def collapse(self) -> None:
        """Collapse the group."""
        if not self.model.is_collapsed:
            self.model.is_collapsed = True

    def expand(self) -> None:
        """Expand the group."""
        if self.model.is_collapsed:
            self.model.is_collapsed = False

    def toggle_collapse(self) -> None:
        """Toggle between collapsed and expanded state."""
        self.model.is_collapsed = not self.model.is_collapsed

    def set_position(self, x: float, y: float) -> None:
        """
        Set the group position.

        Args:
            x: X coordinate
            y: Y coordinate
        """
        self.model.position = QPointF(x, y)

    def set_size(self, width: float, height: float) -> None:
        """
        Set the group size.

        Args:
            width: Width of the group
            height: Height of the group
        """
        self.model.size = QSizeF(width, height)

    def set_boundaries(self, x: float, y: float, width: float, height: float) -> None:
        """
        Update position and size in one operation.

        Args:
            x: X coordinate
            y: Y coordinate
            width: Width of the group
            height: Height of the group
        """
        self.model.set_boundaries(x, y, width, height)

    def ungroup(self) -> None:
        """Remove the group container while keeping all child nodes."""
        self.model.clear_children()
        self.model.removed.emit()

    def delete_container(self) -> None:
        """Delete the group container and all child nodes."""
        self.model.clear_children()
        self.model.removed.emit()

    def update_boundaries(self, rect: QRectF) -> None:
        """
        Update group boundaries from a rectangle.

        Args:
            rect: The new bounding rectangle
        """
        self.model.set_boundaries(rect.x(), rect.y(), rect.width(), rect.height())

    def set_color(self, r: int, g: int, b: int, a: int = 200) -> None:
        """
        Set the group color.

        Args:
            r: Red component (0-255)
            g: Green component (0-255)
            b: Blue component (0-255)
            a: Alpha component (0-255), default 200
        """
        from qtpy.QtGui import QColor
        self.model.color = QColor(r, g, b, a)

    def set_border_color(self, r: int, g: int, b: int) -> None:
        """
        Set the border color.

        Args:
            r: Red component (0-255)
            g: Green component (0-255)
            b: Blue component (0-255)
        """
        from qtpy.QtGui import QColor
        self.model.border_color = QColor(r, g, b)

    def set_title_color(self, r: int, g: int, b: int) -> None:
        """
        Set the title text color.

        Args:
            r: Red component (0-255)
            g: Green component (0-255)
            b: Blue component (0-255)
        """
        from qtpy.QtGui import QColor
        self.model.title_color = QColor(r, g, b)

    def serialize(self) -> dict:
        """
        Serialize the group node to a dictionary.

        Returns:
            Serialized group node data
        """
        return self.model.serialize()

    def deserialize(self, data: dict, restore_id: bool = True) -> bool:
        """
        Deserialize the group node from a dictionary.

        Args:
            data: Dictionary with serialized data
            restore_id: Whether to restore the ID from data

        Returns:
            True if successful, False otherwise
        """
        return self.model.deserialize(data, restore_id)
