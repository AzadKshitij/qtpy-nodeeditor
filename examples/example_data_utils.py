"""
Example: Data Conversion and Comparison Utilities

This example demonstrates:
1. Converting between Qt types and Python types
2. Comparing Qt types with float tolerance
3. Serializing/deserializing complex data structures
"""

from qtpy.QtCore import QPointF, QSizeF, QRectF
from qtpy.QtGui import QColor
from nodeeditor.utils import (
    # Conversion functions
    qpointf_to_tuple,
    tuple_to_qpointf,
    qsizef_to_tuple,
    tuple_to_qsizef,
    qrectf_to_dict,
    dict_to_qrectf,
    qcolor_to_hex,
    hex_to_qcolor,
    normalize_point,
    normalize_size,
    normalize_rect,
    # Comparison functions
    floats_equal,
    tuples_equal,
    qpointf_equal,
    qsizef_equal,
    qrectf_equal,
    qcolor_equal,
    dict_equal,
)


def example_point_conversion():
    """Convert between QPointF and tuples."""
    print("=" * 60)
    print("Example 1: Point Conversion")
    print("=" * 60)
    
    # QPointF to tuple
    point = QPointF(10.5, 20.75)
    tuple_point = qpointf_to_tuple(point)
    print(f"QPointF({point.x()}, {point.y()}) → tuple{tuple_point}")
    
    # Tuple to QPointF
    new_point = tuple_to_qpointf(tuple_point)
    print(f"tuple{tuple_point} → QPointF({new_point.x()}, {new_point.y()})")
    
    # Direct tuple input to to_tuple (passthrough)
    tuple_input = (5.0, 15.0)
    result = qpointf_to_tuple(tuple_input)
    print(f"tuple{tuple_input} → tuple{result}")
    print()


def example_size_conversion():
    """Convert between QSizeF and tuples."""
    print("=" * 60)
    print("Example 2: Size Conversion")
    print("=" * 60)
    
    # QSizeF to tuple
    size = QSizeF(100.0, 200.0)
    tuple_size = qsizef_to_tuple(size)
    print(f"QSizeF({size.width()}, {size.height()}) → tuple{tuple_size}")
    
    # Tuple to QSizeF
    new_size = tuple_to_qsizef(tuple_size)
    print(f"tuple{tuple_size} → QSizeF({new_size.width()}, {new_size.height()})")
    print()


def example_rect_conversion():
    """Convert between QRectF and dictionaries."""
    print("=" * 60)
    print("Example 3: Rectangle Conversion")
    print("=" * 60)
    
    # QRectF to dict
    rect = QRectF(10.0, 20.0, 300.0, 150.0)
    dict_rect = qrectf_to_dict(rect)
    print(f"QRectF({rect.x()}, {rect.y()}, {rect.width()}, {rect.height()})")
    print(f"  → dict{dict_rect}")
    
    # Dict to QRectF
    new_rect = dict_to_qrectf(dict_rect)
    print(f"dict{dict_rect}")
    print(f"  → QRectF({new_rect.x()}, {new_rect.y()}, {new_rect.width()}, {new_rect.height()})")
    print()


def example_color_conversion():
    """Convert between QColor and hex strings."""
    print("=" * 60)
    print("Example 4: Color Conversion")
    print("=" * 60)
    
    # QColor to hex
    color = QColor(255, 128, 64)  # Orange
    hex_color = qcolor_to_hex(color)
    print(f"QColor(255, 128, 64) → '{hex_color}'")
    
    # Hex to QColor
    new_color = hex_to_qcolor(hex_color)
    print(f"'{hex_color}' → QColor({new_color.red()}, {new_color.green()}, {new_color.blue()})")
    
    # With alpha
    color_alpha = QColor(255, 128, 64, 128)  # 50% transparent
    hex_alpha = qcolor_to_hex(color_alpha)
    print(f"QColor(255, 128, 64, 128) → '{hex_alpha}'")
    print()


def example_normalize_values():
    """Normalize various types to consistent formats."""
    print("=" * 60)
    print("Example 5: Normalize Values")
    print("=" * 60)
    
    # Normalize point
    qp = QPointF(1.5, 2.5)
    t = (1.5, 2.5)
    print(f"normalize_point(QPointF) = {normalize_point(qp)}")
    print(f"normalize_point(tuple) = {normalize_point(t)}")
    
    # Normalize size
    qs = QSizeF(100.0, 200.0)
    s = (100.0, 200.0)
    print(f"normalize_size(QSizeF) = {normalize_size(qs)}")
    print(f"normalize_size(tuple) = {normalize_size(s)}")
    
    # Normalize rect
    qr = QRectF(0, 0, 100, 100)
    d = {'x': 0, 'y': 0, 'width': 100, 'height': 100}
    print(f"normalize_rect(QRectF) = {normalize_rect(qr)}")
    print(f"normalize_rect(dict) = {normalize_rect(d)}")
    print()


def example_float_comparison():
    """Compare floats with tolerance."""
    print("=" * 60)
    print("Example 6: Float Comparison with Tolerance")
    print("=" * 60)
    
    # Exact match
    print(f"floats_equal(1.0, 1.0) = {floats_equal(1.0, 1.0)}")
    
    # Close values (within default tolerance 1e-9)
    print(f"floats_equal(1.0, 1.0000000001) = {floats_equal(1.0, 1.0000000001)}")
    
    # Different values
    print(f"floats_equal(1.0, 1.1) = {floats_equal(1.0, 1.1)}")
    
    # Custom tolerance
    print(f"floats_equal(1.0, 1.01, tolerance=0.01) = {floats_equal(1.0, 1.01, 0.01)}")
    print(f"floats_equal(1.0, 1.01, tolerance=0.001) = {floats_equal(1.0, 1.01, 0.001)}")
    print()


