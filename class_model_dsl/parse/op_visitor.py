""" operation_visitor.py """

from arpeggio import PTNodeVisitor
from collections import namedtuple

Op_a = namedtuple('Op_a', 'op_type ee op flows_in flow_out activity')

class OpVisitor(PTNodeVisitor):

    # Root
    @classmethod
    def visit_operation(cls, node, children):
        """
        BLOCK_END ee_prefix signature BLOCK_END activity? EOF
        """
        a = children.results.get('activity')
        a = None if not a else a[0]
        return Op_a(
            op_type=children[0]['op_type'], ee=children[0]['ee'], op=children[1]['op_name'],
            flows_in=children[1]['flows_in'], flow_out=children[1]['flow_out'],
            activity=a
        )

    @classmethod
    def visit_ee_prefix(cls, node, children):
        """
        op_type icaps_name '.'
        """
        op_type = 'ingress' if children[0] == '<<' else 'egress'
        return { 'op_type': op_type, 'ee': children[1] }

    @classmethod
    def visit_signature(cls, node, children):
        """
        icaps_name input_parameters output_types?
        """
        name, iparams = children[:2]
        otypes = None if len(children) < 3 else children[2]
        return {'op_name': name, 'flows_in': iparams, 'flow_out': otypes}

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
