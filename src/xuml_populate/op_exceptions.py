"""
op_exceptions.py – Operation parser specific exceptions
"""

# Every error should have the same format
# with a standard prefix and postfix defined here
pre = "\nxUML operation parser: ["
post = "]"

# ---
# ---

class OpException(Exception):
    pass


class OpIOException(OpException):
    pass

class OpUserInputException(OpException):
    pass

class OpParseError(OpUserInputException):
    def __init__(self, e):
        self.e = e

    def __str__(self):
        return f'{pre}Parse error in operation - \t{self.e}{post}'

class OpGrammarFileOpen(OpIOException):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return f'{pre}Parser cannot open this operation grammar file: "{self.path}"{post}'

class OpInputFileOpen(OpIOException):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return f'{pre}Parser cannot open this operation file: "{self.path}"{post}'

class OpInputFileEmpty(OpIOException):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return f'{pre}For some reason, nothing was read from the operation input file: "{self.path}"{post}'