def example_point_comparison():
    """Compare QPointF objects."""
    print("=" * 60)
    print("Example 7: Point Comparison")
    print("=" * 60)
    
    p1 = QPointF(1.0, 2.0)
    p2 = QPointF(1.0, 2.0)
    p3 = QPointF(1.0000000001, 2.0000000001)  # Tiny difference
    p4 = QPointF(1.5, 2.5)  # Significant difference
    
    print(f"qpointf_equal(QPointF(1, 2), QPointF(1, 2)) = {qpointf_equal(p1, p2)}")
    print(f"qpointf_equal(QPointF(1, 2), QPointF(1.0000000001, 2.0000000001)) = {qpointf_equal(p1, p3)}")
    print(f"qpointf_equal(QPointF(1, 2), QPointF(1.5, 2.5)) = {qpointf_equal(p1, p4)}")
    print()


def example_size_comparison():
    """Compare QSizeF objects."""
    print("=" * 60)
    print("Example 8: Size Comparison")
    print("=" * 60)
    
    s1 = QSizeF(100.0, 200.0)
    s2 = QSizeF(100.0, 200.0)
    s3 = QSizeF(100.0000000001, 200.0000000001)
    s4 = QSizeF(100.5, 200.5)
    
    print(f"qsizef_equal(s1, s2) = {qsizef_equal(s1, s2)}")
    print(f"qsizef_equal(s1, s3) = {qsizef_equal(s1, s3)}")
    print(f"qsizef_equal(s1, s4) = {qsizef_equal(s1, s4)}")
    print()


def example_rect_comparison():
    """Compare QRectF objects."""
    print("=" * 60)
    print("Example 9: Rectangle Comparison")
    print("=" * 60)
    
    r1 = QRectF(10, 20, 100, 200)
    r2 = QRectF(10, 20, 100, 200)
    r3 = QRectF(10.0000000001, 20.0000000001, 100.0000000001, 200.0000000001)
    r4 = QRectF(10.5, 20.5, 100.5, 200.5)
    
    print(f"qrectf_equal(r1, r2) = {qrectf_equal(r1, r2)}")
    print(f"qrectf_equal(r1, r3) = {qrectf_equal(r1, r3)}")
    print(f"qrectf_equal(r1, r4) = {qrectf_equal(r1, r4)}")
    print()


def example_dict_comparison():
    """Deep compare dictionaries with float tolerance."""
    print("=" * 60)
    print("Example 10: Dictionary Comparison")
    print("=" * 60)
    
    d1 = {
        'x': 10.0,
        'y': 20.0,
        'width': 100.0,
        'height': 200.0,
        'name': 'rect1'
    }
    d2 = {
        'x': 10.0,
        'y': 20.0,
        'width': 100.0,
        'height': 200.0,
        'name': 'rect1'
    }
    d3 = {
        'x': 10.0000000001,
        'y': 20.0000000001,
        'width': 100.0000000001,
        'height': 200.0000000001,
        'name': 'rect1'
    }
    
    print(f"dict_equal(d1, d2) = {dict_equal(d1, d2)}")
    print(f"dict_equal(d1, d3) = {dict_equal(d1, d3)}")
    print()


def example_serialization():
    """Complete serialization/deserialization example."""
    print("=" * 60)
    print("Example 11: Complete Serialization")
    print("=" * 60)
    
    # Create complex structure
    data = {
        'nodes': [
            {
                'id': 'node_1',
                'title': 'Input',
                'position': {'x': 10.0, 'y': 20.0},
                'size': {'width': 80.0, 'height': 60.0},
                'color': '#FF5733'
            },
            {
                'id': 'node_2',
                'title': 'Output',
                'position': {'x': 200.0, 'y': 20.0},
                'size': {'width': 80.0, 'height': 60.0},
                'color': '#33FF57'
            }
        ]
    }
    
    print("Original data:")
    for node in data['nodes']:
        print(f"  Node: {node['id']}")
        print(f"    Position: {node['position']}")
        print(f"    Size: {node['size']}")
        print(f"    Color: {node['color']}")
    
    # Convert to objects
    print("\nConverted to Qt objects:")
    for node in data['nodes']:
        pos = tuple_to_qpointf((node['position']['x'], node['position']['y']))
        size = tuple_to_qsizef((node['size']['width'], node['size']['height']))
        color = hex_to_qcolor(node['color'])
        print(f"  Node: {node['id']}")
        print(f"    Position: QPointF({pos.x()}, {pos.y()})")
        print(f"    Size: QSizeF({size.width()}, {size.height()})")
        print(f"    Color: QColor({color.red()}, {color.green()}, {color.blue()})")
    print()


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 8 + "Data Conversion and Comparison Examples" + " " * 12 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\n")
    
    try:
        example_point_conversion()
        example_size_conversion()
        example_rect_conversion()
        example_color_conversion()
        example_normalize_values()
        example_float_comparison()
        example_point_comparison()
        example_size_comparison()
        example_rect_comparison()
        example_dict_comparison()
        example_serialization()
        
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
