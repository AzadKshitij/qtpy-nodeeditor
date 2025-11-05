# MVC Architecture Blueprint for qtpy-nodeeditor

## Comprehensive Model-View-Controller Architecture

**Status**: Planning Phase  
**Goal**: Transform into robust MVC library with Qt signals/slots and property decorators

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                         │
├─────────────────────────────────────────────────────────────┤
│  Controllers (Event Handlers, Business Logic)                │
│  ├─ SceneController                                          │
│  ├─ NodeController                                           │
│  ├─ EdgeController                                           │
│  └─ SocketController                                         │
├─────────────────────────────────────────────────────────────┤
│  Models (Data + Qt Signals)                                  │
│  ├─ NodeModel (with property decorators & signals)           │
│  ├─ EdgeModel (with property decorators & signals)           │
│  ├─ SocketModel (with property decorators & signals)         │
│  └─ SceneModel (with property decorators & signals)          │
├─────────────────────────────────────────────────────────────┤
│  Views (Graphics Rendering)                                  │
│  ├─ QDMGraphicsNode                                          │
│  ├─ QDMGraphicsEdge                                          │
│  ├─ QDMGraphicsSocket                                        │
│  └─ QDMGraphicsScene                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### 1. MODEL LAYER (Pure Data + Signals)

**Purpose**: 
- Store and manage all data
- Emit signals on data changes
- No direct graphics rendering

**Components**:

#### `NodeModel`
```python
class NodeModel(QObject):
    """
    Model for Node data with signals and properties.
    
    Signals:
        titleChanged(str)
        positionChanged(QPointF)
        propertyChanged(str, Any)
        selectedChanged(bool)
        visibleChanged(bool)
    """
    
    # Signals
    titleChanged = Signal(str)
    positionChanged = Signal(QPointF)
    propertyChanged = Signal(str, object)
    selectedChanged = Signal(bool)
    visibleChanged = Signal(bool)
    
    def __init__(self, node_type: str, title: str = "Node"):
        super().__init__()
        self._id = generate_uuid()
        self._type = node_type
        self._title = title
        self._x = 0.0
        self._y = 0.0
        self._properties: Dict[str, Any] = {}
        self._selected = False
        self._visible = True
    
    @property
    def id(self) -> str:
        """Unique node identifier (read-only)"""
        return self._id
    
    @property
    def node_type(self) -> str:
        """Node type identifier (read-only)"""
        return self._type
    
    @property
    def title(self) -> str:
        """Node title/name"""
        return self._title
    
    @title.setter
    def title(self, value: str) -> None:
        if self._title != value:
            self._title = value
            self.titleChanged.emit(value)
    
    @property
    def position(self) -> Tuple[float, float]:
        """Node position (x, y)"""
        return (self._x, self._y)
    
    @position.setter
    def position(self, value: Union[Tuple, QPointF]) -> None:
        if isinstance(value, QPointF):
            x, y = value.x(), value.y()
        else:
            x, y = value
        
        if self._x != x or self._y != y:
            self._x = x
            self._y = y
            self.positionChanged.emit(QPointF(x, y))
    
    @property
    def x(self) -> float:
        """Node X coordinate"""
        return self._x
    
    @x.setter
    def x(self, value: float) -> None:
        if self._x != value:
            self._x = float(value)
            self.positionChanged.emit(QPointF(self._x, self._y))
    
    @property
    def y(self) -> float:
        """Node Y coordinate"""
        return self._y
    
    @y.setter
    def y(self, value: float) -> None:
        if self._y != value:
            self._y = float(value)
            self.positionChanged.emit(QPointF(self._x, self._y))
    
    @property
    def selected(self) -> bool:
        """Whether node is selected"""
        return self._selected
    
    @selected.setter
    def selected(self, value: bool) -> None:
        if self._selected != value:
            self._selected = bool(value)
            self.selectedChanged.emit(value)
    
    @property
    def visible(self) -> bool:
        """Whether node is visible"""
        return self._visible
    
    @visible.setter
    def visible(self, value: bool) -> None:
        if self._visible != value:
            self._visible = bool(value)
            self.visibleChanged.emit(value)
    
    def set_property(self, key: str, value: Any) -> None:
        """Set custom property"""
        if self._properties.get(key) != value:
            self._properties[key] = value
            self.propertyChanged.emit(key, value)
    
    def get_property(self, key: str, default: Any = None) -> Any:
        """Get custom property"""
        return self._properties.get(key, default)
    
    def serialize(self) -> Dict[str, Any]:
        """Serialize model to dictionary"""
        return {
            'id': self._id,
            'type': self._type,
            'title': self._title,
            'x': self._x,
            'y': self._y,
            'properties': self._properties,
            'selected': self._selected,
            'visible': self._visible,
        }
    
    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> 'NodeModel':
        """Deserialize model from dictionary"""
        model = cls(data['type'], data['title'])
        model.position = (data['x'], data['y'])
        model._properties = data.get('properties', {})
        model.selected = data.get('selected', False)
        model.visible = data.get('visible', True)
        return model
```

