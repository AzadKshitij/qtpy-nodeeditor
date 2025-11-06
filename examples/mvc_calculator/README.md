# MVC Calculator Example

A comprehensive example demonstrating the Model-View-Controller (MVC) architecture applied to a node editor application. This example shows how to build scalable, maintainable applications using the qtpy-nodeeditor framework.

## Architecture Overview

The MVC pattern provides clear separation of concerns:

### Models (`models/`)
Data representations of nodes with no graphics or UI logic:
- `CalcNodeModel`: Base model for all calculator nodes
- `CalcInputNodeModel`: Model for input nodes storing numeric values
- `CalcOutputNodeModel`: Model for output nodes displaying results
- `CalcOperationNodeModel`: Base model for binary operations
- `CalcAddNodeModel`, `CalcSubNodeModel`, `CalcMulNodeModel`, `CalcDivNodeModel`: Specific operation models

**Key Characteristics:**
- Pure data objects extending `NodeModel`
- Emit signals when data changes
- No graphics rendering code
- Easy to test and serialize

### Controllers (`controllers/`)
Business logic and state management:
- `CalcNodeController`: Extends `NodeController` with calculator-specific logic
- Manages node evaluation and value propagation
- Coordinates between models and views
- Handles undo/redo via command pattern

**Key Characteristics:**
- Mediate between models and views
- Implement validation and error handling
- Manage operation workflows
- Generate undo/redo commands

### Views (`views/`)
Graphics representation and user interface:
- `MvcCalcGraphicsNode`: Graphics rendering for nodes
- `MvcCalcInputContent`: UI for input nodes with editable fields
- `MvcCalcOutputContent`: UI for output nodes with display labels
- `MvcCalcOperationContent`: UI for operation nodes

**Key Characteristics:**
- Read-only view of model data
- React to model signal changes
- Handle user interactions
- Manage graphics updates

## Node Types

### Input Node
- **Purpose**: Accept user numeric input
- **Inputs**: None
- **Outputs**: 1 (the entered value)
- **Model**: `CalcInputNodeModel`
- **Widget**: Line edit for value entry

### Output Node
- **Purpose**: Display computed results
- **Inputs**: 1
- **Outputs**: None
- **Model**: `CalcOutputNodeModel`
- **Widget**: Label showing result value

### Operation Nodes
Binary arithmetic operations with automatic evaluation:

#### Add
- **Symbol**: +
- **Inputs**: 2
- **Outputs**: 1 (sum)
- **Class**: `MvcCalcNode_Add`

#### Subtract
- **Symbol**: -
- **Inputs**: 2
- **Outputs**: 1 (difference)
- **Class**: `MvcCalcNode_Sub`

#### Multiply
- **Symbol**: *
- **Inputs**: 2
- **Outputs**: 1 (product)
- **Class**: `MvcCalcNode_Mul`

#### Divide
- **Symbol**: /
- **Inputs**: 2
- **Outputs**: 2 (quotient, remainder)
- **Class**: `MvcCalcNode_Div`

## Usage

### Running the Example

```bash
python examples/mvc_calculator/main.py
```

### Creating a Graph

1. **Create Nodes**:
   - Right-click in the editor and select a node type
   - Or drag from the "Nodes" dock on the right
   - Or double-click on a node type in the dock

2. **Connect Nodes**:
   - Click on an output socket (right side) and drag to an input socket (left side)
   - Edge validators prevent invalid connections:
     - Cannot connect output to output
     - Cannot connect input to input
     - Cannot connect two sockets on the same node

3. **Enter Values**:
   - Double-click an Input node to edit the value
   - Press Enter to confirm

4. **View Results**:
   - Results propagate automatically through connected Output nodes
   - The Output node displays the computed value

### File Operations

- **New**: File → New or Ctrl+N
- **Open**: File → Open or Ctrl+O
- **Save**: File → Save or Ctrl+S
- **Save As**: File → Save As or Ctrl+Shift+S

### Editing

- **Undo**: Edit → Undo or Ctrl+Z
- **Redo**: Edit → Redo or Ctrl+Y
- **Cut**: Edit → Cut or Ctrl+X
- **Copy**: Edit → Copy or Ctrl+C
- **Paste**: Edit → Paste or Ctrl+V
- **Delete**: Edit → Delete or Delete key

### View Options

- **Show Grid**: View → Show Grid (toggle grid visibility)
- **Tile Windows**: Window → Tile (arrange multiple documents)
- **Cascade Windows**: Window → Cascade (stack multiple documents)

## Example Workflow

1. **Simple Addition**:
   ```
   [Input: 5] --→ [+] ←-- [Input: 3]
                    ↓
                 [Output: 8]
   ```

2. **Complex Expression** (e.g., (10 + 5) * 2):
   ```
   [10] → [+] ← [5]
            ↓
           [*] ← [2]
            ↓
        [Output: 30]
   ```

