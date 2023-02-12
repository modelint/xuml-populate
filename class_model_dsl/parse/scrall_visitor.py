""" scrall_visitor.py """
from arpeggio import PTNodeVisitor

class ScrallVisitor(PTNodeVisitor):

    def visit_activity(self, node, children):
        return children

    def visit_statement(self, node, children):
        return children

    def visit_name(self, node, children):
        """ Join words and delimiters """
        return ''.join(children)

    def visit_nl(self, node, children):
        """ Discard comments and blank lines """
        return None


