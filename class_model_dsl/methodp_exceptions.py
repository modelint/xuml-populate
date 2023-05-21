"""
methodp_exceptions.py – Method parser specific exceptions
"""

# Every error should have the same format
# with a standard prefix and postfix defined here
pre = "\nxUML method parser: ["
post = "]"

# ---
# ---

class MethodPException(Exception):
    pass


class MethodPIOException(MethodPException):
    pass

class MethodPUserInputException(MethodPException):
    pass

class MethodParseError(MethodPUserInputException):
    def __init__(self, e):
        self.e = e

    def __str__(self):
        return f'{pre}Parse error in method - \t{self.e}{post}'

class MethodGrammarFileOpen(MethodPIOException):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return f'{pre}Parser cannot open this method grammar file: "{self.path}"{post}'

class MethodInputFileOpen(MethodPIOException):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return f'{pre}Parser cannot open this method file: "{self.path}"{post}'

class MethodInputFileEmpty(MethodPIOException):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return f'{pre}For some reason, nothing was read from the method input file: "{self.path}"{post}'

