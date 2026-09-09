
from nodeeditor.node_decorators import MakeSerializable
from typing import List, Dict, Optional
from nodeeditor.node_node import Node
from nodeeditor.node_scene import Scene
from nodeeditor.node_serializable import Serializable


@MakeSerializable.register(key="groups")
class Group(Serializable):
    """Basic group implementation for calculator nodes"""

    def __init__(self, scene: Scene):
        self.scene = scene
        self.groups: Dict[str, List[Node]] = {}
        self.current_group: Optional[str] = None

    def create_group(self, name: str, nodes: List[Node]) -> None:
        """Create a new group with given nodes"""
        print('----------- Creating Groups-----------')
        print(
            f"Creating group '{name}' with nodes {[node.id for node in nodes]}")
        if name not in self.groups:
            self.groups[name] = nodes
            self.current_group = name
        print('--------------------------------------')

    def serialize(self) -> dict:
        """Serialize groups to dict"""
        print('----------- Serializing Groups -----------')
        print(f"Serializing groups: {self.groups}")
        print('-----------------------------------------')
        return {
            name: [node.id for node in nodes]
            for name, nodes in self.groups.items()
        }

    def deserialize(self, data: dict) -> None:
        """Deserialize groups from dict"""

        print('----------- Deserializing Groups -----------')
        print(f"Deserializing groups from data: {data}")
        print('-------------------------------------------')

        self.groups.clear()
        for name, node_ids in data.items():
            nodes = []
            for node_id in node_ids:
                node = self.scene.getNodeByID(node_id)
                if node:
                    nodes.append(node)
            if nodes:
                self.groups[name] = nodes


# Example usage in calculator_window.py:
"""
def __init__(self):
    super().__init__()

    # Create scene
    self.scene = Scene()
    # Initialize groups
    self.groups = Group(self.scene)

    # After creating some nodes:
    nodes = [node1, node2]  # Some calculator nodes
    self.groups.create_group("Math Group", nodes)
"""
