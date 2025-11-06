"""
Example: Using NodeIconModel for nodes with icon support

This example demonstrates:
1. Creating nodes with icons
2. Managing icons with IconRegistry
3. Using the MVC pattern with icons
"""

from nodeeditor.models import NodeIconModel, SceneModel
from nodeeditor.controllers import NodeController, SceneController
from nodeeditor.views.icons import get_icon_registry


def example_basic_icon_node():
    """Create a basic node with an icon."""
    print("=" * 60)
    print("Example 1: Basic Icon Node")
    print("=" * 60)
    
    # Create a node with an icon
    node = NodeIconModel(
        node_type="calculator",
        title="Add",
        icon_path="examples/icons/add.png"  # Adjust path as needed
    )
    
    print(f"Node: {node.title} (type: {node.node_type})")
    print(f"Has Icon: {node.has_icon()}")
    print(f"Icon Path: {node.icon_path}")
    print(f"Icon Size: {node.icon_size}")
    print()


def example_icon_registry():
    """Use the centralized icon registry."""
    print("=" * 60)
    print("Example 2: Icon Registry")
    print("=" * 60)
    
    registry = get_icon_registry()
    
    # Register icons by path
    registry.register_icon_from_path(
        "add_icon",
        "examples/icons/add.png",
        size=(64, 64)
    )
    registry.register_icon_from_path(
        "delete_icon",
        "examples/icons/delete.png",
        size=(64, 64)
    )
    
    # Get cached icons
    add_pixmap = registry.get_icon("add_icon")
    delete_pixmap = registry.get_icon("delete_icon")
    
    print(f"Registered Icons: {registry.list_icons()}")
    print(f"Has 'add_icon': {registry.has_icon('add_icon')}")
    print(f"Cache Size (bytes): {registry.get_cache_size()}")
    print()


def example_mvc_with_icons():
    """Use MVC pattern with icon nodes."""
    print("=" * 60)
    print("Example 3: MVC Pattern with Icon Nodes")
    print("=" * 60)
    
    # Create scene
    scene = SceneModel()
    
    # Create nodes with icons
    add_node = NodeIconModel(
        node_type="math",
        title="Add",
        icon_path="examples/icons/add.png"
    )
    
    multiply_node = NodeIconModel(
        node_type="math",
        title="Multiply",
        icon_path="examples/icons/multiply.png"
    )
    
    # Add to scene
    scene.add_node(add_node)
    scene.add_node(multiply_node)
    
    # Use controller to manipulate
    controller = NodeController(add_node)
    controller.set_position(100.0, 50.0)
    controller.set_title("Addition")
    
    print(f"Scene has {len(scene.nodes)} nodes")
    for node in scene.nodes:
        print(f"  - {node.title} at {node.position}")
        if hasattr(node, 'has_icon') and node.has_icon():
            print(f"    Icon: {node.icon_path}")
    print()


def example_icon_size_management():
    """Manage icon sizes dynamically."""
    print("=" * 60)
    print("Example 4: Icon Size Management")
    print("=" * 60)
    
    node = NodeIconModel(
        node_type="display",
        title="Preview",
        icon_path="examples/icons/preview.png"
    )
    
    print(f"Initial Size: {node.icon_size}")
    
    # Change size (icon is reloaded)
    node.icon_size = (128, 128)
    print(f"New Size: {node.icon_size}")
    
    # Change size again
    node.icon_size = (32, 32)
    print(f"Smallest Size: {node.icon_size}")
    print()


def example_serialization_with_icons():
    """Serialize and deserialize nodes with icons."""
    print("=" * 60)
    print("Example 5: Serialization with Icons")
    print("=" * 60)
    
    # Create and configure node
    original_node = NodeIconModel(
        node_type="input",
        title="Input Data",
        icon_path="examples/icons/input.png"
    )
    original_node.set_position(10.0, 20.0)
    original_node.icon_size = (80, 80)
    
    # Serialize
    data = original_node.serialize()
    print(f"Serialized Data:")
    for key, value in data.items():
        print(f"  {key}: {value}")
    print()
    
    # Deserialize
    restored_node = NodeIconModel.deserialize(data)
    print(f"Restored Node: {restored_node.title}")
    print(f"  Position: {restored_node.position}")
    print(f"  Icon Path: {restored_node.icon_path}")
    print(f"  Icon Size: {restored_node.icon_size}")
    print()


def example_icon_registry_caching():
    """Demonstrate icon caching benefits."""
    print("=" * 60)
    print("Example 6: Icon Registry Caching")
    print("=" * 60)
    
    registry = get_icon_registry()
    
    # First load - reads from disk
    print("Loading icon first time...")
    pixmap1 = registry.get_icon_from_path(
        "examples/icons/cached.png",
        size=(64, 64),
        cache=True
    )
    print(f"  Cache size: {len(registry.list_icons())} icons")
    
    # Second load - returns cached version (no disk I/O)
    print("Loading same icon second time (cached)...")
    pixmap2 = registry.get_icon_from_path(
        "examples/icons/cached.png",
        size=(64, 64),
        cache=True
    )
    print(f"  Cache size: {len(registry.list_icons())} icons")
    print(f"  Same pixmap? {pixmap1 is pixmap2}")
    
    print()


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "NodeIconModel Examples and Usage" + " " * 14 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\n")
    
    try:
        example_basic_icon_node()
        example_icon_registry()
        example_mvc_with_icons()
        example_icon_size_management()
        example_serialization_with_icons()
        example_icon_registry_caching()
        
        print("=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        print()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
