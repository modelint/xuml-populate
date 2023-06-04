"""
action_exceptions.py – Errors that occur while populating actions
"""

# Every error should have the same format
# with a standard prefix and postfix defined here
pre = "\nAction loader: -- "
post = " --"


class ActionException(Exception):
    pass

class TraversalActionException(ActionException):
    pass

class NoDestinationInPath(ActionException):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return f'{pre}No destination class at end of path: [{self.path}].{post}'

class UndefinedClass(ActionException):
    def __init__(self, cname):
        self.cname = cname

    def __str__(self):
        return f'{pre}Class [{self.cname}] not defined.{post}'

class IncompletePath(ActionException):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return f'{pre}Path requires at least one hop: [{self.path}].{post}'

class NoPathFromClass(ActionException):
    def __init__(self, rnum, domain):
        self.rnum = rnum
        self.domain = domain

    def __str__(self):
        return f'{pre}Undefined relationship [{self.rnum}] in domain [{self.domain}].{post}'

class UndefinedRelationship(ActionException):
    def __init__(self, rnum, domain):
        self.rnum = rnum
        self.domain = domain

    def __str__(self):
        return f'{pre}Undefined relationship [{self.rnum}] in domain [{self.domain}].{post}'

class RelationshipUnreachableFromClass(TraversalActionException):
    def __init__(self, rnum, cname, domain):
        self.cname = rnum
        self.rnum = rnum
        self.domain = domain

    def __str__(self):
        return f'{pre}Unreachable relationship [{self.rnum}] from [{self.cname}] in domain [{self.domain}].{post}'
