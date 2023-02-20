""" scrall_visitor.py - path-inst test """
from arpeggio import PTNodeVisitor
from collections import namedtuple

Supplied_Parameter_a = namedtuple('Supplied_Parameter_a', 'pname sval')
"""Parameter name and flow name pair for a set of supplied parameters"""
Call_a = namedtuple('Call_a', 'op_name supplied_params dest')
Attr_Access_a = namedtuple('Attr_Access_a', 'cname attr')
Attr_Comparison_a = namedtuple('Attr_Comparison_a', 'attr op scalar')
Selection_a = namedtuple('Selection_a', 'cname card criteria')

class ScrallVisitor(PTNodeVisitor):

    def visit_activity(self, node, children):
        return [c for c in children if c]

    def visit_statement(self, node, children):
        return children

    def visit_instance_set(self, node, children):
        return {'iset' : children}

    def visit_selection(self, node, children):
        return Selection_a(cname=children[0], card=children[1][0], criteria=None if len(children[1]) != 2 else children[1][1])

    def visit_select_phrase(self, node, children):
        char1 = children[0][0]
        explicit_card = char1 if char1 in ('1', '*') else None
        card = explicit_card if explicit_card else '*'
        if len(children) == 1 and explicit_card:
            return [card]
        else:
            return [card, children[-1]]

    def visit_criteria(self, node, children):
        return children

    def visit_attr_comparison(self, node, children):
        return Attr_Comparison_a(attr=children[0], op=children[1][0], scalar=children[1][1])

    def visit_comparison(self, node, children):
        return children

    def visit_call(self, node, children):
        return Call_a(op_name=children[1]['op_name'], supplied_params=children[1]['params'], dest=children[0])

    def visit_operation(self, node, children):
        """
        Children are name, ?supplied_params
        Returns op_name ?supplied_params dest
        """
        op_name = children[0]
        params = [] if len(children) == 1 else children[-1]
        return {'op_name': op_name, 'params': params}


    def visit_param(self, node, children):
        """
        <flow name> or <parameter name> <flow name> is parsed. If only a flow name is present, it means
        that the supplied flow has the same name Ex: ( shaft id ) as that of the required parameter. Short for
        ( shaft id : shaft id ). This is a convenience that elminates the need for name doubling in a supplied
        parameter set
        """
        s = children[-1] # Last value is always the flow name
        p = children[0] if len(children) > 1 else f # First value is the parameter name only if followed by a flow name
        return Supplied_Parameter_a(pname=p, sval=s)

    def visit_supplied_params(self, node, children):
        return children

    def visit_attr_access(self, node, children):
        return Attr_Access_a(cname=children[0], attr=children[1])


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
    #
    # def visit_NL(self, node, children):
    #     """ Discard comments and blank lines """
    #     return None


