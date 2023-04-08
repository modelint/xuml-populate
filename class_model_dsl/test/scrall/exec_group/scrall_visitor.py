""" scrall_visitor.py - exec_group test """
from arpeggio import PTNodeVisitor
from collections import namedtuple

Supplied_Parameter_a = namedtuple('Supplied_Parameter_a', 'pname sval')
"""Parameter name and flow name pair for a set of supplied parameters"""
Op_a = namedtuple('Op_a', 'op_name supplied_params')
Call_a = namedtuple('Call_a', 'iset ops')
Attr_Access_a = namedtuple('Attr_Access_a', 'cname attr')
Attr_Comparison_a = namedtuple('Attr_Comparison_a', 'attr op scalar_expr')
Selection_a = namedtuple('Selection_a', 'card criteria')
Inst_Assignment_a = namedtuple('Inst_Assignment_a', 'lhs card rhs')
Signal_a = namedtuple('Signal_a', 'event supplied_params dest')
"""Signal sent to trigger event at destination with optional supplied parameters"""
Signal_Action_a = namedtuple('Signal_Action_a', 'event supplied_params dest delay')
Block_a = namedtuple('Block_a', 'actions')
Sequence_Token_a = namedtuple('Sequence_Token_a', 'name')
Execution_Unit_a = namedtuple('Execution_Unit_a', 'input_tokens output_tokens action_group')
Decision_a = namedtuple('Decision_a', 'input true_result false_result')
Delete_Action_a = namedtuple('Delete_Action_a', 'instance_set')
Case_a = namedtuple('Case_a', 'enums execution_unit')
Scalar_Switch_a = namedtuple('Scalar_Switch_a', 'scalar_input_flow cases')
AND_a = namedtuple('AND_a', 'a b')
OR_a = namedtuple('OR_a', 'a b')
NOT_a = namedtuple('NOT_a', 'op a')
FACTOR_a = namedtuple('FACTOR_a', 'op a b')
ADD_a = namedtuple('ADD_a', 'op a b')
EQUALITY_a = namedtuple('EQUALITY_a', 'op a b')
EXPONENT_a = namedtuple('EXPONENT', 'op a b')
SCALAR_a = namedtuple('SCALAR_a', 's m')
Scalar_Assignment_a = namedtuple('Scalar_Assignment_a', 'lhs rhs')
"""op is 'not' if 'not' specified, otherwise noop"""

