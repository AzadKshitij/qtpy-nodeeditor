# -*- coding: utf-8 -*-
"""
A module containing the GroupNode class for node grouping functionality.

GroupNode is a QGraphicsItem-based container for visual grouping of nodes.
It is NOT a Node itself, but rather a visual container that holds references to child nodes.
"""
from qtpy.QtCore import QRectF, Qt, QPointF, QSize
from qtpy.QtGui import QColor, QPainter, QPen, QBrush
from qtpy.QtWidgets import QGraphicsRectItem, QGraphicsItem, QGraphicsTextItem, QGraphicsPathItem, QGraphicsProxyWidget, QPushButton

from nodeeditor.node_serializable import Serializable
from nodeeditor.utils_no_qt import dumpException

from typing import TYPE_CHECKING, List, Optional, Dict, Tuple
from nodeeditor.node_socket import Socket

if TYPE_CHECKING:
    from nodeeditor.node_scene import Scene
    from nodeeditor.node_node import Node
    from nodeeditor.node_edge import Edge


class GroupNode(Serializable, QGraphicsRectItem):
    """
    A QGraphicsItem-based container for grouping nodes together.
    
    This is NOT a Node - it's a pure visual container that manages a group of nodes.
    Nodes retain their independence and can move within/outside the group.
    """

    def __init__(self, scene: 'Scene', title: str = "Group", x: float = 0, y: float = 0, 
                 width: float = 200, height: float = 150) -> None:
        """
        Initialize a GroupNode container.
        
        :param scene: reference to the Scene
        :param title: title of the group
        :param x: x position
        :param y: y position
        :param width: width of the group
        :param height: height of the group
        """
        QGraphicsRectItem.__init__(self, 0, 0, width, height)
        Serializable.__init__(self)

        self.scene: 'Scene' = scene
        self.title: str = title
        self.id: int = id(self)
        self.scene.addGroup(self)
        self.scene.grScene.addItem(self)  # Add to graphics scene for visual rendering

        # Visual properties
        self._title_bar_height = 30
        self._corner_radius = 5
        self._color = QColor(100, 100, 100, 200)
        self._title_color = QColor(255, 255, 255)
        self._border_color = QColor(50, 50, 50)
        self._border_width = 2

        # Collapse state
        self._is_collapsed: bool = False
        self._expanded_rect: Optional[QRectF] = None

        # Child management
        self.child_nodes: List['Node'] = []
        self._child_positions: dict = {}

        # Store original node states for collapse/expand
        self._original_node_states: Dict[int, Dict] = {}

        # Setup graphics
        self.setPos(x, y)
        self.setZValue(-1)  # Groups stay behind nodes
        self.setPen(QPen(self._border_color, self._border_width))
        self.setBrush(QBrush(self._color))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)

        # Create collapse/expand button using QGraphicsProxyWidget
        self._collapse_button = QPushButton("+")
        self._collapse_button.setFixedSize(25, 25)
        self._collapse_button.setStyleSheet("QPushButton { font-size: 14px; padding: 0px; }")
        self._collapse_button.clicked.connect(self._onCollapseButtonClicked)

        # Wrap button in QGraphicsProxyWidget
        self._button_proxy: Optional[QGraphicsProxyWidget] = None
        self._updateButtonProxy()

    def addNode(self, node: 'Node') -> None:
        """
        Add a node to this group.
        
        :param node: node to add to the group
        """
        if node not in self.child_nodes:
            self.child_nodes.append(node)
            node.parent_group = self

            # Store current position
            self._child_positions[id(node)] = (node.pos.x(), node.pos.y())

            # Connect the node's positionChanged signal to our slot
            # This allows us to check boundaries when the node moves
            node.positionChanged.connect(self.onChildNodeMoved)

            self.scene.has_been_modified = True

    def removeNode(self, node: 'Node') -> None:
        """
        Remove a node from this group.
        
        :param node: node to remove from the group
        """
        if node in self.child_nodes:
            # Disconnect the positionChanged signal before removing
            node.positionChanged.disconnect(self.onChildNodeMoved)

            self.child_nodes.remove(node)
            node.parent_group = None

            # Clean up stored position
            node_id = id(node)
            if node_id in self._child_positions:
                del self._child_positions[node_id]

            self.scene.has_been_modified = True
            self.updateGroupBoundaries()

    def _updateButtonProxy(self) -> None:
        """
        Create or update the QGraphicsProxyWidget for the collapse button.
        This wraps the QPushButton in a graphics item so it can be placed in the scene.
        """
        if self._button_proxy is None:
            # Create proxy widget and add to scene
            self._button_proxy = self.scene.grScene.addWidget(self._collapse_button)
            # Set parent so button moves with the group
            self._button_proxy.setParentItem(self)

        # Position button in the top-right corner of the title bar
        # Account for button size (25x25) to keep it fully within the group bounds
        button_x = self.rect().width() - 30  # Button width (25) + padding (5)
        button_y = 2  # 2px padding from top of title bar
        self._button_proxy.setPos(button_x, button_y)

        # Ensure button is visible and on top of the group
        self._button_proxy.show()
        self._button_proxy.setZValue(1)  # Higher than group (which is at -1)

    def _onCollapseButtonClicked(self) -> None:
        """
        Slot called when the collapse/expand button is clicked.
        Prints the current state and toggles collapse.
        """
        current_state = "Collapsed" if self._is_collapsed else "Expanded"
        print(f"Group '{self.title}' is currently {current_state}")
        self.toggleCollapse()

    def getChildNodes(self) -> List['Node']:
        """Get a copy of the list of child nodes."""
        return self.child_nodes.copy()

    def calculateBoundingBox(self) -> QRectF:
        """
        Calculate the bounding box that encompasses all child nodes.
        Accounts for the title bar height so nodes don't overlap it.

        :return: bounding rectangle for all child nodes in scene coordinates
        """
        if not self.child_nodes:
            return QRectF(self.pos().x(), self.pos().y(), 200, 150)

        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')

        for node in self.child_nodes:
            if node.grNode is None:
                continue

            # Get node graphics bounds
            node_x = node.pos.x()
            node_y = node.pos.y()
            gr_node = node.grNode

            # Get the bounding rect in node local coordinates
            local_bounds = gr_node.boundingRect()

            node_left = node_x + local_bounds.left()
            node_top = node_y + local_bounds.top()
            node_right = node_x + local_bounds.right()
            node_bottom = node_y + local_bounds.bottom()

            min_x = min(min_x, node_left)
            min_y = min(min_y, node_top)
            max_x = max(max_x, node_right)
            max_y = max(max_y, node_bottom)

        if min_x == float('inf'):
            # No valid child nodes
            return QRectF(self.pos().x(), self.pos().y(), 200, 150)

        # Add padding around nodes
        padding = 20

        # Calculate actual boundaries with padding
        bbox_left = min_x - padding
        bbox_top = min_y - padding
        bbox_right = max_x + padding
        bbox_bottom = max_y + padding

        # Ensure we have space for the title bar at the top
        # Reserve space for title bar height
        bbox_top = bbox_top - self._title_bar_height

        # Calculate width and height (always positive)
        width = bbox_right - bbox_left
        height = bbox_bottom - bbox_top

        # Return rectangle in scene coordinates with normalized dimensions
        return QRectF(bbox_left, bbox_top, abs(width), abs(height))

    def updateGroupBoundaries(self) -> None:
        """Update the group's position and size to fit all child nodes."""
        bbox = self.calculateBoundingBox()

        # The bounding box is in scene coordinates
        # We need to set the rect in local coordinates (starting from 0,0)
        # and position the group at the bbox top-left

        # Normalize the rectangle to ensure positive width/height
        normalized_width = abs(bbox.width())
        normalized_height = abs(bbox.height())

        # Set rect in local coordinates (always start at 0,0)
        self.setRect(0, 0, normalized_width, normalized_height)

        # Position the group at the top-left of the bounding box in scene coordinates
        self.setPos(bbox.topLeft())

        # Update button position after resizing
        self._updateButtonProxy()

    def itemChange(self, change, value):
        """
        Override itemChange to update button position when group changes.
        This is called whenever the item's geometry or transformation changes.
        
        ItemChange constants:
        - 0: ItemPositionChange
        - 8: ItemRectChange
        """
        # Handle position changes (0 = ItemPositionChange)
        if change == 0:
            # Update button position to keep it in top-right corner
            if self._button_proxy is not None:
                self._updateButtonProxy()

            # When collapsed, move visible child nodes with the container
            if self._is_collapsed and value is not None:
                new_pos = value  # QPointF of new container position
                container_center = new_pos + QPointF(
                    self.rect().width() / 2, self.rect().height() / 2
                )

                # Move only visible (shrunken) child nodes to the new container center
                # Hidden nodes don't need to move
                for node in self.child_nodes:
                    if node.grNode and node.grNode.isVisible():
                        node.setPos(container_center.x(), container_center.y())

                        # For collapsed nodes, ensure sockets remain centered after move
                        if hasattr(node.grNode, "width") and node.grNode.width == 5:
                            center_x = 0.1  # Center of 5px wide node
                            center_y = 0.1  # Center of 5px tall node
                            for socket in node.inputs + node.outputs:
                                socket.grSocket.setPos(center_x, center_y)
                                # Force graphics update to ensure scene position is current
                                socket.grSocket.update()

                        # Force node graphics update before updating edges
                        node.grNode.update()
                        # Update connected edges after moving the node
                        node.updateConnectedEdges()

        # Handle rect changes (8 = ItemRectChange)
        elif change == 8:
            if self._button_proxy is not None:
                self._updateButtonProxy()

        return super().itemChange(change, value)

    def collapse(self) -> None:
        """Collapse the group by shrinking child nodes to near-zero size and moving them to container center.

        This simple approach maintains all edge connections - edges naturally follow the nodes.
        Internal edges become very short, external edges connect to the container center.
        """
        if self._is_collapsed:
            return

        # Store current expanded size
        self._expanded_rect = self.rect()

        # Clear any previous stored states
        self._original_node_states.clear()

        # First, identify which nodes have external connections
        nodes_with_external_connections = set()

        for node in self.child_nodes:
            has_external = False
            for socket in node.inputs + node.outputs:
                for edge in socket.edges:
                    if edge.grEdge is not None:
                        # Get both nodes connected by this edge
                        start_node = (
                            edge.start_socket.node if edge.start_socket else None
                        )
                        end_node = edge.end_socket.node if edge.end_socket else None

                        # Check if this edge connects to outside the group
                        if (
                            start_node in self.child_nodes
                            and end_node not in self.child_nodes
                        ):
                            has_external = True
                            break
                        elif (
                            end_node in self.child_nodes
                            and start_node not in self.child_nodes
                        ):
                            has_external = True
                            break
                        # Hide internal edges (both nodes in group)
                        elif (
                            start_node in self.child_nodes
                            and end_node in self.child_nodes
                        ):
                            edge.grEdge.hide()

            if has_external:
                nodes_with_external_connections.add(node)

        # Process all child nodes
        for node in self.child_nodes:
            # Store original state with relative position to container
            container_pos = self.pos()
            relative_pos = node.pos - container_pos

            self._original_node_states[id(node)] = {
                "relative_position": relative_pos,  # Position relative to container
                "width": getattr(node.grNode, "width", None),
                "height": getattr(node.grNode, "height", None),
                "was_visible": node.grNode.isVisible() if node.grNode else True,
            }

        # Resize container to minimal collapsed size
        self.setRect(0, 0, 150, self._title_bar_height + 5)

        # Calculate container center position after resize
        container_center = self.scenePos() + QPointF(
            self.rect().width() / 2, self.rect().height() / 2
        )

        # Now position the nodes
        for node in self.child_nodes:
            if node in nodes_with_external_connections:
                # Node has external connections - shrink and move to container center
                node.setPos(container_center.x(), container_center.y())

                # Properly shrink the node graphics but keep it visible
                if hasattr(node.grNode, "width") and hasattr(node.grNode, "height"):
                    # Actually change the width and height instead of scaling
                    node.grNode.width = 0.2
                    node.grNode.height = 0.2
                    node.grNode.update()
                    node.grNode.hide()
                    # Keep node visible so edges can connect to it

                    # For tiny nodes, position all sockets at the center
                    # This ensures edges connect to the center of the small node
                    center_x = 2.5  # Center of 5px wide node
                    center_y = 2.5  # Center of 5px tall node

                    for socket in node.inputs + node.outputs:
                        # Manually position socket at the center of the tiny node
                        socket.grSocket.setPos(center_x, center_y)
                        socket.grSocket.hide()  # Hide sockets for collapsed nodes

                    # Force graphics update for all connected edges
                    for socket in node.inputs + node.outputs:
                        for edge in socket.edges:
                            if edge.grEdge:
                                edge.grEdge.update()

                    # Then update all connected edges to follow the new socket positions
                    node.updateConnectedEdges()

            else:
                # Node has only internal connections - hide it completely
                if node.grNode:
                    node.grNode.hide()

        # Update button text
        self._collapse_button.setText("−")
        self._updateButtonProxy()

        self._is_collapsed = True
        self.update()
        self.scene.has_been_modified = True

    def expand(self) -> None:
        """Expand the group, restoring child nodes to their original positions and sizes.

        All edges are shown again, including:
        - Edges between nodes inside the group (internal edges)
        - Edges connecting to nodes outside the group (external connections)
        """
        if not self._is_collapsed:
            return

        # Restore all child nodes to their original positions and sizes
        if hasattr(self, "_original_node_states"):
            for node in self.child_nodes:
                node_id = id(node)
                if node_id in self._original_node_states:
                    original_state = self._original_node_states[node_id]

                    # Restore visibility first
                    if node.grNode and original_state.get("was_visible", True):
                        node.grNode.show()

                    # Restore position using relative position to current container position
                    if (
                        "relative_position" in original_state
                        and original_state["relative_position"]
                    ):
                        relative_pos = original_state["relative_position"]
                        new_absolute_pos = self.pos() + relative_pos
                        node.setPos(new_absolute_pos.x(), new_absolute_pos.y())

                    # Restore size
                    if hasattr(node.grNode, "width") and hasattr(node.grNode, "height"):
                        if original_state.get("width") and original_state.get("height"):
                            # Restore the original width and height
                            node.grNode.width = original_state["width"]
                            node.grNode.height = original_state["height"]
                            node.grNode.update()
                            node.grNode.show()

                            # Force recalculation of socket positions first
                            for socket in node.inputs + node.outputs:
                                socket.setSocketPosition()
                                socket.grSocket.show()

                            # Then update all connected edges
                            node.updateConnectedEdges()

                            # Force graphics update for all connected edges
                            for socket in node.inputs + node.outputs:
                                for edge in socket.edges:
                                    if edge.grEdge:
                                        edge.grEdge.update()

        # Show all edges connected to child nodes (all edges should be visible when expanded)
        for node in self.child_nodes:
            for socket in node.inputs + node.outputs:
                socket.grSocket.show()
                for edge in socket.edges:
                    if edge.grEdge is not None:
                        edge.grEdge.show()

        # Restore previous container size if available
        if self._expanded_rect is not None:
            self.setRect(self._expanded_rect)
        else:
            self.updateGroupBoundaries()

        # Update button text
        self._collapse_button.setText("+")
        self._updateButtonProxy()

        self._is_collapsed = False
        self.update()
        self.scene.has_been_modified = True

    def isCollapsed(self) -> bool:
        """Check if the group is currently collapsed."""
        return self._is_collapsed

    def toggleCollapse(self) -> None:
        """Toggle between collapsed and expanded state."""
        if self._is_collapsed:
            self.expand()
        else:
            self.collapse()

    def onChildNodeMoved(self, node: 'Node') -> None:
        """
        Slot called when a child node's position changes (via signal).
        
        This is called whenever a child node finishes being dragged by the user.
        It triggers boundary checking to auto-remove/expand the group as needed.
        
        :param node: the child node that moved
        """
        self.checkAndAutoAdjustBoundaries()

    def checkAndAutoAdjustBoundaries(self) -> None:
        """
        Check if nodes are still within group boundaries.
        - Nodes completely outside: auto-remove from group
        - Nodes partially outside: auto-expand group
        
        Also ensures nodes don't overlap the title bar area.
        """
        if not self.child_nodes:
            return

        group_rect = self.rect()
        group_pos = self.pos()

        nodes_to_remove = []
        needs_expansion = False

        # Define the content area (below the title bar)
        content_top = self._title_bar_height

        for node in self.child_nodes:
            if node.grNode is None:
                continue

            # Get node bounding box in scene coordinates
            node_x = node.pos.x()
            node_y = node.pos.y()
            node_local_bounds = node.grNode.boundingRect()

            # Calculate node bounds in scene coordinates
            node_left = node_x + node_local_bounds.left()
            node_top = node_y + node_local_bounds.top()
            node_right = node_x + node_local_bounds.right()
            node_bottom = node_y + node_local_bounds.bottom()

            # Calculate group bounds in scene coordinates
            group_left = group_pos.x()
            group_top = group_pos.y()
            group_right = group_pos.x() + group_rect.width()
            group_bottom = group_pos.y() + group_rect.height()

            # Content area starts below the title bar
            content_area_top = group_top + content_top

            # Check if node is completely outside (no intersection)
            if (node_right < group_left or node_left > group_right or 
                node_bottom < group_top or node_top > group_bottom):
                # Completely outside - mark for removal
                nodes_to_remove.append(node)
            else:
                # Node intersects with group - check if partially outside or overlapping header
                if (node_left < group_left or node_right > group_right or 
                    node_top < group_top or node_bottom > group_bottom):
                    # Partially outside - need expansion
                    needs_expansion = True

                # Check if node is overlapping the title bar
                if node_top < content_area_top:
                    # Node is overlapping the title bar - need expansion
                    needs_expansion = True

        # Remove nodes that are completely outside
        for node in nodes_to_remove:
            self.removeNode(node)

        # Expand if needed to accommodate partially-outside nodes or nodes overlapping header
        if needs_expansion:
            self.updateGroupBoundaries()

    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move to also move child nodes."""
        # Calculate movement delta
        if event is None or not hasattr(event, 'pos'):
            super().mouseMoveEvent(event)
            return

        new_pos = self.mapToScene(event.pos())

        if not hasattr(self, '_last_pos'):
            self._last_pos = new_pos
            super().mouseMoveEvent(event)
            return

        delta = new_pos - self._last_pos
        self._last_pos = new_pos

        # Move all child nodes by the same delta
        for node in self.child_nodes:
            old_pos = node.pos
            node.setPos(old_pos.x() + delta.x(), old_pos.y() + delta.y())

        # Move group
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        """Handle mouse release."""
        if hasattr(self, '_last_pos'):
            del self._last_pos
        super().mouseReleaseEvent(event)

    def mousePressEvent(self, event) -> None:
        """
        Handle mouse press events.
        The collapse button is handled by QGraphicsProxyWidget.
        """
        super().mousePressEvent(event)

    def paint(self, painter: QPainter, option, widget) -> None:
        """Paint the group node with title bar. Button is handled by QGraphicsProxyWidget."""
        # Draw main rect
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawRoundedRect(self.rect(), self._corner_radius, self._corner_radius)

        # Draw title bar
        title_bar_rect = QRectF(self.rect().x(), self.rect().y(),
                                 self.rect().width(), self._title_bar_height)
        painter.fillRect(title_bar_rect, QBrush(QColor(60, 60, 60)))

        # Draw title text
        painter.setPen(QPen(self._title_color))
        painter.drawText(title_bar_rect, int(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter), 
                        self.title)

        # Note: Collapse/expand button is drawn by QGraphicsProxyWidget, not here

    def serialize(self) -> dict:
        """Serialize the group node to a dictionary."""
        return {
            'id': self.id,
            'type': 'GroupNode',
            'title': self.title,
            'x': self.pos().x(),
            'y': self.pos().y(),
            'width': self.rect().width(),
            'height': self.rect().height(),
            'is_collapsed': self._is_collapsed,
            'child_node_ids': [node.id for node in self.child_nodes],
            'color': self._color.getRgb(),
            'title_color': self._title_color.getRgb(),
            'border_color': self._border_color.getRgb(),
        }

    def deserialize(self, data: dict, hashmap: Optional[dict] = None, restore_id: bool = True) -> bool:
        """Deserialize the group node from a dictionary."""
        try:
            if restore_id and 'id' in data:
                self.id = data['id']

            self.title = data.get('title', 'Group')
            self._is_collapsed = data.get('is_collapsed', False)

            # Restore position and size
            if 'x' in data and 'y' in data:
                self.setPos(data['x'], data['y'])

            width = data.get('width', 200)
            height = data.get('height', 150)
            self.setRect(0, 0, width, height)

            # Restore colors if present
            if 'color' in data and isinstance(data['color'], (list, tuple)):
                self._color = QColor(*data['color'])
            if 'title_color' in data and isinstance(data['title_color'], (list, tuple)):
                self._title_color = QColor(*data['title_color'])
            if 'border_color' in data and isinstance(data['border_color'], (list, tuple)):
                self._border_color = QColor(*data['border_color'])

            # Child nodes will be restored by the scene deserialization process
            # by setting their parent_group attribute

            return True
        except Exception as e:
            dumpException(e)
            return False
