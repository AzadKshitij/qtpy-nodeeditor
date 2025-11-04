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

if TYPE_CHECKING:
    from nodeeditor.node_scene import Scene
    from nodeeditor.node_node import Node
    from nodeeditor.node_socket import Socket
    from nodeeditor.node_edge import Edge


class ProxySocket:
    """A minimal socket proxy for temporarily redirecting edges to container boundaries."""

    def __init__(
        self, group_node: "GroupNode", position: QPointF, original_socket: "Socket"
    ):
        """
        Create a proxy socket at a specific position.

        :param group_node: The group node this proxy belongs to
        :param position: Position in scene coordinates
        :param original_socket: The original socket being proxied (to copy attributes from)
        """
        self.group_node = group_node
        self._scene_position = position

        # Copy essential attributes from original socket
        self.node = None  # Proxy sockets don't have a real node
        self.edges = []  # Track edges temporarily connected to this proxy

        # Copy socket attributes needed by edge path calculators
        self.position = original_socket.position
        self.socket_type = original_socket.socket_type
        self.index = original_socket.index
        self.is_input = original_socket.is_input
        self.is_output = original_socket.is_output

    def getSocketPosition(self) -> Tuple[float, float]:
        """Return the socket position as (x, y) tuple."""
        return (self._scene_position.x(), self._scene_position.y())

    def updatePosition(self, position: QPointF):
        """Update the proxy socket position and notify edges."""
        self._scene_position = position
        # Update all edges connected to this proxy
        for edge in self.edges:
            if edge.grEdge:
                edge.grEdge.update()


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

        # Track original socket connections for collapse/expand
        # Maps edge id to {'edge': Edge, 'original_socket': Socket, 'socket_type': 'start'|'end', 'proxy_socket': ProxySocket}
        self._redirected_edges: Dict[int, Dict] = {}

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
        # Handle position or transformation changes (0 = ItemPositionChange, 8 = ItemRectChange)
        if change == 0 or change == 8:
            # Update button position to keep it in top-right corner
            if self._button_proxy is not None:
                self._updateButtonProxy()
            
            # Update proxy socket positions when container moves (if collapsed)
            if self._is_collapsed and self._redirected_edges:
                self._updateProxySocketPositions()

        return super().itemChange(change, value)

    def _updateProxySocketPositions(self) -> None:
        """
        Update all proxy socket positions when the container moves or resizes.
        This ensures external edges follow the container correctly.
        """
        for edge_id, edge_data in self._redirected_edges.items():
            original_socket = edge_data["original_socket"]
            proxy_socket = edge_data["proxy_socket"]
            
            # Get the original socket's position
            socket_pos_list = original_socket.getSocketPosition()
            socket_pos = (socket_pos_list[0], socket_pos_list[1])
            
            # Calculate new closest point on container edge
            new_proxy_pos = self._getClosestEdgePoint(socket_pos)
            
            # Update the proxy socket position
            proxy_socket.updatePosition(new_proxy_pos)

    def _getClosestEdgePoint(self, socket_pos: Tuple[float, float]) -> QPointF:
        """
        Calculate the closest point on the container's edge to a given socket position.

        :param socket_pos: Socket position as (x, y) tuple in scene coordinates
        :return: Closest point on container edge in scene coordinates
        """
        # Get container bounds in scene coordinates
        container_rect = self.sceneBoundingRect()

        x, y = socket_pos

        # Calculate distances to each edge
        dist_left = abs(x - container_rect.left())
        dist_right = abs(x - container_rect.right())
        dist_top = abs(y - container_rect.top())
        dist_bottom = abs(y - container_rect.bottom())

        # Find closest edge and clamp position to it
        min_dist = min(dist_left, dist_right, dist_top, dist_bottom)

        if min_dist == dist_left:
            # Stick to left edge
            closest_x = container_rect.left()
            closest_y = max(container_rect.top(), min(y, container_rect.bottom()))
        elif min_dist == dist_right:
            # Stick to right edge
            closest_x = container_rect.right()
            closest_y = max(container_rect.top(), min(y, container_rect.bottom()))
        elif min_dist == dist_top:
            # Stick to top edge
            closest_x = max(container_rect.left(), min(x, container_rect.right()))
            closest_y = container_rect.top()
        else:  # dist_bottom
            # Stick to bottom edge
            closest_x = max(container_rect.left(), min(x, container_rect.right()))
            closest_y = container_rect.bottom()

        return QPointF(closest_x, closest_y)

    def _redirectEdgeToProxy(
        self, edge: "Edge", socket: "Socket", socket_type: str
    ) -> None:
        """
        Redirect an edge from its original socket to a proxy socket on the container edge.

        :param edge: The edge to redirect
        :param socket: The original socket being hidden
        :param socket_type: Either 'start' or 'end' to indicate which socket to redirect
        """
        # Get the original socket position (returns list [x, y])
        socket_pos_list = socket.getSocketPosition()
        socket_pos = (socket_pos_list[0], socket_pos_list[1])

        # Calculate closest point on container edge
        proxy_pos = self._getClosestEdgePoint(socket_pos)

        # Create a proxy socket at the container edge (passing original socket for attributes)
        proxy_socket = ProxySocket(self, proxy_pos, socket)

        # Store original socket for restoration later
        edge_id = id(edge)
        self._redirected_edges[edge_id] = {
            "edge": edge,
            "original_socket": socket,
            "socket_type": socket_type,
            "proxy_socket": proxy_socket,
        }

        # Redirect the edge to use the proxy socket
        if socket_type == "start":
            # Remove edge from original socket
            socket.removeEdge(edge)
            # Temporarily replace the edge's start socket
            edge._start_socket = proxy_socket
            proxy_socket.edges.append(edge)
        else:  # 'end'
            # Remove edge from original socket
            socket.removeEdge(edge)
            # Temporarily replace the edge's end socket
            edge._end_socket = proxy_socket
            proxy_socket.edges.append(edge)

        # Force edge to update its path
        if edge.grEdge:
            edge.grEdge.update()

    def _restoreEdgeFromProxy(self, edge_id: int) -> None:
        """
        Restore an edge from proxy socket back to its original socket.

        :param edge_id: ID of the edge to restore
        """
        if edge_id not in self._redirected_edges:
            return

        edge_data = self._redirected_edges[edge_id]
        edge = edge_data["edge"]
        original_socket = edge_data["original_socket"]
        socket_type = edge_data["socket_type"]
        proxy_socket = edge_data["proxy_socket"]

        # Remove edge from proxy socket
        if edge in proxy_socket.edges:
            proxy_socket.edges.remove(edge)

        # Restore original socket connection
        if socket_type == "start":
            edge._start_socket = original_socket
            original_socket.addEdge(edge)
        else:  # 'end'
            edge._end_socket = original_socket
            original_socket.addEdge(edge)

        # Force edge to update its path
        if edge.grEdge:
            edge.grEdge.update()

        # Clean up
        del self._redirected_edges[edge_id]

    def collapse(self) -> None:
        """Collapse the group, hiding all child nodes and their edges.

        Edges connecting to nodes OUTSIDE the group remain visible and are redirected
        to proxy sockets on the container edge.
        Only edges completely inside the group are hidden.
        """
        if self._is_collapsed:
            return

        # Store current expanded size
        self._expanded_rect = self.rect()

        # Clear any previous redirections
        self._redirected_edges.clear()

        # Hide all child node graphics
        for node in self.child_nodes:
            if node.grNode is not None:
                node.grNode.hide()

        # Process edges: hide internal ones, redirect external ones
        for node in self.child_nodes:
            for socket in node.inputs + node.outputs:
                for edge in socket.edges[
                    :
                ]:  # Use slice to avoid modification during iteration
                    if edge.grEdge is not None:
                        # Get both nodes connected by this edge
                        start_node = (
                            edge.start_socket.node if edge.start_socket else None
                        )
                        end_node = edge.end_socket.node if edge.end_socket else None

                        # Check if both nodes are in the same group (internal edge)
                        both_in_group = (
                            start_node in self.child_nodes
                            and end_node in self.child_nodes
                        )

                        if both_in_group:
                            # Hide internal edges
                            edge.grEdge.hide()
                        else:
                            # External edge - redirect the hidden socket to container edge
                            if start_node in self.child_nodes and edge.start_socket:
                                # Start socket is inside (being hidden), redirect it
                                self._redirectEdgeToProxy(
                                    edge, edge.start_socket, "start"
                                )
                            elif end_node in self.child_nodes and edge.end_socket:
                                # End socket is inside (being hidden), redirect it
                                self._redirectEdgeToProxy(edge, edge.end_socket, "end")

        # Resize to minimal collapsed size
        self.setRect(0, 0, 150, self._title_bar_height + 5)

        # Update button text
        self._collapse_button.setText("−")
        self._updateButtonProxy()

        self._is_collapsed = True
        self.update()
        self.scene.has_been_modified = True

    def expand(self) -> None:
        """Expand the group, showing all child nodes and their edges.

        All edges are shown again, including:
        - Edges between nodes inside the group (internal edges)
        - Edges connecting to nodes outside the group (external connections)

        Edges that were redirected to proxy sockets are restored to their original sockets.
        """
        if not self._is_collapsed:
            return

        # Restore all redirected edges to their original sockets
        edge_ids_to_restore = list(self._redirected_edges.keys())
        for edge_id in edge_ids_to_restore:
            self._restoreEdgeFromProxy(edge_id)

        # Show all child node graphics
        for node in self.child_nodes:
            if node.grNode is not None:
                node.grNode.show()

        # Show all edges connected to child nodes (all edges should be visible when expanded)
        for node in self.child_nodes:
            for socket in node.inputs + node.outputs:
                for edge in socket.edges:
                    if edge.grEdge is not None:
                        edge.grEdge.show()

        # Restore previous size if available
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