3. **Division with Remainder**:
   ```
   [17] → [/] ← [5]
           ↙     ↖
       [Output]  [Output]
        (3)       (2)
   ```

## Key Features

### Edge Validators
Prevent invalid graph configurations:
- Debug validator: Logs all edge operations
- Two-outputs validator: Prevents output-to-output connections
- Same-node validator: Prevents connections within same node

### Graph Persistence
Save and load calculator graphs in JSON format:
- Preserves node positions, values, and connections
- Supports undo/redo for all operations
- Automatic dirty flag tracking

### Multi-Document Interface (MDI)
- Multiple graphs open simultaneously
- Tabbed or tiled view
- Window menu for navigation

### Drag and Drop
- Drag node types from the Nodes dock to create nodes
- Right-click context menu for node creation

## Extending the Example

### Adding New Node Types

1. **Create a Model** in `models/calc_node_models.py`:
   ```python
   class MyOperationModel(CalcOperationNodeModel):
       def __init__(self, node_id=None):
           super().__init__("my_operation", "My Op", OP_CODE, node_id)
   ```

2. **Create a Node Implementation** in `nodes/mvc_operation_nodes.py`:
   ```python
   @register_node(OP_CODE)
   class MvcCalcNode_MyOp(MvcCalcOperationNode):
       op_code = OP_CODE
       op_title = "My Operation"
       op_symbol = "⊕"
       
       def evalOperation(self, input1, input2):
           # Your operation logic
           return result
   ```

3. **Register the Operation Code** in `mvc_conf.py`:
   ```python
   OP_NODE_MY_OP = 8  # Unique code
   ```

### Implementing Graph Algorithms

Use the controller pattern to implement graph traversal:
```python
controller = CalcNodeController(scene_model)
for node_id in scene_model.nodes:
    controller.evaluate_node(node_id)
```

### Custom Styling

Modify `qss/nodeeditor.qss` to change:
- Node colors and sizes
- Font sizes and styles
- Widget dimensions
- Grid appearance

## Files Structure

```
mvc_calculator/
├── main.py                    # Application entry point
├── mvc_conf.py               # Node registration and configuration
├── mvc_window.py             # Main application window
├── mvc_sub_window.py         # MDI child window
├── models/
│   ├── __init__.py
│   └── calc_node_models.py   # Model definitions
├── controllers/
│   ├── __init__.py
│   └── calc_node_controller.py  # Controller logic
├── nodes/
│   ├── __init__.py
│   ├── mvc_input_node.py     # Input node implementation
│   ├── mvc_output_node.py    # Output node implementation
│   └── mvc_operation_nodes.py # Operation node implementations
├── views/
│   └── __init__.py           # (Graphics views for future extension)
├── qss/
│   ├── __init__.py
│   └── nodeeditor.qss        # Qt stylesheets
├── icons/
│   ├── in.png                # Input node icon
│   ├── out.png               # Output node icon
│   ├── add.png               # Addition node icon
│   ├── sub.png               # Subtraction node icon
│   ├── mul.png               # Multiplication node icon
│   ├── divide.png            # Division node icon
│   └── status_icons.png      # Node status indicators
└── README.md                 # This file
```

## Comparison with Old Architecture

### Old Architecture (example_calculator)
- Single large classes handling all concerns
- Mixed model/view logic in node classes
- Tight coupling between data and graphics
- Harder to test and maintain

### MVC Architecture (mvc_calculator)
- Clear separation of concerns
- Independent models, controllers, views
- Loosely coupled components
- Easier to test, extend, and maintain
- Better code organization
- Follows design patterns

## Best Practices Demonstrated

1. **Separation of Concerns**: Models don't know about graphics
2. **Signal/Slot Pattern**: Decoupled communication between components
3. **Dependency Injection**: Controllers receive models as parameters
4. **Node Registration**: Extensible plugin system for node types
5. **Edge Validation**: Enforce graph constraints
6. **Command Pattern**: Undo/redo support via history
7. **Factory Pattern**: Node creation through registry
8. **Observer Pattern**: Signal-based notifications

## Further Reading

- Qt Model/View Architecture: https://doc.qt.io/qt-6/model-view-programming.html
- MVC Pattern: https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller
- PyQt/PySide Signals: https://doc.qt.io/qtforpython/overviews/signals_and_slots.html

## Troubleshooting

### Nodes don't appear
- Check that icon paths are correct in node definitions
- Ensure node registration is working (run with DEBUG=True)
- Check QSS stylesheet is loaded

### Graph doesn't evaluate
- Verify input nodes have valid numeric values
- Check all connections are properly established
- Review edge validator debug output

### Cannot connect nodes
- Verify node types support connection (input/output compatibility)
- Check edge validators aren't blocking connection
- Ensure nodes are on the same scene

## License

This example is part of the qtpy-nodeeditor project and follows the same license terms.
