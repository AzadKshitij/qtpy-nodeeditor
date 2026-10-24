# Canvas comments

A `Comment` is a canvas note: a movable, selectable box that holds multi-line
plain text. It is a visual item like a `Group`, not a `Node`. It has no sockets,
never runs, and has no effect on evaluation.

Use `Scene.addComment()` as the short form:

```python
note = scene.addComment(
    "Remember to tune this after the first run.",
    x=40, y=25, width=260,
)
```

Or construct one directly. Both forms register the note with the scene:

```python
from nodeeditor.node_comment import Comment

note = Comment(scene, "text", x=40, y=25, width=260, height=120)
```

The note auto-sizes: its width is the requested width (at least
`Comment.MIN_WIDTH`) and its height grows to fit the wrapped text, never below
`Comment.MIN_HEIGHT`. `setSize(w, h)` changes the requested size and
`setText()` replaces the text.

## Editing

Double-click the note, or call `begin_edit()`, to open the inline editor.
Editing ends in one of these ways:

- Focus leaves the editor (clicking elsewhere): the text is committed and a
  `"Edited comment"` history entry is stored.
- `Escape` is pressed: the edit is cancelled and the text from before the edit
  is restored. No history entry is stored.
- `Ctrl+Enter` is pressed, or `finish_edit()` is called: the text is committed.
- `cancel_edit()` is called: the edit is cancelled explicitly.

`setText(text, store_history=True)` also stores a history entry. The default
`store_history=False` keeps generated text and scene loading out of the undo
stack. History stamps snapshot the whole scene, and comments are part of that
snapshot, so undo and redo restore comment text, position, size, colours and
z-order.

## Colours and order

The defaults are theme-neutral, so the library does not read an application
theme manager:

```python
note.setBackgroundColor("#fff8d6")
note.setBorderColor((190, 175, 120))
note.setTextColor("#222222")
note.setColors(background="#e8f0ff", border="#8aa4c8")
```

Each setter accepts a `QColor`, a colour name or an RGB/RGBA tuple. Moving a
note updates its scene position. `bringToFront()`, `sendToBack()` and
`resetZValue()` change the stacking order; the z-value is saved with the note.

## Selection and removal

Notes are ordinary selectable items, so rubber-band selection and `Shift`
selection work. `Scene.getSelectedComments()` returns the selected notes.
`Delete` removes them through `QDMGraphicsView.deleteSelected()`, and the
context menu offers edit, order and delete actions. `note.remove()` removes a
note programmatically; the caller decides whether to store a history entry.

## Serialization

Comments are stored in the additive `Scene` key `"comments"`. Files written
before comments existed have no such key and load unchanged.

```json
{
  "id": 1234,
  "type": "Comment",
  "version": 1,
  "text": "first line\nsecond line",
  "x": 40.0,
  "y": 25.0,
  "w": 240.0,
  "h": 110.0,
  "z": 1.0,
  "style": {
    "background": [255, 248, 214, 232],
    "border": [190, 175, 120, 255],
    "text": [35, 35, 35, 255]
  }
}
```

`w` and `h` are the outer size after auto-sizing; `z` is the item z-value.
Missing `style` or `z` keys fall back to the neutral defaults.
