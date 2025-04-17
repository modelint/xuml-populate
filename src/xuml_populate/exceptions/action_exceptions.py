"""
action_exceptions.py – Errors that occur while populating actions
"""

# Every error should have the same format
# with a standard prefix and postfix defined here
pre = "\nScrall populator: -- "
post = " --"


class ActionException(Exception):
    pass

class UndefinedMethod(ActionException):
    pass

class UndefinedSynchOutputExecutionUnit(ActionException):
    pass

class MethodXIFlowNotPopulated(ActionException):
    pass

class UndefinedAttribute(ActionException):
    pass

class UndefinedParameter(ActionException):
    pass
class UndefinedTableAttribute(ActionException):
    pass

class SwitchException(ActionException):
    pass

class BadScalarSwitchInput(SwitchException):
    pass

class FlowException(ActionException):
    pass

class ControlFlowHasNoTargetActions(FlowException):
    pass

class NonScalarFlowRequired(FlowException):
    pass

class TableExpressionException(ActionException):
    pass

class ScalarExpressionException(ActionException):
    pass

class ScalarOperationOrExpressionExpected(ScalarExpressionException):
    pass

class ScalarAssignmentfromMultipleTuples(ScalarExpressionException):
    pass
class ScalarAssignmentFlowMismatch(ScalarExpressionException):
    pass

class UndefinedHeaderExpressionOp(TableExpressionException):
    pass

class ProductForbidsCommonAttributes(TableExpressionException):
    pass

class SetOpRequiresSameHeaders(TableExpressionException):
    pass

class UnjoinableHeaders(TableExpressionException):
    pass

class TraversalActionException(ActionException):
    pass

class SelectActionException(ActionException):
    pass

class NoInputInstanceFlow(SelectActionException):
    pass

class ProjectedAttributeNotDefined(TableExpressionException):
    pass

class TableOperationOrExpressionExpected(TableExpressionException):
    pass

class SelectionOnScalarFlow(ActionException):
    def __init__(self, path, text, x):
        self.path = path
        self.text = text[slice(*x)]

    def __str__(self):
        return f'{pre}Cannot select/restrict on a scalar flow. Verify input to selection phrase' \
               f'{post}\n\t[{self.path}] >> {self.text}'

class AssignZeroOneInstanceHasMultiple(ActionException):
    def __init__(self, path, text, x):
        self.path = path
        self.text = text[slice(*x)]

    def __str__(self):
        return f'{pre}Single instance assignment operator may recieve multiple instances, try ..= operator or ' \
               f'modify RHS to yield at most one instance{post}\n\t[{self.path}] >> {self.text}'

class NoClassOrInstanceFlowForInstanceSetName(ActionException):
    def __init__(self, path, text, x):
        self.path = path
        self.text = text[slice(*x)]

    def __str__(self):
        return f'{pre}Name in instance set is neither a class or an instance flow source' \
               f'{post}\n\t[{self.path}] >> {self.text}'

class ComparingNonAttributeInSelection(SelectActionException):
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

class UndefinedAssociation(ActionException):
    def __init__(self, rnum, domain):
        self.rnum = rnum
        self.domain = domain

    def __str__(self):
        return f'{pre}Undefined association [{self.rnum}] in domain [{self.domain}].{post}'

class PerspectiveNotDefined(TraversalActionException):
    def __init__(self, phrase,domain):
        self.phrase = phrase
        self.domain = domain

    def __str__(self):
        return f'{pre}Perspective [{self.phrase}] not defined in domain [{self.domain}].{post}'

class RelationshipUnreachableFromClass(TraversalActionException):
    def __init__(self, rnum, cname, domain):
        self.cname = cname
        self.rnum = rnum
        self.domain = domain

    def __str__(self):
        return f'{pre}Unreachable relationship [{self.rnum}] from [{self.cname}] in domain [{self.domain}].{post}'

class NeedPerspectiveToHop(TraversalActionException):
    def __init__(self, rnum, domain):
        self.rnum = rnum
        self.domain = domain

    def __str__(self):
        return f'{pre}Reflexive association [{self.rnum}] in domain [{self.domain}] cannot be resolved' \
               f'without perspective.{post}'
class NeedPerspectiveOrClassToHop(TraversalActionException):
    def __init__(self, rnum, domain):
        self.rnum = rnum
        self.domain = domain

    def __str__(self):
        return f'{pre}Association [{self.rnum}] in domain [{self.domain}] cannot be resolved' \
               f'without perspective or class.{post}'

class HopToUnreachableClass(TraversalActionException):
    def __init__(self, cname, rnum, domain):
        self.cname = cname
        self.rnum = rnum
        self.domain = domain

    def __str__(self):
        return f'{pre}Relationship [{self.rnum}] does not reach class [{self.cname}] in domain [{self.domain}].{post}'

class SubclassNotInGeneralization(TraversalActionException):
    def __init__(self, subclass, rnum, domain):
        self.subclass = subclass
        self.rnum = rnum
        self.domain = domain

    def __str__(self):
        return f'{pre}Generalization [{self.rnum}] does not include subclass [{self.subclass}] in domain' \
               f'[{self.domain}].{post}'
class NoSubclassInHop(TraversalActionException):
    def __init__(self, superclass, rnum, domain):
        self.superclass = superclass
        self.rnum = rnum
        self.domain = domain

    def __str__(self):
        return f'{pre}Generalization [{self.rnum}] from [{self.superclass}] does not reach a subclass in domain' \
               f'[{self.domain}].{post}'
class MissingTorPrefInAssociativeRel(TraversalActionException):
    def __init__(self, rnum, domain):
        self.rnum = rnum
        self.domain = domain

    def __str__(self):
        return f'{pre}P or T ref not found for associative relationship [{self.rnum}] in domain [{self.domain}].{post}'

class UnexpectedClassOrPerspectiveInPath(TraversalActionException):
    def __init__(self, name, path):
        self.name = name
        self.path = path

    def __str__(self):
        return f'{pre}Name [{self.name}] not expected in path [{self.path}].{post}'

