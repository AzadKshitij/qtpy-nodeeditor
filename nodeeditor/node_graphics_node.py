# -*- coding: utf-8 -*-
"""
A module containing Graphics representation of :class:`~nodeeditor.node_node.Node`
"""
from qtpy.QtWidgets import QGraphicsItem, QWidget, QGraphicsTextItem, QGraphicsSceneHoverEvent
from qtpy.QtGui import QFont, QColor, QPen, QBrush, QPainterPath, QTextCursor
from qtpy.QtCore import Qt, QRectF

from typing import TYPE_CHECKING, List, Optional, Tuple, Any

from nodeeditor.node_colors_config import get_color_scheme


if TYPE_CHECKING:
    from nodeeditor.node_graphics_view import QDMGraphicsView
    from nodeeditor.node_edge import Edge
    from nodeeditor.node_socket import Socket
    from nodeeditor.node_node import Node


class QDMGraphicsNodeLabel(QGraphicsTextItem):
    """Single-line editable textbox floating above a `QDMGraphicsNode`.

    Parented to the graphics node, so Qt moves it with the node for free.
    Click to focus/edit; ``Enter`` commits, ``Escape`` reverts, focus-out commits.
    """

    def __init__(self, grNode: 'QDMGraphicsNode', parent: QGraphicsItem = None) -> None:
        super().__init__(parent if parent is not None else grNode)
        self._grNode: 'QDMGraphicsNode' = grNode
        self._last_text: str = ""
        self._bg_color = QColor("#E3212121")
        self._border_color = QColor("#FF5A5A5A")
        self._pad_x: float = 6.0
        self._pad_y: float = 3.0
        self._radius: float = 6.0
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        self.setZValue(1)
        try:
            self.document().contentsChanged.connect(self._onContentsChanged)
        except Exception:
            pass

    @staticmethod
    def sanitize(text: str) -> str:
        """Force single-line plain text."""
        if text is None:
            return ""
        return str(text).replace("\r", " ").replace("\n", " ").strip()

    def setLabelColors(self, bg: Optional[QColor] = None, border: Optional[QColor] = None) -> None:
        if bg is not None:
            self._bg_color = bg
        if border is not None:
            self._border_color = border
        self.update()

    def focusInEvent(self, event) -> None:
        self._last_text = self.toPlainText()
        self._setEditing(True)
        super().focusInEvent(event)

    def focusOutEvent(self, event) -> None:
        self._commit()
        self._setEditing(False)
        super().focusOutEvent(event)

    def keyPressEvent(self, event) -> None:
        try:
            key = event.key()
        except Exception:
            return super().keyPressEvent(event)
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            event.accept()
            self.clearFocus()
            return
        if key == Qt.Key.Key_Escape:
            try:
                self.setPlainText(self._last_text)
            except Exception:
                pass
            event.accept()
            self.clearFocus()
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event) -> None:
        try:
            if not self.hasFocus():
                self.setFocus(Qt.FocusReason.MouseFocusReason)
        except Exception:
            pass
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        try:
            if not self.hasFocus():
                self.setFocus(Qt.FocusReason.MouseFocusReason)
            cursor = self.textCursor()
            cursor.select(QTextCursor.SelectionType.Document)
            self.setTextCursor(cursor)
        except Exception:
            pass
        super().mouseDoubleClickEvent(event)

    def paint(self, painter, option, widget=None) -> None:
        rect = self.boundingRect().adjusted(-self._pad_x, -self._pad_y, self._pad_x, self._pad_y)
        painter.setPen(QPen(self._border_color, 1.0))
        painter.setBrush(QBrush(self._bg_color))
        painter.drawRoundedRect(rect, self._radius, self._radius)
        super().paint(painter, option, widget)

    def _onContentsChanged(self) -> None:
        try:
            self._grNode._updateLabelPos()
        except Exception:
            pass

    def _commit(self) -> None:
        text = self.sanitize(self.toPlainText())
        if text != self.toPlainText():
            try:
                self.document().blockSignals(True)
                self.setPlainText(text)
            finally:
                try:
                    self.document().blockSignals(False)
                except Exception:
                    pass
        try:
            self._grNode._updateLabelPos()
        except Exception:
            pass
        try:
            self._grNode._onLabelEdited(text)
        except Exception:
            pass

    def _setEditing(self, value: bool) -> None:
        try:
            view = self._grNode.node.scene.getView()
            view.editingFlag = value
        except Exception:
            pass


