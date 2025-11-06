"""
Icon Registry for managing and caching node icons.

Provides centralized icon management for nodes, preventing duplicate
pixmap loading and enabling efficient icon sharing.
"""

from typing import Dict, Optional
from pathlib import Path
from qtpy.QtGui import QPixmap, QIcon


class IconRegistry:
    """
    Centralized registry for managing node icons.

    Caches loaded icons to avoid repeated file I/O and provides
    efficient icon retrieval by path or name.
    """

    def __init__(self, icon_dir: Optional[str] = None) -> None:
        """
        Initialize the IconRegistry.

        Args:
            icon_dir: Optional base directory for icon files
        """
        self._cache: Dict[str, QPixmap] = {}
        self._icon_dir: Optional[Path] = Path(icon_dir) if icon_dir else None

    def register_icon(self, name: str, pixmap: QPixmap) -> None:
        """
        Register an icon pixmap.

        Args:
            name: Unique name for the icon
            pixmap: QPixmap to cache
        """
        if not isinstance(pixmap, QPixmap):
            raise TypeError(f"Expected QPixmap, got {type(pixmap)}")
        self._cache[name] = pixmap

    def register_icon_from_path(self, name: str, path: str, 
                               size: Optional[tuple] = None) -> bool:
        """
        Register an icon from a file path.

        Args:
            name: Unique name for the icon
            path: File path to the icon
            size: Optional (width, height) to scale the icon

        Returns:
            True if icon loaded successfully
        """
        try:
            pixmap = QPixmap(path)
            if pixmap.isNull():
                print(f"Warning: Failed to load icon from {path}")
                return False

            if size:
                pixmap = pixmap.scaledToWidth(
                    int(size[0]),
                    mode=2  # Qt.TransformationMode.SmoothTransformation
                )

            self._cache[name] = pixmap
            return True
        except Exception as e:
            print(f"Error loading icon {path}: {e}")
            return False

    def get_icon(self, name: str) -> Optional[QPixmap]:
        """
        Get an icon by name.

        Args:
            name: Name of the icon

        Returns:
            QPixmap or None if not found
        """
        return self._cache.get(name)

    def get_icon_from_path(self, path: str, 
                          size: Optional[tuple] = None,
                          cache: bool = True) -> Optional[QPixmap]:
        """
        Get an icon from file path, optionally caching it.

        Args:
            path: File path to the icon
            size: Optional (width, height) to scale the icon
            cache: Whether to cache the loaded pixmap

        Returns:
            QPixmap or None if loading failed
        """
        # Check if already cached by path
        if path in self._cache:
            return self._cache[path]

        try:
            pixmap = QPixmap(path)
            if pixmap.isNull():
                print(f"Warning: Failed to load icon from {path}")
                return None

            if size:
                pixmap = pixmap.scaledToWidth(
                    int(size[0]),
                    mode=2  # Qt.TransformationMode.SmoothTransformation
                )

            if cache:
                self._cache[path] = pixmap

            return pixmap
        except Exception as e:
            print(f"Error loading icon {path}: {e}")
            return None

    def has_icon(self, name: str) -> bool:
        """
        Check if an icon is registered.

        Args:
            name: Name of the icon

        Returns:
            True if icon exists in cache
        """
        return name in self._cache

    def remove_icon(self, name: str) -> bool:
        """
        Remove an icon from the cache.

        Args:
            name: Name of the icon to remove

        Returns:
            True if icon was removed, False if not found
        """
        if name in self._cache:
            del self._cache[name]
            return True
        return False

    def clear_cache(self) -> None:
        """Clear all cached icons."""
        self._cache.clear()

    def list_icons(self) -> list[str]:
        """
        Get list of all cached icon names.

        Returns:
            List of icon names
        """
        return list(self._cache.keys())

    def get_cache_size(self) -> int:
        """
        Get total size of cached pixmaps in bytes (approximate).

        Returns:
            Approximate size in bytes
        """
        total_size = 0
        for pixmap in self._cache.values():
            # Approximate size: width * height * 4 (RGBA)
            total_size += pixmap.width() * pixmap.height() * 4
        return total_size


# Global icon registry instance
_global_icon_registry: Optional[IconRegistry] = None


def get_icon_registry() -> IconRegistry:
    """
    Get or create the global icon registry.

    Returns:
        IconRegistry instance
    """
    global _global_icon_registry
    if _global_icon_registry is None:
        _global_icon_registry = IconRegistry()
    return _global_icon_registry


def set_icon_registry(registry: IconRegistry) -> None:
    """
    Set the global icon registry.

    Args:
        registry: IconRegistry to use globally
    """
    global _global_icon_registry
    if not isinstance(registry, IconRegistry):
        raise TypeError(f"Expected IconRegistry, got {type(registry)}")
    _global_icon_registry = registry
