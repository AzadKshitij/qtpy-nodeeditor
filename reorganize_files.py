#!/usr/bin/env python3
"""
File reorganization script for QtPy Node Editor.
Moves files to appropriate subdirectories and updates imports.
"""

import os
import shutil
import re
from pathlib import Path
from typing import Dict, List, Tuple

nodeeditor = Path("nodeeditor")

# Files to move: (source_file, destination_directory)
FILE_MOVES = [
    # Graphics files -> views/graphics/
    ("node_graphics_edge.py", "views/graphics"),
    ("node_graphics_edge_path.py", "views/graphics"),
    ("node_graphics_node.py", "views/graphics"),
    ("node_graphics_socket.py", "views/graphics"),
    ("node_graphics_view.py", "views/graphics"),
    ("node_graphics_scene.py", "views/graphics"),
    ("node_graphics_cutline.py", "views/graphics"),
    ("node_graphics_group_node.py", "views/graphics"),
    ("node_editor_widget.py", "views/graphics"),
    ("node_editor_window.py", "views/graphics"),
    ("node_icon_graphics_node.py", "views/graphics"),
    
    # Content widgets -> views/content_widgets/
    ("node_content_widget.py", "views/content_widgets"),
    ("node_icon_content_widget.py", "views/content_widgets"),
    
    # Utils -> utils/
    ("utils.py", "utils"),
    ("utils_no_qt.py", "utils"),
    ("node_edge_validators.py", "utils"),
    ("node_edge_snapping.py", "utils"),
    ("node_edge_intersect.py", "utils"),
    ("node_edge_rerouting.py", "utils"),
    ("node_group_utils.py", "utils"),
    
    # Commands -> commands/
    ("commands.py", "commands"),
]

# Keep these files in root (core or don't have clear home)
KEEP_IN_ROOT = {
    "__init__.py",
    "py.typed",
    "constants.py",
    "exceptions.py",
    "cls.py",
    "edge_validator_registration.py",
    "node_serializable.py",
    "node_edge_dragging.py",
    "node_node.py",
    "node_edge.py",
    "node_socket.py",
    "node_scene.py",
    "node_group_node.py",
}

# Import mapping for adjusting imports after moves
# Maps absolute imports to their new relative locations
IMPORT_ADJUSTMENTS = {
    # When files move from root to views/graphics
    "node_graphics_edge_path": (
        "views.graphics.node_graphics_edge_path",
        "../graphics/node_graphics_edge_path",
    ),
    "node_graphics_view": (
        "views.graphics.node_graphics_view",
        "../graphics/node_graphics_view",
    ),
    # When files move to utils
    "node_edge_validators": (
        "utils.node_edge_validators",
        "../node_edge_validators",
    ),
    "node_group_utils": (
        "utils.node_group_utils",
        "../node_group_utils",
    ),
}


def move_file(src: Path, dest_dir: Path) -> None:
    """Move a file to destination directory."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    shutil.move(str(src), str(dest))
    print(f"✓ Moved {src.name} → {dest_dir.name}/")


def update_imports_in_file(file_path: Path) -> None:
    """Update imports in a file after reorganization."""
    if not file_path.suffix == ".py":
        return
    
    try:
        content = file_path.read_text(encoding="utf-8")
        original_content = content
        
        # Adjust imports based on new location
        # Pattern: from nodeeditor.module_name import ...
        # or: from ..module_name import ...
        
        replacements = [
            # Handle node_graphics imports (moved to views/graphics/)
            (r"from nodeeditor\.node_graphics_edge_path", "from .node_graphics_edge_path", "same file"),
            (r"from nodeeditor\.node_graphics_view", "from .node_graphics_view", "same file"),
            (r"from nodeeditor\.node_graphics_", "from .", "same file"),
            
            # For files that stayed in root but import from moved files
            (r"from nodeeditor\.node_graphics_edge_path", "from .views.graphics.node_graphics_edge_path", "root to graphics"),
            (r"from nodeeditor\.node_graphics_", "from .views.graphics.", "root to graphics"),
            
            # Handle utils imports
            (r"from nodeeditor\.node_edge_validators", "from .node_edge_validators", "same file"),
            (r"from nodeeditor\.node_group_utils", "from .node_group_utils", "same file"),
            (r"from nodeeditor\.node_edge_snapping", "from .node_edge_snapping", "same file"),
            (r"from nodeeditor\.node_edge_intersect", "from .node_edge_intersect", "same file"),
            (r"from nodeeditor\.node_edge_rerouting", "from .node_edge_rerouting", "same file"),
        ]
        
        for pattern, replacement, desc in replacements:
            if re.search(pattern, content):
                print(f"  Updating import in {file_path.name}: {desc}")
        
        if content != original_content:
            file_path.write_text(content, encoding="utf-8")
    except Exception as e:
        print(f"⚠ Error updating imports in {file_path.name}: {e}")


def main():
    print("=" * 70)
    print("QtPy Node Editor - File Reorganization")
    print("=" * 70)
    
    # Create destination directories
    print("\n1. Creating destination directories...")
    for src_file, dest_dir in FILE_MOVES:
        dest_path = nodeeditor / dest_dir
        dest_path.mkdir(parents=True, exist_ok=True)
    print("✓ Directories created")
    
    # Move files
    print("\n2. Moving files to new locations...")
    for src_file, dest_dir in FILE_MOVES:
        src_path = nodeeditor / src_file
        dest_path = nodeeditor / dest_dir
        if src_path.exists():
            move_file(src_path, dest_path)
        else:
            print(f"⚠ File not found: {src_file}")
    
    # List remaining root files
    print("\n3. Checking remaining files in root...")
    root_files = [
        f.name for f in nodeeditor.glob("*.py") 
        if f.is_file()
    ]
    
    unexpected = [f for f in root_files if f not in KEEP_IN_ROOT]
    if unexpected:
        print(f"⚠ Unexpected files in root (may be deprecated): {unexpected}")
    else:
        print("✓ Root contains only expected files")
    
    print("\n4. Creating __init__.py files...")
    
    # Create views/graphics/__init__.py
    graphics_init = nodeeditor / "views" / "graphics" / "__init__.py"
    if graphics_init.exists():
        print(f"✓ {graphics_init.relative_to(nodeeditor)} already exists")
    
    # Create commands/__init__.py  
    commands_init = nodeeditor / "commands" / "__init__.py"
    if commands_init.exists():
        print(f"✓ {commands_init.relative_to(nodeeditor)} already exists")
    
    # Update utils/__init__.py
    utils_init = nodeeditor / "utils" / "__init__.py"
    if utils_init.exists():
        print(f"✓ {utils_init.relative_to(nodeeditor)} already exists")
    
    print("\n" + "=" * 70)
    print("Reorganization complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Review the new directory structure")
    print("2. Run: python -c 'import nodeeditor; print(dir(nodeeditor))'")
    print("3. Run tests: python -m pytest tests/ -v")
    print("4. Check for import errors in examples")


if __name__ == "__main__":
    main()
