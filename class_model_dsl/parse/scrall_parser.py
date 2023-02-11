""" scrall_parser.py """

# from class_model_dsl.mp_exceptions import
from class_model_dsl.parse.scrall_visitor import ScrallVisitor
from arpeggio import visit_parse_tree, NoMatch
from arpeggio.cleanpeg import ParserPEG
from collections import namedtuple
import os
from pathlib import Path

# This is each line of the parse / visitor output
Statement = namedtuple('Statement', 'text parse') # Not sure if this is needed

class ScrallParser:
    """
    Parses the text of an Activity written in Scrall

        Attributes

        - debug -- debug flag (used to set arpeggio parser mode)
        - grammar_file -- (class based) Name of the system file defining the Scrall grammar
        - scrall_text -- Unparsed scrall text input for a single metamodel activity (state, method, operation)
    """
    root_rule_name = 'activity' # The required name of the highest level parse element

    # Useful paths within the project
    project = Path(__file__).parent.parent  # Top level directory of this project
    grammar_path = project / "grammar" # The grammar files are all here
    diagnostics_path = project / "diagnostics" # All parser diagnostic output goes here

    # Files
    grammar_file = project / "scrall.peg" # We parse using this peg grammar
    grammar_model_pdf = diagnostics_path / "scrall_model.pdf"
    parse_tree_pdf = diagnostics_path / "scrall_parse_tree.pdf"
    parse_tree_dot = diagnostics_path / f"{root_rule_name}_parse_tree.dot"
    parser_model_dot = diagnostics_path / f"{root_rule_name}_peg_parser_model.dot"

    def __init__(self, scrall_text: str, debug=True):
        """
        Constructor

        :param debug: class attribute
        """
        self.debug = debug

        # Read the grammar file
        self.scrall_grammar = open(ScrallParser.grammar_file, 'r').read()

        self.scrall_text = scrall_text


    def parse(self) -> List[Statement]:
        """
        Parse the layout file and return the content
        :return: The abstract syntax tree content of interest
        """
        # Create an arpeggio parser for our model grammar that does not eliminate whitespace
        # We interpret newlines and indents in our grammar, so whitespace must be preserved
        parser = ParserPEG(self.scrall_grammar, ScrallParser.root_rule_name, skipws=False, debug=self.debug)
        # Now create an abstract syntax tree from our layout text
        try:
            parse_tree = parser.parse(self.scrall_text)
        except NoMatch as e:
            raise ScrallParseError(e)

        # Transform that into a result that is better organized with grammar artifacts filtered out
        result = visit_parse_tree(parse_tree, ScrallVisitor(debug=self.debug))
        if self.debug:
            # Transform dot files into pdfs

            peg_tree_dot = "peggrammar_parse_tree.dot"
            peg_model_dot = "peggrammar_parser_model.dot"
            os.system(f'dot -Tpdf {ScrallParser.parse_tree_dot} -o {ScrallParser.parse_tree_pdf}')
            os.system(f'dot -Tpdf {ScrallParser.parser_model_dot} -o {ScrallParser.grammar_model_pdf}')
            # Cleanup unneeded dot files, we just use the PDFs for now
            Path(ScrallParser.parse_tree_dot).unlink(True)
            Path(ScrallParser.parse_tree_dot).unlink(True)
            Path(ScrallParser.parser_model_dot).unlink(True)
            Path(peg_tree_dot).unlink(True)
            Path(peg_model_dot).unlink(True)
        return result


if __name__ == "__main__":
    # For diagnostics
    scrall_path = Path(__file__).parent.parent / "Examples" / 'e1.scrall'
    x = ScrallParser(scrall_file_path=scrall_path, debug=True)
    try:
        x.parse()
    except ScrallParseError as e:
        print(e)
