# MVC Calculator Example - Quick Start Guide

This guide helps you get started with the MVC Calculator example.

## Installation & Setup

### Requirements
- Python 3.7+
- PyQt5/PySide2 (via qtpy)
- qtpy-nodeeditor framework

### Running the Example

From the project root directory:

```bash
python examples/mvc_calculator/main.py
```

Or from the example directory:

```bash
cd examples/mvc_calculator
python main.py
```

## Basic Usage

### Step 1: Create a Simple Calculation

1. **Launch** the application
2. **Right-click** in the empty editor area
3. **Select "Input"** from the context menu
4. **Right-click** again and select "Output"
5. **Left-click** the output socket (white dot) on the Input node
6. **Drag** to the input socket on the Output node to create an edge

You now have:
```
[Input] → [Output]
```

### Step 2: Set and View Values

1. **Double-click** the Input node (or the number inside it)
2. **Type a new number** (e.g., "42")
3. **Press Enter** to confirm
4. **Watch** the Output node update automatically

### Step 3: Build a Complex Graph

Create (10 + 5) × 2:

1. Create an **Input** node with value 10
2. Create an **Input** node with value 5
3. Create an **Add** node by right-clicking and selecting "Add"
4. Connect both Input nodes to the Add node
5. Create an **Input** node with value 2
6. Create a **Multiply** node
7. Connect the Output of the Add node to the first input of Multiply
8. Connect the Input (2) to the second input of Multiply
9. Create an **Output** node and connect to Multiply
10. **Result**: The Output shows 30

Visual:
```
    10 ──→ [+] ←── 5
            ↓
           [×] ←── 2
            ↓
          30 (Output)
```

## Menu Functions

### File Menu
- **New** (Ctrl+N): Create a new graph
- **Open** (Ctrl+O): Load a saved graph
- **Save** (Ctrl+S): Save current graph
- **Save As** (Ctrl+Shift+S): Save with new name
- **Recent**: Quick access to recently opened files
- **Exit** (Alt+F4): Close application

### Edit Menu
- **Undo** (Ctrl+Z): Undo last action
- **Redo** (Ctrl+Y): Redo undone action
- **Cut** (Ctrl+X): Cut selected nodes
- **Copy** (Ctrl+C): Copy selected nodes
- **Paste** (Ctrl+V): Paste copied nodes
- **Delete**: Remove selected nodes/edges

### View Menu
- **Show Grid**: Toggle grid visibility

### Window Menu
- **Nodes Toolbar**: Show/hide node creation dock
- **Tile**: Arrange all open graphs side-by-side
- **Cascade**: Stack all open graphs
- **Next**: Switch to next open graph
- **Previous**: Switch to previous open graph

### Help Menu
- **About**: Show application information

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+N | New graph |
| Ctrl+O | Open graph |
| Ctrl+S | Save graph |
| Ctrl+Shift+S | Save As |
| Ctrl+Z | Undo |
| Ctrl+Y | Redo |
| Ctrl+X | Cut |
| Ctrl+C | Copy |
| Ctrl+V | Paste |
| Delete | Delete selected |
| F5 | Evaluate graph |

## Node Types

### Input
- **Icon**: Green input symbol
- **Purpose**: Enter numeric values
- **Usage**: 
  - Double-click to edit value
  - Connect output to other nodes
- **Constraints**: Must contain valid integer

### Output
- **Icon**: Red output symbol
- **Purpose**: Display results
- **Usage**:
  - Connect an input from another node
  - Result displays automatically
- **Constraints**: Can have only one input

### Add (+)
- **Icon**: + symbol
- **Purpose**: Add two numbers
- **Usage**: `a + b`
- **Inputs**: 2 (top and bottom)
- **Outputs**: 1

### Subtract (-)
- **Icon**: - symbol
- **Purpose**: Subtract numbers
- **Usage**: `a - b`
- **Inputs**: 2
- **Outputs**: 1

### Multiply (*)
- **Icon**: × symbol
- **Purpose**: Multiply numbers
- **Usage**: `a × b`
- **Inputs**: 2
- **Outputs**: 1

### Divide (/)
- **Icon**: ÷ symbol
- **Purpose**: Integer division
- **Usage**: `a ÷ b` returns quotient and remainder
- **Inputs**: 2
- **Outputs**: 2 (quotient on top, remainder on bottom)
- **Warning**: Division by zero produces error

## Connection Rules

✓ **Valid Connections:**
- Output socket → Input socket
- Any node type can connect to any other (same layer)
- Multiple connections to same input/output possible

✗ **Invalid Connections:**
- Output → Output (prevented by edge validator)
- Input → Input (prevented by edge validator)
- Same node to itself (prevented by edge validator)
- Will show red indicator or refuse connection

## Saving Your Work

