""" test_parse.py -- Test successful parsing of *.op files """

import pytest
from pathlib import Path
from op2_parser.op_parser import OpParser

operations = [
    "arrived-at-floor",
    "goto-floor",
]

@pytest.mark.parametrize("op", operations)
def test_ops_pdf(op):

    input_path = Path(__file__).parent / "operations" / f"{op}.op"
    result = OpParser.parse_file(file_input=input_path, debug=False)
    assert result
