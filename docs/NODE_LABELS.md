# Node labels (single-line, user-editable)

Nodes support a floating single-line textbox drawn above the node.

- **User-editable.** The label is a `QDMGraphicsNodeLabel` (`QGraphicsTextItem`)
  child of the graphics node, so it follows node moves/drags automatically.
  Click to focus/edit, `Enter` commits, `Escape` reverts, focus-out commits.
- **Code can set it at creation time and at runtime.**

## Usage

```python
node.setNodeLabel("intake valve")
assert node.getNodeLabel() == node.grNode.labelText() == "intake valve"

# hide / show (empty text always hides)
node.setNodeLabelVisible(False)
node.setNodeLabelVisible(True)

# gap between node top and label, px
node.setNodeLabelOffset(12)

# remove
node.clearNodeLabel()

# styling (optional)
node.grNode.setLabelColor("#ffffff")
node.grNode.setLabelFont(my_qfont)
node.grNode.setLabelBackground("#E3212121", "#FF5A5A5A")

# change notification (emitted on user commit and setNodeLabel)
node.labelChanged.connect(lambda text: print("label:", text))
```

Single-line is enforced: `\r`/`\n` are replaced with spaces and the result is
stripped, both for programmatic sets and user commits.

## How it works

- `QDMGraphicsNode.initLabel()` / `QDMIconGraphicsNode.initLabel()` create a
  `QDMGraphicsNodeLabel` parented to the graphics node
  (`nodeeditor/node_graphics_node.py`). Child items move with the parent, so no
  position tracking is needed; `_updateLabelPos()` only recenters it above the
  node after text/size changes.
- The label is `ItemIsFocusable` with `TextEditorInteraction`, but
  `ItemIsSelectable`/`ItemIsMovable` unset and no `.node` attribute, so rubber-band
  selection, node drag, and `Scene.getSelectedNodes()` are unaffected.
- Focus in/out sets `view.editingFlag` (same convention as
  `nodeeditor/node_content_widget.py`) for apps that gate shortcuts while typing.
- User commits go through `QDMGraphicsNodeLabel._commit()` ->
  `grNode._onLabelEdited()`, which emits `Node.labelChanged` and stores
  `"Node label changed"` history. `Node.setNodeLabel(..., store_history=True)`
  does the same for programmatic changes; deserialize passes `False`.
- `Node.serialize()` stores `'label_text'`, `'label_visible'`, `'label_offset'`;
  `Node.deserialize()` restores them with `data.get(...)` defaults, so old
  `.tds` files without the keys load with no label. Clipboard
  (`Node.serialize` round-trip) and file save/load preserve the label.
