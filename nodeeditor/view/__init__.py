"""
View Layer - Graphics wrappers and coordination for MVC architecture.

This package contains wrapper classes and coordinators that bridge the
Model/Controller layers with the Graphics layer (Qt graphics items).

Components:
    QDMGraphicsNodeModel: Wrapper for NodeModel with graphics synchronization
    QDMGraphicsEdgeModel: Wrapper for EdgeModel with graphics synchronization
    QDMGraphicsSocketModel: Wrapper for SocketModel with graphics synchronization
    QDMGraphicsSceneModel: Coordinator for scene-level synchronization

Architecture:
    The view layer wraps existing graphics items (QDMGraphicsNode, QDMGraphicsEdge,
    QDMGraphicsSocket) and adds synchronization with the model/controller layers
    through Qt signals and slots.

Example:
    >>> from nodeeditor.models import NodeModel, SceneModel
    >>> from nodeeditor.controllers import SceneController
    >>> from nodeeditor.view import QDMGraphicsSceneModel
    >>> 
    >>> scene_model = SceneModel()
    >>> scene_controller = SceneController(scene_model)
    >>> coordinator = QDMGraphicsSceneModel(scene_model, graphics_scene, scene_controller)
    >>> 
    >>> # Creating a node through the controller updates both model and graphics
    >>> node = scene_controller.create_node("my_node", "Display", (100, 200))
"""

from .graphics_node_model import QDMGraphicsNodeModel
from .graphics_edge_model import QDMGraphicsEdgeModel
from .graphics_socket_model import QDMGraphicsSocketModel
from .graphics_scene_model import QDMGraphicsSceneModel

__all__ = [
    "QDMGraphicsNodeModel",
    "QDMGraphicsEdgeModel",
    "QDMGraphicsSocketModel",
    "QDMGraphicsSceneModel",
]

__version__ = "1.0.0"
__author__ = "NodeEditor Contributors"
