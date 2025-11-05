"""
NodeModel - MVC Model for representing nodes in the scene.

A NodeModel stores all data related to a node including its identity,
position, title, and custom properties. It emits signals when data changes,
allowing views and controllers to react to updates.

Signals:
    titleChanged: Emitted when node title changes (str)
    positionChanged: Emitted when node position changes (QPointF)
    propertyChanged: Emitted when custom property changes (str, Any)
    selectedChanged: Emitted when selection state changes (bool)
    visibleChanged: Emitted when visibility state changes (bool)
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import logging

from qtpy.QtCore import QPointF, QObject, Signal

logger = logging.getLogger(__name__)


class NodeModel(QObject):
    """
    Model representing a node in the scene.

    A NodeModel is a pure data object that represents the state of a node.
    It does not contain any graphics rendering code. When data changes,
    it emits signals that views and controllers can connect to.

    Signals:
        titleChanged(str): Emitted when title is changed
        positionChanged(QPointF): Emitted when position is changed
        propertyChanged(str, object): Emitted when custom property is changed
        selectedChanged(bool): Emitted when selection state changes
        visibleChanged(bool): Emitted when visibility state changes

    Example:
        >>> node = NodeModel("MyNodeType", "My Node")
        >>> node.titleChanged.connect(lambda title: print(f"Title: {title}"))
        >>> node.title = "Updated Title"  # Emits titleChanged signal
        Title: Updated Title
    """

    # Qt Signals
    titleChanged = Signal(str)
    positionChanged = Signal(QPointF)
    propertyChanged = Signal(str, object)
    selectedChanged = Signal(bool)
    visibleChanged = Signal(bool)

    def __init__(
        self,
        node_type: str,
        title: str = "Node",
        node_id: Optional[int] = None,
    ) -> None:
        """
        Initialize a new NodeModel.

        Args:
            node_type: Type identifier for this node (e.g., "add_node", "multiply_node")
            title: Display name for the node, defaults to "Node"
            node_id: Optional unique identifier, auto-generated if not provided

        Raises:
            ValueError: If node_type is empty
        """
        super().__init__()

        if not node_type or not isinstance(node_type, str):
            raise ValueError("node_type must be a non-empty string")

        self._id: int = node_id or id(self)
        self._type: str = node_type
        self._title: str = str(title)
        self._x: float = 0.0
        self._y: float = 0.0
        self._properties: Dict[str, Any] = {}
        self._selected: bool = False
        self._visible: bool = True
        self._sockets: List = []  # Track all sockets belonging to this node

    @property
    def id(self) -> int:
        """
        Get the unique identifier for this node (read-only).

        Returns:
            Unique node ID (UUID string)
        """
        return self._id

    @property
    def node_type(self) -> str:
        """
        Get the node type identifier (read-only).

        Returns:
            Type identifier string (e.g., "add_node", "multiply_node")
        """
        return self._type

    @property
    def title(self) -> str:
        """
        Get the node's display title.

        Returns:
            Current title string
        """
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        """
        Set the node's display title.

        Emits titleChanged signal if value changed.

        Args:
            value: New title string

        Raises:
            TypeError: If value is not a string
        """
        if not isinstance(value, str):
            raise TypeError(f"title must be str, got {type(value).__name__}")

        if self._title != value:
            self._title = value
            self.titleChanged.emit(value)

    @property
    def position(self) -> Tuple[float, float]:
        """
        Get the node's position as (x, y) tuple.

        Returns:
            Tuple of (x, y) coordinates as floats
        """
        return (self._x, self._y)

    @position.setter
    def position(self, value: Union[Tuple[float, float], QPointF]) -> None:
        """
        Set the node's position.

        Emits positionChanged signal if position changed.

        Args:
            value: Either (x, y) tuple or QPointF object

        Raises:
            TypeError: If value is not tuple or QPointF
            ValueError: If tuple doesn't have 2 elements
        """
        if isinstance(value, QPointF):
            x, y = float(value.x()), float(value.y())
        elif isinstance(value, (tuple, list)) and len(value) == 2:
            x, y = float(value[0]), float(value[1])
        else:
            raise TypeError(
                f"position must be tuple(x, y) or QPointF, got {type(value).__name__}"
            )

        if self._x != x or self._y != y:
            self._x = x
            self._y = y
            self.positionChanged.emit(QPointF(x, y))

    @property
    def x(self) -> float:
        """
        Get the node's X coordinate.

        Returns:
            X position as float
        """
        return self._x

    @x.setter
    def x(self, value: float) -> None:
        """
        Set the node's X coordinate.

        Emits positionChanged signal if value changed.

        Args:
            value: New X coordinate

        Raises:
            TypeError: If value cannot be converted to float
        """
        try:
            new_x = float(value)
        except (TypeError, ValueError) as e:
            raise TypeError(f"x must be numeric, got {type(value).__name__}") from e

        if self._x != new_x:
            self._x = new_x
            self.positionChanged.emit(QPointF(self._x, self._y))

    @property
    def y(self) -> float:
        """
        Get the node's Y coordinate.

        Returns:
            Y position as float
        """
        return self._y

    @y.setter
    def y(self, value: float) -> None:
        """
        Set the node's Y coordinate.

        Emits positionChanged signal if value changed.

        Args:
            value: New Y coordinate

        Raises:
            TypeError: If value cannot be converted to float
        """
        try:
            new_y = float(value)
        except (TypeError, ValueError) as e:
            raise TypeError(f"y must be numeric, got {type(value).__name__}") from e

        if self._y != new_y:
            self._y = new_y
            self.positionChanged.emit(QPointF(self._x, self._y))

    @property
    def selected(self) -> bool:
        """
        Get whether the node is currently selected.

        Returns:
            True if selected, False otherwise
        """
        return self._selected

    @selected.setter
    def selected(self, value: bool) -> None:
        """
        Set the node's selection state.

        Emits selectedChanged signal if state changed.

        Args:
            value: True to select, False to deselect

        Raises:
            TypeError: If value is not boolean
        """
        if not isinstance(value, bool):
            raise TypeError(f"selected must be bool, got {type(value).__name__}")

        if self._selected != value:
            self._selected = value
            self.selectedChanged.emit(value)

    @property
    def visible(self) -> bool:
        """
        Get whether the node is currently visible.

        Returns:
            True if visible, False otherwise
        """
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        """
        Set the node's visibility state.

        Emits visibleChanged signal if state changed.

        Args:
            value: True to show, False to hide

        Raises:
            TypeError: If value is not boolean
        """
        if not isinstance(value, bool):
            raise TypeError(f"visible must be bool, got {type(value).__name__}")

        if self._visible != value:
            self._visible = value
            self.visibleChanged.emit(value)

    @property
    def is_selected(self) -> bool:
        """
        Alias for selected property.

        Returns:
            True if selected, False otherwise
        """
        return self._selected

    @is_selected.setter
    def is_selected(self, value: bool) -> None:
        """
        Alias setter for selected property.

        Args:
            value: True to select, False to deselect
        """
        self.selected = value

    @property
    def is_visible(self) -> bool:
        """
        Alias for visible property.

        Returns:
            True if visible, False otherwise
        """
        return self._visible

    @is_visible.setter
    def is_visible(self, value: bool) -> None:
        """
        Alias setter for visible property.

        Args:
            value: True to show, False to hide
        """
        self.visible = value

    def set_property(self, key: str, value: Any) -> None:
        """
        Set a custom property on the node.

        Custom properties allow storing arbitrary data. Emits propertyChanged
        signal if value changed.

        Args:
            key: Property key/name
            value: Property value (can be any serializable type)

        Raises:
            TypeError: If key is not a string
        """
        if not isinstance(key, str):
            raise TypeError(f"property key must be str, got {type(key).__name__}")

        if self._properties.get(key) != value:
            self._properties[key] = value
            self.propertyChanged.emit(key, value)

    def get_property(self, key: str, default: Any = None) -> Any:
        """
        Get a custom property from the node.

        Args:
            key: Property key/name
            default: Default value if key not found

        Returns:
            Property value, or default if not found

        Raises:
            TypeError: If key is not a string
        """
        if not isinstance(key, str):
            raise TypeError(f"property key must be str, got {type(key).__name__}")

        return self._properties.get(key, default)

    def has_property(self, key: str) -> bool:
        """
        Check if a custom property exists.

        Args:
            key: Property key/name

        Returns:
            True if property exists, False otherwise
        """
        return key in self._properties

    def remove_property(self, key: str) -> bool:
        """
        Remove a custom property.

        Args:
            key: Property key/name

        Returns:
            True if property was removed, False if it didn't exist
        """
        if key in self._properties:
            del self._properties[key]
            return True
        return False

    def get_all_properties(self) -> Dict[str, Any]:
        """
        Get all custom properties as a dictionary.

        Returns a copy to prevent external modification.

        Returns:
            Dictionary of all custom properties
        """
        return dict(self._properties)

    def serialize(self) -> Dict[str, Any]:
        """
        Serialize the node model to a dictionary.

        Used for saving/loading nodes to/from files. The returned dictionary
        can be serialized to JSON and later deserialized.

        Returns:
            Dictionary containing all node data
        """
        return {
            'id': self._id,
            'type': self._type,
            'title': self._title,
            'x': self._x,
            'y': self._y,
            'properties': dict(self._properties),
            'selected': self._selected,
            'visible': self._visible,
        }

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> 'NodeModel':
        """
        Deserialize a node model from a dictionary.

        Creates a new NodeModel instance from serialized data.

        Args:
            data: Dictionary containing node data

        Returns:
            New NodeModel instance

        Raises:
            KeyError: If required keys are missing
            ValueError: If data is invalid
            TypeError: If data is not a dictionary
        """
        if not isinstance(data, dict):
            raise TypeError(f"data must be dict, got {type(data).__name__}")

        try:
            node = cls(
                node_type=data['type'],
                title=data.get('title', 'Node'),
                node_id=data.get('id'),
            )
            node.position = (data.get('x', 0.0), data.get('y', 0.0))
            node._properties = dict(data.get('properties', {}))
            node._selected = bool(data.get('selected', False))
            node._visible = bool(data.get('visible', True))
            return node
        except KeyError as e:
            raise ValueError(f"Missing required field in node data: {e}") from e

    def __repr__(self) -> str:
        """Return string representation of the node model."""
        return (
            f"NodeModel(id={self._id!r}, type={self._type!r}, "
            f"title={self._title!r}, pos=({self._x}, {self._y}))"
        )

    def __str__(self) -> str:
        """Return human-readable string of the node model."""
        return f"{self._type}: {self._title}"

    def __eq__(self, other: Any) -> bool:
        """Check equality based on node ID."""
        if not isinstance(other, NodeModel):
            return False
        return self._id == other._id

    def __hash__(self) -> int:
        """Make NodeModel hashable for use in sets/dicts."""
        return hash(self._id)
