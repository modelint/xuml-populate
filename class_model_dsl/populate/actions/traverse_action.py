"""
traverse_action.py – Populate a traverse action instance in PyRAL
"""

import logging
from typing import TYPE_CHECKING, Set, Dict, List
from class_model_dsl.exceptions.action_exceptions import UndefinedRelationship, IncompletePath,\
    NoDestinationInPath, UndefinedClass, RelationshipUnreachableFromClass, HopToUnreachableClass,\
    MissingTorPrefInAssociativeRel, NoSubclassInHop, SubclassNotInGeneralization, PerspectiveNotDefined,\
    UndefinedAssociation, NeedPerspectiveOrClassToHop, NeedPerspectiveToHop, UnexpectedClassOrPerspectiveInPath
from class_model_dsl.parse.scrall_visitor import PATH_a
from PyRAL.relation import Relation
from collections import namedtuple

Hop = namedtuple('Hop', 'cname rnum')

if TYPE_CHECKING:
    from tkinter import Tk

_logger = logging.getLogger(__name__)

class TraverseAction:
    """
    Create all relations for a Traverse Action
    """

    path_index = 0
    path = None
    source_flow = None
    dest_flow = None
    resolved_path = []
    id = None
    dest_class = None # End of path
    source_class = None # Beginning of path
    class_cursor = None
    rel_cursor = None
    hnum = 1 # Current hop number
    path_name = "" # Text representation of path as name
    from_class = None # Current hop
    mmdb = None
    domain = None

    @classmethod
    def validate_rel(cls, rnum: str):
        rel = f"Rnum:[{rnum}], Domain:[{cls.domain}]"
        if not Relation.restrict2(tclral=cls.mmdb, restriction=rel, relation="Relationship").body:
            _logger.error(f"Undefined Rnum {rnum} in Domain {cls.domain}")
            raise UndefinedRelationship(rnum, cls.domain)


    @classmethod
    def ordinal_hop(cls, cname:str, perspective:str):
        pass

    @classmethod
    def symmetric_hop(cls, cname:str):
        pass

    @classmethod
    def asymmetric_circular_hop(cls, cname:str, side:str):
        _logger.info("ACTION:Traverse - Populating a from symmetric assoc class hop")
        pass

    @classmethod
    def from_symmetric_association_class(cls, rnum: str):
        _logger.info("ACTION:Traverse - Populating a from symmetric assoc class hop")

    @classmethod
    def from_asymmetric_association_class(cls, side:str):
        """
        :param side: Perspective side (T or P)
        :return:
        """
        _logger.info("ACTION:Traverse - Populating a from asymmetric assoc class hop")

    @classmethod
    def to_association_class(cls):
        _logger.info("ACTION:Traverse - Populating a to association class hop")

    @classmethod
    def straight_hop(cls):
        _logger.info("ACTION:Traverse - Populating a straight hop")

    @classmethod
    def to_superclass_hop(cls):
        _logger.info("ACTION:Traverse - Populating a to superclass hop")

    @classmethod
    def to_subclass_hop(cls, sub_class: str):
        _logger.info("ACTION:Traverse - Populating a to subclass hop")

    @classmethod
    def is_assoc_class(cls, cname:str, rnum:str) -> bool:
        """
        Returns true
        :param cname: Class to investigate
        :param rnum: Class participates in this association
        :return: True of the class is an association class formalizing the specified association
        """
        r = f"Class:<{cname}>, Rnum:<{rnum}>, Domain:<{cls.domain}>"
        return bool(Relation.restrict3(tclral=cls.mmdb, restriction=r, relation="Association_Class").body)

    @classmethod
    def is_reflexive(cls, rnum:str) -> int:
        """
        Is this a reflexive association and, if so, how many perspectives does it have?
        An association with both a T and P perspective is an asymmetric association while
        an association with a single S perspective is a symmetric association

        :param rnum: The association rnum to inspect
        :return: Zero if non-reflexive, 1 if symmetric and 2 if assymmetric reflexive
        """
        # Get all perspectives defined on rnum
        r = f"Rnum:<{rnum}>, Domain:<{cls.domain}>"
        perspectives = Relation.restrict3(tclral=cls.mmdb, restriction=r, relation="Perspective")
        if not perspectives.body:
            # Every association relationship defines at least one perspective
            raise UndefinedAssociation(rnum, cls.domain)
        vclasses = Relation.project2(tclral=cls.mmdb, attributes=('Viewed_class',)).body
        # Reflexive if there is both viewed classes are the same (only 1)
        # So, if reflexive, return 1 (S - Symmetric) or 2 (T,P - Assymetric), otherwise 0, non-reflexive
        return len(perspectives.body) if len(vclasses) == 1 else 0

    @classmethod
    def reachable_classes(cls, rnum:str) -> Set[str]:
        """
        Return a set of all classes reachable on the provided relationship

        :param rnum:
        :return:
        """
        reachable_classes = set()
        r = f"Rnum:<{rnum}>, Domain:<{cls.domain}>"
        refs = Relation.restrict3(tclral=cls.mmdb, restriction=r, relation="Reference").body
        for ref in refs:
            reachable_classes.add(ref['To_class'])
            reachable_classes.add(ref['From_class'])
        return reachable_classes

    @classmethod
    def hop_ordinal(cls):
        pass

    @classmethod
    def hop_generalization(cls, refs:List[Dict[str,str]]):
        """
        Populate a Generalization Hop

        :param refs:
        :return:
        """
        # It's a set of generalization references
        super_class = refs[0]['To_class']
        P = ("From_class",)
        sub_tuples = Relation.project2(cls.mmdb, attributes=P, relation="rhop").body
        subclasses = {s['From_class'] for s in sub_tuples}
        if cls.class_cursor == super_class:
            # Superclass to subclass
            #  must be specified in the next hop
            cls.path_index += 1
            next_hop = cls.path.hops[cls.path_index]
            if next_hop not in subclasses:
                raise NoSubclassInHop(superclass=super_class, rnum=cls.rel_cursor, domain=cls.domain)
            cls.class_cursor = next_hop
            cls.to_subclass_hop(sub_class=cls.class_cursor)
            return
        else:
            # Subclass to Superclass
            # Assume we are jumping to the superclass, but verify that the current class is a subclass
            if cls.class_cursor not in subclasses:
                raise SubclassNotInGeneralization(subclass=cls.class_cursor, rnum=cls.rel_cursor,
                                                  domain=cls.domain)
            # Create a To Superclass Hop using superclass, rnum, and class_cursor
            cls.class_cursor = super_class
            cls.to_superclass_hop()
            return

    @classmethod
    def hop_association(cls, refs:List[Dict[str,str]]):
        """
        Populate hop across the association

        :param refs: A list of tuple references where the to or from class is the cursor class
        """
        # Single reference, R, T or P
        if len(refs) == 1:
            ref, from_class, to_class = map(refs[0].get, ('Ref', 'From_class', 'To_class'))
            if ref == 'R':
                if to_class == from_class:
                    # This must be an asymmetric cycle unconditional on both ends
                    # which means a perspective must be specified like: /R1/next
                    # So we need to assume that the next hop is a perspective.
                    # We advance to the next hop in the path and then resolve the perspective
                    # (If it isn't a perspective, an exception will be raised in the perspective resolveer)
                    cls.path_index += 1
                    cls.resolve_perspective(phrase=cls.path.hops[cls.path_index])
                else:
                    # Create a straight hop and update the class_cursor to either the to or from class
                    # whichever does not match the class_cursor
                    cls.class_cursor = to_class if to_class != cls.class_cursor else from_class
                    cls.straight_hop()
                return

            if ref == 'T' or ref == 'P':
                # We are traversing an associative relationship
                # This means that we could be traversing to either the association class
                # or a straight hop to a participating class
                # We already know the association class as the from class. So we need to get both
                # to classes (same class may be on each side in a reflexive)
                # Then we look ahead for the next step which MUST be either a class name
                # or a perspective
                cls.path_index += 1
                next_hop = cls.path.hops[cls.path_index]
                # The next hop must be either a class name or a perspective phrase on the current rel
                if type(next_hop).__name__ == 'R_a':
                    # In other words, it cannot be an rnum
                    raise NeedPerspectiveOrClassToHop(cls.rel_cursor, domain=cls.domain)
                # Is the next hop the association class?
                if next_hop.name == from_class:
                    cls.class_cursor = from_class
                    cls.to_association_class()
                    return
                elif next_hop.name == to_class:
                    # Asymmetric reflexive hop requires a perspective phrase
                    raise NeedPerspectiveToHop(cls.rel_cursor, domain=cls.domain)

                else:
                    # Get the To class of the other (T or P) reference
                    other_ref_name = 'P' if ref == 'T' else 'T'
                    R = f"Ref:<{other_ref_name}>, Rnum:<{cls.rel_cursor}>, Domain:<{cls.domain}>"
                    other_ref = Relation.restrict3(tclral=cls.mmdb, restriction=R, relation="Reference").body
                    if not other_ref:
                        # The model must be currupted somehow
                        raise MissingTorPrefInAssociativeRel(rnum=cls.rel_cursor, domain=cls.domain)
                    other_participating_class = other_ref[0]['To_class']
                    if next_hop.name == other_participating_class:
                        cls.class_cursor = next_hop.name
                        cls.straight_hop()
                        return
                    else:
                        # Next hop must be a perspective
                        cls.resolve_perspective(phrase=next_hop.name)
                        return

        # T and P reference
        else:
            # Current hop is from an association class
            cls.path_index += 1
            next_hop = cls.path.hops[cls.path_index]
            # Does the next hop match either of the participating classes
            particip_classes = {refs[0]['To_class'], refs[1]['To_class']}
            if next_hop.name in particip_classes:
                # The particpating class is explicitly named
                cls.class_cursor = next_hop.name
                R = f"Class:<{cls.class_cursor}>, Rnum:<{cls.rel_cursor}>, Domain:<{cls.domain}>"
                Relation.restrict3(cls.mmdb, relation='Perspective', restriction=R)
                P = ('Side',)
                side = Relation.project2(cls.mmdb, attributes=P).body[0]['Side']
                cls.from_asymmetric_association_class(side=side)
                return
            else:
                # The next hop needs to be a perspective
                cls.resolve_perspective(phrase=next_hop.name)
                return


    @classmethod
    def resolve_perspective(cls, phrase:str):
        """
        Populate hop across the association perspective

        :param phrase:  Perspective phrase text such as 'travels along'
        """
        # Find phrase and ensure that it is on an association that involves the class cursor
        r = f"Phrase:<{phrase}>, Domain:<{cls.domain}>"
        r_result = Relation.restrict3(cls.mmdb, relation='Perspective', restriction=r)
        if not r_result.body:
            raise PerspectiveNotDefined(phrase, cls.domain)
        p = ('Side', 'Rnum', 'Viewed_class')
        p_result = Relation.project2(cls.mmdb, attributes=p)
        side, rnum, viewed_class = map(p_result.body[0].get, p)
        cls.rel_cursor = rnum
        # We found the perspective
        # Now we decide which kind of hop to populate
        # We start by asking, "Is this association reflexive?"
        if symmetry := cls.is_reflexive(rnum):
            # Symmetry is zero if non-reflexive, otherwise 1:symmetric, 2:asymmetric
            # So it must be either 1 or 2
            if cls.class_cursor == viewed_class:
                # The class_cursor is one of the participating classes, i.e. not the association class
                # So it is a Circular Hop from-to the same class
                if symmetry == 1:
                    # Populate a symmetric hop
                    cls.symmetric_hop(viewed_class)
                else:
                    # Populate an assymetric hop
                    cls.asymmetric_circular_hop(viewed_class, side)
                return # Circular hop populated
            else:
                # The class_cursor must be the association class
                if symmetry == 1:
                    cls.from_symmetric_association_class(rnum)
                else:
                    cls.from_asymmetric_association_class(side)
                return # From assoc class hop populated
        else:  # Non-reflexive association (non-circular hop)
            # We are either hopping from the association class to a viewed class or
            # from the other participating class to the viewed class
            if cls.is_assoc_class(cname=cls.class_cursor, rnum=rnum):
                cls.from_asymmetric_association_class(side)
            else:
                cls.straight_hop()
            return # Non-reflexive hop to a participating class

    @classmethod
    def build_path(cls, mmdb: 'Tk', source_class: str, domain: str, path: PATH_a):
        """
        Populate the entire Action

        :param mmdb:
        :param source_class:
        :param domain:
        :param path:
        :return:
        """
        cls.mmdb = mmdb
        cls.path = path
        cls.source_class = source_class # Source of first hop
        cls.class_cursor = source_class # Validation cursor is on this class now
        cls.domain = domain

        # Verify adequate path length
        if len(path.hops) < 2:
            raise IncompletePath(path)
        # Path has at least 2 hop elements

        # Validate destination class at the end of the path
        terminal_hop = path.hops[-1]
        if type(terminal_hop).__name__ != 'N_a':
            # Destination class must a name
            raise NoDestinationInPath(path)
        cls.dest_class = terminal_hop.name

        # Verify destination class is defined (we should do this in the loop instead)
        # class_id = f'Name:[{cls.dest_class.name}], Domain:[{domain}]'
        # if not Relation.restrict2(mmdb, restriction=class_id, relation='Class').body:
        #     raise UndefinedClass(cls.dest_class.name)

        # Destination class is valid

        # Valdiate path continuity
        # Step through the path validating each relationship, phrase, and class
        # Ensure that each step is reachable on the class model
        cls.path_index = 0
        while cls.path_index < len(path.hops):
            hop = path.hops[cls.path_index]

            if type(hop).__name__ == 'N_a':
                if cls.path_index == 0:
                    # This is the first hop and it must a perspective
                    cls.resolve_perspective(phrase=hop.name)
                else:
                    # All other class/perspective hops should be processed in the rel hop methods
                    raise UnexpectedClassOrPerspectiveInPath(name=hop.name, path=path)

            elif type(hop).__name__ == 'R_a':
                cls.rel_cursor = hop.rnum
                # This is either an Association, Generalization, or Ordinal Relationship
                # Determine the type and call the corresponding hop populator

                # First we look for any References to or from the class cursor
                R = f"(From_class:<{cls.class_cursor}> OR To_class:<{cls.class_cursor}>), Rnum:<{hop.rnum}>, " \
                       f"Domain:<{cls.domain}>"
                if Relation.restrict3(tclral=cls.mmdb, restriction=R, relation="Reference").body:
                    P = ('Ref', 'From_class', 'To_class')
                    refs = Relation.project2(cls.mmdb, attributes=P, svar_name='rhop').body

                    # Generalization
                    if len(refs) > 1 and refs[0]['Ref'] == 'G':
                        cls.hop_generalization(refs)
                    else:
                        cls.hop_association(refs)
                else:
                    cls.hop_ordinal()

            cls.path_index += 1


        if cls.dest_class != cls.class_cursor:
            # Path does not reach destination
            pass
        pass # Success
