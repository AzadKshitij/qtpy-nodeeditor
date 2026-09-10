# -*- coding: utf-8 -*-
"""
Reliable ground-up grouping system.

Design notes (v2, clean break):
- Group is a pure visual container (QGraphicsRectItem + Serializable), NOT a Node.
- Nodes keep their positions/sizes at all times. Collapse only hides/shows,
  never resizes/scales nodes. This removes the fragile 0.2/scale(0)/width==5 hacks.
- Logical Edges never mutate on collapse. Only their graphics endpoints are
  overridden to per-edge stub rows on the collapsed box.
- Auto-fit + header-drag only. Child moves auto-expand, never auto-remove.
- Serialization is versioned (version=2, type="Group", key "children").
  Old files (type="GroupNode", "child_node_ids") load best-effort as expanded.
- Delete-key semantics (handled in view): delete group + children.
  Context menu offers Ungroup (delete only the group, keep nodes).
- Stub stacking: per-edge rows, left=incoming (end inside), right=outgoing (start inside).
"""
from qtpy.QtCore import QRectF, Qt, QPointF
from qtpy.QtGui import QColor, QPainter, QPainterPath, QPen, QBrush, QCursor
from qtpy.QtWidgets import QGraphicsRectItem, QGraphicsItem, QMenu, QInputDialog, QColorDialog

from nodeeditor.node_serializable import Serializable
from nodeeditor.utils_no_qt import dumpException

from typing import TYPE_CHECKING, List, Optional, Dict, Tuple, Set

if TYPE_CHECKING:
    from nodeeditor.node_scene import Scene
    from nodeeditor.node_node import Node
    from nodeeditor.node_edge import Edge


GROUP_SERIALIZATION_VERSION = 2


