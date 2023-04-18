"""
sp_exceptions.py – Scrall parser specific exceptions
"""

# Every error should have the same format
# with a standard prefix and postfix defined here
pre = "\nxUML scrall parser: ["
post = "]"


class SPException(Exception):
    pass


class SPIOException(SPException):
    pass

class SPUserInputException(SPException):
    pass

class ScrallMissingParameterName(SPUserInputException):
    def __init__(self, e):
        self.e = e

    def __str__(self):
        return f'{pre}Paramater name required if value is an expr \t{self.e}{post}'

class ScrallItsRequiresOpchain(SPUserInputException):
    def __init__(self, e):
        self.e = e

    def __str__(self):
        return f'{pre}"its" keyword must precede an opchain \t{self.e}{post}'

class ScrallCallWithoutOperation(SPUserInputException):
    def __init__(self, e):
        self.e = e

    def __str__(self):
        return f'{pre}Call action missing operation \t{self.e}{post}'

class ScrallParseError(SPUserInputException):
    def __init__(self, e):
        self.e = e

    def __str__(self):
        return f'{pre}Parse error in activity - \t{self.e}{post}'

class ScrallGrammarFileOpen(SPIOException):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return f'{pre}Parser cannot open this scrall grammar file: "{self.path}"{post}'