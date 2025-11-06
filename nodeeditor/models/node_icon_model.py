"""
NodeIconModel - Extended node model with icon support.

Extends NodeModel to provide icon properties and rendering capabilities.
"""

from typing import Optional
from qtpy.QtGui import QPixmap, QIcon
from nodeeditor.models import NodeModel


class NodeIconModel(NodeModel):
    """
    Node model with icon support.

    Extends NodeModel to add icon properties that can be rendered in
    graphics views and content widgets.

    Attributes:
        icon_path (str): Path to the icon file
        icon_pixmap (QPixmap): Cached pixmap for the icon
        icon_size (tuple): (width, height) size for icon rendering
    """

    def __init__(
        self,
        node_type: str,
        title: str = "Node",
        node_id: Optional[str] = None,
        icon_path: Optional[str] = None,
    ) -> None:
        """
        Initialize a NodeIconModel.

        Args:
            node_type: Type identifier for this node
            title: Display name for the node
            node_id: Optional unique identifier
            icon_path: Optional path to icon file

        Raises:
            ValueError: If node_type is empty
        """
        super().__init__(node_type, title, node_id)
        
        self._icon_path: Optional[str] = icon_path
        self._icon_pixmap: Optional[QPixmap] = None
        self._icon_size: tuple = (64, 64)  # Default icon size
        
        # Try to load the icon if provided
        if icon_path:
            self._load_icon(icon_path)

    def _load_icon(self, path: str) -> bool:
        """
        Load icon from file path.

        Args:
            path: Path to icon file

        Returns:
            True if icon loaded successfully, False otherwise
        """
        try:
            pixmap = QPixmap(path)
            if pixmap.isNull():
                print(f"Warning: Failed to load icon from {path}")
                return False
            
            # Scale to icon size
            self._icon_pixmap = pixmap.scaledToWidth(
                int(self._icon_size[0]),
                Qt.TransformationMode.SmoothTransformation
            )
            self._icon_path = path
            return True
        except Exception as e:
            print(f"Error loading icon {path}: {e}")
            return False

    @property
    def icon_path(self) -> Optional[str]:
        """
        Get the icon file path.

        Returns:
            Path to icon file or None
        """
        return self._icon_path

    @icon_path.setter
    def icon_path(self, value: Optional[str]) -> None:
        """
        Set the icon file path and load it.

        Args:
            value: Path to icon file or None
        """
        if value:
            self._load_icon(value)
        else:
            self._icon_path = None
            self._icon_pixmap = None

    @property
    def icon_pixmap(self) -> Optional[QPixmap]:
        """
        Get the cached icon pixmap.

        Returns:
            QPixmap or None if no icon is loaded
        """
        return self._icon_pixmap

    @property
    def icon_size(self) -> tuple:
        """
        Get the icon rendering size.

        Returns:
            Tuple of (width, height)
        """
        return self._icon_size

    @icon_size.setter
    def icon_size(self, value: tuple) -> None:
        """
        Set the icon rendering size and reload icon.

        Args:
            value: Tuple of (width, height)
        """
        if len(value) != 2 or not all(isinstance(v, (int, float)) for v in value):
            raise ValueError(f"icon_size must be (width, height) tuple, got {value}")
        
        self._icon_size = (float(value[0]), float(value[1]))
        
        # Reload icon with new size
        if self._icon_path:
            self._load_icon(self._icon_path)

    def has_icon(self) -> bool:
        """
        Check if this node has a valid icon loaded.

        Returns:
            True if icon is loaded, False otherwise
        """
        return self._icon_pixmap is not None

    def serialize(self) -> dict:
        """
        Serialize the node to a dictionary.

        Returns:
            Dictionary containing node data including icon path
        """
        data = super().serialize()
        data.update({
            'icon_path': self._icon_path,
            'icon_size': list(self._icon_size),
        })
        return data

    @classmethod
    def deserialize(cls, data: dict, restore_id: bool = True) -> 'NodeIconModel':
        """
        Deserialize a node from dictionary.

        Args:
            data: Dictionary containing node data
            restore_id: Whether to restore the ID from data

        Returns:
            NodeIconModel instance
        """
        node_id = data.get('id') if restore_id else None
        icon_path = data.get('icon_path')
        
        node = cls(
            node_type=data['type'],
            title=data.get('title', 'Node'),
            node_id=node_id,
            icon_path=icon_path,
        )
        
        # Restore other properties
        if 'position' in data:
            node.position = data['position']
        if 'properties' in data:
            for key, value in data['properties'].items():
                node.set_property(key, value)
        if 'icon_size' in data:
            node.icon_size = tuple(data['icon_size'])
        
        return node


# Import Qt after class definition to avoid circular imports
try:
    from qtpy.QtCore import Qt
except ImportError:
    Qt = None
