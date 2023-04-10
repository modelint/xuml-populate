""" scrall_visitor.py - exec_group test """
from arpeggio import PTNodeVisitor
from collections import namedtuple
from class_model_dsl.sp_exceptions import ScrallCallWithoutOperation
import logging

_logger = logging.getLogger(__name__)

Supplied_Parameter_a = namedtuple('Supplied_Parameter_a', 'pname sval')
"""Parameter name and flow name pair for a set of supplied parameters"""
Op_a = namedtuple('Op_a', 'op_name supplied_params')
Call_a = namedtuple('Call_a', 'subject ops')
"""The subject of a call could be an instance set (method) or an external entity (ee operation)"""
Attr_Access_a = namedtuple('Attr_Access_a', 'cname attr')
Attr_Comparison_a = namedtuple('Attr_Comparison_a', 'attr op scalar_expr')
Comparison_phrase_a = namedtuple('Comparison_phrase_a', 'op scalar_expr')
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


    @classmethod
    def visit_inst_assignment(cls, node, children):
        """
        name INST_ASSIGN instance_set
        """
        return Inst_Assignment_a(
            lhs=children.results['name'][0],
            card='1' if children.results['INST_ASSIGN'] == '.=' else 'Mc',
            rhs=children.results['instance_set']
        )

    @classmethod
    def visit_instance_set(cls, node, children):
        """
        (name / path) (selection / operation / path)*

        An instance set begins with a required name (instance flow) or a path. The path can then be followed
        by any sequence of selection, operation, and paths. The parser won't find two paths in sequence since
        any encounter path will be fully consumed
        """
        return {'iset' : children}

    @classmethod
    def visit_selection(cls, node, children):
        """
        '(' select_phrase ')'
        """
        return Selection_a(card=children[0][0], criteria=None if len(children[0]) < 2 else children[0][1])

    @classmethod
    def visit_select_phrase(cls, node, children):
        """
        (CARD ',' criteria) / CARD / criteria

        """
        explicit_card = children.results.get('CARD')
        card = '*' if not explicit_card else explicit_card[0]
        criteria = children.results.get('scalar_expr')
        if criteria:
            return [card, criteria[0]]
        else:
            return [card]

    # @classmethod
    # def visit_criteria(cls, node, children):
    #     """
    #     logical_or
    #     """
    #     return children
    #
    # @classmethod
    # def visit_attr_comparison(cls, node, children):
    #     """
    #     RANK? REFLEX? name comparison?
    #
    #     name is an attribute name to be compared
    #     """
    #     rhs_compare = children.results.get('comparison_phrase')
    #     op, scalar_expr = (':', 'true') if not rhs_compare else rhs_compare[0]
    #     return Attr_Comparison_a(attr=children.results['name'][0], op=op, scalar_expr=scalar_expr)

    # @classmethod
    # def visit_comparison_phrase(cls, node, children):
    #     return Comparison_phrase_a(*children)

    # @classmethod
    # def visit_logical_or(cls, node, children):
    #     if len(children) == 1:
    #         return children[0]
    #     else:
    #         return BOOL_a('OR', children.results['logical_and'])
    #
    # @classmethod
    # def visit_logical_and(cls, node, children):
    #     if len(children) == 1:
    #         return children[0]
    #     else:
    #         return BOOL_a('AND', children.results['logical_not'])
    #
    # @classmethod
    # def visit_logical_not(cls, node, children):
    #     if len(children) == 1:
    #         return children[0]
    #     else:
    #         a = children[1]
    #         return BOOL_a('NOT', list(a))

    # Scalar assignment and operations
    @classmethod
    def visit_scalar_assignment(cls, node, children):
        """
        name SCALAR_ASSIGN scalar_expr
        """
        return Scalar_Assignment_a(*children)

    @classmethod
    def visit_scalar_expr(cls, node, children):
        """
        Returns a fully parsed scalar expression
        """
        return children[0]

    @classmethod
    def visit_scalar_logical_or(cls, node, children):
        """
        scalar_logical_and (OR scalar_logical_and)*

        Returns a higher precedence operation or one or more OR'ed conjunctions
        """
        if len(children) == 1: # No OR operation
            return children[0]
        else:
            return BOOL_a('OR', children.results['scalar_logical_and'])

    @classmethod
    def visit_scalar_logical_and(cls, node, children):
        """
        equality (AND equality)*

        Returns a higher precedence operation or one or more AND'ed equalities
        """
        if len(children) == 1: # No AND operation
            return children[0]
        else:
            return BOOL_a('AND', children.results['equality'])

    @classmethod
    def visit_comparison(cls, node, children):
        """
        comparison = addition (COMPARE addition)*

        Returns a higher precedence operation or one or more compared additions (>, <=, etc)
        """
        if len(children) == 1:
            return children[0]
        else:
            return BOOL_a(children.results['COMPARE'], children.results['addition'])

    @classmethod
    def visit_addition(cls, node, children):
        """
        factor (ADD factor)*

        Returns a higher precedence operation or one or more added/subtracted factors
        """
        if len(children) == 1:
            return children[0]
        else:
            return MATH_a(children.results['ADD'], children.results['factor'])

    @classmethod
    def visit_equality(cls, node, children) -> BOOL_a:
        """
        comparison (EQUAL comparison)*

        Returns a higher precedence operation or one or more equalities (==, !=)
        """
        if len(children) == 1:
            return children[0]
        else:
            return BOOL_a(children.results['EQUAL'], children.results['comparison'])

    @classmethod
    def visit_factor(cls, node, children):
        """
        term (MULT term)*

        Returns a higher precedence operation or one or more multipled/divided terms
        """
        if len(children) == 1:
            return children[0]
        else:
            return MATH_a(children.results['MULT'], children.results['term'])

    @classmethod
    def visit_term(cls, node, children):
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
            return BOOL_a('NOT', scalar)
        if unary_minus and not_op:
            return BOOL_a('NOT', UNARY_a('-', scalar))


    # Synchronous method or operation

    @classmethod
    def visit_call(cls, node, children):
        """
        instance_set
        Post-parse verify that last element is an operation, otherwise invalid call
        """
        if not isinstance(children[-1], Op_a):
            # There's no terminating operation in the action, so this isn't a complete call
            _logger.error(f"Call action without operation: [{children.results}]")
            raise ScrallCallWithoutOperation(children.results)
        return Call_a(subject=children[0], ops=children[1:])

    @classmethod
    def visit_operation(cls, node, children):
        """
        Children are name, ?supplied_params
        Returns op_name ?supplied_params dest
        """
        op_name = children[0]
        params = [] if len(children) == 1 else children[-1]
        return Op_a(op_name=op_name, supplied_params=params)

    @classmethod
    def visit_param(cls, node, children):
        """
        <flow name> or <parameter name> <flow name> is parsed. If only a flow name is present, it means
        that the supplied flow has the same name Ex: ( shaft id ) as that of the required parameter. Short for
        ( shaft id : shaft id ). This is a convenience that elminates the need for name doubling in a supplied
        parameter set
        """
        s = children[-1] # Last value is always the flow name
        p = children[0] if len(children) > 1 else s # First value is the parameter name only if followed by a flow name
        return Supplied_Parameter_a(pname=p, sval=s)

    @classmethod
    def visit_supplied_params(cls, node, children):
        return children


    def visit_attr_access(self, node, children):
        return Attr_Access_a(cname=children[0], attr=children[1])

    # Relationship traversal (paths)
    @classmethod
    def visit_path(cls, node, children):
        """ hop+  A sequence of hops """
        return {'path': children}

    @classmethod
    def visit_hop(cls, node, children):
        """ '/' (rnum / name)  An rnum, phrase, or class name """
        return children[0]

    # Names
    @classmethod
    def visit_rnum(cls, node, children):
        """
        r'O?R[1-9][0-9]*'
        Relationship number such as R23

        This is how relationships are named
        """
        return {'rnum': node.value}

    @classmethod
    def visit_name(cls, node, children):
        """ Join words and delimiters """
        return ''.join(children)

    # Discarded whitespace and comments
    @classmethod
    def visit_LINEWRAP(cls, node, children):
        """
        EOL SP*
        end of line followed by optional indent on next line
        """
        return None

    @classmethod
    def visit_EOL(cls, node, children):
        """
        SP* COMMENT? '\n'

        end of line: Spaces, Comments, blank lines, whitespace we can omit from the parser result
        """
        return None

    @classmethod
    def visit_SP(cls, node, children):
        """ ' '  Single space character (SP) """
        return None