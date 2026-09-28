#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example demonstrating the Color Configuration Feature in qtpy-nodeeditor

This example shows how to:
1. Create custom color schemes
2. Update edge colors
3. Update socket colors
4. Apply themes dynamically
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from qtpy.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QComboBox, QLabel, QGroupBox
)
from nodeeditor.node_edge import Edge
from nodeeditor.node_editor_widget import NodeEditorWidget
from nodeeditor.node_node import Node
from nodeeditor.node_colors_config import get_color_scheme


class ColorSchemes:
    """Collection of predefined color schemes"""

    DEFAULT = {
        'name': 'Default',
        'edges': {
            'default': '#333334',
            'selected': '#00ff00',
            'hovered': '#FF37A6FF',
            'dragging': '#333334'
        },
        'sockets': {
            'outline': '#FF000000',
            'highlight': '#FF37A6FF',
            'type_colors': [
                '#FFFF7700',
                '#FF52e220',
                '#FF0056a6',
                '#FFa86db1',
                '#FFb54747',
                '#FFdbe220',
                '#FF888888',
            ]
        }
    }

    DARK = {
        'name': 'Dark Theme',
        'edges': {
            'default': '#1e1e1e',
            'selected': '#4CAF50',
            'hovered': '#FF9800',
            'dragging': '#9C27B0'
        },
        'sockets': {
            'outline': '#ffffff',
            'highlight': '#FF6B6B',
            'type_colors': [
                '#FF6B6B',  # Red
                '#4ECDC4',  # Teal
                '#45B7D1',  # Blue
                '#FFA07A',  # Light Salmon
                '#98D8C8',  # Mint
                '#F7DC6F',  # Yellow
                '#BB8FCE',  # Purple
            ]
        }
    }

    LIGHT = {
        'name': 'Light Theme',
        'edges': {
            'default': '#cccccc',
            'selected': '#0066cc',
            'hovered': '#ff6600',
            'dragging': '#0066cc'
        },
        'sockets': {
            'outline': '#333333',
            'highlight': '#ff6600',
            'type_colors': [
                '#ff0000',  # Red
                '#00aa00',  # Green
                '#0000ff',  # Blue
                '#ff00ff',  # Magenta
                '#00ffff',  # Cyan
                '#ffaa00',  # Orange
                '#888888',  # Gray
            ]
        }
    }

    NEON = {
        'name': 'Neon Theme',
        'edges': {
            'default': '#00ffff',
            'selected': '#ff00ff',
            'hovered': '#00ff00',
            'dragging': '#ffff00'
        },
        'sockets': {
            'outline': '#ffffff',
            'highlight': '#00ff00',
            'type_colors': [
                '#ff0080',  # Hot Pink
                '#00ff80',  # Spring Green
                '#0080ff',  # Deep Sky Blue
                '#ff00ff',  # Magenta
                '#ffff00',  # Yellow
                '#00ffff',  # Cyan
                '#ff8000',  # Orange
            ]
        }
    }

    SOLARIZED = {
        'name': 'Solarized',
        'edges': {
            'default': '#586e75',
            'selected': '#859900',
            'hovered': '#d33682',
            'dragging': '#268bd2'
        },
        'sockets': {
            'outline': '#002b36',
            'highlight': '#dc322f',
            'type_colors': [
                '#dc322f',  # red
                '#859900',  # green
                '#268bd2',  # blue
                '#6c71c4',  # violet
                '#2aa198',  # cyan
                '#b58900',  # yellow
                '#93a1a1',  # base1
            ]
        }
    }

    @classmethod
    def get_all(cls):
        """Get all available schemes"""
        return [
            cls.DEFAULT,
            cls.DARK,
            cls.LIGHT,
            cls.NEON,
            cls.SOLARIZED,
        ]


