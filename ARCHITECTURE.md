# Node Editor Library Architecture

## Overview

The QtPy Node Editor library follows a clean **Model-View-Controller (MVC) architecture** to provide a flexible and maintainable node graph editing framework.

## Directory Structure

```
nodeeditor/
├── models/                  # MVC Model Layer
│   ├── node_model.py
│   ├── node_icon_model.py  # Extended node with icon support
│   ├── edge_model.py
│   ├── socket_model.py
│   ├── scene_model.py
│   ├── group_node_model.py
│   ├── edge_dragging_model.py
│   └── __init__.py
│
├── controllers/             # MVC Controller Layer
│   ├── node_controller.py
│   ├── edge_controller.py
│   ├── socket_controller.py
│   ├── scene_controller.py
│   ├── group_node_controller.py
│   └── __init__.py
│
├── views/                   # MVC View Layer (Graphics)
│   ├── graphics_*.py        # Graphics item implementations
│   ├── content_widgets/     # Custom content widgets
│   │   ├── node_content_widget.py
│   │   ├── node_icon_content_widget.py
│   │   └── __init__.py
│   ├── icons/              # Icon management
│   │   ├── icon_registry.py # Centralized icon cache
│   │   └── __init__.py
│   └── __init__.py
│
├── commands/                # Undo/Redo Commands
│   └── *.py                # Command implementations
│
├── utils/                   # Utility Functions
│   ├── data_conversion.py  # Qt type conversion utilities
│   ├── data_comparison.py  # Deep comparison with tolerance
│   └── __init__.py
│
├── constants.py             # Global constants
├── exceptions.py            # Custom exceptions
├── py.typed                 # PEP 561 marker
└── __init__.py
```

## Architecture Layers

### 1. Model Layer (`models/`)

Pure data objects with **no graphics rendering code**. Each model:
- Stores data with complete type hints
- Emits Qt signals on data changes
- Uses property decorators for encapsulation
- Supports serialization/deserialization

**Key Models:**
- `NodeModel`: Represents a graph node with position, title, properties
- `NodeIconModel`: Extended `NodeModel` with icon support
- `EdgeModel`: Connection between two sockets
- `SocketModel`: Input/output port on a node
- `SceneModel`: Complete graph/scene state
- `GroupNodeModel`: Visual container for organizing nodes
- `EdgeDraggingModel`: State during edge dragging

### 2. Controller Layer (`controllers/`)

Business logic that coordinates between models and views:
- Validates operations
- Manages model state changes
- Coordinates with undo/redo system
- Emits meaningful signals for view updates

**Key Controllers:**
- `NodeController`: Node operations (position, title, properties)
- `EdgeController`: Edge creation, deletion, validation
- `SocketController`: Socket state management
- `SceneController`: Scene-level operations
- `GroupNodeController`: Group management

### 3. View Layer (`views/`)

Graphics representation and rendering:
- `graphics_*.py`: Qt graphics items for rendering
- `content_widgets/`: Custom widgets for node content
- `icons/`: Icon management and caching

### 4. Commands (`commands/`)

Undo/redo command implementations using Qt's `QUndoCommand`:
- Node operations (move, delete, create)
- Edge operations
- Property changes

### 5. Utils (`utils/`)

Helper functions for:
- **Data Conversion**: Qt types ↔ Python types
- **Data Comparison**: Deep comparison with float tolerance
- Type validation and normalization

## Signal Flow

```
User Interaction
    ↓
View/Graphics Item
    ↓
Controller.method()
    ↓
Model.property = value
    ↓
Model emits signal (e.g., positionChanged)
    ↓
Connected slots in:
  - Other models (cross-model updates)
  - Views (graphics updates)
  - History system (undo/redo)
```

## Key Design Patterns

### 1. Property with Signals
```python
@property
def title(self) -> str:
    return self._title

@title.setter
def title(self, value: str) -> None:
    if self._title != value:
        self._title = value
        self.titleChanged.emit(value)  # Qt signal
```

### 2. MVC Separation
- **Model**: Pure data, no graphics knowledge
- **Controller**: Business logic, validation
- **View**: Graphics rendering only

### 3. Type Safety
- Complete type hints throughout
- PEP 561 compatible (py.typed marker)
- Mypy/Pylance compatible

## Utility Examples

### Data Conversion
```python
from nodeeditor.utils import qpointf_to_tuple, tuple_to_qpointf
from qtpy.QtCore import QPointF

point = QPointF(10.0, 20.0)
tuple_point = qpointf_to_tuple(point)  # (10.0, 20.0)
back_to_point = tuple_to_qpointf(tuple_point)  # QPointF(10.0, 20.0)
```

### Data Comparison
```python
from nodeeditor.utils import qpointf_equal, floats_equal

p1 = QPointF(1.0, 2.0)
p2 = QPointF(1.0000001, 2.0000001)
assert qpointf_equal(p1, p2)  # True (within default tolerance)

assert floats_equal(1.0, 1.0000001)  # True
assert not floats_equal(1.0, 1.1)  # False
```

### Icon Management
```python
from nodeeditor.views.icons import get_icon_registry

registry = get_icon_registry()
pixmap = registry.get_icon_from_path("path/to/icon.png", size=(64, 64))
```

### Node with Icon
```python
from nodeeditor.models import NodeIconModel

node = NodeIconModel(
    node_type="calculator",
    title="Add",
    icon_path="icons/add.png"
)

if node.has_icon():
    pixmap = node.icon_pixmap
```

## Migration from Legacy Code

If you have legacy code using old files:

1. **Old graphics classes** → Use models with controllers
2. **Old scene manipulation** → Use `SceneController`
3. **Old node operations** → Use `NodeController`
4. **Type conversions** → Use `nodeeditor.utils` functions

## Adding New Features

### Adding a New Node Type with Icon
1. Extend `NodeIconModel` in `models/`
2. Create a controller in `controllers/` if needed
3. Add graphics item in `views/`
4. Register in appropriate `__init__.py`

### Adding Validation Logic
1. Add validation method in the controller
2. Emit appropriate signals/errors
3. Connect in command classes for undo/redo

### Adding Utilities
1. Add to `utils/data_conversion.py` or `utils/data_comparison.py`
2. Export in `utils/__init__.py`
3. Add tests in `tests/`

## Testing

Run tests with:
```bash
python -m pytest tests/ -v
```

Test categories:
- `test_signal_flow.py`: Signal propagation tests
- `test_*.py`: Individual component tests
