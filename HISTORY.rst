History
=======

Release history for **qtpy-nodeeditor**.

This file tracks releases of this project. For the pre-fork upstream
`PyNodeEditor <https://github.com/benbyjones/PyQtNodeEditor>`_ lineage that
this code started from, see `CHANGES.md <CHANGES.md>`_.

0.7 - 2026-09-29
----------------

**Features**

- Added centralized color configuration for edges, sockets, and node hover
  highlights, with scene helpers to refresh existing graphics items.
- Added an interactive color configuration example with theme selection.

**Fixes**

- Preserve the existing socket type palette and transparent fallback when
  applying color configuration, and restore node colors when resetting defaults.
- Preserve upstream grouping behavior while applying color changes.
- Renamed a case-colliding scene fixture for Windows compatibility.

**Tests**

- Added headless regression coverage for color updates, icon nodes, the color
  demo, and group collapse/expand and serialization with node and edge labels.

0.6 - 2026-09-27
----------------

**Features**

- Added ``MultiInputNode``: a node whose input `Socket` accepts any number of
  `Edges` and reads them in an explicit, persisted order. It defines no
  ``__init__``, so it can be mixed into an existing node hierarchy without
  changing its constructor chain. Every input socket is multi-edged by default;
  set ``multi_input_socket`` with ``multi_input_all_inputs = False`` to make
  only one socket do so.
- Reading: ``getOrderedEdges``, ``getOrderedSources``, ``getOrderedValues``,
  ``getOrderedNodes``, and ``describeInputOrder``. ``getOrderedValues`` returns
  one entry per connected `Edge`, substituting ``None`` for a source that fails
  to evaluate, so its length always matches the connection count.
- Reordering: ``setEdgeOrder``, ``setEdgeOrderByNodes``, ``moveEdgeTo``,
  ``moveEdgeBy`` (clamped at both ends), ``swapEdges``, ``reverseEdgeOrder``,
  and ``compactEdgeOrder``. A partial order list is accepted; the remaining
  `Edges` keep their relative order. Successful reorders mark the node and its
  descendants dirty so they re-evaluate.
- Order labels: when ``show_input_order_labels`` is ``True`` (the default), each
  `Edge` on the ordered input is labeled ``#1``, ``#2``, ... Labels are kept in
  sync on connection, reorder, and removal, and are cleared on detach only when
  they still match the ``#N`` pattern, so a custom label set from code is never
  destroyed. Set the flag to ``False`` to opt out.
- ``Edge.input_index``: the 0-based read position of an `Edge` on its end
  (input) `Socket`, settable at construction as ``Edge(..., input_index=n)`` to
  insert at a slot instead of appending. Output sockets are never ordered and
  reset the value to ``-1``.
- ``Socket`` ordering API: ``addEdge`` accepts an ``index``, and
  ``orderedEdges``, ``edgeIndex``, ``compactEdgeOrder``, ``setEdgeOrder``,
  ``moveEdgeTo``, and ``swapEdges`` round out the set. The owning input `Socket`
  keeps read positions gap free after every add and remove, so the order stays
  compact through every connection path without per-path plumbing.
- ``input_index`` is persisted by ``Edge.serialize()`` / ``deserialize()``.
  Because the number travels on the `Edge`, the order survives save/load,
  copy/paste, and undo/redo even when the file's ``"edges"`` array is shuffled.
  Files written before this release load in connection order.
- Calculator example: new ``Sum`` node (op code ``OP_NODE_SUM``), plus
  *Reverse Input Order*, *Move First/Last Input to Last/First* in the node
  context menu and *Move Input Earlier/Later* in the edge context menu. Each
  action stores an undo-history entry. Menu entries are gated on the target
  actually being a ``MultiInputNode`` with 2+ edges.

**Fixes**

- Rerouting an `Edge` onto a multi-edged input no longer drops the socket's
  other `Edges`; each moved `Edge` lands at the read position it held on the
  old socket. Single-edged inputs still replace, as before.

**Docs and tests**

- Added ``docs/MULTI_INPUT_NODES.md`` and the Sphinx page for
  ``nodeeditor.node_multi_input_node``.
- Added ``tests/test_100_multi_input.py`` covering read order, reordering,
  label handling, and persistence.

0.5 - 2026-09-27
----------------

**Features**

- Node labels: added ``QDMGraphicsNodeLabel``, a floating single-line text box
  that is editable by the user, integrated into both ``QDMGraphicsNode`` and
  ``QDMIconGraphicsNode``. Supports styling, visibility, offset, and edit
  handling.
- Exposed the node label API on ``Node``: ``setNodeLabel``, ``getNodeLabel``,
  ``clearNodeLabel``, ``setNodeLabelVisible``, ``isNodeLabelVisible``,
  ``setNodeLabelOffset``, plus a ``labelChanged`` signal.
