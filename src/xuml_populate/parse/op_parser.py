""" op_parser.py """

from class_model_dsl.op_exceptions import OpGrammarFileOpen, OpParseError,\
    OpInputFileEmpty, OpInputFileOpen
from class_model_dsl.parse.op_visitor import OpVisitor
from arpeggio import visit_parse_tree, NoMatch
from arpeggio.cleanpeg import ParserPEG
import os # For issuing system commands to generate diagnostic files
from pathlib import Path

class OpParser:
    """
    Parses an operation file
    """
    op_grammar = None # We haven't read it in yet
    op_text = None # User will provide this

    root_rule_name = 'operation' # The required name of the highest level parse element

    # Useful paths within the project
    project_path = Path(__file__).parent.parent.parent
    module_path = project_path / 'xuml_populate'
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
    def parse(cls, op_path:Path, debug=False):
        """
        Parse an Operation

        :param op_path: Path to the op file
        :param debug: Debug mode prints out diagnostic .dots and pdfs of the grammar and parse
        :return: Operation signature with activity as unparsed text to be handed off to the scrall parser
        """
        # Read the grammar file
        try:
            cls.op_grammar = open(cls.grammar_file, 'r').read()
        except OSError as e:
            raise OpGrammarFileOpen(cls.grammar_file)

        # Read the method file
        try:
            cls.op_text = open(op_path, 'r').read() + '\n' # Ensure there is at least one newline at the end
        except OSError as e:
            raise OpInputFileOpen(op_path)

        if not cls.op_text:
            raise OpInputFileEmpty(op_path)



        # Create an arpeggio parser for our model grammar that does not eliminate whitespace
        # We interpret newlines and indents in our grammar, so whitespace must be preserved
        parser = ParserPEG(cls.op_grammar, cls.root_rule_name, ignore_case=True, skipws=False, debug=debug)
        if debug:
            # Transform dot files into pdfs
            # os.system(f'dot -Tpdf {cls.pg_tree_dot} -o {cls.pg_tree_pdf}')
            # os.system(f'dot -Tpdf {cls.pg_model_dot} -o {cls.pg_model_pdf}')
            os.system(f'dot -Tpdf {cls.parser_model_dot} -o {cls.grammar_model_pdf}')
            cls.parser_model_dot.unlink(True)
            cls.pg_tree_dot.unlink(True)
            cls.pg_model_dot.unlink(True)

        # Now create an abstract syntax tree from our Operation text
        try:
            parse_tree = parser.parse(cls.op_text)
        except NoMatch as e:
            raise OpParseError(e) from None

        # Transform that into a result that is better organized with grammar artifacts filtered out
        result = visit_parse_tree(parse_tree, OpVisitor(debug=debug))

        if debug:
            # Transform dot files into pdfs
            os.system(f'dot -Tpdf {cls.parse_tree_dot} -o {cls.parse_tree_pdf}')
            # Delete dot files since we are only interested in the generated PDFs
            # Comment this part out if you want to retain the dot files
            cls.parse_tree_dot.unlink(True)

        return result