#### `EdgeModel`
```python
class EdgeModel(QObject):
    """Model for Edge data with signals"""
    
    connectionChanged = Signal()
    typeChanged = Signal(int)
    
    def __init__(self):
        super().__init__()
        self._id = generate_uuid()
        self._start_socket: Optional[SocketModel] = None
        self._end_socket: Optional[SocketModel] = None
        self._type = 2  # BEZIER by default
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def start_socket(self) -> Optional['SocketModel']:
        return self._start_socket
    
    @start_socket.setter
    def start_socket(self, value: 'SocketModel') -> None:
        if self._start_socket != value:
            self._start_socket = value
            self.connectionChanged.emit()
    
    @property
    def end_socket(self) -> Optional['SocketModel']:
        return self._end_socket
    
    @end_socket.setter
    def end_socket(self, value: 'SocketModel') -> None:
        if self._end_socket != value:
            self._end_socket = value
            self.connectionChanged.emit()
    
    @property
    def edge_type(self) -> int:
        return self._type
    
    @edge_type.setter
    def edge_type(self, value: int) -> None:
        if self._type != value:
            self._type = int(value)
            self.typeChanged.emit(value)
```

#### `SocketModel`
```python
class SocketModel(QObject):
    """Model for Socket/Port data with signals"""
    
    connectionChanged = Signal(object)  # emits connected edge
    
    def __init__(self, name: str, socket_type: int):
        super().__init__()
        self._id = generate_uuid()
        self._name = name
        self._type = socket_type  # 1=INPUT, 2=OUTPUT
        self._node_model: Optional[NodeModel] = None
        self._edges: List[EdgeModel] = []
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def socket_type(self) -> int:
        return self._type
    
    @property
    def node_model(self) -> Optional[NodeModel]:
        return self._node_model
    
    def add_edge(self, edge: 'EdgeModel') -> None:
        if edge not in self._edges:
            self._edges.append(edge)
            self.connectionChanged.emit(edge)
    
    def remove_edge(self, edge: 'EdgeModel') -> None:
        if edge in self._edges:
            self._edges.remove(edge)
            self.connectionChanged.emit(None)
```

#### `SceneModel`
```python
class SceneModel(QObject):
    """Model for Scene/Graph data with signals"""
    
    nodeAdded = Signal(object)  # NodeModel
    nodeRemoved = Signal(str)   # node_id
    edgeAdded = Signal(object)  # EdgeModel
    edgeRemoved = Signal(str)   # edge_id
    modifiedChanged = Signal(bool)
    
    def __init__(self):
        super().__init__()
        self._nodes: Dict[str, NodeModel] = {}
        self._edges: Dict[str, EdgeModel] = {}
        self._modified = False
    
    @property
    def nodes(self) -> List[NodeModel]:
        return list(self._nodes.values())
    
    @property
    def edges(self) -> List[EdgeModel]:
        return list(self._edges.values())
    
    @property
    def modified(self) -> bool:
        return self._modified
    
    @modified.setter
    def modified(self, value: bool) -> None:
        if self._modified != value:
            self._modified = bool(value)
            self.modifiedChanged.emit(value)
    
    def add_node(self, node: NodeModel) -> None:
        if node.id not in self._nodes:
            self._nodes[node.id] = node
            self.nodeAdded.emit(node)
            self.modified = True
    
    def remove_node(self, node_id: str) -> None:
        if node_id in self._nodes:
            del self._nodes[node_id]
            self.nodeRemoved.emit(node_id)
            self.modified = True
    
    def get_node(self, node_id: str) -> Optional[NodeModel]:
        return self._nodes.get(node_id)
    
    def add_edge(self, edge: EdgeModel) -> None:
        if edge.id not in self._edges:
            self._edges[edge.id] = edge
            self.edgeAdded.emit(edge)
            self.modified = True
    
    def remove_edge(self, edge_id: str) -> None:
        if edge_id in self._edges:
            del self._edges[edge_id]
            self.edgeRemoved.emit(edge_id)
            self.modified = True
```

---

