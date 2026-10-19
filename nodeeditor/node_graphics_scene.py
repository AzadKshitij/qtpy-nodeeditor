# -*- coding: utf-8 -*-
"""
A module containing Graphic representation of :class:`~nodeeditor.node_scene.Scene`
"""
from array import array
import math
from qtpy.QtWidgets import QGraphicsScene, QWidget
from qtpy.QtCore import Signal, QRectF, QLine, Qt, Property, QObject
from qtpy.QtGui import QColor, QPen, QFont, QPainter
from nodeeditor.utils import dumpException
from nodeeditor.node_graphics_view import STATE_STRING, DEBUG_STATE

from typing import TYPE_CHECKING, List, Mapping, Optional, Tuple, Any


#: How `QGraphicsScene` indexes its items.
#:
#: The class used to force ``NoIndex`` to dodge QTBUG-18021 (an item left
#: dangling after being removed while an event was being delivered, affecting
#: Qt 4.7 - 5.7). That bug was fixed years ago; ``NoIndex`` makes every paint
#: culling pass, hit test, rubber-band query and highlight scan walk the entire
#: item list, which is what made a few hundred nodes crawl. ``BspTreeIndex`` is
#: Qt's default and turns those into log-time queries.
DEFAULT_ITEM_INDEX_METHOD = QGraphicsScene.ItemIndexMethod.BspTreeIndex


if TYPE_CHECKING:
    from nodeeditor.node_graphics_view import QDMGraphicsView
    from nodeeditor.node_edge import Edge
    from nodeeditor.node_socket import Socket
    from nodeeditor.node_scene import Scene


