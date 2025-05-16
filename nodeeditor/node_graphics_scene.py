# -*- coding: utf-8 -*-
"""
A module containing Graphic representation of :class:`~nodeeditor.node_scene.Scene`
"""
from array import array
import math
from qtpy import PYSIDE2
from qtpy.QtWidgets import QGraphicsScene, QWidget
from qtpy.QtCore import Signal, QRectF, QLine, Qt, Property
from qtpy.QtGui import QColor, QPen, QFont, QPainter
from nodeeditor.utils import dumpException
from nodeeditor.node_graphics_view import STATE_STRING, DEBUG_STATE

from typing import TYPE_CHECKING, List, Optional, Tuple, Any


if TYPE_CHECKING:
    from nodeeditor.node_graphics_view import QDMGraphicsView
    from nodeeditor.node_edge import Edge
    from nodeeditor.node_socket import Socket
    from nodeeditor.node_scene import Scene


class QDMGraphicsScene(QGraphicsScene):
    """Class representing Graphic of :class:`~nodeeditor.node_scene.Scene`"""
    #: pyqtSignal emitted when some item is selected in the `Scene`
    itemSelected = Signal()
    #: pyqtSignal emitted when items are deselected in the `Scene`
    itemsDeselected = Signal()

    gridColorLightChanged = Signal()
    gridColorDarkChanged = Signal()
    backgroundColorChanged = Signal()

    def __init__(self, scene: 'Scene', parent: QWidget = None) -> None:
        """
        :param scene: reference to the :class:`~nodeeditor.node_scene.Scene`
        :type scene: :class:`~nodeeditor.node_scene.Scene`
        :param parent: parent widget
        :type parent: QWidget
        """
        super().__init__(parent)

        self.scene: 'Scene' = scene

        # There is an issue when reconnecting edges -> mouseMove and trying to delete/remove them
        # the edges stayed in the scene in Qt, however python side was deleted
        # this caused a lot of troubles...
        #
        # I've spend months to find this sh*t!!
        #
        # https://bugreports.qt.io/browse/QTBUG-18021
        # https://bugreports.qt.io/browse/QTBUG-50691
        # Affected versions: 4.7.1, 4.7.2, 4.8.0, 5.5.1, 5.7.0 - LOL!
        self.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.NoIndex)

        # settings
        self.gridSize = 20
        self.gridSquares = 5
        self._show_grid = True

        self._color_background = QColor("#393939")
        self._color_light = QColor("#2f2f2f")
        self._color_dark = QColor("#292929")
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

    def drawBackground(self, painter: Optional[QPainter], rect: QRectF) -> None:
        """Draw background scene grid"""
        super().drawBackground(painter, rect)

        if self.showGrid is False:
            return

        # here we create our grid
        left = int(math.floor(rect.left()))
        right = int(math.ceil(rect.right()))
        top = int(math.floor(rect.top()))
        bottom = int(math.ceil(rect.bottom()))

        first_left = left - (left % self.gridSize)
        first_top = top - (top % self.gridSize)

        # compute all lines to be drawn
        lines_light: List[QLine] = []
        lines_dark: List[QLine] = []

        for x in range(first_left, right, self.gridSize):
            if (x % (self.gridSize*self.gridSquares) != 0):
                lines_light.append(QLine(x, top, x, bottom))
            else:
                lines_dark.append(QLine(x, top, x, bottom))

        for y in range(first_top, bottom, self.gridSize):
            if (y % (self.gridSize*self.gridSquares) != 0):
                lines_light.append(QLine(left, y, right, y))
            else:
                lines_dark.append(QLine(left, y, right, y))
        if painter is not None:
            # draw the lines
            painter.setPen(self._pen_light)
            if PYSIDE2:
                # supporting PySide2
                painter.drawLines(lines_light)  # type: ignore
            else:
                # supporting PyQt5
                painter.drawLines(*lines_light)

            painter.setPen(self._pen_dark)
            if PYSIDE2:
                # supporting PySide2
                painter.drawLines(lines_light)  # type: ignore
            else:
                # supporting PyQt5
                painter.drawLines(*lines_dark)

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
