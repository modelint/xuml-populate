"""
exceptions.py – Exceptions encountered when loading a model
"""

# Every error should have the same format
# with a standard prefix and postfix defined here
pre = "\nModel loader -- "
post = " --"

# ---
# ---

class UserModel(Exception):
    pass
