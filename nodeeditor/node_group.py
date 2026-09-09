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
from qtpy.QtGui import QColor, QPainter, QPen, QBrush, QCursor
from qtpy.QtWidgets import QGraphicsRectItem, QGraphicsItem, QMenu

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
        self._last_scene_pos: Optional[QPointF] = None
        self._toggle_rect = QRectF()

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
        """Auto-expand only. Never auto-remove (explicit Ungroup instead)."""
        try:
            if self._collapsed:
                return
            if node not in self.child_nodes:
                return
            gr = getattr(node, 'grNode', None)
            if gr is None:
                return
            try:
                lb = gr.boundingRect()
            except Exception:
                return
            nx = node.pos.x() + lb.left()
            ny = node.pos.y() + lb.top()
            nr = node.pos.x() + lb.right()
            nb = node.pos.y() + lb.bottom()
            gp = self.pos()
            grct = self.rect()
            gl = gp.x()
            gt = gp.y()
            grr = gp.x() + grct.width()
            gbb = gp.y() + grct.height()
            content_top = gt + float(self.TITLE_BAR_HEIGHT)
            if nx < gl or nr > grr or ny < content_top or nb > gbb:
                self.updateBounds()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # edge classification + per-edge stub rows
    # ------------------------------------------------------------------
    def _classifyEdges(self) -> Tuple[List['Edge'], List['Edge'], List['Edge']]:
        """Return (incoming, outgoing, internal). Incoming=end inside, outgoing=start inside."""
        child_set: Set[int] = set(id(n) for n in self.child_nodes)
        # map id(node) -> node for quick lookup
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
                s_in = sn is not None and id(sn) in child_set
                e_in = en is not None and id(en) in child_set
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
                try:
                    self._last_scene_pos = self.mapToScene(lp)
                except Exception:
                    self._last_scene_pos = None
                try:
                    self.setSelected(True)
                except Exception:
                    pass
                super().mousePressEvent(event)
            else:
                self._can_move = False
                self._last_scene_pos = None
                # select group on body click but don't start a move; children
                # are in front (z) so child clicks go to children first
                super().mousePressEvent(event)
        except Exception:
            try:
                super().mousePressEvent(event)
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
            # move hidden or visible children by same delta to preserve layout
            for node in list(self.child_nodes):
                try:
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
        self._can_move = False
        self._last_scene_pos = None
        try:
            super().mouseReleaseEvent(event)
        except Exception:
            pass
        if moved:
            try:
                # children setPos already updated edges; ensure stubs + history
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
            menu = QMenu()
            toggle_act = menu.addAction("Expand" if self._collapsed else "Collapse")
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
