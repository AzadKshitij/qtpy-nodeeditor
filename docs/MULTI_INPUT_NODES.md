# Ordered multi-input nodes

A `MultiInputNode` is a `Node` whose input socket accepts any number of
`Edges` and reads them **in an explicit order**: connection order by default,
reorderable manually from code (and from the calculator example's
right-click menu).

```python
from nodeeditor.node_multi_input_node import MultiInputNode

class Sum(MultiInputNode):
    def __init__(self, scene):
        # one input socket accepting many edges, one output
        super().__init__(scene, "Sum", inputs=[2], outputs=[1])

    def evalImplementation(self):
        return [sum(v for v in self.getOrderedValues() if v is not None)]
```

## How it works

- Every `Edge` carries an `input_index`: its 0-based read position on its
  end (input) socket (`nodeeditor/node_edge.py`). `-1` means "not attached
  to an input" and is also the append-at-end default.
- The owning input `Socket` compacts the numbers to a gap-free `0..n-1`
  sequence after every add/remove (`nodeeditor/node_socket.py`:
  `addEdge`, `removeEdge`, `_reindexEdges`, `orderedEdges`).
- `MultiInputNode` (`nodeeditor/node_multi_input_node.py`) turns
  `input_multi_edged` on, reads via `getOrderedEdges` /
  `getOrderedSources` / `getOrderedValues`, and reorders via `setEdgeOrder`,
  `setEdgeOrderByNodes`, `moveEdgeTo`, `moveEdgeBy`, `swapEdges`,
  `reverseEdgeOrder`. Successful reorders mark the node and its
  descendants dirty so they re-evaluate.
- `onEdgeConnectionChanged` is the single hook every connection path
  (drag, reroute, remove, paste) already calls, so the order stays compact
  with no per-path plumbing. `onInputChanged` is intentionally untouched
  so existing subclass chains (e.g. `CalcNode`) keep working.

## Setting the order

```python
# at connection time: insert at the front instead of appending
edge = Edge(scene, out_socket, node.inputs[0], input_index=0)

# afterwards, from code (all return True when the order changed)
node.setEdgeOrder([edge_b, edge_a])   # partial lists keep the rest in place
node.setEdgeOrderByNodes([node_b, node_a])
node.moveEdgeTo(edge, 0)
node.moveEdgeBy(edge, -1)             # clamped at both ends
node.swapEdges(edge_a, edge_b)
node.reverseEdgeOrder()

# raw assignment also works, but must be followed by compaction
edge.input_index = 5
node.compactEdgeOrder()

# introspection
node.getOrderedEdges()    # [Edge, ...] in read order
node.getOrderedSources()  # [(node, socket), ...], one entry per edge
node.getOrderedValues()   # [evaluated, ...], None for failed sources
node.describeInputOrder() # "0: Input [out 0]\n1: Add [out 0]"
```

Output sockets are never ordered; `input_index` on them is reset to `-1`.

## Order labels (`#1`, `#2`, ...)

When `MultiInputNode.show_input_order_labels` is `True` (the default),
every edge on the ordered input is labeled `#1`, `#2`, ... — the 1-based
display of its read position. Labels are written on every connection
change and every reorder, compacted on removal, and cleared when an edge
detaches (only when the label still matches the `#N` pattern, so a custom
label you set from code survives disconnects). Set the flag to `False` to
opt out; re-enabling backfills via `updateInputOrderLabels()`.

One caveat, shared with eval/dirty-marking in this codebase: the labels
are applied in `onEdgeConnectionChanged`, which the view (`EdgeDragging`,
`EdgeRerouting`, `Edge.remove`) calls for you. If you connect nodes purely
from code with `Edge(scene, out, node.inputs[0])`, send the same
notifications a drag would, then read the labels:

```python
edge = Edge(scene, out_socket, node.inputs[0])
node.onEdgeConnectionChanged(edge)   # like EdgeDragging does
assert edge.getLabel() == "#1"
```

## Worked example

`examples/example_calculator/nodes/multi_input.py` (`Sum`, op code
`OP_NODE_SUM` in `examples/example_calculator/calc_conf.py`) sums every
input in read order and shows the order in its tooltip. Right-click menus
in `examples/example_calculator/calc_sub_window.py`:

- node menu (on a `MultiInputNode` with 2+ edges): *Reverse Input Order*,
  *Move First Input to Last*, *Move Last Input to First*;
- edge menu (on an edge feeding such a socket): *Move Input Earlier/Later*.

All menu actions store an undo-history entry.

## Persistence

- `Edge.serialize()` stores `'input_index'`; `Edge.deserialize()`
  restores it with `data.get('input_index', -1)`, so old files without the
  key load in file (connection) order — same back-compat pattern as the
  `'label'` key (see `docs/EDGE_LABELS.md`).
- Because the number travels on the edge, the order survives save/load,
  copy/paste, and undo/redo even when the file's `"edges"` array is
  shuffled: attaching inserts each edge at its stored slot.
- Clipboard paste and history snapshots go through the same
  `Edge`/`Socket` APIs, so no extra handling was needed.
- Rerouting onto a multi-edge input keeps the socket's other edges
  (`nodeeditor/node_edge_rerouting.py`); rerouting onto a single-edge
  input still replaces, as before.
