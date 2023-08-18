""" model_visitor.py """

from arpeggio import PTNodeVisitor
from collections import namedtuple

Method_a = namedtuple('Method_a', 'class_name method flows_in flow_out activity')

class MethodVisitor(PTNodeVisitor):

    # Root
    @classmethod
    def visit_method(cls, node, children):
        """
        BLOCK_END class_prefix signature BLOCK_END activity EOF
        """
        class_name = children[0]
        method_name, flows_in, flow_out = children[1].values()
        activity = children[2]
        return Method_a(class_name, method_name, flows_in, flow_out, activity)

    @classmethod
    def visit_class_prefix(cls, node, children):
        """
        icaps_name '.'
        """
        return children[0]

    @classmethod
    def visit_signature(cls, node, children):
        """
        icaps_name input_parameters output_types?
        """
        name, iparams = children[:2]
        otype = None if len(children) < 3 else children[2]
        return {'method_name': name, 'flows_in': iparams, 'flow_out': otype}

    @classmethod
    def visit_input_parameters(cls, node, children):
        """
        parameters?
        """
        return [] if not children else children[0]

    @classmethod
    def visit_output_type(cls, node, children):
        """
        ' : ' icaps_all_name
        """
        return children[0]

    @classmethod
    def visit_parameters(cls, node, children):
        """
        parameter (', ' parameter)*
        """
        return children

    @classmethod
    def visit_parameter(cls, node, children):
        """
        name ':' name
        """
        return {'name': children[0], 'type': children[1]}

    @classmethod
    def visit_phrase(cls, node, children):
        """
        lword (DELIM lword)*
        """
        phrase = ''.join(children)
        return phrase

    @classmethod
    def visit_activity(cls, node, children):
        """
        body_line*
        """
        return  '\n'.join(children)+'\n'

    @classmethod
    def visit_body_line(cls, node, children):
        """
        r'.*' NL
        """
        body_text_line = "" if not children else children[0]
        return body_text_line

    # Text and delimiters

    @classmethod
    def visit_icaps_all_name(cls, node, children):
        """
        iword (DELIM iword)*
        """
        name = ''.join(children)
        return name

    @classmethod
    def visit_icaps_name(cls, node, children):
        """
        iword (DELIM word)*
        """
        name = ''.join(children)
        return name

    @classmethod
    def visit_NL(cls, node, children):
        """
        "\n"
        """
        return None

    @classmethod
    def visit_SP(cls, node, children):
        """
        " "  // Single space
        """
        return None
