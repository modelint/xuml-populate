"""
mp_exceptions.py – Model parser specific exceptions
"""

# Every error should have the same format
# with a standard prefix and postfix defined here
pre = "\nxUML model parser: ["
post = "]"


class MPException(Exception):
    pass

class MDPopulationException(MPException):
    pass

class BadStateModelName(MPException):
    pass

class MultipleDomainsException(MPException):
    def __str__(self):
        return f'{pre}Only one domain may be loaded at a time.{post}'

class UnknownRelationshipType(MDPopulationException):
    def __str__(self):
        return f'{pre}Relationship is not a Generalization, Ordinal or Assocation.{post}'

class CnumsExceeded(MDPopulationException):
    def __init__(self, maxcnum):
        self.maxcnum = maxcnum

    def __str__(self):
        return f'{pre}Exceeded maximum cnum {self.maxcnum} for subsystem. Adjust number range.{post}'

class MismatchedStateSignature(MDPopulationException):
    def __init__(self, event, state):
        self.event = event
        self.state = event

    def __str__(self):
        return f'{pre}Event spec <{self.event}> on transition into state [{self.state}] has a different signature.{post}'

class LnumsExceeded(MDPopulationException):
    def __init__(self, maxlnum):
        self.maxlnum = maxlnum

    def __str__(self):
        return f'{pre}Exceeded maximum lnum (lineage number) {self.maxlnum} for subsystem. Adjust number range.{post}'

class LessThanTwoSubclassesInGeneralization(MDPopulationException):
    def __init__(self, rnum):
        self.rnum = rnum

    def __str__(self):
        return f'{pre}Generalization [{rnum}] requires at least two subclasses to form a minimal paritition.{post}'

class MPIOException(MPException):
    pass

class MPDBException(MPException):
    pass


class MPUserInputException(MPException):
    pass

class ModelParseError(MPUserInputException):
    def __init__(self, model_file, e):
        self.model_file = model_file
        self.e = e

    def __str__(self):
        return f'{pre}Parse error in model "{self.model_file}"\n\t{self.e}"{post}'

class ModelInputFileOpen(MPIOException):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return f'{pre}Parser cannot open this model input file: "{self.path}"{post}'

class ModelInputFileEmpty(MPIOException):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return f'{pre}For some reason, nothing was read from the model input file: "{self.path}"{post}'

class ModelGrammarFileOpen(MPIOException):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return f'{pre}Parser cannot open this model grammar file: "{self.path}"{post}'