class QDMGraphicsNode(QGraphicsItem):
    """Class describing Graphics representation of :class:`~nodeeditor.node_node.Node`"""

    def __init__(self, node: 'Node', parent: QGraphicsItem = None) -> None:
        """
        :param node: reference to :class:`~nodeeditor.node_node.Node`
        :type node: :class:`~nodeeditor.node_node.Node`
        :param parent: parent widget
        :type parent: QWidget

        :Instance Attributes:

            - **node** - reference to :class:`~nodeeditor.node_node.Node`
        """
        super().__init__(parent)
        self.node: 'Node' = node

        # init our flags
        self.hovered: bool = False
        self._was_moved: bool = False
        self._last_selected_state: bool = False

        self.initSizes()
        self.initAssets()
        self.initUI()

    @property
    def content(self):
        """Reference to `Node Content`"""
        return self.node.content if self.node else None

    @property
    def title(self):
        """title of this `Node`

        :getter: current Graphics Node title
        :setter: stores and make visible the new title
        :type: str
        """
        return self._title

    @title.setter
    def title(self, value) -> None:
        self._title = value
        self.title_item.setPlainText(self._title)

    def initUI(self) -> None:
        """Set up this ``QGraphicsItem``"""
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setAcceptHoverEvents(True)

        # init title
        self.initTitle()
        # self.title = self.node.title

        self.initContent()
        self.initLabel()

    def initSizes(self) -> None:
        """Set up internal attributes like `width`, `height`, etc."""
        self.width: float = 180
        self.height: float = 240
        self.edge_roundness = 10.0
        self.edge_padding = 10
        self.title_height = 24
        self.title_horizontal_padding = 4.0
        self.title_vertical_padding = 4.0
        self.label_offset: float = 10.0
        self._label_visible: bool = False

    def initAssets(self) -> None:
        """Initialize ``QObjects`` like ``QColor``, ``QPen`` and ``QBrush``"""
        self._title_color = Qt.GlobalColor.white
        self._title_font = QFont("Ubuntu", 10)

        # Get colors from global color scheme
        scheme = get_color_scheme()
        self._color = QColor("#7F000000")
        self._color_selected = QColor("#FFFFA637")
        self._color_hovered = scheme.edges.hovered

        self._pen_default = QPen(self._color)
        self._pen_default.setWidthF(2.0)
        self._pen_selected = QPen(self._color_selected)
        self._pen_selected.setWidthF(2.0)
        self._pen_hovered = QPen(self._color_hovered)
        self._pen_hovered.setWidthF(3.0)

        self._brush_title = QBrush(QColor("#FF313131"))
        self._brush_background = QBrush(QColor("#E3212121"))

        self._label_font = QFont("Ubuntu", 9)
        self._label_color = QColor("#EEEEEE")

    def onSelected(self) -> None:
        """Our event handling when the node was selected"""
        self.node.scene.grScene.itemSelected.emit()

    def doSelect(self, new_state: bool = True) -> None:
        """Safe version of selecting the `Graphics Node`. Takes care about the selection state flag used internally

        :param new_state: ``True`` to select, ``False`` to deselect
        :type new_state: ``bool``
        """
        self.setSelected(new_state)
        self._last_selected_state = new_state
        if new_state:
            self.onSelected()

    def mousePressEvent(self, event) -> None:
        # Collapsed groups hide child grNodes, so no special guard needed.
        # Keep default Qt behavior (move/select).
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """Overridden event to detect that we moved with this `Node`"""
        super().mouseMoveEvent(event)
        if self.scene() is None:
            return
        # optimize me! just update the selected nodes
        for node in self.scene().scene.nodes:
            if node.grNode.isSelected():
                node.updateConnectedEdges()
        self._was_moved = True

    def mouseReleaseEvent(self, event) -> None:
        """Overriden event to handle when we moved, selected or deselected this `Node`"""
        super().mouseReleaseEvent(event)

        # handle when grNode moved
        if self._was_moved:
            try:
                self.node.positionChanged.emit(self.node)
            except Exception:
                pass

            self._was_moved = False
            self.node.scene.history.storeHistory(
                "Node moved", setModified=True)

            self.node.scene.resetLastSelectedStates()
            self.doSelect()     # also trigger itemSelected when node was moved

            # we need to store the last selected state, because moving does also select the nodes
            self.node.scene._last_selected_items = self.node.scene.getSelectedItems()

            # Emit signal to notify that node position has changed (for group boundary checks)

            # now we want to skip storing selection
            return

        # handle when grNode was clicked on
        if self._last_selected_state != self.isSelected() or self.node.scene._last_selected_items != self.node.scene.getSelectedItems():
            self.node.scene.resetLastSelectedStates()
            self._last_selected_state = self.isSelected()
            self.onSelected()

    def mouseDoubleClickEvent(self, event) -> None:
        """Overriden event for doubleclick. Resend to `Node::onDoubleClicked`"""
        self.node.onDoubleClicked(event)

    def hoverEnterEvent(self, event: Optional['QGraphicsSceneHoverEvent']) -> None:
        """Handle hover effect"""
        self.hovered = True
        self.update()

    def hoverLeaveEvent(self, event: Optional['QGraphicsSceneHoverEvent']) -> None:
        """Handle hover effect"""
        self.hovered = False
        self.update()

    def boundingRect(self) -> QRectF:
        """Defining Qt' bounding rectangle"""
        return QRectF(
            0,
            0,
            self.width,
            self.height
        ).normalized()

    def initTitle(self) -> None:
        """Set up the title Graphics representation: font, color, position, etc."""
        self.title_item = QGraphicsTextItem(self)
        self.title = self.node.title
        self.title_item.node = self.node
        self.title_item.setDefaultTextColor(self._title_color)
        self.title_item.setFont(self._title_font)

        # Calculate horizontal and vertical center positions
        horizontal_center = (self.boundingRect().width(
        ) - self.title_item.boundingRect().width()) / 2
        vertical_center = (self.title_height -
                           self.title_item.boundingRect().height()) / 2

        self.title_item.setPos(horizontal_center, vertical_center)

    def initContent(self) -> None:
        """Set up the `grContent` - ``QGraphicsProxyWidget`` to have a container for `Graphics Content`"""
        if self.content is not None:
            self.content.setGeometry(self.edge_padding, self.title_height + self.edge_padding,
                                     self.width - 2 * self.edge_padding, self.height - 2 * self.edge_padding - self.title_height)

        # get the QGraphicsProxyWidget when inserted into the grScene
        self.grContent = self.node.scene.grScene.addWidget(self.content)
        self.grContent.node = self.node
        self.grContent.setParentItem(self)

    def initLabel(self) -> None:
        """Create the floating single-line label above the node (hidden until text is set)."""
        self.label_item = QDMGraphicsNodeLabel(self, self)
        self.label_item.setFont(self._label_font)
        self.label_item.setDefaultTextColor(self._label_color)
        self._label_visible = False
        self.label_item.setVisible(False)
        self._updateLabelPos()

    def setLabelText(self, text: str) -> None:
        """Set label text (single-line). Empty text hides the label. No history stored."""
        text = QDMGraphicsNodeLabel.sanitize(text)
        self.label_item.setPlainText(text)
        if text:
            self._label_visible = True
        self._refreshLabelVisibility()
        self._updateLabelPos()

    def labelText(self) -> str:
        """Return current label text."""
        try:
            return self.label_item.toPlainText()
        except Exception:
            return ""

    def setLabelVisible(self, visible: bool) -> None:
        """Show/hide the label. Hidden when text is empty regardless."""
        self._label_visible = bool(visible)
        self._refreshLabelVisibility()

    def isLabelVisible(self) -> bool:
        return bool(self._label_visible and bool(self.labelText()))

    def setLabelOffset(self, offset: float) -> None:
        """Gap in px between node top and label bottom."""
        self.label_offset = float(offset)
        self._updateLabelPos()

    def labelOffset(self) -> float:
        return float(self.label_offset)

    def setLabelColor(self, color) -> None:
        self._label_color = QColor(color) if not isinstance(color, QColor) else color
        self.label_item.setDefaultTextColor(self._label_color)

    def setLabelFont(self, font: QFont) -> None:
        self._label_font = font
        self.label_item.setFont(font)
        self._updateLabelPos()

    def setLabelBackground(self, bg, border=None) -> None:
        bg = QColor(bg) if not isinstance(bg, QColor) else bg
        b = QColor(border) if border is not None and not isinstance(border, QColor) else border
        self.label_item.setLabelColors(bg=bg, border=b)

    def _refreshLabelVisibility(self) -> None:
        try:
            self.label_item.setVisible(bool(self._label_visible and bool(self.label_item.toPlainText())))
        except Exception:
            pass

    def _updateLabelPos(self) -> None:
        """Center label horizontally above the node."""
        try:
            w = self.label_item.boundingRect().width()
            h = self.label_item.boundingRect().height()
            self.label_item.setPos((self.width - w) / 2, -h - self.label_offset)
        except Exception:
            pass

    def _onLabelEdited(self, text: str) -> None:
        """Called by label item on user commit. Syncs visibility, emits signal, stores history."""
        text = QDMGraphicsNodeLabel.sanitize(text)
        if text:
            self._label_visible = True
        self._refreshLabelVisibility()
        self._updateLabelPos()
        try:
            self.node.labelChanged.emit(text)
        except Exception:
            pass
        try:
            self.node.scene.history.storeHistory("Node label changed", setModified=True)
        except Exception:
            pass

    def paint(self, painter, QStyleOptionGraphicsItem, widget=None) -> None:
        """Painting the rounded rectanglar `Node`"""
        # title
        path_title = QPainterPath()
        path_title.setFillRule(Qt.WindingFill)
        path_title.addRoundedRect(
            0, 0, self.width, self.title_height, self.edge_roundness, self.edge_roundness)
        path_title.addRect(0, self.title_height - self.edge_roundness,
                           self.edge_roundness, self.edge_roundness)
        path_title.addRect(self.width - self.edge_roundness, self.title_height -
                           self.edge_roundness, self.edge_roundness, self.edge_roundness)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._brush_title)
        painter.drawPath(path_title.simplified())

        # content
        path_content = QPainterPath()
        path_content.setFillRule(Qt.WindingFill)
        path_content.addRoundedRect(0, self.title_height, self.width, self.height -
                                    self.title_height, self.edge_roundness, self.edge_roundness)
        path_content.addRect(0, self.title_height,
                             self.edge_roundness, self.edge_roundness)
        path_content.addRect(self.width - self.edge_roundness,
                             self.title_height, self.edge_roundness, self.edge_roundness)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._brush_background)
        painter.drawPath(path_content.simplified())

        # outline
        path_outline = QPainterPath()
        path_outline.addRoundedRect(-1, -1, self.width+2,
                                    self.height+2, self.edge_roundness, self.edge_roundness)
        painter.setBrush(Qt.NoBrush)
        if self.hovered:
            painter.setPen(self._pen_hovered)
            painter.drawPath(path_outline.simplified())
            painter.setPen(self._pen_default)
            painter.drawPath(path_outline.simplified())
        else:
            painter.setPen(
                self._pen_default if not self.isSelected() else self._pen_selected)
            painter.drawPath(path_outline.simplified())
