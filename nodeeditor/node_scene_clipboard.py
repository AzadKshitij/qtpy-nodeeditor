# -*- coding: utf-8 -*-
"""
A module containing all code for working with Clipboard

Supports:
- Copying and pasting nodes within the scene
- Copying and pasting text from line edits and text widgets
- Copying and pasting data from table widgets
- Cut/Copy/Paste operations with history tracking
"""
from collections import OrderedDict
from nodeeditor.views.graphics.node_graphics_edge import QDMGraphicsEdge
from nodeeditor.node_edge import Edge

from typing import TYPE_CHECKING, List, Optional, Tuple, Any, Callable, Dict
import json

if TYPE_CHECKING:
    from nodeeditor.views.graphics.node_graphics_view import QDMGraphicsView
    from nodeeditor.node_socket import Socket
    from nodeeditor.node_scene import Scene
    from nodeeditor.node_node import Node


DEBUG = False
DEBUG_PASTING = False


class SceneClipboard():
    """
    Class contains all the code for serialization/deserialization from Clipboard
    """

    def __init__(self, scene: 'Scene') -> None:
        """
        :param scene: Reference to the :class:`~nodeeditor.node_scene.Scene`
        :type scene: :class:`~nodeeditor.node_scene.Scene`

        :Instance Attributes:

        - **scene** - reference to the :class:`~nodeeditor.node_scene.Scene`
        """
        self.scene = scene

    def serializeSelected(self, delete: bool = False) -> OrderedDict:
        """
        Serializes selected items in the Scene into ``OrderedDict``

        :param delete: True if you want to delete selected items after serialization. Useful for Cut operation
        :type delete: ``bool``
        :return: Serialized data of current selection in NodeEditor :class:`~nodeeditor.node_scene.Scene`
        """
        if DEBUG:
            print("-- COPY TO CLIPBOARD ---")

        sel_nodes, sel_edges, sel_sockets = [], [], {}

        # sort edges and nodes
        for item in self.scene.grScene.selectedItems():
            node: Optional["Node"] = getattr(item, "node", None)
            if node is not None:
                sel_nodes.append(node.serialize())
                for socket in node.inputs + node.outputs:
                    sel_sockets[socket.id] = socket
            elif isinstance(item, QDMGraphicsEdge):
                sel_edges.append(item.edge)

        # debug
        if DEBUG:
            print("  NODES\n      ", sel_nodes)
            print("  EDGES\n      ", sel_edges)
            print("  SOCKETS\n     ", sel_sockets)

        # remove all edges which are not connected to a nodeeditor in our list
        edges_to_remove = []
        for edge in sel_edges:
            if edge.start_socket.id in sel_sockets and edge.end_socket.id in sel_sockets:
                # if DEBUG: print(" edge is ok, connected with both sides")
                pass
            else:
                if DEBUG:
                    print("edge", edge, "is not connected with both sides")
                edges_to_remove.append(edge)
        for edge in edges_to_remove:
            sel_edges.remove(edge)

        # make final list of edges
        edges_final = []
        for edge in sel_edges:
            edges_final.append(edge.serialize())

        if DEBUG:
            print("our final edge list:", edges_final)

        data = OrderedDict([
            ('nodes', sel_nodes),
            ('edges', edges_final),
        ])

        # if CUT (aka delete) remove selected items
        if delete:
            self.scene.getView().deleteSelected()
            # store our history
            self.scene.history.storeHistory(
                "Cut out elements from scene", setModified=True)

        return data

    def deserializeFromClipboard(self, data: dict, *args, **kwargs) -> List['Node']:
        """
        Deserializes data from Clipboard.

        :param data: ``dict`` data for deserialization to the :class:`nodeeditor.node_scene.Scene`.
        :type data: ``dict``
        """

        hashmap: dict = {}

        # calculate mouse pointer - scene position
        view = self.scene.getView()
        mouse_scene_pos = view.last_scene_mouse_position

        # calculate selected objects bbox and center
        minx, max_x, min_y, max_y = 10000000, -10000000, 10000000, -10000000
        for node_data in data['nodes']:
            if 'pos_x' in node_data and 'pos_y' in node_data:
                x, y = node_data['pos_x'], node_data['pos_y']
            else:
                # added support if node pos serializes into `pos` instead of `pos_x` and `pos_y`
                x, y = node_data['pos']
            if x < minx:
                minx = x
            if x > max_x:
                max_x = x
            if y < min_y:
                min_y = y
            if y > max_y:
                max_y = y

        # add width and height of a node
        max_x -= 180
        max_y += 100

        relbboxcenterx = (minx + max_x) / 2 - minx
        relbboxcentery = (min_y + max_y) / 2 - min_y

        if DEBUG_PASTING:
            print(" *** PASTA:")
            print("Copied boudaries:\n\tX:", minx,
                  max_x, "   Y:", min_y, max_y)
            print("\tbbox_center:", relbboxcenterx, relbboxcentery)

        # calculate the offset of the newly creating nodes
        mouse_x, mouse_y = mouse_scene_pos.x(), mouse_scene_pos.y()

        # create each node
        created_nodes: List['Node'] = []

        self.scene.setSilentSelectionEvents()

        self.scene.doDeselectItems()

        for node_data in data['nodes']:
            new_node = self.scene.getNodeClassFromData(node_data)(self.scene)
            new_node.deserialize(node_data, hashmap, False, *args, **kwargs)
            created_nodes.append(new_node)

            # readjust the new nodeeditor's position

            # new node's current position
            pos_x, pos_y = new_node.pos.x(), new_node.pos.y()
            new_x, new_y = mouse_x + pos_x - minx, mouse_y + pos_y - min_y

            new_node.setPos(new_x, new_y)

            new_node.doSelect()

            if DEBUG_PASTING:
                print("** PASTA SUM:")
                print("\tMouse pos:", mouse_x, mouse_y)
                print("\tnew node pos:", pos_x, pos_y)
                print("\tFINAL:", new_x, new_y)

        # create each edge
        if 'edges' in data:
            for edge_data in data['edges']:
                new_edge = Edge(self.scene)
                # kwargs_copy = kwargs.copy()
                # if 'restore_id' in kwargs_copy:
                #     del kwargs_copy['restore_id']
                new_edge.deserialize(edge_data, hashmap,
                                     False, *args, **kwargs)

        self.scene.setSilentSelectionEvents(False)

        # store history
        self.scene.history.storeHistory(
            "Pasted elements in scene", setModified=True)

        return created_nodes

    # ==================== Enhanced Clipboard Operations ====================

    def copyNodes(self) -> bool:
        """
        Copy selected nodes to clipboard (without deleting them).
        
        :return: True if copy was successful, False otherwise
        :rtype: ``bool``
        
        Example:
            >>> clipboard = scene.clipboard
            >>> clipboard.copyNodes()  # Copy selected nodes
            >>> clipboard.pasteNodes()  # Paste them elsewhere
        """
        try:
            data = self.serializeSelected(delete=False)
            if not data.get('nodes'):
                if DEBUG:
                    print("No nodes to copy")
                return False
            
            # Store in scene clipboard buffer
            self.scene._clipboard_data = data
            if DEBUG:
                print(f"Copied {len(data['nodes'])} node(s) to clipboard")
            return True
        except Exception as e:
            if DEBUG:
                print(f"Error copying nodes: {e}")
            return False

    def cutNodes(self) -> bool:
        """
        Cut selected nodes (copy and delete).
        
        :return: True if cut was successful, False otherwise
        :rtype: ``bool``
        
        Example:
            >>> clipboard = scene.clipboard
            >>> clipboard.cutNodes()  # Cut selected nodes
            >>> clipboard.pasteNodes()  # Paste them elsewhere
        """
        try:
            data = self.serializeSelected(delete=True)
            if not data.get('nodes'):
                if DEBUG:
                    print("No nodes to cut")
                return False
            
            # Store in scene clipboard buffer
            self.scene._clipboard_data = data
            if DEBUG:
                print(f"Cut {len(data['nodes'])} node(s)")
            return True
        except Exception as e:
            if DEBUG:
                print(f"Error cutting nodes: {e}")
            return False

    def pasteNodes(self) -> List['Node']:
        """
        Paste nodes from clipboard.
        
        :return: List of pasted nodes, empty list if nothing to paste
        :rtype: ``List[Node]``
        
        Example:
            >>> clipboard = scene.clipboard
            >>> clipboard.copyNodes()
            >>> pasted_nodes = clipboard.pasteNodes()
            >>> print(f"Pasted {len(pasted_nodes)} nodes")
        """
        try:
            if not hasattr(self.scene, '_clipboard_data') or not self.scene._clipboard_data:
                if DEBUG:
                    print("Clipboard is empty")
                return []
            
            data = self.scene._clipboard_data
            pasted_nodes = self.deserializeFromClipboard(data)
            if DEBUG:
                print(f"Pasted {len(pasted_nodes)} node(s)")
            return pasted_nodes
        except Exception as e:
            if DEBUG:
                print(f"Error pasting nodes: {e}")
            return []

    def hasClipboardData(self) -> bool:
        """
        Check if clipboard has data to paste.
        
        :return: True if clipboard has nodes, False otherwise
        :rtype: ``bool``
        """
        return (hasattr(self.scene, '_clipboard_data') and 
                bool(self.scene._clipboard_data and 
                self.scene._clipboard_data.get('nodes')))

    def clearClipboard(self) -> None:
        """
        Clear the clipboard buffer.
        
        Example:
            >>> clipboard = scene.clipboard
            >>> clipboard.clearClipboard()
        """
        if hasattr(self.scene, '_clipboard_data'):
            self.scene._clipboard_data = None
        if DEBUG:
            print("Clipboard cleared")

    # ==================== Text Clipboard Operations ====================

    def copyText(self, text: str) -> bool:
        """
        Copy text to clipboard buffer.
        
        :param text: Text to copy
        :type text: ``str``
        :return: True if copy was successful
        :rtype: ``bool``
        
        Example:
            >>> clipboard = scene.clipboard
            >>> clipboard.copyText("Some text from line edit")
        """
        try:
            if not hasattr(self.scene, '_text_clipboard'):
                self.scene._text_clipboard = None
            
            self.scene._text_clipboard = text
            if DEBUG:
                print(f"Copied text: {text[:50]}...")
            return True
        except Exception as e:
            if DEBUG:
                print(f"Error copying text: {e}")
            return False

    def pasteText(self) -> Optional[str]:
        """
        Paste text from clipboard buffer.
        
        :return: Pasted text or None if clipboard is empty
        :rtype: ``Optional[str]``
        
        Example:
            >>> clipboard = scene.clipboard
            >>> text = clipboard.pasteText()
            >>> if text:
            ...     line_edit.setText(text)
        """
        try:
            if not hasattr(self.scene, '_text_clipboard'):
                return None
            
            text = self.scene._text_clipboard
            if DEBUG and text:
                print(f"Pasted text: {text[:50]}...")
            return text
        except Exception as e:
            if DEBUG:
                print(f"Error pasting text: {e}")
            return None

    def hasTextData(self) -> bool:
        """
        Check if clipboard has text data.
        
        :return: True if clipboard has text
        :rtype: ``bool``
        """
        return (hasattr(self.scene, '_text_clipboard') and 
                bool(self.scene._text_clipboard))

    # ==================== Table Clipboard Operations ====================

    def copyTableData(self, table_data: List[List[Any]]) -> bool:
        """
        Copy table data to clipboard buffer.
        
        :param table_data: 2D list of table data (rows and columns)
        :type table_data: ``List[List[Any]]``
        :return: True if copy was successful
        :rtype: ``bool``
        
        Example:
            >>> clipboard = scene.clipboard
            >>> table_data = [['Name', 'Value'], ['Item1', 100], ['Item2', 200]]
            >>> clipboard.copyTableData(table_data)
        """
        try:
            if not hasattr(self.scene, '_table_clipboard'):
                self.scene._table_clipboard = None
            
            self.scene._table_clipboard = table_data
            if DEBUG:
                print(f"Copied table data: {len(table_data)} rows, "
                      f"{len(table_data[0]) if table_data else 0} columns")
            return True
        except Exception as e:
            if DEBUG:
                print(f"Error copying table data: {e}")
            return False

    def pasteTableData(self) -> Optional[List[List[Any]]]:
        """
        Paste table data from clipboard buffer.
        
        :return: Pasted table data or None if clipboard is empty
        :rtype: ``Optional[List[List[Any]]]``
        
        Example:
            >>> clipboard = scene.clipboard
            >>> data = clipboard.pasteTableData()
            >>> if data:
            ...     for row in data:
            ...         table.insertRow(row)
        """
        try:
            if not hasattr(self.scene, '_table_clipboard'):
                return None
            
            data = self.scene._table_clipboard
            if DEBUG and data:
                print(f"Pasted table data: {len(data)} rows")
            return data
        except Exception as e:
            if DEBUG:
                print(f"Error pasting table data: {e}")
            return None

    def hasTableData(self) -> bool:
        """
        Check if clipboard has table data.
        
        :return: True if clipboard has table data
        :rtype: ``bool``
        """
        return (hasattr(self.scene, '_table_clipboard') and 
                bool(self.scene._table_clipboard))

    def exportTableToCSV(self, table_data: List[List[Any]], delimiter: str = ',') -> str:
        """
        Export table data to CSV format string.
        
        :param table_data: 2D list of table data
        :type table_data: ``List[List[Any]]``
        :param delimiter: CSV delimiter (default: ',')
        :type delimiter: ``str``
        :return: CSV formatted string
        :rtype: ``str``
        
        Example:
            >>> clipboard = scene.clipboard
            >>> csv_string = clipboard.exportTableToCSV(table_data)
            >>> print(csv_string)
        """
        try:
            if not table_data:
                return ""
            
            lines = []
            for row in table_data:
                # Convert to strings and escape if needed
                cells = []
                for cell in row:
                    cell_str = str(cell)
                    # Escape quotes and wrap in quotes if contains delimiter
                    if delimiter in cell_str or '"' in cell_str or '\n' in cell_str:
                        cell_str = '"' + cell_str.replace('"', '""') + '"'
                    cells.append(cell_str)
                lines.append(delimiter.join(cells))
            
            return '\n'.join(lines)
        except Exception as e:
            if DEBUG:
                print(f"Error exporting to CSV: {e}")
            return ""

    def importTableFromCSV(self, csv_string: str, delimiter: str = ',') -> Optional[List[List[str]]]:
        """
        Import table data from CSV format string.
        
        :param csv_string: CSV formatted string
        :type csv_string: ``str``
        :param delimiter: CSV delimiter (default: ',')
        :type delimiter: ``str``
        :return: 2D list of table data or None if error
        :rtype: ``Optional[List[List[str]]]``
        
        Example:
            >>> clipboard = scene.clipboard
            >>> csv_string = "Name,Value\nItem1,100\nItem2,200"
            >>> data = clipboard.importTableFromCSV(csv_string)
        """
        try:
            if not csv_string:
                return None
            
            lines = csv_string.strip().split('\n')
            table_data = []
            
            for line in lines:
                # Simple CSV parsing (doesn't handle all edge cases)
                cells = []
                current_cell = ""
                in_quotes = False
                
                for char in line:
                    if char == '"':
                        in_quotes = not in_quotes
                    elif char == delimiter and not in_quotes:
                        cells.append(current_cell.strip())
                        current_cell = ""
                    else:
                        current_cell += char
                
                cells.append(current_cell.strip())
                table_data.append(cells)
            
            if DEBUG:
                print(f"Imported {len(table_data)} rows from CSV")
            return table_data
        except Exception as e:
            if DEBUG:
                print(f"Error importing from CSV: {e}")
            return None

    # ==================== Utility Methods ====================

    def getClipboardInfo(self) -> Dict[str, Any]:
        """
        Get information about what's currently in the clipboard.
        
        :return: Dictionary with clipboard contents info
        :rtype: ``Dict[str, Any]``
        
        Example:
            >>> clipboard = scene.clipboard
            >>> info = clipboard.getClipboardInfo()
            >>> print(f"Nodes: {info['node_count']}, Text: {info['has_text']}, Table: {info['has_table']}")
        """
        info = {
            'has_nodes': self.hasClipboardData(),
            'node_count': len(self.scene._clipboard_data.get('nodes', [])) 
                         if (hasattr(self.scene, '_clipboard_data') and self.scene._clipboard_data) else 0,
            'edge_count': len(self.scene._clipboard_data.get('edges', [])) 
                         if (hasattr(self.scene, '_clipboard_data') and self.scene._clipboard_data) else 0,
            'has_text': self.hasTextData(),
            'text_length': len(self.scene._text_clipboard) if (self.hasTextData() and self.scene._text_clipboard) else 0,
            'has_table': self.hasTableData(),
            'table_rows': len(self.scene._table_clipboard) if (self.hasTableData() and self.scene._table_clipboard) else 0,
            'table_cols': len(self.scene._table_clipboard[0]) if (self.hasTableData() and self.scene._table_clipboard) else 0,
        }
        return info

    def clearAllClipboards(self) -> None:
        """
        Clear all clipboard buffers (nodes, text, and table data).
        
        Example:
            >>> clipboard = scene.clipboard
            >>> clipboard.clearAllClipboards()
        """
        self.clearClipboard()
        if hasattr(self.scene, '_text_clipboard'):
            self.scene._text_clipboard = None
        if hasattr(self.scene, '_table_clipboard'):
            self.scene._table_clipboard = None
        if DEBUG:
            print("All clipboards cleared")
