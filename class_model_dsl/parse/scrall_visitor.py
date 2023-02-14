""" scrall_visitor.py """
from arpeggio import PTNodeVisitor
from collections import namedtuple

Signal_a = namedtuple('Signal_a', 'event supplied_params dest')
"""Signal sent to trigger event at destination with optional supplied parameters"""
Supplied_Parameter_a = namedtuple('Supplied_Parameter_a', 'pname fname')
"""Parameter name and flow name pair for a set of supplied parameters"""
Sync_Call_a = namedtuple('Sync_Call_a', 'op_name supplied_params dest')

class ScrallVisitor(PTNodeVisitor):

    def visit_activity(self, node, children):
        return [c for c in children if c]


    def visit_statement(self, node, children):
        return children


    def visit_sync_call(self, node, children):
        """
        Children are dest, op_name, ?supplied_params
        Returns op_name ?supplied_params dest
        """
        params = [] if len(children) == 2 else children[-1]
        return Sync_Call_a(op_name=children[0], supplied_params=params, dest=children[0])

    def visit_signal_action(self, node, children):
        """
        Returns event_name ?supplied_params instance_set
        """
        params = [] if len(children) == 2 else children[1]
        return Signal_a(event=children[0], supplied_params=params, dest=children[-1]['path'])

    def visit_param(self, node, children):
        """
        <flow name> or <parameter name> <flow name> is parsed. If only a flow name is present, it means
        that the supplied flow has the same name Ex: ( shaft id ) as that of the required parameter. Short for
        ( shaft id : shaft id ). This is a convenience that elminates the need for name doubling in a supplied
        parameter set
        """
        f = children[-1] # Last value is always the flow name
        p = children[0] if len(children) > 1 else f # First value is the parameter name only if followed by a flow name
        return Supplied_Parameter_a(pname=p, fname=f)

    def visit_supplied_params(self, node, children):
        return children

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

    def visit_NL(self, node, children):
        """ Discard comments and blank lines """
        return None