### Save Graph
1. **File** → **Save** or Ctrl+S
2. File is saved as `.json` format
3. Includes:
   - Node positions
   - Node values
   - All connections (edges)
   - Graph metadata

### Load Graph
1. **File** → **Open** or Ctrl+O
2. Select a `.json` file
3. Graph is restored with all nodes and connections
4. Values are automatically re-evaluated

## Tips & Tricks

### Organizing Large Graphs
- Use **Grid** (View → Show Grid) to align nodes
- **Ctrl+Drag** multiple nodes to move them together
- **Right-click and drag** to pan the view
- **Mouse wheel** to zoom in/out

### Efficient Editing
- **Copy** frequently used subgraphs (e.g., add chains)
- **Paste** multiple times to reuse patterns
- **Undo** frequently - don't worry about mistakes!
- Use **MDI** (multiple documents) to compare graphs

### Debugging Graphs
- Check Input node values are correct
- Verify all connections are established
- Look for red highlighted nodes (errors)
- Check Output node displays something
- Use Nodes panel to verify all nodes exist

## Common Issues & Solutions

### "Please enter a valid integer"
- **Problem**: Invalid value in Input node
- **Solution**: Double-click Input, enter number, press Enter

### Output shows "NaN" or "None"
- **Problem**: Disconnected or invalid input
- **Solution**: Connect an output to the Output node input

### Cannot connect nodes
- **Problem**: Invalid connection attempted
- **Solution**: 
  - Ensure you're connecting output → input
  - Try different node pair
  - Check edge validators

### Changes not saved
- **Problem**: Window title shows asterisk (*)
- **Solution**: 
  - **File** → **Save** to save
  - Use Ctrl+S shortcut
  - Automatic save not enabled by default

### Slow performance
- **Problem**: Graph is very large
- **Solution**:
  - Save and close some graphs
  - Reduce grid zoom level
  - Use simpler node types

## Examples

### Example 1: Simple Addition
**Task**: Calculate 15 + 25

```python
# Setup:
1. Input node (15) → Add node
2. Input node (25) → Add node
3. Add node → Output node
# Result: 40
```

### Example 2: Compound Expression
**Task**: Calculate (100 + 50) ÷ 3 = 50

```
Input(100) ──→ Add ←── Input(50)
                ↓
            Divide ←── Input(3)
                ↓
              Output
              (50,1)
```

### Example 3: Factorial Pattern
**Task**: Calculate 5! = 120

```
Input(1) ──→ Mul ←── Input(2)
              ↓
            Mul ←── Input(3)
              ↓
            Mul ←── Input(4)
              ↓
            Mul ←── Input(5)
              ↓
            Output
            (120)
```

## Keyboard & Mouse Actions

### Mouse
- **Left-click**: Select node/edge
- **Left-drag**: Move node (click on title bar) or pan (Shift+drag)
- **Ctrl+left-drag**: Pan view
- **Right-click**: Context menu
- **Mouse wheel**: Zoom in/out
- **Drag from socket**: Create edge
- **Double-click**: Edit value (Input node)

### Keyboard (Editor)
- **Arrow keys**: Move selected node
- **Delete**: Remove selected
- **Ctrl+A**: Select all
- **Ctrl+D**: Deselect all
- **Esc**: Cancel current operation

## Advanced Usage

### Saving as Templates
1. Create a useful subgraph
2. **File** → **Save As**
3. Name it descriptively (e.g., "add_chain_template.json")
4. Later, **File** → **Open** to load template
5. **Edit** → **Paste** to add to new graphs

### Multiple Graphs
- Open multiple graphs via **File** → **Open**
- Switch between them in **Window** menu
- Use **Tile** or **Cascade** for side-by-side editing
- Copy/paste between graphs

### Export Results
1. Right-click on Output node
2. Create multiple Output nodes for different branches
3. Save the graph
4. Print/screenshot the results

## Performance Tips

- **Large graphs**: Disable grid for better performance
- **Many connections**: Simplify graph structure
- **Slow evaluation**: Reduce number of operations
- **Memory**: Close unused graphs

## Next Steps

- Check `README.md` for architecture details
- Review source code to understand MVC pattern
- Extend with custom node types
- Build your own applications using this pattern

## Getting Help

### Errors & Debugging
1. Check console for error messages
2. Review node values and connections
3. Test with simpler graphs first
4. Verify all inputs are connected

### Feature Requests
- Star the repository on GitHub
- Create an issue with description
- Include example graphs showing use case

## File Format

Graphs are saved as JSON:
```json
{
  "id": 1,
  "type": "InputNode",
  "pos_x": 100,
  "pos_y": 200,
  "title": "Input",
  "properties": {
    "value": "42"
  }
}
```

This allows:
- Easy manual editing
- Version control tracking
- Integration with other tools
- Export to other formats

---

**Enjoy building node graphs!** 🚀

For more details, see `README.md` and source code documentation.
