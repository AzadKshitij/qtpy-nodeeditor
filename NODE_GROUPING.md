# Node Grouping Feature

This document describes the node grouping feature that has been added to the qtpy-nodeeditor project.

## Overview

Node grouping allows you to visually group related nodes together into a single container, similar to node grouping in Blender or other node-based editors. Groups can be:
- **Collapsed** - to hide child nodes and edges, reducing visual clutter
- **Expanded** - to show all child nodes
- **Moved** - all child nodes move together with the group
- **Serialized** - groups persist in saved files

## Architecture

### Core Components

#### 1. **GroupNode** (`nodeeditor/node_group_node.py`)
- **Extends**: `QGraphicsRectItem` (not `Node`) - pure visual container
- **Purpose**: Container for grouping nodes together
- **Key attributes**:
  - `child_nodes` - list of nodes in the group
  - `_is_collapsed` - collapse state
  - `title` - group title (shown in title bar)

#### 2. **Node Enhancement** (`nodeeditor/node_node.py`)
- **New attribute**: `parent_group: Optional['GroupNode'] = None`
- **Purpose**: Tracks which group (if any) contains the node

#### 3. **Scene Integration** (`nodeeditor/node_scene.py`)
- **Modified**: `getNodeClassFromData()` method
- **Purpose**: Handles deserialization of GroupNode objects from JSON

## Features

### Basic Operations

#### Creating a Group
```python
from nodeeditor.node_group_node import GroupNode

# Create a group
group = GroupNode(scene, title="My Group", x=100, y=100, width=300, height=200)

# Add nodes to the group
group.addNode(node1)
group.addNode(node2)

# Update group boundaries to fit all nodes
group.updateGroupBoundaries()

# Add to graphics scene
scene.grScene.addItem(group)
```

#### Collapsing/Expanding Groups
```python
# Collapse - hides child nodes and edges
group.collapse()

# Expand - shows child nodes and edges
group.expand()

# Toggle
group.toggleCollapse()

# Check state
if group.isCollapsed():
    print("Group is collapsed")
```

#### Managing Group Membership
```python
# Add a node
group.addNode(node)

# Remove a node
group.removeNode(node)

# Get all child nodes
children = group.getChildNodes()

# Check if node is in a group
if node.parent_group is not None:
    print(f"Node is in group: {node.parent_group.title}")
```

### Automatic Boundary Management

The group automatically:
- **Removes** nodes that move completely outside the group boundary
- **Expands** to fit nodes that partially move outside the boundary

```python
# Triggered automatically when:
# 1. Nodes are moved
# 2. Nodes are removed
# 3. Group boundaries are updated

group.checkAndAutoAdjustBoundaries()
```

### Serialization

Groups are fully serializable and persist in saved files:

```python
# Serialize
data = group.serialize()
# Returns: {
#     'type': 'GroupNode',
#     'title': 'Group Title',
#     'x': 100.0,
#     'y': 100.0,
#     'width': 300.0,
#     'height': 200.0,
#     'is_collapsed': False,
#     'child_node_ids': [node_id1, node_id2, ...],
#     'color': (r, g, b, a),
#     'title_color': (r, g, b, a),
#     'border_color': (r, g, b, a)
# }

# Deserialize
group = GroupNode(scene)
success = group.deserialize(data)
```

## Calculator Example Integration

The calculator example now includes grouping functionality:

### Using Grouping in Calculator

1. **Create nodes** - drag nodes from the node list
2. **Select multiple nodes** - click nodes while holding Shift/Ctrl
3. **Right-click** - on the selected nodes
4. **Select "Group Selected Nodes"** - from the context menu
5. **Group is created** - automatically sized to contain all nodes

### Visual Feedback

- Groups appear as **rounded rectangles** with a title bar
- Title bar shows group name and collapse/expand button
- Groups have **semi-transparent background** (configurable color)
- Groups display a **+/-** indicator for collapse state
- Groups are **selectable and movable** like regular nodes

## Customization

### Custom Group Appearance

```python
from qtpy.QtGui import QColor

group = GroupNode(scene, title="Custom Group")

# Customize colors
group._color = QColor(150, 100, 200, 200)           # Fill color
group._title_color = QColor(255, 255, 255)         # Title text color
group._border_color = QColor(100, 50, 150)         # Border color
group._border_width = 3                             # Border width
group._title_bar_height = 40                        # Title bar height
group._corner_radius = 10                           # Corner radius

group.update()  # Refresh display
```

### Custom Group Factory

For more complex scenarios, use the `GroupNodeFactory`:

```python
from nodeeditor.node_group_utils import GroupNodeFactory

# Create a group with nodes
group = GroupNodeFactory.createGroup(
    scene=scene,
    title="My Group",
    nodes=[node1, node2, node3]
)

# Create from selected nodes
group = GroupNodeFactory.groupSelectedNodes(
    scene=scene,
    title="Selected Group"
)
```

## API Reference

### GroupNode Methods

#### Creation & Management
- `__init__(scene, title, x, y, width, height)` - Create group
- `addNode(node)` - Add node to group
- `removeNode(node)` - Remove node from group
- `getChildNodes()` - Get list of child nodes

