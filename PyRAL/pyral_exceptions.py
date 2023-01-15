"""
pyral_exceptions.py – Pyral exceptions
"""

# Every error should have the same format
# with a standard prefix and postfix defined here
pre = "\nPyRAL: ["
post = "]"


class PyRALException(Exception):
    pass

class Transaction(PyRALException):
    pass

class NoOpenTransaction(PyRALException):
    def __str__(self):
        return f'{pre}Attempt to add statement when no transaction has been opened.{post}'

class IncompleteTransactionPending(PyRALException):
    def __str__(self):
        return f'{pre}Only one transaction may be open at a time.{post}'

class RestrictOneOnZeroCardinality(PyRALException):
    def __str__(self):
        return f'{pre}Attempted restrict one operation on relation with no tuples.{post}'
