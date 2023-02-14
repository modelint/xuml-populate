""" scrall_visitor.py """
from arpeggio import PTNodeVisitor
from collections import namedtuple

Signal_a = namedtuple('Signal_a', 'event_name signature path')
Parameter_a = namedtuple('Parameter_a', 'name type')

class ScrallVisitor(PTNodeVisitor):

    def visit_activity(self, node, children):
        return [c for c in children if c]


    def visit_statement(self, node, children):
        return children


    def visit_signal_action(self, node, children):
        """
        Returns event_name ?signature path
        """
        sig = [] if len(children) == 2 else children[1]
        return Signal_a(event_name=children[0], signature=sig, path=children[-1]['path'])

    def visit_param(self, node, children):
        return Parameter_a(name=children[0], type=children[1])

    def visit_signature(self, node, children):
        return children

    def visit_type_qual(self, node, children):
        return children[0]

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

    def visit_nl(self, node, children):
        """ Discard comments and blank lines """
        return None


