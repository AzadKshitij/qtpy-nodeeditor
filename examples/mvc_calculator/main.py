"""
MVC Calculator Example - Main Entry Point

This example demonstrates building a node editor application using the
Model-View-Controller (MVC) architecture with the nodeeditor framework.

The MVC pattern ensures clear separation of concerns:
- Models: CalcNodeModel classes store node data and state
- Controllers: CalcNodeController manages business logic and node operations
- Views: Graphics nodes and editor widgets handle visualization

The calculator supports:
- Input nodes: Enter numeric values
- Output nodes: Display computed results
- Operation nodes: Add, Subtract, Multiply, Divide
- Edge validation: Prevents invalid connections
- Undo/Redo: Full history support
- Save/Load: Persist graphs to disk

Usage:
    python main.py

Features:
    - Multiple document interface (MDI)
    - Drag-and-drop node creation
    - Right-click context menu for node creation
    - Grid visualization
    - Edge type selection
    - File operations (New, Open, Save, Save As)

Architecture:
    examples/mvc_calculator/
    ├── models/           # Data models (CalcNodeModel classes)
    ├── controllers/      # Business logic (CalcNodeController)
    ├── nodes/            # Node implementations (Input, Output, Operations)
    ├── views/            # Graphics views (can be extended)
    ├── mvc_window.py     # Main application window
    ├── mvc_sub_window.py # MDI child window
    └── mvc_conf.py       # Node registration and configuration
"""

import os
import sys

# Add parent directories to path to allow imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from qtpy.QtWidgets import QApplication

from examples.mvc_calculator.mvc_window import MvcCalculatorWindow


def main():
    """Main entry point for the MVC Calculator application."""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    # Create and show main window
    wnd = MvcCalculatorWindow()
    wnd.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
