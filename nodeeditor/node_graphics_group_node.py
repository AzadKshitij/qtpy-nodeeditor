# -*- coding: utf-8 -*-
"""
A module containing Graphics representation of GroupNode
"""
from qtpy.QtWidgets import QGraphicsItem
from qtpy.QtGui import QFont, QColor, QPen, QBrush, QFontMetrics
from qtpy.QtCore import Qt, QRectF
from nodeeditor.node_graphics_node import QDMGraphicsNode

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nodeeditor.node_group_node import GroupNode


class QDMGraphicsGroupNode(QDMGraphicsNode):
    """Graphics representation of a GroupNode with collapsible header"""
    
    def __init__(self, node: 'GroupNode', parent: QGraphicsItem = None) -> None:
        """
        Initialize graphics group node
        
        :param node: reference to GroupNode
        :param parent: parent QGraphicsItem
        """
        super().__init__(node, parent)
        
        # Group-specific graphics attributes
        self.is_collapsed = False
        self.collapse_button_rect = QRectF()
    
    def initSizes(self) -> None:
        """Set up group node sizes"""
        self.width = 300
        self.height = 200
        self.edge_roundness = 10.0
        self.edge_padding = 10
        self.title_height = 28
        self.title_horizontal_padding = 4.0
        self.title_vertical_padding = 4.0
    
    def initAssets(self) -> None:
        """Initialize group node styling"""
        self._title_color = QColor("#FFFFFF")
        self._title_font = QFont("Arial", 10)
        self._title_font.setBold(True)
        
        # Group colors
        self._color = QColor("#FF4A4A4A")
        self._color_selected = QColor("#FFFFA637")
        self._color_hovered = QColor("#FF37A6FF")
        
        self._pen_default = QPen(self._color)
        self._pen_default.setWidthF(2.0)
        self._pen_selected = QPen(self._color_selected)
        self._pen_selected.setWidthF(2.5)
        self._pen_hovered = QPen(self._color_hovered)
        self._pen_hovered.setWidthF(3.0)
        
        # Group brush (semi-transparent)
        self._brush_title = QBrush(QColor("#FF2E5090"))
        self._brush_background = QBrush(QColor("#E3303030"))
    
    def setCollapsed(self, collapsed: bool) -> None:
        """Set collapsed state"""
        self.is_collapsed = collapsed
        self.update()
    
    def setRect(self, width: float, height: float) -> None:
        """Set the size of the group node"""
        self.width = width
        self.height = height
        self.updateBoundingRect()
    
    def updateBoundingRect(self) -> None:
        """Update bounding rect"""
        self.boundingRect_cache = QRectF(0, 0, self.width, self.height)
    
    def initUI(self) -> None:
        """Set up the graphics item"""
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setAcceptHoverEvents(True)
        
        # Init title
        self.initTitle()
        
        # Don't init content for groups
        self.content = None
    
    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle of this node"""
        if self.is_collapsed:
            return QRectF(0, 0, self.width, self.title_height + 10)
        return QRectF(0, 0, self.width, self.height)
    
    def paint(self, painter, option, widget=None) -> None:
        """Paint the group node"""
        if self.is_collapsed:
            self._paintCollapsed(painter)
        else:
            self._paintExpanded(painter)
    
    def _paintExpanded(self, painter) -> None:
        """Paint the expanded group node"""
        # Select appropriate pen and brush
        if self.isSelected():
            pen = self._pen_selected
        elif self.hovered:
            pen = self._pen_hovered
        else:
            pen = self._pen_default
        
        # Draw rounded rectangle
        painter.setPen(pen)
        painter.setBrush(self._brush_background)
        
        path = self._getPath()
        painter.drawPath(path)
        
        # Draw title bar
        title_rect = QRectF(0, 0, self.width, self.title_height)
        painter.setBrush(self._brush_title)
        painter.drawRect(title_rect)
        
        # Draw title text
        painter.setPen(QPen(self._title_color))
        painter.setFont(self._title_font)
        text_rect = QRectF(self.title_horizontal_padding,
                          self.title_vertical_padding,
                          self.width - self.title_height - self.title_horizontal_padding * 2,
                          self.title_height - self.title_vertical_padding * 2)
        painter.drawText(text_rect, Qt.TextFlag.AlignLeft | Qt.TextFlag.AlignVCenter, self.title)
        
        # Draw collapse button
        button_size = self.title_height - 8
        self.collapse_button_rect = QRectF(self.width - button_size - 4, 4, button_size, button_size)
        painter.setBrush(QBrush(QColor("#FF555555")))
        painter.drawRect(self.collapse_button_rect)
        painter.setPen(QPen(self._title_color))
        painter.drawText(self.collapse_button_rect, Qt.TextFlag.AlignCenter, "-")
    
    def _paintCollapsed(self, painter) -> None:
        """Paint the collapsed group node"""
        # Select appropriate pen
        if self.isSelected():
            pen = self._pen_selected
        elif self.hovered:
            pen = self._pen_hovered
        else:
            pen = self._pen_default
        
        # Draw rounded rectangle
        painter.setPen(pen)
        painter.setBrush(self._brush_background)
        
        # Draw collapsed appearance
        path = self._getPath()
        painter.drawPath(path)
        
        # Draw title bar
        title_rect = QRectF(0, 0, self.width, self.title_height)
        painter.setBrush(self._brush_title)
        painter.drawRect(title_rect)
        
        # Draw title text
        painter.setPen(QPen(self._title_color))
        painter.setFont(self._title_font)
        text_rect = QRectF(self.title_horizontal_padding,
                          self.title_vertical_padding,
                          self.width - self.title_height - self.title_horizontal_padding * 2,
                          self.title_height - self.title_vertical_padding * 2)
        painter.drawText(text_rect, Qt.TextFlag.AlignLeft | Qt.TextFlag.AlignVCenter, f"{self.title} [Collapsed]")
        
        # Draw expand button
        button_size = self.title_height - 8
        self.collapse_button_rect = QRectF(self.width - button_size - 4, 4, button_size, button_size)
        painter.setBrush(QBrush(QColor("#FF555555")))
        painter.drawRect(self.collapse_button_rect)
        painter.setPen(QPen(self._title_color))
        painter.drawText(self.collapse_button_rect, Qt.TextFlag.AlignCenter, "+")
    
    def _getPath(self) -> 'QPainterPath':
        """Get the QPainterPath for the node"""
        from qtpy.QtGui import QPainterPath
        
        path = QPainterPath()
        
        if self.is_collapsed:
            height = self.title_height + 10
        else:
            height = self.height
        
        path.addRoundedRect(0, 0, self.width, height, self.edge_roundness, self.edge_roundness)
        return path
    
    def mousePressEvent(self, event) -> None:
        """Handle mouse press to detect collapse button clicks"""
        if self.collapse_button_rect.contains(event.pos()):
            # Toggle collapse
            self.node.collapse() if not self.node.isCollapsed() else self.node.expand()
            event.accept()
        else:
            super().mousePressEvent(event)
