# Events

The framework has its own event system for what happens inside the scene, and
avoids `pyqtSignal` for it. You subscribe to an event by registering a
callback:

```python
scene.addHasBeenModifiedListener(callback)
```

Callbacks take no arguments and can be registered at any time. The classes
that emit events list them at the top of their documentation.

## Scene events

| Listener | Fired when |
| --- | --- |
| `addHasBeenModifiedListener` | something in the scene has changed |
| `addItemSelectedListener` | a node or an edge is selected |
| `addItemsDeselectedListener` | the selection is cleared |
| `addDragEnterListener` | something is dragged onto the scene; the callback may allow or deny the drag |
| `addDropListener` | something is dropped into the scene |

```python
scene.addHasBeenModifiedListener(lambda: print("the graph changed"))
```

## History events

`SceneHistory` reports what the undo/redo stack is doing:

| Listener | Fired when |
| --- | --- |
| `addHistoryModifiedListener` | a history stamp has been stored or restored |
| `addHistoryStoredListener` | a history stamp has been stored |
| `addHistoryRestoredListener` | a history stamp has been restored |

The history listeners can also be removed again, which is handy when a dialog
or a temporary widget subscribes and then goes away:

```python
scene.history.addHistoryStoredListener(on_stored)
scene.history.removeHistoryStoredListener(on_stored)
```