- Edge labels: added a code-set, read-only label to ``QDMGraphicsEdge`` and
  ``Edge``, constructible as ``Edge(..., label=...)`` and mutable through the
  ``label`` property (``getLabel`` / ``setLabel``), with rendering and
  bounding-box updates.
- Node label ``label_text`` / ``label_visible`` / ``label_offset`` and edge
  labels are persisted across ``serialize`` / ``deserialize``.
- Added ``docs/NODE_LABELS.md`` and ``docs/EDGE_LABELS.md``.

0.4 - 2026-09-26
----------------

**Features**

- ``SceneHistory.restoring()``: nestable context manager backed by a
  restore-depth counter, replacing the ``is_restoring_history`` flag. A callback
  fired mid-restore can no longer re-enable history storage and record a bogus
  stamp. ``is_restoring_history`` is retained as a property for legacy callers
  that assign to it.
- ``SceneHistory.storeHistory()`` gained ``merge_key`` and ``merge``, coalescing
  consecutive related stores (for example a burst of keystrokes) into a single
  undo step. Merging only happens at the tip of the stack, so a redo tail is
  never rewritten.
- ``history_limit`` is now an optional ``SceneHistory`` constructor argument;
  ``None`` (the default) means unlimited. Previously hard-coded to 32.
- ``storeHistory()`` now returns ``bool`` reporting whether a stamp was pushed.
- Added ``SceneHistory.currentText()`` and ``nextText()`` for describing the
  next undo/redo step, and ``removeHistoryModifiedListener()``.
- Added ``Scene.undo()``, ``redo()``, ``canUndo()``, and ``canRedo()`` so
  subclasses can layer an alternative undo backend. ``NodeEditorWindow`` now
  routes Edit Undo/Redo through the ``Scene`` rather than calling
  ``scene.history`` directly.

**Fixes**

- ``history_stamp_callback`` is resolved defensively via a dedicated dispatch
  helper. A stamp whose node has since been deleted, or one whose content class
  never implemented the callback, no longer aborts the restore. Exceptions
  raised by the callback are logged instead of propagating.

**Docs**

- Rewrote ``docs/NODE_GROUPING.md`` as a complete usage guide: grouping API,
  collapse/expand with per-edge stubs, appearance, serialization format,
  selection model, the three distinct delete operations, and troubleshooting.

0.3 - 2026-09-12
----------------

**Dependencies**

- Pinned ``orjson>=3.12.0``.

0.2 - 2026-09-11
----------------

**Features**

- Node grouping, developed through a ``Group`` class refactor of the earlier
  ``GroupNode`` container. ``Group`` is a pure visual container and
  intentionally not a ``Node``: no sockets, no evaluation, no content widget.
- Group actions for the Edit menu: group selected nodes, ungroup, and
  collapse/expand, with keyboard shortcuts.
- Drag-and-drop support for moving nodes into a group, with drop highlighting.
- Group serialization, including collapse state, and saving/loading of
  container expand/collapse.
- Correct edge drawing and correct internal-edge handling for collapsed groups.
- Hit-testing improvements: the expanded group body is click-through, and
  header context-menu handling was refined.
- ``Scene.addGroup`` / ``removeGroup`` / ``getGroupById`` /
  ``findCollapsedGroupForNode`` / ``findGroupForDrop`` / ``dropNodesIntoGroup``
  helpers, and a ``parent_group`` attribute on ``Node``.

**Fixes**

- Edge intersection logic now validates edges before modification, uses the
  proper edge class, and notifies node connections on auto-splits.
- Fixed a bug where internal edges of a group were removed on collapse.
- More robust edge deserialization error handling, and a new
  ``restoreExpandedVisuals`` method.

**Project**

- ``QDMNodeIconContentWidget`` accepts an optional ``parent`` argument.
- Refactored child ID retrieval in ``Scene`` for readability.
- Adopted ``uv`` for project and lock management.

0.1.8 and earlier - 2025-01-28 to 2025-10-22
--------------------------------------------

Pre-grouping baseline. The project was imported from upstream at ``0.9.15``
and renumbered from ``0.1.0``; ``pyproject.toml`` was introduced at ``0.1.0``
on 2026-09-09.

- Switched data transfer from node-based to socket-based, and the backing
  format from ``json`` to ``orjson`` with a ``.tds`` file extension.
- New undo/redo implementation, and shift+scroll to zoom horizontally.
- Icon-based nodes, in the style of Alteryx / n8n, with enhanced icon handling
  in the node UI and improved evaluation logging.
- Type hints with ``mypy`` checks, and a ``py.typed`` marker.
- Grid show/hide, and text inside sockets.
- Edge-handling improvements: cancel with ``Esc`` or by clicking outside, and
  alt+click on a socket to get the socket.
- Fixed a bug where a rubber-band box was created when no item was created.
