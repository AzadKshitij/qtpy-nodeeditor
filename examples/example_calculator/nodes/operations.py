from examples.example_calculator.calc_conf import register_node, OP_NODE_ADD, OP_NODE_SUB, OP_NODE_MUL, OP_NODE_DIV
from examples.example_calculator.calc_node_base import CalcNode


@register_node(OP_NODE_ADD)
class CalcNode_Add(CalcNode):
    icon = "icons/add.png"
    op_code = OP_NODE_ADD
    op_title = "Add"
    content_label = "+"
    content_label_objname = "calc_node_bg"

    def evalOperation(self, input1, input2):
        return input1 + input2


@register_node(OP_NODE_SUB)
class CalcNode_Sub(CalcNode):
    icon = "icons/sub.png"
    op_code = OP_NODE_SUB
    op_title = "Substract"
    content_label = "-"
    content_label_objname = "calc_node_bg"

    def evalOperation(self, input1, input2):
        return input1 - input2


@register_node(OP_NODE_MUL)
class CalcNode_Mul(CalcNode):
    icon = "icons/mul.png"
    op_code = OP_NODE_MUL
    op_title = "Multiply"
    content_label = "*"
    content_label_objname = "calc_node_mul"

    def evalOperation(self, input1, input2):
        print('foo')
        return input1 * input2


@register_node(OP_NODE_DIV)
class CalcNode_Div(CalcNode):
    icon = "icons/divide.png"
    op_code = OP_NODE_DIV
    op_title = "Divide and Mod"
    content_label = "/"
    content_label_objname = "calc_node_div"

    def __init__(self, scene):
        # Two inputs, two outputs (quotient and remainder)
        super().__init__(scene, inputs=[2, 2], outputs=[1, 1],
                         input_text=["a", "b"], output_text=["q", "r"])

    def evalOperation(self, input1, input2):
        if input1 is None or input2 is None:
            return [
                {'value': None, 'type': 'quotient'},
                {'value': None, 'type': 'remainder'}
            ]

        if input2 == 0:
            raise ValueError("Division by zero!")

        return [
            {'value': input1 // input2, 'type': 'quotient'},
            {'value': input1 % input2, 'type': 'remainder'}
        ]

    # def evalOperation(self, input1, input2):
    #     return input1 / input2

# way how to register by function call
# register_node_now(OP_NODE_ADD, CalcNode_Add)
