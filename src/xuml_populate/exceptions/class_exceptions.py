"""
class_exceptions.py – Exceptions encountered when loading a model
"""

# Every error should have the same format
# with a standard prefix and postfix defined here
pre = "\nModel loader -- "
post = " --"

# ---
# ---

class UserModel(Exception):
    pass

class ReferenceToNonIdentifier(UserModel):
    def __str__(self):
        return f"{pre}Attribute does not reference an identifier in target"

class MixedTargetID(UserModel):
    def __str__(self):
        return f"{pre}Attributes from more than one ID in target reference"
