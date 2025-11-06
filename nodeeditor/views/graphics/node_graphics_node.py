# -*- coding: utf-8 -*-
"""
A module containing Graphics representation of :class:`~nodeeditor.node_node.Node`

Refactored for MVC architecture - responds to NodeModel signals for title/position changes.
"""
from qtpy.QtWidgets import QGraphicsItem, QWidget, QGraphicsTextItem, QGraphicsSceneHoverEvent
from qtpy.QtGui import QFont, QColor, QPen, QBrush, QPainterPath
from qtpy.QtCore import Qt, QRectF

from typing import TYPE_CHECKING, List, Optional, Tuple, Any


if TYPE_CHECKING:
    from .node_graphics_view import QDMGraphicsView
    from nodeeditor.node_edge import Edge
    from nodeeditor.node_socket import Socket
    from nodeeditor.node_node import Node


class QDMGraphicsNode(QGraphicsItem):
    """
    Graphics representation of Node with MVC signal integration.
    
    Responds to NodeModel signals for real-time graphics updates.
    Graphics state is derived from model state via signals.
    """

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

        # Connect to model signals for real-time updates
        self._connect_model_signals()

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

    def initSizes(self) -> None:
        """Set up internal attributes like `width`, `height`, etc."""
        self.width: float = 180
        self.height: float = 240
        self.edge_roundness = 10.0
        self.edge_padding = 10
        self.title_height = 24
        self.title_horizontal_padding = 4.0
        self.title_vertical_padding = 4.0

    def initAssets(self) -> None:
        """Initialize ``QObjects`` like ``QColor``, ``QPen`` and ``QBrush``"""
        self._title_color = Qt.GlobalColor.white
        self._title_font = QFont("Ubuntu", 10)

        self._color = QColor("#7F000000")
        self._color_selected = QColor("#FFFFA637")
        self._color_hovered = QColor("#FF37A6FF")

        self._pen_default = QPen(self._color)
        self._pen_default.setWidthF(2.0)
        self._pen_selected = QPen(self._color_selected)
        self._pen_selected.setWidthF(2.0)
        self._pen_hovered = QPen(self._color_hovered)
        self._pen_hovered.setWidthF(3.0)

        self._brush_title = QBrush(QColor("#FF313131"))
        self._brush_background = QBrush(QColor("#E3212121"))

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
        """
        Override to restrict movement to header when node is in a collapsed container.
        Only allow dragging from the title bar area for collapsed nodes.
        """
        # Check if this node is inside a collapsed container
        if (
            self.node.parent_group
            and self.node.parent_group.isCollapsed()
            and self.node.grNode.isVisible()
        ):
            # Node is in a collapsed container
            # Only allow movement if click is on the header (top part of the node)
            local_y = event.pos().y()
            # Allow movement only from top portion (header area, roughly 25px)
            if local_y > 25:
                # Click is not on header - disable movable flag to allow selection only
                was_movable = (
                    self.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable
                )
                self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
                super().mousePressEvent(event)
                self.setFlag(
                    QGraphicsItem.GraphicsItemFlag.ItemIsMovable, bool(was_movable)
                )
                return

        # Allow normal press event handling for movement
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
            self.node.positionChanged.emit(self.node)
            print("Emitted positionChanged for node:", self.node.title)

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

    def _connect_model_signals(self) -> None:
        """Connect to NodeModel signals for real-time graphics updates."""
        if hasattr(self.node, 'model'):
            # Connect to title changes
            if hasattr(self.node.model, 'titleChanged'):
                try:
                    self.node.model.titleChanged.connect(self._on_node_title_changed)
                except (AttributeError, TypeError):
                    pass

            # Connect to position changes
            if hasattr(self.node.model, 'positionChanged'):
                try:
                    self.node.model.positionChanged.connect(self._on_node_position_changed)
                except (AttributeError, TypeError):
                    pass

    def _on_node_title_changed(self, new_title: str) -> None:
        """Handle node title change from model - update graphics text."""
        if hasattr(self, 'title_item'):
            self.title = new_title
            self.update()

    def _on_node_position_changed(self, new_position) -> None:
        """Handle node position change from model - update graphics position."""
        from qtpy.QtCore import QPointF
        # Handle both QPointF and tuple formats
        if isinstance(new_position, QPointF):
            self.setPos(new_position)
        else:
            self.setPos(QPointF(new_position[0], new_position[1]))
        self.update()

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
