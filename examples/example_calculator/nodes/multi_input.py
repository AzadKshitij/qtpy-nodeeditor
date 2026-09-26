from examples.example_calculator.calc_conf import register_node, OP_NODE_SUM
from examples.example_calculator.calc_node_base import CalcNode
from nodeeditor.node_multi_input_node import MultiInputNode


@register_node(OP_NODE_SUM)
class CalcNode_Sum(MultiInputNode, CalcNode):
    """Ordered multi-input demo node: sums every connected input in read order.

    Connect any number of ``Input`` (or operation) nodes to the single ``in``
    socket. The node reads them in order of connection; reorder from code::

        node.setEdgeOrder([...])
        node.moveEdgeTo(edge, 0)
        node.swapEdges(edge_a, edge_b)

    or with :meth:`Edge.input_index <nodeeditor.node_edge.Edge.input_index>`
    at connection time::

        Edge(scene, out_socket, node.inputs[0], input_index=0)
    """
    icon = "icons/add.png"
    op_code = OP_NODE_SUM
    op_title = "Sum"
    content_label = "Σ"
    content_label_objname = "calc_node_bg"

    def __init__(self, scene):
        super().__init__(scene, inputs=[2], outputs=[1],
                         input_text=["in"], output_text=["Σ"])
        self.eval()

    @staticmethod
    def _unwrap(value):
        """Reduce CalcNode-style nested ``[[v]]`` / ``[v]`` wrappers to a scalar."""
        seen = 0
        while isinstance(value, list) and len(value) == 1 and seen < 8:
            value = value[0]
            seen += 1
        if isinstance(value, dict):
            value = value.get('value', None)
        return value

    def evalImplementation(self):
        raw_values = self.getOrderedValues()

        numbers = []
        for value in raw_values:
            value = self._unwrap(value)
            if value is None:
                continue
            if isinstance(value, bool):
                numbers.append(int(value))
            elif isinstance(value, (int, float)):
                numbers.append(value)
            else:
                try:
                    numbers.append(float(value))
                except (TypeError, ValueError):
                    continue

        if not numbers:
            self.markInvalid()
            self.markDescendantsDirty()
            self.grNode.setToolTip("Connect at least one numeric input")
            return [None]

        total = sum(numbers)
        self.values = [[total]]
        self.markDirty(False)
        self.markInvalid(False)
        self.markDescendantsDirty()
        try:
            self.grNode.setToolTip(self.describeInputOrder() + "\n= %s" % (total,))
        except Exception:
            pass
        self.evalChildren()
        return self.values
