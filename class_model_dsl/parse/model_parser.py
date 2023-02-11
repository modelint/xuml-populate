""" model_parser.py – First attempt to parse class block """

from class_model_dsl.mp_exceptions import ModelGrammarFileOpen, ModelInputFileOpen, ModelInputFileEmpty, ModelParseError
from class_model_dsl.parse.model_visitor import SubsystemVisitor
from arpeggio import visit_parse_tree, NoMatch
from arpeggio.cleanpeg import ParserPEG
from class_model_dsl.parse.nocomment import nocomment
from collections import namedtuple
import os
from pathlib import Path

# This is the parse / visitor output
Subsystem = namedtuple('Subsystem', 'subsystem domain classes rels metadata')

class ModelParser:
    """
    Parses an Executable UML subsystem model input file using the arpeggio parser generator

        Attributes

        - grammar_file -- (class based) Name of the system file defining the Executable UML grammar
        - root_rule_name -- (class based) Name of the top level grammar element found in grammar file
        - debug -- debug flag (used to set arpeggio parser mode)
        - model_grammar -- The model grammar text read from the system grammar file
        - model_text -- The input model text read from the user supplied text file
    """
    root_rule_name = 'subsystem' # The required name of the highest level parse element

    grammar_file_name = "grammar/class_model.peg"
    grammar_file = Path(__file__).parent.parent / grammar_file_name
    xuml_model_dir = Path(__file__).parent.parent / "input"

    def __init__(self, model_file_path, debug=True):
        """
        Constructor

        :param model_file_path:  Where to find the user supplied model input file
        :param debug:  class attribute
        """
        self.debug = debug
        self.model_file_path = model_file_path

        # Read the grammar file
        try:
            self.model_grammar = nocomment(open(ModelParser.grammar_file, 'r').read())
        except OSError as e:
            raise ModelGrammarFileOpen(ModelParser.grammar_file)

        # Read the model file
        try:
            self.model_text = nocomment(open(self.model_file_path, 'r').read())
        except OSError as e:
            raise ModelInputFileOpen(self.model_file_path)

        if not self.model_text:
            raise ModelInputFileEmpty(self.model_file_path)

    def parse(self) -> Subsystem:
        """
        Parse the model file and return the content
        :return:  The abstract syntax tree content of interest
        """
        # Create an arpeggio parser for our model grammar that does not eliminate whitespace
        # We interpret newlines and indents in our grammar, so whitespace must be preserved
        parser = ParserPEG(self.model_grammar, ModelParser.root_rule_name, skipws=False, debug=self.debug)
        # Now create an abstract syntax tree from our model text
        try:
            parse_tree = parser.parse(self.model_text)
        except NoMatch as e:
            raise ModelParseError(self.model_file_path.name, e) from None
        # Transform that into a result that is better organized with grammar artifacts filtered out
        result = visit_parse_tree(parse_tree, SubsystemVisitor(debug=self.debug))
        # Make it even nicer using easy to reference named tuples
        if self.debug:
            # Transform dot files into pdfs
            peg_tree_dot = Path("peggrammar_parse_tree.dot")
            peg_model_dot = Path("peggrammar_parser_model.dot")
            parse_tree_dot = Path("subsystem_parse_tree.dot")
            parser_model_dot = Path("subsystem_peg_parser_model.dot")

            parse_tree_file = str(ModelParser.xuml_model_dir / self.model_file_path.stem) + "_parse_tree.pdf"
            model_file = str(ModelParser.xuml_model_dir / self.model_file_path.stem) + "_model.pdf"
            os.system(f'dot -Tpdf {parse_tree_dot} -o {parse_tree_file}')
            os.system(f'dot -Tpdf {parser_model_dot} -o {model_file}')
            # Cleanup unneeded dot files, we just use the PDFs for now
            # parse_tree_dot.unlink(missing_ok=True)
            # parser_model_dot.unlink(missing_ok=True)
            # peg_tree_dot.unlink(missing_ok=True)
            # peg_model_dot.unlink(missing_ok=True)
        # Return the refined model data, checking sequence length
        metadata = result.results.get('metadata', None)  # Optional section
        subsys_name = result.results['subsystem_header'][0]  # Required by model parser
        domain_name = result.results['domain_header'][0]  # Required by model parser
        class_data = result.results['class_set'][0]  # Required by model parser
        rel_data = result.results.get('rel_section', None)  # Optional section
        return Subsystem(
            subsystem=subsys_name, domain=domain_name, classes=class_data, rels=[] if not rel_data else rel_data[0],
            metadata=None if not metadata else metadata[0]
        )

