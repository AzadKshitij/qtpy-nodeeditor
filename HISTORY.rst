History
=======

Release history for **qtpy-nodeeditor**.

This file tracks releases of this project. For the pre-fork upstream
`PyNodeEditor <https://github.com/benbyjones/PyQtNodeEditor>`_ lineage that
this code started from, see `CHANGES.md <CHANGES.md>`_.

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
