# -*- coding: utf-8 -*-
"""
A module containing the GroupNode class for node grouping functionality.

GroupNode is a QGraphicsItem-based container for visual grouping of nodes.
It is NOT a Node itself, but rather a visual container that holds references to child nodes.

Refactored for MVC: Uses GroupNodeModel and GroupNodeController for state management.
"""
from qtpy.QtCore import QPoint
from qtpy.QtWidgets import QGraphicsSceneMouseEvent
from qtpy.QtCore import QRectF, Qt, QPointF, QSize
from qtpy.QtGui import QColor, QPainter, QPen, QBrush, QCursor
from qtpy.QtWidgets import (
    QGraphicsRectItem,
    QGraphicsItem,
    QGraphicsTextItem,
    QGraphicsPathItem,
    QGraphicsProxyWidget,
    QPushButton,
    QMenu,
)

from nodeeditor.node_serializable import Serializable
from nodeeditor.utils.utils_no_qt import dumpException
from nodeeditor.models.group_node_model import GroupNodeModel
from nodeeditor.controllers.group_node_controller import GroupNodeController

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
    
    Refactored for MVC architecture: Uses GroupNodeModel for state and 
    GroupNodeController for operations.
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
        self.id: int = id(self)

        # Create MVC components
        self.model: GroupNodeModel = GroupNodeModel(self.id, title, x, y, width, height)
        self.controller: GroupNodeController = GroupNodeController(self.model, scene.model if hasattr(scene, 'model') else None)

        self.scene.addGroup(self)
        self.scene.grScene.addItem(self)  # Add to graphics scene for visual rendering

        # Child management
        self.child_nodes: List['Node'] = []

        # Hover tracking
        self._is_hovering_header: bool = False
        self.setAcceptHoverEvents(True)

        # Setup graphics
        self.setPos(x, y)
        self.setZValue(-1)  # Groups stay behind nodes
        self.setPen(QPen(self.model.border_color, self.model.border_width))
        self.setBrush(QBrush(self.model.color))
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

        # Connect model signals to update graphics
        self._connect_model_signals()

    def _connect_model_signals(self) -> None:
        """Connect to model signals for automatic graphics updates."""
        if hasattr(self.model, 'titleChanged'):
            self.model.titleChanged.connect(self._on_title_changed)
        if hasattr(self.model, 'collapsedChanged'):
            self.model.collapsedChanged.connect(self._on_collapsed_changed)
        if hasattr(self.model, 'boundariesChanged'):
            self.model.boundariesChanged.connect(self._on_boundaries_changed)
        if hasattr(self.model, 'positionChanged'):
            self.model.positionChanged.connect(self._on_position_changed)
        if hasattr(self.model, 'sizeChanged'):
            self.model.sizeChanged.connect(self._on_size_changed)

    def _on_title_changed(self, title: str) -> None:
        """Handle title change from model."""
        self.update()

    def _on_collapsed_changed(self, is_collapsed: bool) -> None:
        """Handle collapse state change from model."""
        if is_collapsed:
            self.collapse()
        else:
            self.expand()

    def _on_boundaries_changed(self, rect: QRectF) -> None:
        """Handle boundaries change from model."""
        self.update()

    def _on_position_changed(self, pos: QPointF) -> None:
        """Handle position change from model."""
        # Only update if not already at this position (avoid circular updates)
        if self.pos() != pos:
            self.setPos(pos)

    def _on_size_changed(self, size) -> None:
        """Handle size change from model."""
        # Only update if size has changed (avoid circular updates)
        current_rect = self.rect()
        if current_rect.width() != size.width() or current_rect.height() != size.height():
            self.setRect(0, 0, size.width(), size.height())
            self._updateButtonProxy()

    @property
    def title(self) -> str:
        """Get group title from model."""
        return self.model.title

    @title.setter
    def title(self, value: str) -> None:
        """Set group title via controller."""
        self.controller.set_title(value)

    @property
    def _title_bar_height(self) -> int:
        """Get title bar height from model."""
        return self.model.title_bar_height

    @property
    def _corner_radius(self) -> int:
        """Get corner radius from model."""
        return self.model.corner_radius

    @property
    def _color(self) -> QColor:
        """Get color from model."""
        return self.model.color

    @property
    def _title_color(self) -> QColor:
        """Get title color from model."""
        return self.model.title_color

    @property
    def _border_color(self) -> QColor:
        """Get border color from model."""
        return self.model.border_color

    @property
    def _border_width(self) -> int:
        """Get border width from model."""
        return self.model.border_width

    @property
    def _is_collapsed(self) -> bool:
        """Get collapse state from model."""
        return self.model.is_collapsed

    @property
    def _original_node_states(self) -> Dict[int, Dict]:
        """Get original node states from model."""
        return self.model.original_node_states

    @property
    def _expanded_rect(self) -> Optional[QRectF]:
        """Get expanded rect - store locally."""
        return getattr(self, '_stored_expanded_rect', None)

    @_expanded_rect.setter
    def _expanded_rect(self, value: Optional[QRectF]) -> None:
        """Store expanded rect locally."""
        self._stored_expanded_rect = value

    def addNode(self, node: 'Node') -> None:
        """
        Add a node to this group.
        
        :param node: node to add to the group
        """
        if node not in self.child_nodes:
            self.child_nodes.append(node)
            node.parent_group = self

            # Add to model only if node.model is not None
            if (
                hasattr(self.controller, "add_node")
                and hasattr(node, "model")
                and node.model is not None
            ):
                self.controller.add_node(node.model)

            # Connect the node's positionChanged signal to our slot
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

            # Remove from model only if node.model is not None
            if (
                hasattr(self.controller, "remove_node")
                and hasattr(node, "model")
                and node.model is not None
            ):
                self.controller.remove_node(node.model)

            self.scene.has_been_modified = True
            self.updateGroupBoundaries()

    def _updateButtonProxy(self) -> None:
        """
        Create or update the QGraphicsProxyWidget for the collapse button.
        This wraps the QPushButton in a graphics item so it can be placed in the scene.
        """
        if self._button_proxy is None:
            # Create proxy widget and add to scene
            if hasattr(self.scene, "grScene") and self.scene.grScene is not None:
                proxy = self.scene.grScene.addWidget(self._collapse_button)
                if proxy is not None:
                    self._button_proxy = proxy
                    # Set parent so button moves with the group
                    self._button_proxy.setParentItem(self)

        if self._button_proxy is not None:
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
        current_state = "Collapsed" if self.model.is_collapsed else "Expanded"
        print(f"Group '{self.title}' is currently {current_state}")
        self.controller.toggle_collapse()

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

        # Update model to reflect changes
        self.controller.set_boundaries(bbox.x(), bbox.y(), normalized_width, normalized_height)

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
            if self.model.is_collapsed and value is not None:
                new_pos = value  # QPointF of new container position
                container_width = self.rect().width()
                container_height = self.rect().height()
                container_center_y = new_pos.y() + container_height / 2

                # Move only visible (shrunken) child nodes to maintain their edge direction positions
                for node in self.child_nodes:
                    if node.grNode and node.grNode.isVisible():
                        # Determine if this node has incoming or outgoing edges
                        has_incoming = any(socket.edges for socket in node.inputs)
                        has_outgoing = any(socket.edges for socket in node.outputs)

                        # Position node on left for incoming edges, right for outgoing edges
                        if has_incoming and not has_outgoing:
                            # Node has only incoming edges - position on the left
                            node_x = new_pos.x() - 10
                        elif has_outgoing and not has_incoming:
                            # Node has only outgoing edges - position on the right
                            node_x = new_pos.x() + container_width + 10
                        else:
                            # Node has both incoming and outgoing edges - position in center
                            node_x = new_pos.x() + container_width / 2

                        # Position node at calculated x, and vertically at container center
                        node.setPos(node_x, container_center_y)

                        # For collapsed nodes, ensure sockets remain centered after move
                        if hasattr(node.grNode, "width") and node.grNode.width <= 0.2:
                            center_x = 0.1  # Center of scaled down node
                            center_y = 0.1  # Center of scaled down node
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
        if self.model.is_collapsed:
            return

        # Store current expanded size
        self._expanded_rect = self.rect()

        # Clear any previous stored states
        self.model._original_node_states.clear()

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

            self.model._original_node_states[node.id] = {
                "relative_position": relative_pos,  # Position relative to container
                "width": getattr(node.grNode, "width", None),
                "height": getattr(node.grNode, "height", None),
                "scale": (
                    node.grNode.scale() if node.grNode else 1.0
                ),  # Store original scale
                "was_visible": node.grNode.isVisible() if node.grNode else True,
            }

        # Resize container to minimal collapsed size
        self.setRect(0, 0, 150, self._title_bar_height + 5)

        # Calculate container positions
        container_pos = self.scenePos()
        container_width = self.rect().width()
        container_height = self.rect().height()
        container_center_y = container_pos.y() + container_height / 2
        left_edge_center = container_pos + QPointF(0, container_height / 2)
        right_edge_center = container_pos + QPointF(
            container_width, container_height / 2
        )

        # Now position the nodes based on edge direction
        for node in self.child_nodes:
            if node in nodes_with_external_connections:
                # Determine if this node has incoming or outgoing edges
                has_incoming = any(socket.edges for socket in node.inputs)
                has_outgoing = any(socket.edges for socket in node.outputs)

                # Position node on left for incoming edges, right for outgoing edges
                if has_incoming and not has_outgoing:
                    # Node has only incoming edges - position on the left
                    node.setPos(container_pos.x() - 10, container_center_y)
                elif has_outgoing and not has_incoming:
                    # Node has only outgoing edges - position on the right
                    # node_x = container_pos.x() + container_width + 10
                    node.setPos(
                        container_pos.x() + container_width + 10, container_center_y
                    )
                else:
                    # Node has both incoming and outgoing edges - position in center (or could prioritize one)
                    node_x = container_pos.x() + container_width / 2
                    node.setPos(node_x, container_center_y)

                # Position node at calculated x, and vertically at container center
                # node.setPos(node_x, container_center_y)

                # Properly shrink the node graphics but keep it visible
                if hasattr(node.grNode, "width") and hasattr(node.grNode, "height"):
                    # Actually change the width and height instead of scaling
                    node.grNode.width = 0.2
                    node.grNode.height = 0.2
                    # Set scale to zero after changing dimensions
                    node.grNode.setScale(0)
                    node.grNode.update()
                    node.grNode.hide()

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

        # Update model
        self.model.is_collapsed = True
        self.update()
        self.scene.has_been_modified = True

    def expand(self) -> None:
        """Expand the group, restoring child nodes to their original positions and sizes.

        All edges are shown again, including:
        - Edges between nodes inside the group (internal edges)
        - Edges connecting to nodes outside the group (external connections)
        """
        if self.model.is_collapsed is False:
            return

        # Restore all child nodes to their original positions and sizes
        if hasattr(self, "_original_node_states"):
            for node in self.child_nodes:
                node_id = node.id
                if node_id in self.model._original_node_states:
                    original_state = self.model._original_node_states[node_id]

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

                    # Restore size and scale
                    if hasattr(node.grNode, "width") and hasattr(node.grNode, "height"):
                        # Get original width and height, default to 120x120 if not stored
                        original_width = original_state.get("width", 120)
                        original_height = original_state.get("height", 120)
                        original_scale = original_state.get("scale", 1.0)

                        # Restore the original width and height
                        node.grNode.width = original_width if original_width else 120
                        node.grNode.height = original_height if original_height else 120

                        # Restore the original scale (default to 1.0)
                        node.grNode.setScale(original_scale if original_scale else 1.0)

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
                else:
                    # No original state stored - restore to default size
                    if node.grNode:
                        node.grNode.width = 120
                        node.grNode.height = 120
                        node.grNode.setScale(1.0)
                        node.grNode.update()
                        node.grNode.show()

                        # Recalculate socket positions
                        for socket in node.inputs + node.outputs:
                            socket.setSocketPosition()
                            socket.grSocket.show()

                        # Update edges
                        node.updateConnectedEdges()

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

        # Update model
        self.model.is_collapsed = False
        self.update()
        self.scene.has_been_modified = True

    def isCollapsed(self) -> bool:
        """Check if the group is currently collapsed."""
        return self.model.is_collapsed

    def toggleCollapse(self) -> None:
        """Toggle between collapsed and expanded state."""
        self.controller.toggle_collapse()

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

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """
        Handle mouse press events.
        Only allow movement from the header area (title bar).
        Clicks elsewhere allow selection logic to work.
        Select the container when clicking on header.
        """
        local_pos = event.pos()
        # Check if click is in the header area (top _title_bar_height pixels)
        if local_pos.y() < self._title_bar_height:
            # Click is on header - allow movement and select the container
            self._can_move = True
            # Select the group
            self.setSelected(True)
        else:
            # Click is not on header - disable movable flag to allow selection only
            self._can_move = False
            # was_movable = self.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            # self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
            # super().mousePressEvent(event)
            # self.setFlag(
            #     QGraphicsItem.GraphicsItemFlag.ItemIsMovable, bool(was_movable)
            # )
            event.ignore()
            super().mousePressEvent(event)
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        """Handle mouse move to also move child nodes."""
        # Only allow movement if click was on header
        if not getattr(self, "_can_move", False):
            return

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
        if hasattr(self, "_can_move"):
            del self._can_move
        super().mouseReleaseEvent(event)

    def hoverEnterEvent(self, event) -> None:
        """Handle hover enter event - show hint for header selection."""
        # Accept QGraphicsSceneHoverEvent only
        if event is not None and hasattr(event, "pos"):
            local_pos = event.pos()
            if local_pos.y() < self._title_bar_height:
                self._is_hovering_header = True
                self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                self.update()
        super().hoverEnterEvent(event)

    def hoverMoveEvent(self, event) -> None:
        """Handle hover move event to update cursor based on position."""
        if event is not None and hasattr(event, "pos"):
            local_pos = event.pos()
            if local_pos.y() < self._title_bar_height:
                if not self._is_hovering_header:
                    self._is_hovering_header = True
                    self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                    self.update()
            else:
                if self._is_hovering_header:
                    self._is_hovering_header = False
                    self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
                    self.update()
        super().hoverMoveEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        """Handle hover leave event."""
        self._is_hovering_header = False
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.update()
        super().hoverLeaveEvent(event)

    def contextMenuEvent(self, event) -> None:
        """Handle context menu event to show group options."""
        menu = QMenu()

        # Add ungroup option
        ungroup_action = menu.addAction("Ungroup")
        if ungroup_action is not None and hasattr(ungroup_action, "triggered"):
            ungroup_action.triggered.connect(self.ungroup)

        # Add delete option
        delete_action = menu.addAction("Delete Container")
        if delete_action is not None and hasattr(delete_action, "triggered"):
            delete_action.triggered.connect(self.deleteContainer)

        # Show menu at cursor position
        if event is not None and hasattr(event, "screenPos"):
            menu.exec(event.screenPos())

    def ungroup(self) -> None:
        """Remove the container while keeping all child nodes."""
        # Expand if collapsed first
        if self.model.is_collapsed:
            self.expand()

        # Remove all nodes from this group (but don't delete them)
        nodes_to_remove = self.child_nodes.copy()
        for node in nodes_to_remove:
            self.removeNode(node)

        # Remove from graphics scene
        if self.scene.grScene and self in self.scene.grScene.items():
            self.scene.grScene.removeItem(self)

        # Remove the group from the scene
        self.scene.removeGroup(self)

    def deleteContainer(self) -> None:
        """Delete the container and all its child nodes."""
        # Get all child nodes
        nodes_to_delete = self.child_nodes.copy()

        # Delete all child nodes
        for node in nodes_to_delete:
            node.remove()

        # Remove from graphics scene
        if self.scene.grScene and self in self.scene.grScene.items():
            self.scene.grScene.removeItem(self)

        # Remove the group from the scene
        self.scene.removeGroup(self)

    def paint(self, painter: QPainter, option, widget) -> None:
        """Paint the group node with title bar. Button is handled by QGraphicsProxyWidget."""
        # Draw main rect
        painter.setPen(self.pen())
        painter.setBrush(self.brush())
        painter.drawRoundedRect(self.rect(), self._corner_radius, self._corner_radius)

        # Draw title bar
        title_bar_rect = QRectF(self.rect().x(), self.rect().y(),
                                 self.rect().width(), self._title_bar_height)

        # Change title bar color if hovering
        title_bar_color = (
            QColor(80, 80, 80) if self._is_hovering_header else QColor(60, 60, 60)
        )
        painter.fillRect(title_bar_rect, QBrush(title_bar_color))

        # Draw hover hint border on header
        if self._is_hovering_header:
            painter.setPen(QPen(QColor(255, 200, 0), 2))  # Gold border for hover
            painter.drawRect(title_bar_rect)

        # Draw title text
        painter.setPen(QPen(self._title_color))
        painter.drawText(title_bar_rect, int(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter), 
                        self.title)

        # Note: Collapse/expand button is drawn by QGraphicsProxyWidget, not here

    def serialize(self) -> dict:
        """Serialize the group node to a dictionary."""
        return self.controller.serialize()

    def deserialize(self, data: dict, hashmap: Optional[dict] = None, restore_id: bool = True) -> bool:
        """Deserialize the group node from a dictionary."""
        return self.controller.deserialize(data, restore_id)