class ScrallVisitor(PTNodeVisitor):

    def visit_activity(self, node, children):
        return [c for c in children if c]

    def visit_execution_unit(self, node, children):
        itok = children.results.get('input_tokens')
        itok = None if not itok else itok[0]
        otok = children.results.get('output_tokens')
        otok = None if not otok else otok[0]
        ag = children.results.get('action_group')[0]
        return Execution_Unit_a(input_tokens=itok, output_tokens=otok, action_group=ag)

    def visit_scalar_switch(self, node, children):
        return Scalar_Switch_a(scalar_input_flow=children[0], cases=children[1:])

    def visit_case_block(self, node, children):
        return children

    def visit_case(self, node, children):
        return Case_a(enums=children.results['enum_value'], execution_unit=children.results['execution_unit'][0])

    def visit_enum_value(self, node, children):
        return children.results['name'][0]

    def visit_delete(self, node, children):
        iset = children.results.get('instance_set')
        return Delete_Action_a(instance_set=iset)

    def visit_block(self, node, children):
        return Block_a(actions=children)

    def visit_action(self, node, children):
        return children[0]

    def visit_decision(self, node, children):
        return Decision_a(input=children[0], true_result=children[1], false_result=None if len(children) < 3 else children[2])

    def visit_true_result(self, node, children):
        return children[0]

    def visit_false_result(self, node, children):
        return children[0]

    def visit_input_tokens(self, node, children):
        return children

    def visit_output_tokens(self, node, children):
        return children

    def visit_sequence_token(self, node, children):
        return Sequence_Token_a(name=children[0])

    def visit_token_name(self, node, children):
        return node.value

    def visit_signal_action(self, node, children):
        """
        Returns event_name ?supplied_params instance_set
        """
        s = children[0]
        delay = None if len(children) < 2 else children[1]['delay']
        return Signal_Action_a(event=s.event, supplied_params=s.supplied_params, dest=s.dest, delay=delay)

    def visit_signal(self, node, children):
        params = [] if len(children) == 2 else children[1]
        return Signal_a(event=children[0], supplied_params=params, dest=children[-1])

    def visit_delay(self, node, children):
        return {'delay': children[0]}


    def visit_inst_assignment(self, node, children):
        card = '1' if children[1] == '.=' else 'Mc'
        return Inst_Assignment_a(lhs=children[0], card=card, rhs=children[2])

    def visit_instance_set(self, node, children):
        return {'iset' : children}

    def visit_selection(self, node, children):
        # return Selection_a(card=children[0], criteria=None)
        return Selection_a(card=children[0][0], criteria=None if len(children[0]) < 2 else children[0][1])

    def visit_select_phrase(self, node, children):
        explicit_card = children.results.get('CARD')
        card = '*' if not explicit_card else explicit_card[0]
        criteria = children.results.get('criteria')
        if criteria:
            return [card, criteria[0]]
        else:
            return [card]

    def visit_criteria(self, node, children):
        return children

    def visit_attr_comparison(self, node, children):
        rhs_compare = children.results.get('comparison')
        op, scalar_expr = (':', 'true') if not rhs_compare else rhs_compare[0]
        return Attr_Comparison_a(attr=children.results['name'][0], op=op, scalar_expr=scalar_expr)

    def visit_logical_or(self, node, children):
        a = children[0]
        b = None if len(children) < 2 else children[1]
        return OR_a(a,b)

    def visit_logical_and(self, node, children):
        a = children[0]
        b = None if len(children) < 2 else children[1]
        return AND_a(a,b)

    def visit_logical_not(self, node, children):
        op = 'not' if len(children) > 1 else None
        a = children[0] if not op else children[1]
        return NOT_a(op,a)

    def visit_scalar_logical_not(self, node, children):
        op = 'not' if len(children) > 1 else None
        a = children[0] if not op else children[1]
        return NOT_a(op,a)

    def visit_scalar_logical_and(self, node, children):
        a = children[0]
        b = None if len(children) < 2 else children[1]
        return AND_a(a,b)

    def visit_scalar_logical_or(self, node, children):
        a = children[0]
        b = None if len(children) < 2 else children[1]
        return OR_a(a,b)

    def visit_comparison(self, node, children):
        return children

    def visit_call(self, node, children):
        return Call_a(iset=children[0], ops=children[1:])

    def visit_operation(self, node, children):
        """
        Children are name, ?supplied_params
        Returns op_name ?supplied_params dest
        """
        op_name = children[0]
        params = [] if len(children) == 1 else children[-1]
        return Op_a(op_name=op_name, supplied_params=params)

    def visit_param(self, node, children):
        """
        <flow name> or <parameter name> <flow name> is parsed. If only a flow name is present, it means
        that the supplied flow has the same name Ex: ( shaft id ) as that of the required parameter. Short for
        ( shaft id : shaft id ). This is a convenience that elminates the need for name doubling in a supplied
        parameter set
        """
        s = children[-1] # Last value is always the flow name
        p = children[0] if len(children) > 1 else s # First value is the parameter name only if followed by a flow name
        return Supplied_Parameter_a(pname=p, sval=s)

    def visit_supplied_params(self, node, children):
        return children

    def visit_scalar_assignment(self, node, children):
        return Scalar_Assignment_a(*children)

    def visit_scalar_expr(self, node, children):
        add_op = children.results.get('ADD')
        if not add_op:
            return children[0]
        else:
            a, b = children.results['term']
            e = ADD_a(add_op, a, b)
        return e

    def visit_factor(self, node, children):
        if len(children) == 1:
            return children[0]
        else:
            a, b = children.results['exponent']
            factor_op = children.results['MULT'][0]
            return FACTOR_a(factor_op, a, b)

    def visit_equality(self, node, children):
        if len(children) == 1:
            return children[0]
        else:
            a, b = children.results['exponent']
            exp_op = children.results['EQUAL'][0]
            return EQUALITY_a(exp_op, a, b)

    def visit_exponent(self, node, children):
        if len(children) == 1:
            return children[0]
        else:
            a, b = children.results['exponent']
            exp_op = children.results['EXP'][0]
            return EXPONENT_a(exp_op, a, b)

    def visit_term(self, node, children):
        """
        unary? ( scalar / scalar_exp )
        """
        if len(children) == 2:
            s, m = children
        else:
            s, m = None, children[0]
        return SCALAR_a( s, m )

    def visit_attr_access(self, node, children):
        return Attr_Access_a(cname=children[0], attr=children[1])

    def visit_path(self, node, children):
        return {'path': children}

    def visit_hop(self, node, children):
        return children[0]

    def visit_rnum(self, node, children):
        """ Join words and delimiters """
        return {'rnum': node.value}


    def visit_name(self, node, children):
        """ Join words and delimiters """
        return ''.join(children)

    def visit_LINEWRAP(self, node, children):
        """ Discard space character """
        return None

    def visit_EOL(self, node, children):
        """ Discard space character """
        return None

    def visit_SP(self, node, children):
        """ Discard space character """
        return None