#### Boundaries
- `calculateBoundingBox()` - Calculate bbox of all children
- `updateGroupBoundaries()` - Resize group to fit children
- `checkAndAutoAdjustBoundaries()` - Auto-remove/expand

#### State Management
- `collapse()` - Hide child nodes and edges
- `expand()` - Show child nodes and edges
- `toggleCollapse()` - Toggle collapse state
- `isCollapsed()` - Check if collapsed

#### Serialization
- `serialize()` - Export to dict
- `deserialize(data, hashmap, restore_id)` - Import from dict

#### Graphics
- `paint(painter, option, widget)` - Custom painting
- `mouseMoveEvent(event)` - Group + children movement
- `mouseReleaseEvent(event)` - Cleanup

### Node Enhancement

#### New Attribute
- `node.parent_group` - Reference to parent group (or None)

## Implementation Details

### Why GroupNode extends QGraphicsRectItem

GroupNode is intentionally **not** a Node subclass because:

1. **No evaluation** - Groups don't have inputs/outputs/sockets
2. **Pure container** - Groups hold references to nodes, not evaluation data
3. **Graphics layer** - Groups live purely in the graphics scene
4. **No signals** - Groups don't participate in node evaluation signals
5. **Lightweight** - Minimal overhead compared to full Node implementation

### Edge Visibility Management

When collapsing/expanding groups:
- All edges connected to child nodes are hidden/shown
- Edges are found via `node.inputs[i].edges` and `node.outputs[i].edges`
- External edges (connecting to nodes outside the group) remain visible
- Internal edges (between child nodes) are also affected

### Performance Considerations

- **Lazy boundary updates** - Boundaries only recalculate when needed
- **Efficient storage** - Groups store only node references, not copies
- **Graphics optimization** - GroupNode uses QGraphicsRectItem's efficient painting
- **Serialization** - Groups only store node IDs, not full node data

## Testing

### Unit Tests
```bash
python test_groupnode_basic.py
```

### Calculator Example Tests
```bash
python test_grouping_calculator.py
```

### Manual Testing in Calculator
1. Run: `python examples/example_calculator/main.py`
2. Create several nodes
3. Select 2+ nodes (Shift+click)
4. Right-click → "Group Selected Nodes"
5. Test collapse/expand by right-clicking group
6. Save file and reload to verify serialization

## Limitations & Future Enhancements

### Current Limitations
- Groups cannot be nested (groups inside groups)
- No built-in "Ungroup" context menu option
- Groups require manual scene.grScene.addItem() after creation
- Collapse button is visual only (no click handler in current version)

### Planned Enhancements
- [ ] Nested group support
- [ ] Click-to-collapse button
- [ ] Group color/style customization UI
- [ ] Ungroup context menu option
- [ ] Group properties dialog
- [ ] Multi-select group operations
- [ ] Group templates/presets

## Troubleshooting

### Group not appearing
- Ensure `scene.grScene.addItem(group)` is called
- Verify `group.updateGroupBoundaries()` is called before display

### Nodes not moving with group
- Check that `node.parent_group` is set correctly
- Verify `mouseMoveEvent()` is being triggered

### Collapse/expand not working
- Ensure group has child nodes with valid `grNode` graphics items
- Check that edges have valid `grEdge` graphics items

### Serialization issues
- Verify all child nodes are properly serialized
- Check that `child_node_ids` matches actual nodes in scene
- Ensure Scene deserialization recognizes `type: 'GroupNode'`

## Examples

### Complete Example: Group Calculator Nodes

```python
from qtpy.QtWidgets import QApplication
from nodeeditor.node_scene import Scene
from nodeeditor.node_group_node import GroupNode
from examples.example_calculator.nodes.input import CalcNode_Input
from examples.example_calculator.nodes.operations import CalcNode_Add, CalcNode_Multiply
from examples.example_calculator.nodes.output import CalcNode_Output

app = QApplication([])
scene = Scene()

# Create nodes
inp = CalcNode_Input(scene)
inp.setPos(0, 0)

add = CalcNode_Add(scene)
add.setPos(200, 0)

mul = CalcNode_Multiply(scene)
mul.setPos(400, 0)

out = CalcNode_Output(scene)
out.setPos(600, 0)

# Connect
scene.createEdge(inp.outputs[0], add.inputs[0])
scene.createEdge(add.outputs[0], mul.inputs[0])
scene.createEdge(mul.outputs[0], out.inputs[0])

# Create group
group = GroupNode(scene, title="Math Operations")
group.addNode(add)
group.addNode(mul)
group.updateGroupBoundaries()
scene.grScene.addItem(group)

# Now the group contains Add and Multiply nodes
# Collapse the group to hide them
group.collapse()
```

## See Also

- `nodeeditor/node_group_node.py` - Main GroupNode implementation
- `nodeeditor/node_group_utils.py` - Factory and utility functions
- `examples/example_calculator/calc_sub_window.py` - Calculator integration
- `test_groupnode_basic.py` - Unit tests
- `test_grouping_calculator.py` - Integration tests
