"""
traverse_action.py – Populate a traverse action instance in PyRAL
"""

import logging
from typing import TYPE_CHECKING, List, Set
from class_model_dsl.exceptions.action_exceptions import UndefinedRelationship, IncompletePath,\
    NoDestinationInPath, UndefinedClass, RelationshipUnreachableFromClass, HopToUnreachableClass,\
    MissingTorPrefInAssociativeRel
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

    # @classmethod
    # def validate_rel_hop(cls, from_classes: Set[str], rnum: str) -> Set[str]:
    #     """
    #     Is the specified relationship associated/attached to the from_class?
    #     If so, return the set of classes that can be reached by that relationship.
    #     If the relationship is reflexive or ordinal, a from_class class may be included
    #     in the set of reachable classes.
    #
    #     :param mmdb:
    #     :param rnum:
    #     :param from_classes: The set of classes that could be the start of this hop
    #     :param domain:
    #     :return: False if the relationship is not associated with the from_class
    #     """
    #     # Verify that the relationship is defined on the class model
    #     cls.validate_rel(rnum)
    #
    #     # Verify that the relationship is attached to the from_class
    #     # Association or generalization? Check for a reference from or to the from_class
    #     rhop = f"(From_class:<{from_classes}> OR To_class:<{from_classes}>), Rnum:<{rnum}>, Domain:<{cls.domain}>"
    #     reachable_classes = set()
    #     if Relation.restrict3(tclral=cls.mmdb, restriction=rhop, relation="Reference").body:
    #         from_tos = Relation.project2(cls.mmdb, attributes=['From_class', 'To_class']).body
    #         # Reflexive association, from_class is both to and from, valid
    #         if len(from_tos) == 1 and set(from_tos[0].values() == {from_classes}):
    #             # the set of from_tos matches the fro
    #             return from_classes
    #
    #         for t in from_tos:
    #             cnames = [n for n in t.values()]
    #             if from_class == cnames[0] == cnames[1]:
    #                 # Reflexive association, from_class is both to and from, valid
    #                 reachable_classes.add(from_class)
    #                 return reachable_classes
    #             if from_class == cnames[0]:
    #                 reachable_classes.add(cnames[1])
    #             else:
    #                 reachable_classes.add(cnames[0])
    #         return reachable_classes
    #     else:
    #         # Possibly an Ordinal which does not involve any Reference
    #         orhop = f"Ranked_class:[{from_class}], Rnum:[{rnum}, Domain:[{domain}]"
    #         if Relation.restrict2(tclral=mmdb, restriction=orhop, relation="Ordinal").body:
    #             reachable_classes.add(from_class)
    #             return reachable_classes
    #
    #     # The relationship is not associated with the from_class
    #     raise RelationshipUnreachableFromClass(rnum, from_class, domain)

    # @classmethod
    # def rel_hop(cls, rnum:str):
    #     """
    #     Process an rnum found in a path
    #     :param rnum:
    #     :return:
    #     """
    #     # Ensure rel exists and is attached to one of the cursor classes
    #     reachable_classes = cls.validate_rel_hop(from_classes=cls.cursor_classes, rnum=rnum)
    #     # Move cursor to this validated rel
    #     cls.cursor_rel = rnum
    #     #
    #     if len(cls.cursor_classes) == 1:
    #         cls.resolved_path.append(Hop(cname=cls.cursor_classes.pop(), rnum=rnum))
    #     else:
    #         # for the current cursor rel, which of the cursor classes is reachable?
    #         c = reachable_classes.intersection(cls.cursor_classes)
    #         if c and c not in cls.cursor_classes:
    #             # If none, path is invalid
    #             raise
    #         # Otherwise, the one that is reachable becomes the new hop, append it
    #         cls.resolved_path.append(Hop(cname=c, rnum=rnum))
    #     cls.cursor_classes = reachable_classes

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
                # This is either a relationship phrase or a class name
                # First look for a class name
                class_id = f"Name:<{hop.name}>, Domain:<{domain}>"

                if Relation.restrict3(tclral=cls.mmdb, restriction=class_id, relation="Class").body:
                    # Class exists

                    if cls.class_cursor != hop.name:
                        raise HopToUnreachableClass(cname=hop.name, rnum=cls.rel_cursor, domain=domain)
                else:
                    # Try a phrase name (and get Rnum, Viewed class
                    r = f"Phrase:{hop.name}, Domain: {domain}"
                    Relation.restrict(mmdb, relation='Perspective', restriction=r)
                    result = Relation.project(mmdb, attributes=['Rnum', 'Viewed_class'])
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
                        if cls.class_cursor == super_class:
                            # Create a To Subclass Hop
                            # Determine subclass
                            subs = Relation.project2(cls.mmdb, attributes=['From_class'], relation="rhop").body
                            pass
                        else:
                            # Create a To Superclass Hop
                            pass

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
