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
MATH_a = namedtuple('MATH_a', 'op operands')
UNARY_a = namedtuple('UNARY_a', 'op operand')
BOOL_a = namedtuple('BOOL_a', 'op operands')
Scalar_Assignment_a = namedtuple('Scalar_Assignment_a', 'lhs rhs')

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
        if len(children) == 1:
            return children[0]
        else:
            return BOOL_a('OR', children)

    def visit_logical_and(self, node, children):
        if len(children) == 1:
            return children[0]
        else:
            return BOOL_a('AND', children)

    def visit_logical_not(self, node, children):
        if len(children) == 1:
            return children[0]
        else:
            a = children[1]
            return BOOL_a('NOT', list(a))

    def visit_scalar_assignment(self, node, children):
        return Scalar_Assignment_a(*children)


    # Scalar expression

    def visit_scalar_expr(self, node, children):
        """
        scalar_logical_or
        """
        return children[0]

    def visit_scalar_logical_or(self, node, children):
        """
        scalar_logical_and (OR scalar_logical_and)*

        """
        if len(children) == 1: # No OR operation
            return children[0]
        else:
            return BOOL_a('OR', children)

    def visit_scalar_logical_and(self, node, children):
        """
        equality (AND equality)*

        """
        if len(children) == 1: # No AND operation
            return children[0]
        else:
            return BOOL_a('AND', children)

    def visit_comparison(self, node, children):
        if len(children) == 1:
            return children[0]
        else:
            a, b = children.results['addition']
            compare_op = children.results['COMPARE'][0]
            return BOOL_a(compare_op, a, b)

    def visit_addition(self, node, children):
        """
        factor (ADD factor)*

        Returns a previously parsed factor or added/subtracted factors
        """
        if len(children) == 1:
            return children[0]
        else:
            return MATH_a(children.results['ADD'], children.results['factor'])

    def visit_equality(self, node, children) -> BOOL_a:
        """
        Boolean comparison operation examples:
            a == b
            a != b
        """
        if len(children) == 1:
            return children[0]
        else:
            a, b = children.results['comparison']
            exp_op = children.results['EQUAL'][0]
            return BOOL_a(exp_op, a, b)

    def visit_factor(self, node, children):
        """
        term (MULT term)*

        Returns a previously parsed term or multipled/divided terms
        """
        if len(children) == 1:
            return children[0]
        else:
            return MATH_a(children.results['MULT'], children.results['term'])

    def visit_term(self, node, children):
        """
        NOT? UNARY_MINUS? (scalar / scalar_expr)
        ---
        If the not or unary minus operations are not specified, returns whatever was parsed out earlier,
        either a simple scalar (attribute, attribute access, etc) or any scalar expression

        Otherwise, a unary minus expression nested inside a boolean not operation, or just the boolean not,
        or just the unary minus expressions individually are returned.
        """
        s = children.results.get('scalar')
        s = s if s else children.results['scalar_expr']
        scalar = s[0]
        if len(children) == 1:
            return scalar
        not_op = children.results.get('NOT')
        unary_minus = children.results.get('UNARY_MINUS')
        if unary_minus and not not_op:
            return UNARY_a('-', scalar)
        if not_op and not unary_minus:
            return BOOL_a('NOT', scalar, None)
        if unary_minus and not_op:
            return BOOL_a('NOT', UNARY_a('-', scalar), None)


    # Synchronous method or operation

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
