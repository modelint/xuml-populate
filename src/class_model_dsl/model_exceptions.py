"""
model_exceptions.py – Exceptions encountered when loading a model
"""

# Every error should have the same format
# with a standard prefix and postfix defined here
pre = "\nModel loader -- "
post = " --"

# ---
# ---

class Metamodel(Exception):
    pass

class UserModel(Exception):
    pass
