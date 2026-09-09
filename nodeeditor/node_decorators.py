from typing import Any, Callable, Optional, Type, Dict, TypeVar, List, TYPE_CHECKING

if TYPE_CHECKING:
    from nodeeditor.node_scene import Scene


T = TypeVar('T')


class MakeSerializable:
    """Registry for classes that should be automatically serialized"""
    _registry: Dict[str, Type] = {}
    _instances: Dict[str, List['Scene']] = {}  # Track instances per scene

    @classmethod
    def register(cls, key: str = "") -> Callable[[Type[T]], Type[T]]:
        """Class decorator to mark a class as automatically serializable"""
        def decorator(wrapped_class: Type[T]) -> Type[T]:
            # Use class name as key if none provided
            serialize_key = key or wrapped_class.__name__.lower()

            # Ensure the class has required methods
            if not hasattr(wrapped_class, 'serialize') or not hasattr(wrapped_class, 'deserialize'):
                raise TypeError(
                    f"Class {wrapped_class.__name__} must implement serialize and deserialize methods")

            # Store the original __init__
            original_init = wrapped_class.__init__

            # Create new __init__ that registers with scene
            def new_init(self, scene: 'Scene', *args, **kwargs):
                original_init(self, scene, *args, **kwargs)
                # Auto-register with scene
                if serialize_key not in cls._instances:
                    cls._instances[serialize_key] = []
                cls._instances[serialize_key].append(scene)
                # Force scene to register serializers
                scene._register_auto_serializers()

            wrapped_class.__init__ = new_init
            cls._registry[serialize_key] = wrapped_class
            return wrapped_class
        return decorator

    @classmethod
    def get_registered(cls) -> Dict[str, Type]:
        return cls._registry

    @classmethod
    def get_instance(cls, key: str, scene: 'Scene') -> Optional[Any]:
        """Get instance for given key and scene"""
        if key in cls._instances:
            scenes = cls._instances[key]
            if scene in scenes:
                return next((obj for obj in scene.__dict__.values()
                             if isinstance(obj, cls._registry[key])), None)
        return None