### 2. CONTROLLER LAYER (Business Logic)

**Purpose**:
- Handle user interactions
- Coordinate between Model and View
- Manage application state
- Handle undo/redo

**Components**:

#### `NodeController`
```python
class NodeController(QObject):
    """Controller for Node operations"""
    
    def __init__(self, model: NodeModel, view: QDMGraphicsNode):
        super().__init__()
        self.model = model
        self.view = view
        
        # Connect model signals to view updates
        model.titleChanged.connect(self.on_title_changed)
        model.positionChanged.connect(self.on_position_changed)
        model.selectedChanged.connect(self.on_selected_changed)
        model.visibleChanged.connect(self.on_visible_changed)
    
    def on_title_changed(self, title: str) -> None:
        """Handle title change in model"""
        self.view.set_title(title)
    
    def on_position_changed(self, pos: QPointF) -> None:
        """Handle position change in model"""
        self.view.setPos(pos)
    
    def on_selected_changed(self, selected: bool) -> None:
        """Handle selection change in model"""
        self.view.update_selection_state(selected)
    
    def on_visible_changed(self, visible: bool) -> None:
        """Handle visibility change in model"""
        self.view.setVisible(visible)
    
    def move_node(self, x: float, y: float) -> bool:
        """Move node - coordinates to model"""
        try:
            self.model.position = (x, y)
            return True
        except Exception as e:
            logger.error(f"Failed to move node: {e}")
            return False
    
    def set_title(self, title: str) -> bool:
        """Set node title"""
        try:
            self.model.title = title
            return True
        except Exception as e:
            logger.error(f"Failed to set title: {e}")
            return False
```

#### `EdgeController`
```python
class EdgeController(QObject):
    """Controller for Edge operations"""
    
    def __init__(self, model: EdgeModel, view: QDMGraphicsEdge):
        super().__init__()
        self.model = model
        self.view = view
        
        model.connectionChanged.connect(self.on_connection_changed)
        model.typeChanged.connect(self.on_type_changed)
    
    def on_connection_changed(self) -> None:
        """Handle connection change"""
        self.view.update()
    
    def on_type_changed(self, edge_type: int) -> None:
        """Handle edge type change"""
        self.view.set_edge_type(edge_type)
    
    def connect_sockets(self, 
                       start_socket: SocketModel,
                       end_socket: SocketModel) -> bool:
        """Connect two sockets"""
        try:
            self.model.start_socket = start_socket
            self.model.end_socket = end_socket
            return True
        except Exception as e:
            logger.error(f"Failed to connect sockets: {e}")
            return False
```

#### `SceneController`
```python
class SceneController(QObject):
    """Controller for Scene operations"""
    
    nodeCreated = Signal(object)  # NodeModel
    nodeDeleted = Signal(str)     # node_id
    edgeCreated = Signal(object)  # EdgeModel
    edgeDeleted = Signal(str)     # edge_id
    
    def __init__(self, model: SceneModel):
        super().__init__()
        self.model = model
        self.undo_stack = QUndoStack()
        
        # Connect model signals to controller signals
        model.nodeAdded.connect(self.on_node_added)
        model.nodeRemoved.connect(self.on_node_removed)
        model.edgeAdded.connect(self.on_edge_added)
        model.edgeRemoved.connect(self.on_edge_removed)
    
    def create_node(self, 
                   node_type: str, 
                   title: str = "Node",
                   x: float = 0.0,
                   y: float = 0.0) -> Optional[NodeModel]:
        """Create a new node"""
        try:
            node = NodeModel(node_type, title)
            node.position = (x, y)
            
            # Push undo/redo command
            cmd = NodeCreatedCmd(self.model, node)
            self.undo_stack.push(cmd)
            
            return node
        except Exception as e:
            logger.error(f"Failed to create node: {e}")
            return None
    
    def delete_node(self, node_id: str) -> bool:
        """Delete a node"""
        try:
            node = self.model.get_node(node_id)
            if not node:
                return False
            
            cmd = NodeDeletedCmd(self.model, node)
            self.undo_stack.push(cmd)
            return True
        except Exception as e:
            logger.error(f"Failed to delete node: {e}")
            return False
    
    def on_node_added(self, node: NodeModel) -> None:
        """Handle node added"""
        self.nodeCreated.emit(node)
    
    def on_node_removed(self, node_id: str) -> None:
        """Handle node removed"""
        self.nodeDeleted.emit(node_id)
    
    def on_edge_added(self, edge: EdgeModel) -> None:
        """Handle edge added"""
        self.edgeCreated.emit(edge)
    
    def on_edge_removed(self, edge_id: str) -> None:
        """Handle edge removed"""
        self.edgeDeleted.emit(edge_id)
```