class QDMGraphicsScene(QGraphicsScene):
    """Class representing Graphic of :class:`~nodeeditor.node_scene.Scene`"""
    #: pyqtSignal emitted when some item is selected in the `Scene`
    itemSelected = Signal()
    socketClicked = Signal(QObject, QObject)  # (socket, node)
    #: pyqtSignal emitted when items are deselected in the `Scene`
    itemsDeselected = Signal()

    gridColorLightChanged = Signal()
    gridColorDarkChanged = Signal()
    backgroundColorChanged = Signal()

    #: Below this on-screen spacing (in pixels) a grid level is not drawn: its
    #: lines are closer together than they are wide, so they read as a wash and
    #: cost time proportional to the number of lines in view.
    MIN_GRID_SPACING_PX = 4.0

    #: Below this on-screen scale, items are asked to drop their fine detail
    #: (see :meth:`updateDetailLod` / :meth:`setDetailLod`). At half size a
    #: node's label text and its
    #: status sprite are illegible, while the widget, sprite and socket draws
    #: they cost dominate a frame once hundreds of nodes share the viewport.
    DETAIL_LOD_THRESHOLD = 0.5

    #: The parts of a node the level-of-detail switch can drop. An application
    #: may register elements of its own (see :meth:`set_detail_policy`).
    DETAIL_ELEMENTS = ("content", "label", "sockets")

    #: How an element behaves when the canvas simplifies: always drawn, drawn
    #: only while the zoom warrants it, or never drawn.
    DETAIL_MODES = ("always", "auto", "never")

    def __init__(self, scene: 'Scene', parent: QWidget = None) -> None:
        """
        :param scene: reference to the :class:`~nodeeditor.node_scene.Scene`
        :type scene: :class:`~nodeeditor.node_scene.Scene`
        :param parent: parent widget
        :type parent: QWidget
        """
        super().__init__(parent)

        self.scene: 'Scene' = scene

        # Kept for the record: QTBUG-18021 ("reconnecting/removing edges during
        # a mouse move leaves them in the scene") is why this used to be
        # ``NoIndex``. The affected versions were 4.7.1 - 5.7.0; the linear
        # index it forced is ruinous for a large graph, so the default BSP
        # index is back (see DEFAULT_ITEM_INDEX_METHOD).
        self.setItemIndexMethod(DEFAULT_ITEM_INDEX_METHOD)

        # settings
        self.gridSize = 20
        self.gridSquares = 5
        self._show_grid = True

        #: Current level-of-detail state broadcast to items (see
        #: :meth:`setDetailLod`). Starts fully detailed.
        self._detail_visible = True

        #: Zoom scale at which items are asked to drop their fine detail. Per
        #: instance, so an application can move the point where the canvas
        #: simplifies without touching the class default.
        self.detail_lod_threshold = float(self.DETAIL_LOD_THRESHOLD)

        #: Per-element detail modes, seeded with the library's own elements.
        self.detail_policy: dict[str, str] = {
            name: "auto" for name in self.DETAIL_ELEMENTS
        }

        #: Resolved per-element state, recomputed on every flip.
        self._detail_state: dict[str, bool] = {}
        self._resolve_detail_state()

        self._color_background = QColor("#14171a")
        self._color_light = QColor("#1d2225")
        self._color_dark = QColor("#1d2225")
        self._color_state = QColor("#ccc")

        self.initAssets()
        self.setBackgroundBrush(self._color_background)

    def getGridColorLight(self) -> QColor:
        """Get the light grid color"""
        print("🐍 File: nodeeditor/node_graphics_scene.py:71 | __init__ ~ getGridColorLight")
        return self._color_light

    def setGridColorLight(self, color: QColor) -> None:
        """Set the light grid color"""
        print("🐍 File: nodeeditor/node_graphics_scene.py:76 | getGridColorLight ~ setGridColorLight", color)
        self._color_light = color
        self._pen_light.setColor(color)
        self.update()

    def getGridColorDark(self) -> QColor:
        """Get the dark grid color"""
        return self._color_dark

    def setGridColorDark(self, color: QColor) -> None:
        """Set the dark grid color"""
        self._color_dark = color
        self._pen_dark.setColor(color)
        self.update()

    def getBackgroundColor(self) -> QColor:
        """Get the background color"""
        return self._color_background

    def setBackgroundColor(self, color: QColor) -> None:
        """Set the background color"""
        self._color_background = color
        self.setBackgroundBrush(color)

    gridColorLight = Property(
        QColor, fget=getGridColorLight, fset=setGridColorLight, notify=gridColorLightChanged)
    gridColorDark = Property(
        QColor, fget=getGridColorDark, fset=setGridColorDark, notify=gridColorDarkChanged)
    backgroundColor = Property(
        QColor, fget=getBackgroundColor, fset=setBackgroundColor, notify=backgroundColorChanged)

    def initAssets(self) -> None:
        """Initialize ``QObjects`` like ``QColor``, ``QPen`` and ``QBrush``"""

        # Initialize pens and fonts
        self._pen_light = QPen(self._color_light)
        self._pen_light.setWidth(1)
        self._pen_dark = QPen(self._color_dark)
        self._pen_dark.setWidth(2)

        self._pen_state = QPen(self._color_state)
        self._font_state = QFont("Ubuntu", 16)

    # the drag events won't be allowed until dragMoveEvent is overwritten

    @property
    def showGrid(self) -> bool:
        """
        Get grid visibility state

        Returns:
            bool: True if grid is visible, False otherwise
        """
        return self._show_grid

    @showGrid.setter
    def showGrid(self, value: bool) -> None:
        """
        Set grid visibility state and update the scene

        Args:
            value: True to show grid, False to hide
        """
        self._show_grid = value
        self.update()  # Refresh the scene when grid visibility changes

    def dragMoveEvent(self, event) -> None:
        """Overriden Qt's dragMoveEvent to enable Qt's Drag Events"""
        pass

    def setGrScene(self, width: int, height: int) -> None:
        """Set `width` and `height` of the `Graphics Scene`"""
        self.setSceneRect(-width // 2, -height // 2, width, height)

    def updateDetailLod(self, scale: float) -> bool:
        """Match the items' detail to `scale`; ``True`` when the state flipped.

        Only a float comparison per frame; the broadcast to items runs once per
        flip. Callers must not be inside a paint pass - see
        :meth:`setDetailLod`.
        """
        visible = scale >= self.detail_lod_threshold
        if visible == self._detail_visible:
            return False
        self.setDetailLod(visible)
        return True

    def setDetailLod(self, visible: bool) -> None:
        """Tell every item that cares whether the current zoom warrants detail.

        Never call this while the scene is being painted. Hiding an item during
        a paint pass leaves the pixels it had already claimed on screen, and
        those ghosts then travel with the next scroll - which is why the view
        decides this before it paints rather than from ``drawBackground``.
        """
        if visible == self._detail_visible:
            return
        self._detail_visible = visible
        self._resolve_detail_state()
        self._broadcast_detail_state()

    def set_detail_policy(self, policy: Mapping[str, str]) -> None:
        """Say what each element may do when the canvas simplifies.

        ``policy`` maps an element key to ``always``, ``auto`` or ``never``.
        ``auto`` follows the zoom threshold, ``always`` keeps the element at
        every zoom and ``never`` drops it at every zoom. Keys the library does
        not know are kept, so an application can register an element of its own
        and read the answer back with :meth:`detail_enabled`.
        """
        cleaned: dict[str, str] = {}
        for key, mode in dict(policy).items():
            mode = str(mode).strip().lower()
            if mode not in self.DETAIL_MODES:
                print(
                    f"nodeeditor: unknown detail mode {mode!r} for {key!r}, ignored"
                )
                continue
            cleaned[str(key)] = mode
        merged = dict(self.detail_policy)
        merged.update(cleaned)
        if merged == self.detail_policy:
            return
        self.detail_policy = merged
        self._resolve_detail_state()
        self._broadcast_detail_state()

    def detail_enabled(self, element: str) -> bool:
        """Whether ``element`` should be drawn at the current zoom."""
        return self._detail_state.get(element, self._detail_visible)

    def detail_state(self) -> dict[str, bool]:
        """The resolved per-element state, plus the zoom state under "detail"."""
        state = dict(self._detail_state)
        state["detail"] = self._detail_visible
        return state

    def _resolve_detail_state(self) -> None:
        """Turn the policy and the zoom state into one on/off map."""
        state: dict[str, bool] = {}
        for key, mode in self.detail_policy.items():
            if mode == "always":
                state[key] = True
            elif mode == "never":
                state[key] = False
            else:
                state[key] = self._detail_visible
        self._detail_state = state

    def _broadcast_detail_state(self) -> None:
        """Hand the resolved state to every item that cares about it."""
        state = self.detail_state()
        for item in self.items():
            setter = getattr(item, "setDetailState", None)
            if setter is not None:
                try:
                    setter(dict(state))
                except RuntimeError:
                    pass  # C++ side already gone
                continue
            setter = getattr(item, "setDetailVisible", None)
            if setter is not None:
                try:
                    setter(self._detail_visible)
                except RuntimeError:
                    pass  # C++ side already gone

    def drawBackground(self, painter: Optional[QPainter], rect: QRectF) -> None:
        """Draw background scene grid"""
        super().drawBackground(painter, rect)

        if painter is None:
            return

        if self.showGrid is False:
            return

        scale = abs(painter.transform().m11())

        # Zoom level decides which grid levels are worth drawing at all. When a
        # level's spacing collapses below MIN_GRID_SPACING_PX its lines land on
        # top of each other, so they cost a per-line Python loop and a huge
        # drawLines batch to produce a uniform wash. Zoomed out over a big
        # graph that is most of a frame, so drop to the major lines and, past
        # that, drop the grid entirely.
        major_step = self.gridSize * self.gridSquares
        draw_minor = self.gridSize * scale >= self.MIN_GRID_SPACING_PX
        if major_step * scale < self.MIN_GRID_SPACING_PX:
            return

        # here we create our grid
        left = int(math.floor(rect.left()))
        right = int(math.ceil(rect.right()))
        top = int(math.floor(rect.top()))
        bottom = int(math.ceil(rect.bottom()))

        # Only walk the minor step when the minor lines are actually drawn.
        step = self.gridSize if draw_minor else major_step
        first_left = left - (left % step)
        first_top = top - (top % step)

        # compute all lines to be drawn
        lines_light: List[QLine] = []
        lines_dark: List[QLine] = []

        for x in range(first_left, right, step):
            if (x % major_step != 0):
                lines_light.append(QLine(x, top, x, bottom))
            else:
                lines_dark.append(QLine(x, top, x, bottom))

        for y in range(first_top, bottom, step):
            if (y % major_step != 0):
                lines_light.append(QLine(left, y, right, y))
            else:
                lines_dark.append(QLine(left, y, right, y))

        # The grid is axis aligned, so antialiasing cannot smooth anything; it
        # only blends every line into its neighbours and costs time.
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        try:
            if lines_light:
                painter.setPen(self._pen_light)
                painter.drawLines(lines_light)
            if lines_dark:
                painter.setPen(self._pen_dark)
                painter.drawLines(lines_dark)
        finally:
            painter.restore()

        if DEBUG_STATE:
            try:
                view = self.views()[0]
                if not isinstance(view, QDMGraphicsView):
                    return
                painter.setFont(self._font_state)
                painter.setPen(self._pen_state)
                painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
                offset = 14
                rect_state = QRectF(rect.x()+offset,
                                    rect.y()+offset,
                                    rect.width()-2*offset,
                                    rect.height()-2*offset)
                painter.drawText(rect_state, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop,
                                 STATE_STRING[view.mode].upper())
            except:
                dumpException()