class ColorConfigDemo(QMainWindow):
    """Main window demonstrating color configuration"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Node Editor - Color Configuration Demo')
        self.setGeometry(100, 100, 1200, 800)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create layout
        layout = QHBoxLayout(central_widget)

        # Create editor widget
        self.editor = NodeEditorWidget()
        layout.addWidget(self.editor, 1)

        # Create control panel
        control_panel = self._create_control_panel()
        layout.addWidget(control_panel)

        # Connect signals
        self._create_demo_nodes()

    def _create_control_panel(self) -> QGroupBox:
        """Create the control panel for color configuration"""
        panel = QGroupBox('Color Configuration')
        layout = QVBoxLayout()

        # Theme selector
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel('Theme:'))
        self.theme_combo = QComboBox()
        for scheme in ColorSchemes.get_all():
            self.theme_combo.addItem(scheme['name'], scheme)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        theme_layout.addWidget(self.theme_combo)
        layout.addLayout(theme_layout)

        # Edge color buttons
        edge_group = QGroupBox('Edge Colors')
        edge_layout = QVBoxLayout()

        self.edge_default_btn = QPushButton('Default Color')
        self.edge_default_btn.clicked.connect(
            lambda: self._change_edge_color('default', '#FF0000')
        )
        edge_layout.addWidget(self.edge_default_btn)

        self.edge_selected_btn = QPushButton('Selected Color')
        self.edge_selected_btn.clicked.connect(
            lambda: self._change_edge_color('selected', '#00FF00')
        )
        edge_layout.addWidget(self.edge_selected_btn)

        self.edge_hovered_btn = QPushButton('Hovered Color')
        self.edge_hovered_btn.clicked.connect(
            lambda: self._change_edge_color('hovered', '#0000FF')
        )
        edge_layout.addWidget(self.edge_hovered_btn)

        edge_group.setLayout(edge_layout)
        layout.addWidget(edge_group)

        # Socket color buttons
        socket_group = QGroupBox('Socket Colors')
        socket_layout = QVBoxLayout()

        self.socket_highlight_btn = QPushButton('Highlight Color')
        self.socket_highlight_btn.clicked.connect(
            lambda: self._change_socket_highlight('#FF00FF')
        )
        socket_layout.addWidget(self.socket_highlight_btn)

        self.socket_outline_btn = QPushButton('Outline Color')
        self.socket_outline_btn.clicked.connect(
            lambda: self._change_socket_outline('#000000')
        )
        socket_layout.addWidget(self.socket_outline_btn)

        socket_group.setLayout(socket_layout)
        layout.addWidget(socket_group)

        # Reset button
        reset_btn = QPushButton('Reset to Default')
        reset_btn.clicked.connect(self._reset_colors)
        layout.addWidget(reset_btn)

        layout.addStretch()
        panel.setLayout(layout)
        return panel

    def _create_demo_nodes(self):
        """Create some demo nodes in the scene"""
        scene = self.editor.scene
        source = Node(scene, "Source", inputs=[1], outputs=[2])
        target = Node(scene, "Target", inputs=[2], outputs=[3])
        source.setPos(-250, -100)
        target.setPos(100, -100)
        Edge(scene, source.outputs[0], target.inputs[0])

    def _on_theme_changed(self, index):
        """Handle theme selection change"""
        scheme_data = self.theme_combo.itemData(index)
        if scheme_data:
            scheme = get_color_scheme()
            scheme.from_dict(scheme_data)
            # Refresh the scene
            if self.editor and self.editor.scene:
                self.editor.scene._refresh_colors()

    def _change_edge_color(self, color_type: str, color: str):
        """Change an edge color"""
        scene = self.editor.scene
        if color_type == 'default':
            scene.setEdgeColors(default=color)
        elif color_type == 'selected':
            scene.setEdgeColors(selected=color)
        elif color_type == 'hovered':
            scene.setEdgeColors(hovered=color)

    def _change_socket_highlight(self, color: str):
        """Change socket highlight color"""
        scene = self.editor.scene
        scene.setSocketColors(highlight=color)

    def _change_socket_outline(self, color: str):
        """Change socket outline color"""
        scene = self.editor.scene
        scene.setSocketColors(outline=color)

    def _reset_colors(self):
        """Reset colors to default"""
        scheme = get_color_scheme()
        scheme.reset_to_defaults()
        # Refresh the scene
        if self.editor and self.editor.scene:
            self.editor.scene._refresh_colors()
        # Reset combo box
        self.theme_combo.setCurrentIndex(0)


def main():
    """Main entry point"""
    app = QApplication([])

    # Create and show the demo window
    demo = ColorConfigDemo()
    demo.show()

    app.exec_()


if __name__ == '__main__':
    main()
