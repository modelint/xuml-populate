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

class IncompleteTransactionPending(PyRALException):
    def __str__(self):
        return f'{pre}Only one transaction may be open at a time.{post}'