class Group(Serializable, QGraphicsRectItem):
    """Visual container grouping Nodes together."""

    TITLE_BAR_HEIGHT = 30
    PADDING = 20
    ROW_HEIGHT = 22
    MIN_WIDTH = 180
    MIN_HEIGHT_EXPANDED = 100
    COLLAPSED_WIDTH = 180
    TOGGLE_SIZE = 20

    def __init__(self, scene: 'Scene', title: str = "Group",
                 x: float = 0, y: float = 0,
                 width: float = 200, height: float = 150) -> None:
        QGraphicsRectItem.__init__(self, 0, 0, width, height)
        Serializable.__init__(self)

        self.scene: 'Scene' = scene
        self.title: str = title

        self._collapsed: bool = False
        self.child_nodes: List['Node'] = []

        self._color = QColor(100, 100, 100, 200)
        self._title_color = QColor(255, 255, 255)
        self._border_color = QColor(50, 50, 50)
        self._border_width = 2

        self._hover_header: bool = False
        self._can_move: bool = False
        self._moved: bool = False
        self._last_scene_pos: Optional[QPointF] = None
        self._toggle_rect = QRectF()
        self._drop_highlight: bool = False

        self.setPos(x, y)
        self.setZValue(-1)
        self.setPen(QPen(self._border_color, self._border_width))
        self.setBrush(QBrush(self._color))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setAcceptHoverEvents(True)

        # Register with scene (guard against double-add during deserialize reuse)
        if self not in self.scene.groups:
            self.scene.addGroup(self)
        try:
            if self not in self.scene.grScene.items():
                self.scene.grScene.addItem(self)
        except Exception:
            # grScene may not exist yet in some test setups; ignore
            try:
                self.scene.grScene.addItem(self)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # membership
    # ------------------------------------------------------------------
    def addNode(self, node: 'Node') -> None:
        if node is None:
            return
        if node in self.child_nodes:
            return
        # single-parent invariant: move between groups
        try:
            old = getattr(node, 'parent_group', None)
        except Exception:
            old = None
        if old is not None and old is not self:
            try:
                old.removeNode(node)
            except Exception:
                pass
        self.child_nodes.append(node)
        try:
            node.parent_group = self
        except Exception:
            pass
        # ensure single connection for auto-expand
        try:
            try:
                node.positionChanged.disconnect(self.onChildMoved)
            except Exception:
                pass
            node.positionChanged.connect(self.onChildMoved)
        except Exception:
            pass
        try:
            self.scene.has_been_modified = True
        except Exception:
            pass

    def removeNode(self, node: 'Node', update_bounds: bool = True) -> None:
        if node not in self.child_nodes:
            return
        try:
            try:
                node.positionChanged.disconnect(self.onChildMoved)
            except Exception:
                pass
        except Exception:
            pass
        try:
            self.child_nodes.remove(node)
        except ValueError:
            pass
        try:
            if getattr(node, 'parent_group', None) is self:
                node.parent_group = None
        except Exception:
            pass
        try:
            self.scene.has_been_modified = True
        except Exception:
            pass
        if update_bounds:
            try:
                if self._collapsed:
                    self._updateCollapsedSize()
                    self.refreshExternalEdges()
                else:
                    # don't auto-shrink on removal jitter; only ensure sane size
                    pass
            except Exception:
                pass

    def getChildNodes(self) -> List['Node']:
        return list(self.child_nodes)

    def contains(self, node: 'Node') -> bool:
        return node in self.child_nodes

    def isCollapsed(self) -> bool:
        return self._collapsed

    # ------------------------------------------------------------------
    # bounds: auto-fit + header drag
    # ------------------------------------------------------------------
    def calculateBounds(self) -> QRectF:
        if not self.child_nodes:
            p = self.pos()
            r = self.rect()
            w = max(r.width(), float(self.MIN_WIDTH))
            h = max(r.height(), float(self.MIN_HEIGHT_EXPANDED))
            return QRectF(p.x(), p.y(), w, h)
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')
        valid = False
        for node in self.child_nodes:
            try:
                gr = getattr(node, 'grNode', None)
                if gr is None:
                    continue
                np = node.pos
                try:
                    lb = gr.boundingRect()
                except Exception:
                    continue
                min_x = min(min_x, np.x() + lb.left())
                min_y = min(min_y, np.y() + lb.top())
                max_x = max(max_x, np.x() + lb.right())
                max_y = max(max_y, np.y() + lb.bottom())
                valid = True
            except Exception:
                continue
        if not valid:
            p = self.pos()
            return QRectF(p.x(), p.y(), 200, 150)
        pad = float(self.PADDING)
        left = min_x - pad
        top = min_y - pad - float(self.TITLE_BAR_HEIGHT)
        right = max_x + pad
        bottom = max_y + pad
        w = max(right - left, float(self.MIN_WIDTH))
        h = max(bottom - top, float(self.MIN_HEIGHT_EXPANDED))
        return QRectF(left, top, w, h)

    def updateBounds(self) -> None:
        """Recompute expanded bounds to tightly fit children."""
        if self._collapsed:
            self._updateCollapsedSize()
            return
        try:
            bbox = self.calculateBounds()
            self.setRect(0, 0, bbox.width(), bbox.height())
            self.setPos(bbox.topLeft())
        except Exception:
            dumpException()

    def onChildMoved(self, node: 'Node') -> None:
        """Recalculate the group boundary whenever a child node moves.

        Tight refit (may grow, shrink, or shift the origin). Never removes
        nodes — use Ungroup/detach explicitly. Collapsed groups ignore child
        moves (children are hidden and move with the container instead).
        """
        try:
            if self._collapsed:
                return
            if node not in self.child_nodes:
                return
            if getattr(node, 'grNode', None) is None:
                return
            self.updateBounds()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # edge classification + per-edge stub rows
    # ------------------------------------------------------------------
    def _classifyEdges(self) -> Tuple[List['Edge'], List['Edge'], List['Edge']]:
        """Return (incoming, outgoing, internal). Incoming=end inside, outgoing=start inside."""
        # Use persistent node.id (not id(node)) so classification survives
        # deserialize detach/relink, GC id() reuse, and stale socket.node refs.
        child_set: Set[int] = set()
        for n in self.child_nodes:
            try:
                nid = getattr(n, 'id', None)
                child_set.add(nid if nid is not None else id(n))
            except Exception:
                continue
        seen: Dict[int, 'Edge'] = {}
        try:
            for node in self.child_nodes:
                try:
                    sockets = list(getattr(node, 'inputs', [])) + list(getattr(node, 'outputs', []))
                except Exception:
                    continue
                for sock in sockets:
                    try:
                        for e in list(getattr(sock, 'edges', [])):
                            if e is None:
                                continue
                            seen[id(e)] = e
                    except Exception:
                        continue
        except Exception:
            pass
        incoming: List['Edge'] = []
        outgoing: List['Edge'] = []
        internal: List['Edge'] = []
        for e in seen.values():
            try:
                s = getattr(e, 'start_socket', None)
                t = getattr(e, 'end_socket', None)
                sn = getattr(s, 'node', None) if s is not None else None
                en = getattr(t, 'node', None) if t is not None else None
                try:
                    sn_key = getattr(sn, 'id', None) if sn is not None else None
                    sn_key = sn_key if sn_key is not None else (id(sn) if sn is not None else None)
                except Exception:
                    sn_key = None
                try:
                    en_key = getattr(en, 'id', None) if en is not None else None
                    en_key = en_key if en_key is not None else (id(en) if en is not None else None)
                except Exception:
                    en_key = None
                s_in = sn_key is not None and sn_key in child_set
                e_in = en_key is not None and en_key in child_set
                if s_in and e_in:
                    internal.append(e)
                elif (not s_in) and e_in:
                    incoming.append(e)
                elif s_in and (not e_in):
                    outgoing.append(e)
                else:
                    continue
            except Exception:
                continue
        try:
            incoming.sort(key=lambda e: getattr(e, 'id', 0))
            outgoing.sort(key=lambda e: getattr(e, 'id', 0))
            internal.sort(key=lambda e: getattr(e, 'id', 0))
        except Exception:
            pass
        return incoming, outgoing, internal

    def externalEdges(self) -> Tuple[List['Edge'], List['Edge']]:
        inc, out, _ = self._classifyEdges()
        return inc, out

    def _updateCollapsedSize(self) -> None:
        try:
            inc, out, _ = self._classifyEdges()
            rows = max(len(inc), len(out), 1)
            h = float(self.TITLE_BAR_HEIGHT) + 10.0 + rows * float(self.ROW_HEIGHT) + 10.0
            self.setRect(0, 0, float(self.COLLAPSED_WIDTH), h)
        except Exception:
            try:
                self.setRect(0, 0, float(self.COLLAPSED_WIDTH),
                             float(self.TITLE_BAR_HEIGHT) + 42.0)
            except Exception:
                pass

    def stubPosFor(self, edge: 'Edge') -> Optional[QPointF]:
        """Scene position of the stub for `edge` on THIS collapsed group, or None."""
        try:
            if not self._collapsed:
                return None
            inc, out, _ = self._classifyEdges()
            # find row index deterministically
            try:
                if edge in inc:
                    idx = inc.index(edge)
                    gp = self.pos()
                    y = gp.y() + float(self.TITLE_BAR_HEIGHT) + 10.0 + idx * float(self.ROW_HEIGHT) + float(self.ROW_HEIGHT) / 2.0
                    return QPointF(gp.x(), y)
                if edge in out:
                    idx = out.index(edge)
                    gp = self.pos()
                    y = gp.y() + float(self.TITLE_BAR_HEIGHT) + 10.0 + idx * float(self.ROW_HEIGHT) + float(self.ROW_HEIGHT) / 2.0
                    return QPointF(gp.x() + self.rect().width(), y)
            except ValueError:
                return None
            return None
        except Exception:
            return None

    def refreshExternalEdges(self) -> None:
        try:
            inc, out, internal = self._classifyEdges()
            for e in inc + out:
                try:
                    if getattr(e, 'grEdge', None) is not None:
                        try:
                            e.grEdge.show()
                        except Exception:
                            pass
                        e.updatePositions()
                except Exception:
                    continue
            for e in internal:
                try:
                    if getattr(e, 'grEdge', None) is not None:
                        if self._collapsed:
                            try:
                                e.grEdge.hide()
                            except Exception:
                                pass
                        else:
                            try:
                                e.grEdge.show()
                            except Exception:
                                pass
                            e.updatePositions()
                except Exception:
                    continue
        except Exception:
            pass

    # ------------------------------------------------------------------
    # collapse / expand (no node resize, positions preserved)
    # ------------------------------------------------------------------
    def collapse(self) -> None:
        if self._collapsed:
            return
        self._collapsed = True
        try:
            for node in list(self.child_nodes):
                try:
                    gr = getattr(node, 'grNode', None)
                    if gr is not None:
                        gr.hide()
                except Exception:
                    continue
            _, _, internal = self._classifyEdges()
            for e in internal:
                try:
                    if getattr(e, 'grEdge', None) is not None:
                        e.grEdge.hide()
                except Exception:
                    continue
            self._updateCollapsedSize()
            self.refreshExternalEdges()
            try:
                self.scene.has_been_modified = True
            except Exception:
                pass
            self.update()
        except Exception:
            dumpException()

    def expand(self) -> None:
        if not self._collapsed:
            return
        self._collapsed = False
        try:
            for node in list(self.child_nodes):
                try:
                    gr = getattr(node, 'grNode', None)
                    if gr is not None:
                        gr.show()
                except Exception:
                    continue
            # show all connected edges; positions recomputed from real sockets
            try:
                for node in list(self.child_nodes):
                    try:
                        sockets = list(getattr(node, 'inputs', [])) + list(getattr(node, 'outputs', []))
                    except Exception:
                        continue
                    for sock in sockets:
                        try:
                            for e in list(getattr(sock, 'edges', [])):
                                try:
                                    if getattr(e, 'grEdge', None) is not None:
                                        e.grEdge.show()
                                except Exception:
                                    pass
                        except Exception:
                            continue
                    try:
                        node.updateConnectedEdges()
                    except Exception:
                        pass
            except Exception:
                pass
            self.updateBounds()
            try:
                self.scene.has_been_modified = True
            except Exception:
                pass
            self.update()
        except Exception:
            dumpException()

    def restoreExpandedVisuals(self) -> None:
        """Idempotent expanded visuals for undo/redo/load (mirrors expand without toggling)."""
        try:
            for node in list(self.child_nodes):
                try:
                    gr = getattr(node, 'grNode', None)
                    if gr is not None:
                        gr.show()
                except Exception:
                    continue
            try:
                for node in list(self.child_nodes):
                    try:
                        sockets = list(getattr(node, 'inputs', [])) + list(getattr(node, 'outputs', []))
                    except Exception:
                        continue
                    for sock in sockets:
                        try:
                            for e in list(getattr(sock, 'edges', [])):
                                try:
                                    if getattr(e, 'grEdge', None) is not None:
                                        e.grEdge.show()
                                except Exception:
                                    pass
                        except Exception:
                            continue
                    try:
                        node.updateConnectedEdges()
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                self.updateBounds()
            except Exception:
                pass
            try:
                self.refreshExternalEdges()
            except Exception:
                pass
            try:
                self.update()
            except Exception:
                pass
        except Exception:
            pass

    def toggleCollapse(self) -> None:
        if self._collapsed:
            self.expand()
        else:
            self.collapse()

    def setCollapsed(self, collapsed: bool) -> None:
        if collapsed:
            self.collapse()
        else:
            self.expand()

    # ------------------------------------------------------------------
    # title + colors (rename via double-click header, recolor via menu)
    # ------------------------------------------------------------------
    GROUP_COLOR_PRESETS = {
        "Gray": (QColor(100, 100, 100, 200), QColor(60, 60, 60)),
        "Blue": (QColor(70, 110, 180, 200), QColor(45, 70, 120)),
        "Green": (QColor(80, 160, 100, 200), QColor(45, 95, 60)),
        "Purple": (QColor(140, 100, 180, 200), QColor(85, 60, 110)),
        "Orange": (QColor(200, 130, 60, 200), QColor(120, 75, 35)),
        "Red": (QColor(180, 80, 80, 200), QColor(110, 45, 45)),
    }

    def setTitle(self, title: str) -> bool:
        """Set group title. Returns True if changed."""
        try:
            title = (title or "").strip()
            if not title or title == self.title:
                return False
            self.title = title
            try:
                self.scene.has_been_modified = True
            except Exception:
                pass
            try:
                self.update()
            except Exception:
                pass
            return True
        except Exception:
            return False

    def renameInteractive(self, parent=None) -> bool:
        """Open rename dialog. Returns True if renamed (caller stores history)."""
        try:
            text, ok = QInputDialog.getText(parent, "Rename Group", "Group title:", text=self.title)
            if not ok:
                return False
            return self.setTitle(text)
        except Exception:
            return False

    def setColors(self, color=None, title_color=None, border_color=None) -> bool:
        """Set group colors. Any None arg is left unchanged. Returns True if changed."""
        changed = False
        try:
            if color is not None:
                c = QColor(color) if not isinstance(color, QColor) else color
                if c.isValid() and c != self._color:
                    self._color = c
                    changed = True
            if title_color is not None:
                c = QColor(title_color) if not isinstance(title_color, QColor) else title_color
                if c.isValid() and c != self._title_color:
                    self._title_color = c
                    changed = True
            if border_color is not None:
                c = QColor(border_color) if not isinstance(border_color, QColor) else border_color
                if c.isValid() and c != self._border_color:
                    self._border_color = c
                    changed = True
            if changed:
                try:
                    self.setPen(QPen(self._border_color, self._border_width))
                    self.setBrush(QBrush(self._color))
                except Exception:
                    pass
                try:
                    self.scene.has_been_modified = True
                except Exception:
                    pass
                try:
                    self.update()
                except Exception:
                    pass
            return changed
        except Exception:
            return False

    def recolorInteractive(self, parent=None) -> bool:
        """Open color dialog for fill color. Returns True if changed."""
        try:
            c = QColorDialog.getColor(self._color, parent, "Group fill color")
            if not c.isValid():
                return False
            return self.setColors(color=c)
        except Exception:
            return False

    def setDropHighlight(self, enabled: bool) -> None:
        try:
            if self._drop_highlight != bool(enabled):
                self._drop_highlight = bool(enabled)
                self.update()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # removal: Delete-key = delete children; context menu Ungroup = keep nodes
    # ------------------------------------------------------------------
    def ungroup(self) -> None:
        """Delete only the group, keep all child nodes (explicit, no auto-remove elsewhere)."""
        try:
            if self._collapsed:
                # show children first so positions/edges restore correctly
                self.expand()
        except Exception:
            pass
        for node in list(self.child_nodes):
            try:
                self.removeNode(node, update_bounds=False)
            except Exception:
                continue
        self.dispose()

    def deleteWithChildren(self) -> None:
        """Delete-key semantics: delete container AND all child nodes (and their edges)."""
        for node in list(self.child_nodes):
            try:
                # Node.remove() detaches from group itself; guard double-remove
                try:
                    node.remove()
                except Exception:
                    try:
                        self.removeNode(node, update_bounds=False)
                    except Exception:
                        pass
            except Exception:
                continue
        self.child_nodes.clear()
        self.dispose()

    def dispose(self) -> None:
        try:
            try:
                if self.scene.grScene is not None and self in self.scene.grScene.items():
                    self.scene.grScene.removeItem(self)
            except Exception:
                pass
        except Exception:
            pass
        try:
            self.scene.removeGroup(self)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # interaction: header-only drag, painted toggle, hover, context menu
    # ------------------------------------------------------------------
    def _toggleRectLocal(self) -> QRectF:
        try:
            w = self.rect().width()
            s = float(self.TOGGLE_SIZE)
            return QRectF(w - s - 6.0, (float(self.TITLE_BAR_HEIGHT) - s) / 2.0, s, s)
        except Exception:
            return QRectF()

    def shape(self):
        """Hit-testing only: expanded = header (+toggle) only, collapsed = full rect.

        boundingRect()/paint() stay full so the background still draws; only
        clicks/selection/rubber-band/itemAt ignore the expanded body, making it
        behave like plain canvas.
        """
        try:
            path = QPainterPath()
            # WindingFill: overlapping subpaths (toggle lives inside the header
            # rect) must UNION, not punch an odd-even hole that swallows clicks.
            try:
                path.setFillRule(Qt.FillRule.WindingFill)
            except Exception:
                pass
            r = self.rect()
            if self._collapsed:
                path.addRoundedRect(0, 0, r.width(), r.height(), 8.0, 8.0)
            else:
                path.addRect(0, 0, r.width(), float(self.TITLE_BAR_HEIGHT))
                try:
                    tog = self._toggleRectLocal()
                    if tog.isValid():
                        path.addRect(tog)
                except Exception:
                    pass
            return path
        except Exception:
            return super().shape()

    def mousePressEvent(self, event) -> None:
        try:
            lp = event.pos()
        except Exception:
            super().mousePressEvent(event)
            return
        # toggle button first
        try:
            if self._toggleRectLocal().contains(lp):
                self.toggleCollapse()
                try:
                    self.scene.history.storeHistory(
                        "Collapsed group" if self._collapsed else "Expanded group",
                        setModified=True)
                except Exception:
                    pass
                try:
                    event.accept()
                except Exception:
                    pass
                return
        except Exception:
            pass
        try:
            if lp.y() < float(self.TITLE_BAR_HEIGHT):
                self._can_move = True
                self._moved = False
                try:
                    self._last_scene_pos = self.mapToScene(lp)
                except Exception:
                    self._last_scene_pos = None
                try:
                    # Exclusive selection (unless Shift): a header click must NOT
                    # leave nodes + group jointly selected, otherwise a later
                    # node drag moves the group along (and a group drag
                    # double-moves selected children via Qt's selection move).
                    mods = None
                    try:
                        mods = event.modifiers()
                    except Exception:
                        mods = None
                    additive = False
                    try:
                        additive = bool(mods is not None and (mods & Qt.KeyboardModifier.ShiftModifier))
                    except Exception:
                        additive = False
                    if not additive:
                        try:
                            for it in list(self.scene.grScene.selectedItems()):
                                try:
                                    if it is not self:
                                        it.setSelected(False)
                                except Exception:
                                    continue
                        except Exception:
                            pass
                    self.setSelected(True)
                    try:
                        self.scene._last_selected_items = self.scene.getSelectedItems()
                    except Exception:
                        pass
                except Exception:
                    pass
                super().mousePressEvent(event)
            else:
                # Expanded body is click-through: behave as if the group is not
                # there (plain canvas -> deselect, rubber-band, canvas menu).
                # Children are in front (z) so child clicks still hit children.
                self._can_move = False
                self._last_scene_pos = None
                try:
                    event.ignore()
                except Exception:
                    pass
                return
        except Exception:
            try:
                super().mousePressEvent(event)
            except Exception:
                pass

    def mouseDoubleClickEvent(self, event) -> None:
        # Double-click header renames; body is click-through like press.
        try:
            lp = event.pos()
            if self._toggleRectLocal().contains(lp):
                return
            if lp.y() < float(self.TITLE_BAR_HEIGHT) or self._collapsed:
                if self.renameInteractive():
                    try:
                        self.scene.history.storeHistory("Renamed group", setModified=True)
                    except Exception:
                        pass
                try:
                    event.accept()
                except Exception:
                    pass
                return
            try:
                event.ignore()
            except Exception:
                pass
        except Exception:
            pass

    def mouseMoveEvent(self, event) -> None:
        if not self._can_move:
            return
        try:
            try:
                new_scene = self.mapToScene(event.pos())
            except Exception:
                super().mouseMoveEvent(event)
                return
            if self._last_scene_pos is None:
                self._last_scene_pos = new_scene
                super().mouseMoveEvent(event)
                return
            delta = new_scene - self._last_scene_pos
            self._last_scene_pos = new_scene
            try:
                if not delta.isNull():
                    self._moved = True
            except Exception:
                self._moved = True
            # move hidden or visible children by same delta to preserve layout,
            # skipping selected ones: Qt's selection move already shifts them
            # (otherwise selected children move 2x per drag).
            for node in list(self.child_nodes):
                try:
                    try:
                        gr = getattr(node, 'grNode', None)
                        if gr is not None and gr.isSelected():
                            continue
                    except Exception:
                        pass
                    p = node.pos
                    node.setPos(p.x() + delta.x(), p.y() + delta.y())
                except Exception:
                    continue
            super().mouseMoveEvent(event)
            # keep external stubs glued while dragging collapsed group
            if self._collapsed:
                self.refreshExternalEdges()
        except Exception:
            try:
                super().mouseMoveEvent(event)
            except Exception:
                pass

    def mouseReleaseEvent(self, event) -> None:
        moved = self._can_move
        actually_moved = bool(moved and getattr(self, '_moved', False))
        if not moved:
            # Press was ignored (expanded body click-through): don't let
            # release select the group; let view handle rubber-band/deselect.
            self._can_move = False
            self._last_scene_pos = None
            try:
                self._moved = False
            except Exception:
                pass
            try:
                event.ignore()
            except Exception:
                pass
            return
        self._can_move = False
        self._last_scene_pos = None
        try:
            self._moved = False
        except Exception:
            pass
        try:
            super().mouseReleaseEvent(event)
        except Exception:
            pass
        if actually_moved:
            try:
                # children setPos already updated edges; ensure stubs + history.
                # No history stamp for a plain header click without movement.
                if self._collapsed:
                    self.refreshExternalEdges()
                self.scene.history.storeHistory("Moved group", setModified=True)
            except Exception:
                pass

    def hoverEnterEvent(self, event) -> None:
        try:
            lp = event.pos()
            self._hover_header = lp.y() < float(self.TITLE_BAR_HEIGHT)
            if self._hover_header:
                self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.update()
        except Exception:
            pass
        try:
            super().hoverEnterEvent(event)
        except Exception:
            pass

    def hoverMoveEvent(self, event) -> None:
        try:
            lp = event.pos()
            in_header = lp.y() < float(self.TITLE_BAR_HEIGHT)
            if in_header != self._hover_header:
                self._hover_header = in_header
                self.update()
            if in_header:
                self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            else:
                self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        except Exception:
            pass
        try:
            super().hoverMoveEvent(event)
        except Exception:
            pass

    def hoverLeaveEvent(self, event) -> None:
        self._hover_header = False
        try:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        except Exception:
            pass
        try:
            self.update()
        except Exception:
            pass
        try:
            super().hoverLeaveEvent(event)
        except Exception:
            pass

    def contextMenuEvent(self, event) -> None:
        try:
            # Expanded body is click-through: let canvas context menu handle it.
            # (shape() already excludes the body; this is belt-and-suspenders.)
            try:
                lp = event.pos()
                if (not self._collapsed and lp.y() >= float(self.TITLE_BAR_HEIGHT)
                        and not self._toggleRectLocal().contains(lp)):
                    try:
                        event.ignore()
                    except Exception:
                        pass
                    return
            except Exception:
                pass
            menu = QMenu()
            toggle_act = menu.addAction("Expand" if self._collapsed else "Collapse")
            rename_act = menu.addAction("Rename…")
            color_menu = menu.addMenu("Set color")
            color_actions = {}
            for name in self.GROUP_COLOR_PRESETS:
                color_actions[color_menu.addAction(name)] = name
            custom_color_act = color_menu.addAction("Custom…")
            ungroup_act = menu.addAction("Ungroup (keep nodes)")
            delete_act = menu.addAction("Delete Group + Children")
            try:
                action = menu.exec(event.screenPos())
            except Exception:
                action = None
            if action == toggle_act:
                self.toggleCollapse()
                try:
                    self.scene.history.storeHistory(
                        "Collapsed group" if self._collapsed else "Expanded group",
                        setModified=True)
                except Exception:
                    pass
            elif action == rename_act:
                if self.renameInteractive():
                    try:
                        self.scene.history.storeHistory("Renamed group", setModified=True)
                    except Exception:
                        pass
            elif action in color_actions:
                try:
                    fill, _title = self.GROUP_COLOR_PRESETS[color_actions[action]]
                    if self.setColors(color=fill):
                        self.scene.history.storeHistory("Recolored group", setModified=True)
                except Exception:
                    pass
            elif action == custom_color_act:
                if self.recolorInteractive():
                    try:
                        self.scene.history.storeHistory("Recolored group", setModified=True)
                    except Exception:
                        pass
            elif action == ungroup_act:
                self.ungroup()
                try:
                    self.scene.history.storeHistory("Ungrouped", setModified=True)
                except Exception:
                    pass
            elif action == delete_act:
                self.deleteWithChildren()
                try:
                    self.scene.history.storeHistory("Deleted group", setModified=True)
                except Exception:
                    pass
        except Exception:
            dumpException()

    def paint(self, painter: QPainter, option, widget=None) -> None:
        try:
            rect = self.rect()
            painter.setPen(self.pen())
            painter.setBrush(self.brush())
            painter.drawRoundedRect(rect, 8.0, 8.0)

            title_rect = QRectF(rect.x(), rect.y(), rect.width(), float(self.TITLE_BAR_HEIGHT))
            title_col = QColor(80, 80, 80) if self._hover_header else QColor(60, 60, 60)
            painter.fillRect(title_rect, QBrush(title_col))
            if self._hover_header:
                painter.setPen(QPen(QColor(255, 200, 0), 2))
                painter.drawRect(title_rect)
                painter.setPen(self.pen())

            painter.setPen(QPen(self._title_color))
            label = self.title + (" [Collapsed]" if self._collapsed else "")
            painter.drawText(title_rect,
                             int(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter),
                             label)

            # toggle button (painted, no proxy widget)
            tog = self._toggleRectLocal()
            self._toggle_rect = tog
            painter.setPen(QPen(QColor(200, 200, 200)))
            painter.setBrush(QBrush(QColor(85, 85, 85)))
            painter.drawRect(tog)
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.drawText(tog, int(Qt.AlignmentFlag.AlignCenter), "+" if self._collapsed else "\u2212")

            # drop-target highlight (drag node into group)
            if self._drop_highlight:
                try:
                    hl = QPen(QColor(255, 200, 0), 3)
                    hl.setStyle(Qt.PenStyle.DashLine)
                    painter.setPen(hl)
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 8.0, 8.0)
                    painter.setPen(self.pen())
                except Exception:
                    pass

            # per-edge stub dots on collapsed box
            if self._collapsed:
                try:
                    inc, out, _ = self._classifyEdges()
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QBrush(QColor(255, 255, 255)))
                    r = 3.0
                    for e in inc:
                        p = self.stubPosFor(e)
                        if p is None:
                            continue
                        lp = self.mapFromScene(p)
                        painter.drawEllipse(lp, r, r)
                    for e in out:
                        p = self.stubPosFor(e)
                        if p is None:
                            continue
                        lp = self.mapFromScene(p)
                        painter.drawEllipse(lp, r, r)
                except Exception:
                    pass
        except Exception:
            pass

    # ------------------------------------------------------------------
    # serialization v2 (clean break, best-effort old load as expanded)
    # ------------------------------------------------------------------
    def serialize(self) -> dict:
        try:
            p = self.pos()
            r = self.rect()
        except Exception:
            p = QPointF(0, 0)
            r = QRectF(0, 0, 200, 150)
        return {
            "id": self.id,
            "type": "Group",
            "version": GROUP_SERIALIZATION_VERSION,
            "title": self.title,
            "x": p.x(),
            "y": p.y(),
            "w": r.width(),
            "h": r.height(),
            "collapsed": bool(self._collapsed),
            "children": [getattr(n, 'id', None) for n in self.child_nodes if getattr(n, 'id', None) is not None],
            "style": {
                "color": self._color.getRgb(),
                "title_color": self._title_color.getRgb(),
                "border_color": self._border_color.getRgb(),
            },
        }

    def deserialize(self, data: dict, hashmap: Optional[dict] = None, restore_id: bool = True) -> bool:
        try:
            if restore_id and 'id' in data:
                self.id = data['id']
            self.title = data.get('title', 'Group')
            # clean break: old payloads load as expanded
            is_old = data.get('type') == 'GroupNode' or ('children' not in data and 'child_node_ids' in data)
            if is_old:
                self._collapsed = False
            else:
                self._collapsed = bool(data.get('collapsed', data.get('is_collapsed', False)))
            try:
                if 'x' in data and 'y' in data:
                    self.setPos(float(data['x']), float(data['y']))
                w = float(data.get('w', data.get('width', 200)))
                h = float(data.get('h', data.get('height', 150)))
                self.setRect(0, 0, w, h)
            except Exception:
                pass
            try:
                style = data.get('style', {})
                if isinstance(style, dict):
                    if 'color' in style and isinstance(style['color'], (list, tuple)):
                        self._color = QColor(*style['color'])
                    if 'title_color' in style and isinstance(style['title_color'], (list, tuple)):
                        self._title_color = QColor(*style['title_color'])
                    if 'border_color' in style and isinstance(style['border_color'], (list, tuple)):
                        self._border_color = QColor(*style['border_color'])
                else:
                    # old flat keys
                    if 'color' in data and isinstance(data['color'], (list, tuple)):
                        self._color = QColor(*data['color'])
                    if 'title_color' in data and isinstance(data['title_color'], (list, tuple)):
                        self._title_color = QColor(*data['title_color'])
                    if 'border_color' in data and isinstance(data['border_color'], (list, tuple)):
                        self._border_color = QColor(*data['border_color'])
                try:
                    self.setPen(QPen(self._border_color, self._border_width))
                    self.setBrush(QBrush(self._color))
                except Exception:
                    pass
            except Exception:
                pass
            # children linked by Scene after all groups deserialized
            return True
        except Exception as e:
            dumpException(e)
            return False

    def applyCollapsedAfterLoad(self) -> None:
        """Apply collapsed visuals after Scene linked children (no history)."""
        try:
            if not self._collapsed:
                return
            if not self.child_nodes:
                self._updateCollapsedSize()
                return
            for node in list(self.child_nodes):
                try:
                    gr = getattr(node, 'grNode', None)
                    if gr is not None:
                        gr.hide()
                except Exception:
                    continue
            try:
                _, _, internal = self._classifyEdges()
                for e in internal:
                    try:
                        if getattr(e, 'grEdge', None) is not None:
                            e.grEdge.hide()
                    except Exception:
                        continue
            except Exception:
                pass
            self._updateCollapsedSize()
            self.refreshExternalEdges()
            self.update()
        except Exception:
            pass


# Backward-compatible alias (old imports keep working)
GroupNode = Group
