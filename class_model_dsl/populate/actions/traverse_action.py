"""
traverse_action.py – Populate a traverse action instance in PyRAL
"""

import logging
from typing import TYPE_CHECKING, List, Set
from class_model_dsl.exceptions.action_exceptions import UndefinedRelationship, IncompletePath,\
    NoDestinationInPath, UndefinedClass, RelationshipUnreachableFromClass, HopToUnreachableClass,\
    MissingTorPrefInAssociativeRel, NoSubclassInHop, SubclassNotInGeneralization, PerspectiveNotDefined,\
    UndefinedAssociation
from class_model_dsl.parse.scrall_visitor import PATH_a
from PyRAL.relation import Relation
from collections import namedtuple

Hop = namedtuple('Hop', 'cname rnum')

if TYPE_CHECKING:
    from tkinter import Tk

class TraverseAction:
    """
    Create all relations for a Traverse Action
    """
    _logger = logging.getLogger(__name__)

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
            cls._logger.error(f"Undefined Rnum {rnum} in Domain {cls.domain}")
            raise UndefinedRelationship(rnum, cls.domain)


    @classmethod
    def ordinal_hop(cls, rnum: str, cname:str, perspective:str):
        pass

    @classmethod
    def symmetric_hop(cls, rnum: str, cname:str):
        pass

    @classmethod
    def assymetric_circular_hop(cls, rnum: str, cname:str, perspective:str):
        pass

    @classmethod
    def from_association_class(cls, rnum: str, assoc_class:str, to_class:str, symmetric:bool = False):
        pass

    @classmethod
    def to_association_class(cls, rnum: str, from_class:str, assoc_class:str):
        pass

    @classmethod
    def straight_hop(cls, rnum: str, from_class:str, to_class:str):
        pass

    @classmethod
    def to_superclass_hop(cls, rnum: str, sub_class: str, super_class:str):
        pass

    @classmethod
    def to_subclass_hop(cls, rnum: str, sub_class: str, super_class:str):
        pass

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
    def resolve_perspective(cls, phrase:str):
        """
        Populate hop across the perspective

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
        # We found the perspective
        # Now we need to determine if the cursor class can reach that perspective
        # If the association is reflexive, there is only one viewed class which must be the cursor class
        # If not, the cursor class must be reachable in the association but not be the viewed class on
        # the found perspective
        if cls.is_reflexive(rnum):
            if cls.class_cursor == viewed_class:
                # Reflexive and on the current class, perspective is reachable
                cls.rel_cursor = rnum
                return
        elif cls.class_cursor != viewed_class and cls.class_cursor in cls.reachable_classes(rnum):
            cls.rel_cursor = rnum
            return

        # If we haven't returned, the perspective is unreachable
        raise RelationshipUnreachableFromClass(rnum, cname=cls.class_cursor, domain=cls.domain)


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
        path_index = 0
        while path_index < len(path.hops):
            hop = path.hops[path_index]

            if type(hop).__name__ == 'N_a':
                if path_index == 0:
                    # This is the first hop and it must a perspective
                    cls.resolve_perspective(phrase=hop.name)
                    pass
                # This is either a relationship phrase or a class name
                # First look for a class name
                class_id = f"Name:<{hop.name}>, Domain:<{domain}>"

                if Relation.restrict3(tclral=cls.mmdb, restriction=class_id, relation="Class").body:
                    # Class exists

                    if cls.class_cursor != hop.name:
                        raise HopToUnreachableClass(cname=hop.name, rnum=cls.rel_cursor, domain=domain)
                else:
                    # Try a phrase name (and get Rnum, Viewed class
                    # Reflexive if both T/P references are to the same class OR
                    # If single R reference has same from/to classes
                    # If assoc not reflexive, get relationship number and process as rnum
                    # If reflexive:
                    #
                    # Check for Binary or Unary
                    cls.resolve_perspective(phrase=hop.name)
                    ptuples = Relation.make_pyrel(result).body
                    found = False
                    for t in ptuples:
                        pass

            elif type(hop).__name__ == 'R_a':
                cls.rel_cursor = hop.rnum
                rhop = f"(From_class:<{cls.class_cursor}> OR To_class:<{cls.class_cursor}>), Rnum:<{hop.rnum}>, Domain:<{cls.domain}>"
                # Is it an association?
                if Relation.restrict3(tclral=cls.mmdb, restriction=rhop, relation="Reference").body:
                    refs = Relation.project2(cls.mmdb, attributes=['Ref', 'From_class', 'To_class'], svar_name='rhop').body

                    if len(refs) == 1:
                        ref, from_class, to_class = map(refs[0].get, ('Ref', 'From_class', 'To_class'))
                        if ref == 'R':
                            if to_class == from_class:
                                # Create an Asymmetric Circular Hop and do not update the class_cursor
                                pass
                            else:
                                # Create a straight hop and update the class_cursor to either the to or from class
                                # whichever does not match the class_cursor
                                cls.class_cursor = to_class if to_class != cls.class_cursor else from_class
                                pass
                        elif ref == 'T' or ref == 'P':
                            # We are traversing an associative relationship
                            # This means that we could be traversing to either the association class
                            # or a straight hop to a participating class
                            # We already know the association class as the from class. So we need to get both
                            # to classes (same class may be on each side in a reflexive)
                            # Then we look ahead for the next step which MUST be either a class name
                            # or a perspective
                            path_index += 1
                            next_hop = path.hops[path_index]
                            # The next hop must be either a class name or a perspective phrase on the current rel
                            # Class?
                            # Assoc class always has a T and P ref, get the other one
                            other_ref = 'P' if ref == 'T' else 'T'
                            pref_r = f"Ref:<{other_ref}>, Rnum:<{hop.rnum}>, Domain:<{domain}>"
                            pref = Relation.restrict3(tclral=cls.mmdb, restriction=pref_r, relation="Reference").body
                            if not pref:
                                raise MissingTorPrefInAssociativeRel(rnum=hop.rnum, domain=domain)
                            pref_dest_class = pref[0]['To_class']
                            # This is the destination class
                            if next_hop.name == pref_dest_class:
                                # It is the association class (source of the T ref)
                                # Create a To Association Class Hop
                                cls.class_cursor = next_hop.name
                                pass
                            else:
                                # next_hop must be a perspective phrase and not a class, but let's check to be sure
                                r = f"Phrase:<{next_hop}>, Rnum:<{hop.rnum}>, Domain:<{domain}>"
                                perspective = Relation.restrict3(tclral=cls.mmdb, restriction=r, relation="Perspective").body
                                if perspective:
                                    pass
                                    #
                                #
                                pass
                                # Create


                    if len(refs) == 2 and refs[0]['Ref'] in {'T', 'P'}:
                        # Current hop is from an association class
                        # So we have both a T and a P reference
                        path_index += 1
                        next_hop = path.hops[path_index]
                        # Does the next hop match either of the participating classes
                        particip_classes = {refs[0]['To_class'], refs[1]['To_class']}
                        if next_hop.name in particip_classes:
                            # This is the participating class, create from asym assoc hop
                            cls.class_cursor = next_hop.name
                            pass
                        else:
                            pass
                            # pref_r = f"Ref:<{other_ref}>, Rnum:<{hop.rnum}>, Domain:<{domain}>"
                            # pref = Relation.restrict3(tclral=cls.mmdb, restriction=pref_r, relation="Reference").body
                            # if not pref:
                            #     raise MissingTorPrefInAssociativeRel(rnum=hop.rnum, domain=domain)
                            # pref_dest_class = pref[0]['To_class']
                            # # This is the destination class
                            # if next_hop.name == pref_dest_class:
                            #     # It is the association class (source of the T ref)
                            #     # Create a To Association Class Hop
                            #     cls.class_cursor = next_hop.name
                            #     pass
                            # next_hop must be a perspective phrase and not a class, but let's check to be sure
                            # r = f"Phrase:<{next_hop}>, Rnum:<{hop.rnum}>, Domain:<{domain}>"
                            # perspective = Relation.restrict3(tclral=cls.mmdb, restriction=r,
                            #                                  relation="Perspective").body
                            # if perspective:
                            #     pass
                                #
                    if len(refs) > 1 and refs[0]['Ref'] == 'G':
                        # It's a set of generalization references
                        super_class = refs[0]['To_class']
                        sub_tuples = Relation.project2(cls.mmdb, attributes=['From_class'], relation="rhop").body
                        subclasses = {s['From_class'] for s in sub_tuples}
                        if cls.class_cursor == super_class:
                            # Determine subclass
                            path_index += 1
                            next_hop = path.hops[path_index]
                            if next_hop not in subclasses:
                                raise NoSubclassInHop(superclass=super_class, rnum=hop.rnum, domain=domain)
                            cls.class_cursor = next_hop
                            # Create a To Subclass Hop
                        else:
                            # Assume we are jumping to the superclass, but verify that the current class is a subclass
                            if cls.class_cursor not in subclasses:
                                raise SubclassNotInGeneralization(subclass=cls.class_cursor, rnum=hop.rnum, domain=domain)
                            # Create a To Superclass Hop using superclass, rnum, and class_cursor
                            cls.class_cursor = superclass
                        pass

            path_index += 1

                #   break
                # Two refs T and P, associative hop
                #   Look ahead to next hop
                #   If Rnum or phrase:
                #      Get all reached classes of next hop and take intersection of
                #      reached classes to get destination
                #      break;
                #   Else name:
                #      If class name:
                #      That is the destination class, create the approriate
                #      hop subclass based on reference direction







        if cls.dest_class != cls.class_cursor:
            # Path does not reach destination
            pass
        pass # Success
