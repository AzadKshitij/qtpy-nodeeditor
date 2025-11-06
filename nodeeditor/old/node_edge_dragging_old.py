# -*- coding: utf-8 -*-
"""
A module containing the Edge Dragging functionality.

This module provides the EdgeDragging class which manages edge dragging operations
at the view level. It uses EdgeDraggingModel for state management and signal-based
updates to graphics components.
"""
from nodeeditor.node_graphics_socket import QDMGraphicsSocket
from nodeeditor.node_edge import EDGE_TYPE_DEFAULT
from nodeeditor.utils import dumpException
from nodeeditor.models import EdgeDraggingModel

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qtpy.QtWidgets import QGraphicsItem
    from nodeeditor.node_socket import Socket
    from nodeeditor.node_edge import Edge
    from nodeeditor.node_graphics_view import QDMGraphicsView

DEBUG = False


class EdgeDragging:
    """Manages edge dragging operations with MVC state management.
    
    This class handles the visual and state management of dragging edges from one
    socket to another. It uses EdgeDraggingModel to maintain state and emits signals
    for connected graphics components.
    
    Attributes:
        grView: The graphics view managing the scene
        model: EdgeDraggingModel for state management
        drag_edge: The edge currently being dragged (for backward compatibility)
        drag_start_socket: The starting socket (for backward compatibility)
    """
    
    def __init__(self, grView: 'QDMGraphicsView') -> None:
        self.grView = grView
        self.model = EdgeDraggingModel()
        
        # Initialize state variables for backward compatibility
        self.drag_edge: Edge | None = None
        self.drag_start_socket: Socket | None = None
        
        # Connect model signals to state tracking
        self._connect_model_signals()

    def _connect_model_signals(self) -> None:
        """Connect EdgeDraggingModel signals for state synchronization."""
        self.model.dragStarted.connect(self._on_drag_started)
        self.model.dragEnded.connect(self._on_drag_ended)
        self.model.dragCancelled.connect(self._on_drag_cancelled)

    def _on_drag_started(self, edge_id: str, socket_id: int) -> None:
        """Handle drag started signal from model."""
        # State is updated separately in edgeDragStart
        pass

    def _on_drag_ended(self, socket_id: int, is_valid: bool) -> None:
        """Handle drag ended signal from model."""
        # State cleanup is handled in edgeDragEnd
        pass

    def _on_drag_cancelled(self) -> None:
        """Handle drag cancelled signal from model."""
        # State cleanup is handled in cancelDragEdge
        pass

    def getEdgeClass(self):
        """Helper function to get the Edge class. Using what Scene class provides"""
        return self.grView.grScene.scene.getEdgeClass()

    def updateDestination(self, x: float, y: float) -> None:
        """
        Update the end point of our dragging edge

        :param x: new X scene position
        :param y: new Y scene position
        """
        # according to sentry: 'NoneType' object has no attribute 'grEdge'
        if self.drag_edge is None:
            print(">>> Warning: drag_edge is None!")
            return

        if self.drag_edge.grEdge is None:
            print(">>> Warning: drag_edge.grEdge is None!")
            return

        self.drag_edge.grEdge.setDestination(x, y)
        self.drag_edge.grEdge.update()

    def edgeDragStart(self, item: QDMGraphicsSocket) -> None:
        """Code handling the start of a dragging an `Edge` operation.
        
        Initializes drag state and creates a temporary edge for visual feedback.
        
        :param item: Graphics socket where drag started
        """
        try:
            if DEBUG:
                print('View::edgeDragStart ~ Start dragging edge')
            if DEBUG:
                print('View::edgeDragStart ~   assign Start Socket to:', item.socket)
            
            self.drag_start_socket = item.socket
            
            # Create temporary edge for dragging visualization
            # Type ignore because Edge.__init__ accepts None for end_socket during creation
            self.drag_edge = self.getEdgeClass()(
                item.socket.node.scene, item.socket, None, EDGE_TYPE_DEFAULT)  # type: ignore

            if self.drag_edge is None:
                print(">>> Warning: Failed to create drag_edge")
                return

            if self.drag_edge.grEdge is None:
                print(">>> Warning: drag_edge.grEdge is None")
                return

            self.drag_edge.grEdge.makeUnselectable()
            
            # Update model state and emit signals
            self.model.start_drag(str(id(self.drag_edge)), self.drag_start_socket.id)

            if DEBUG:
                print('View::edgeDragStart ~   dragEdge:', self.drag_edge)

        except Exception as e:
            dumpException(e)

    def edgeDragEnd(self, item: 'QGraphicsItem'):
        """Code handling the end of the dragging an `Edge` operation. If this code returns True then skip the
        rest of the mouse event processing. Can be called with ``None`` to cancel the edge dragging mode

        :param item: Item in the `Graphics Scene` where we ended dragging an `Edge`
        :type item: ``QGraphicsItem``
        """

        # Cancel edge if clicking on empty space or receiving None (ESC pressed)
        if item is None or not isinstance(item, QDMGraphicsSocket):
            self.cancelDragEdge()
            return False

        # early out - clicked on something else than Socket
        if not isinstance(item, QDMGraphicsSocket):
            self.grView.resetMode()
            if DEBUG:
                print('View::edgeDragEnd ~ End dragging edge early')

            # don't notify sockets about removing drag_edge
            if self.drag_edge is not None:
                self.drag_edge.remove(silent=True)
            self.drag_edge = None
            self.model.cancel_drag()
            return

        # clicked on socket
        if isinstance(item, QDMGraphicsSocket):
            if self.drag_edge is None or self.drag_start_socket is None:
                return False

            # check if edge would be valid using model validators and legacy method
            from nodeeditor.models import EdgeModel
            is_valid = False
            
            # Try MVC validator path first
            if EdgeModel.validate_socket_connection(self.drag_start_socket, item.socket):
                is_valid = True
            # Fall back to legacy validation method
            elif self.drag_edge.validateEdge(self.drag_start_socket, item.socket):
                is_valid = True
            
            if not is_valid:
                print("NOT VALID EDGE")
                self.model.end_drag(item.socket.id, is_valid=False)
                return False

            # regular processing of drag edge
            self.grView.resetMode()

            if DEBUG:
                print('View::edgeDragEnd ~ End dragging edge')
            # don't notify sockets about removing drag_edge
            self.drag_edge.remove(silent=True)
            self.drag_edge = None
            
            # Update model state
            self.model.end_drag(item.socket.id, is_valid=True)

            try:
                if item.socket != self.drag_start_socket:
                    # First verify both sockets exist
                    if self.drag_start_socket is None:
                        print(">>> Warning: drag_start_socket is None!")
                        return False

                    # First remove old edges / send notifications
                    for socket in (item.socket, self.drag_start_socket):
                        if socket is None:
                            print(">>> Warning: socket is None!")
                            continue

                        if not socket.is_multi_edges:
                            if socket.is_input:
                                socket.removeAllEdges(silent=True)
                            else:
                                socket.removeAllEdges(silent=False)

                    # Create new Edge
                    new_edge = self.getEdgeClass()(item.socket.node.scene, self.drag_start_socket,
                                                   item.socket, edge_type=EDGE_TYPE_DEFAULT)
                    if DEBUG:
                        print("View::edgeDragEnd ~  created new edge:", new_edge,
                              "connecting", new_edge.start_socket, "<-->", new_edge.end_socket)

                    # Send notifications for the new edge
                    for socket in [self.drag_start_socket, item.socket]:
                        # @TODO: Add possibility (ie when an input edge was replaced) to be silent and don't trigger change
                        socket.node.onEdgeConnectionChanged(new_edge)
                        if socket.is_input:
                            socket.node.onInputChanged(socket)

                    self.grView.grScene.scene.history.storeHistory(
                        "Created new edge by dragging", setModified=True)
                    return True
            except Exception as e:
                dumpException(e)

        if DEBUG:
            print('View::edgeDragEnd ~ everything done.')
        return False

    def cancelDragEdge(self) -> None:
        """Cancel the edge dragging operation and clean up.
        
        Reverts any visual changes and resets drag state.
        """
        self.grView.resetMode()
        if DEBUG:
            print('View::cancelDragEdge ~ Cancel dragging edge')

        if self.drag_edge is not None:
            self.drag_edge.remove(silent=True)
            self.drag_edge = None
        self.drag_start_socket = None
        
        # Signal model state change
        self.model.cancel_drag()