---

### 3. VIEW LAYER (Graphics Rendering)

**Purpose**:
- Render models visually
- Respond to controller updates
- Handle graphics-specific operations

**Key Changes**:
```python
class QDMGraphicsNode(QGraphicsItem):
    """Graphics view for node - responds to model changes"""
    
    def __init__(self, node_model: NodeModel):
        super().__init__()
        self.model = node_model
        
        # Store reference for updates
        self._label = QGraphicsTextItem(self)
        
        # Connect to model changes
        node_model.titleChanged.connect(self.on_title_changed)
        node_model.positionChanged.connect(self.on_position_changed)
        node_model.selectedChanged.connect(self.on_selected_changed)
    
    def on_title_changed(self, title: str) -> None:
        """Update graphics when title changes"""
        self._label.setPlainText(title)
        self.update()
    
    def on_position_changed(self, pos: QPointF) -> None:
        """Update graphics when position changes"""
        self.setPos(pos)
    
    def on_selected_changed(self, selected: bool) -> None:
        """Update graphics when selection changes"""
        self._update_appearance()
```

---

## Implementation Phases

### Phase 1: Core Models with Signals
- [x] Create `NodeModel` with property decorators and signals
- [x] Create `EdgeModel` with signals
- [x] Create `SocketModel` with signals
- [x] Create `SceneModel` with signals
- **Files**: `models/node_model.py`, `models/edge_model.py`, `models/socket_model.py`, `models/scene_model.py`

### Phase 2: Controllers
- [ ] Create `NodeController`
- [ ] Create `EdgeController`
- [ ] Create `SceneController`
- [ ] Implement undo/redo integration
- **Files**: `controllers/node_controller.py`, `controllers/edge_controller.py`, `controllers/scene_controller.py`

### Phase 3: View Refactoring
- [ ] Update `QDMGraphicsNode` to work with `NodeModel`
- [ ] Update `QDMGraphicsEdge` to work with `EdgeModel`
- [ ] Update `QDMGraphicsSocket` to work with `SocketModel`
- [ ] Ensure proper signal connections

### Phase 4: Integration
- [ ] Update `Scene` to use `SceneModel` and `SceneController`
- [ ] Update `Node` to use `NodeModel` and `NodeController`
- [ ] Update `Edge` to use `EdgeModel` and `EdgeController`
- [ ] Update serialization/deserialization

### Phase 5: Documentation
- [ ] Architecture guide
- [ ] MVC pattern explanation
- [ ] API documentation
- [ ] Usage examples

---

## Key Design Principles

### 1. **Separation of Concerns**
- **Model**: Pure data, no graphics, emits signals
- **View**: Graphics rendering, reads from model
- **Controller**: Business logic, coordinates M&V

### 2. **Type Hints Throughout**
- All parameters typed
- All return values typed
- Type hints in properties and methods
- Support for mypy validation

### 3. **Property Decorators**
- Use `@property` for getters
- Use `@setter` for setters
- Emit signals on changes
- Type hints on properties

### 4. **Qt Signals/Slots**
- Models emit signals on changes
- Views connect to model signals
- Controllers coordinate signals
- Automatic UI updates

### 5. **Proper Encapsulation**
- Private attributes (`_name`)
- Public properties (`name`)
- Protected methods (leading underscore for helpers)
- Getters/setters for all data

---

## Benefits of This Architecture

✅ **Clear Separation** - Models, Views, Controllers are independent  
✅ **Type Safe** - Full type hints everywhere  
✅ **Reactive** - Signals/slots for automatic updates  
✅ **Testable** - Models can be tested without graphics  
✅ **Maintainable** - Clear responsibilities  
✅ **Scalable** - Easy to add new node/edge types  
✅ **Professional** - Industry-standard patterns  
✅ **Modern** - Uses Qt best practices  

---

## File Structure

```
nodeeditor/
├── models/
│   ├── __init__.py
│   ├── node_model.py
│   ├── edge_model.py
│   ├── socket_model.py
│   └── scene_model.py
├── controllers/
│   ├── __init__.py
│   ├── node_controller.py
│   ├── edge_controller.py
│   └── scene_controller.py
├── views/
│   ├── __init__.py
│   └── (existing graphics classes, refactored)
├── base/
│   └── (existing core classes)
└── __init__.py
```

---

This blueprint provides a robust MVC architecture with proper separation of concerns, type hints, and Qt signal/slot patterns. Ready to implement?
