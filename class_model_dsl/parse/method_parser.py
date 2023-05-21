""" method_parser.py """

from class_model_dsl.methodp_exceptions import MethodGrammarFileOpen, MethodParseError,\
    MethodInputFileEmpty, MethodInputFileOpen
from class_model_dsl.parse.method_visitor import MethodVisitor
from arpeggio import visit_parse_tree, NoMatch
from arpeggio.cleanpeg import ParserPEG
import os # For issuing system commands to generate diagnostic files
from pathlib import Path

class MethodParser:
    """
    Parses a method file
    """
    method_grammar = None # We haven't read it in yet
    method_text = None # User will provide this

    root_rule_name = 'method' # The required name of the highest level parse element

    # Useful paths within the project
    project_path = Path(__file__).parent.parent.parent
    module_path = project_path / 'class_model_dsl'
    grammar_path = module_path / 'grammar' # The grammar files are all here
    diagnostics_path = module_path / 'diagnostics' # All parser diagnostic output goes here

    # Files
    grammar_file = grammar_path / f"{root_rule_name}.peg" # We parse using this peg grammar
    grammar_model_pdf = diagnostics_path / f"{root_rule_name}_model.pdf"
    parse_tree_pdf = diagnostics_path / f"{root_rule_name}_parse_tree.pdf"
    parse_tree_dot = project_path / f"{root_rule_name}_parse_tree.dot"
    parser_model_dot = project_path / f"{root_rule_name}_peg_parser_model.dot"

    pg_tree_dot = project_path / "peggrammar_parse_tree.dot"
    pg_model_dot = project_path / "peggrammar_parser_model.dot"
    pg_tree_pdf = diagnostics_path / "peggrammar_parse_tree.pdf"
    pg_model_pdf = diagnostics_path / "peggrammar_parser_model.pdf"

    @classmethod
    def parse(cls, method_path:Path, debug=False):
        """
        Parse a Method

        :param method_path: Path to the method file
        :param debug: Debug mode prints out diagnostic .dots and pdfs of the grammar and parse
        :return: Method signature with activity as unparsed text to be handed off to the scrall parser
        """
        # Read the grammar file
        try:
            cls.method_grammar = open(cls.grammar_file, 'r').read()
        except OSError as e:
            raise MethodGrammarFileOpen(cls.grammar_file)

        # Read the method file
        try:
            cls.method_text = open(method_path, 'r').read()
        except OSError as e:
            raise MethodInputFileOpen(method_path)

        if not cls.method_text:
            raise MethodInputFileEmpty(method_path)



        # Create an arpeggio parser for our model grammar that does not eliminate whitespace
        # We interpret newlines and indents in our grammar, so whitespace must be preserved
        parser = ParserPEG(cls.method_grammar, cls.root_rule_name, ignore_case=True, skipws=False, debug=debug)
        if debug:
            # Transform dot files into pdfs
            # os.system(f'dot -Tpdf {cls.pg_tree_dot} -o {cls.pg_tree_pdf}')
            # os.system(f'dot -Tpdf {cls.pg_model_dot} -o {cls.pg_model_pdf}')
            os.system(f'dot -Tpdf {cls.parser_model_dot} -o {cls.grammar_model_pdf}')
            cls.parser_model_dot.unlink(True)
            cls.pg_tree_dot.unlink(True)
            cls.pg_model_dot.unlink(True)

        # Now create an abstract syntax tree from our Scrall activity text
        try:
            parse_tree = parser.parse(cls.method_text)
        except NoMatch as e:
            raise MethodParseError(e) from None

        # Transform that into a result that is better organized with grammar artifacts filtered out
        result = visit_parse_tree(parse_tree, MethodVisitor(debug=debug))

        if debug:
            # Transform dot files into pdfs
            os.system(f'dot -Tpdf {cls.parse_tree_dot} -o {cls.parse_tree_pdf}')
            # Delete dot files since we are only interested in the generated PDFs
            # Comment this part out if you want to retain the dot files
            cls.parse_tree_dot.unlink(True)

        return result