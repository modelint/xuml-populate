"""
traverse_action.py – Populate a traverse action instance in PyRAL
"""

import logging
from typing import Set, Dict, List, Optional
from xuml_populate.config import mmdb
from xuml_populate.exceptions.action_exceptions import UndefinedRelationship, IncompletePath, \
    NoDestinationInPath, UndefinedClass, RelationshipUnreachableFromClass, HopToUnreachableClass, \
    MissingTorPrefInAssociativeRel, NoSubclassInHop, SubclassNotInGeneralization, PerspectiveNotDefined, \
    UndefinedAssociation, NeedPerspectiveOrClassToHop, NeedPerspectiveToHop, UnexpectedClassOrPerspectiveInPath
from scrall.parse.visitor import PATH_a
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content, Activity_ap
from xuml_populate.populate.mmclass_nt import Action_i, Traverse_Action_i, Path_i, Hop_i, Association_Class_Hop_i, \
    Circular_Hop_i, Symmetric_Hop_i, Asymmetric_Circular_Hop_i, Ordinal_Hop_i, Straight_Hop_i, \
    From_Asymmetric_Association_Class_Hop_i, From_Symmetric_Association_Class_Hop_i, To_Association_Class_Hop_i, \
    Perspective_Hop_i, Generalization_Hop_i, To_Subclass_Hop_i, To_Superclass_Hop_i, Association_Hop_i
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction
from collections import namedtuple

# HopArgs = namedtuple('HopArgs', 'cname rnum attrs')
Hop = namedtuple('Hop', 'hoptype to_class rnum attrs')

_logger = logging.getLogger(__name__)

# Transactions
tr_Traverse = "Traverse Action"

class TraverseAction:
    """
    Create all relations for a Traverse Statement
    """

    path_index = 0
    path = None
    name = None
    input_instance_flow = None
    id = None
    dest_class = None  # End of path
    class_cursor = None
    rel_cursor = None
    domain = None
    hops = []
    anum = None
    action_id = None
    mult = None  # Max mult of the current hop
    dest_fid = None
    activity_path = None
    scrall_text = None

    @classmethod
    def populate(cls):
        """
        Populate the Traverse Statement, Path and all Hops
        """
        cls.name = cls.name.rstrip('/')  # Remove trailing '/' from the path name
        # Create a Traverse Action and Path
        Transaction.open(mmdb, tr_Traverse)
        cls.action_id = Action.populate(tr=tr_Traverse, anum=cls.anum, domain=cls.domain)
        # Create the Traverse action destination flow (the output for R930)
        cls.dest_fid = Flow.populate_instance_flow(cname=cls.dest_class, anum=cls.anum,
                                                   domain=cls.domain, label=None,
                                                   single=True if cls.mult == MaxMult.ONE else False).fid

        _logger.info(f"INSERT Traverse action output Flow: ["
                     f"{cls.domain}:{cls.dest_class}:{cls.activity_path.split(':')[-1]}"
                     f":{cls.dest_fid}]")
        Relvar.insert(mmdb, tr=tr_Traverse, relvar='Traverse_Action', tuples=[
            Traverse_Action_i(ID=cls.action_id, Activity=cls.anum, Domain=cls.domain, Path=cls.name,
                              Source_flow=cls.input_instance_flow.fid, Destination_flow=cls.dest_fid)
        ])
        Relvar.insert(mmdb, tr=tr_Traverse, relvar='Path', tuples=[
            Path_i(Name=cls.name, Domain=cls.domain, Dest_class=cls.dest_class)
        ])

        # Get the next action ID
        # Then process each hop
        for number, h in enumerate(cls.hops, start=1):
            h.hoptype(number=number, to_class=h.to_class, rnum=h.rnum,
                      attrs=h.attrs)  # Call hop type method with hop type general and specific args
        Transaction.execute(mmdb, tr_Traverse)

    @classmethod
    def validate_rel(cls, rnum: str):
        rel = f"Rnum:<{rnum}>, Domain:<{cls.domain}>"
        if not Relation.restrict(mmdb, restriction=rel, relation="Relationship").body:
            _logger.error(f"Undefined Rnum {rnum} in Domain {cls.domain}")
            raise UndefinedRelationship(rnum, cls.domain)

    @classmethod
    def ordinal_hop(cls, cname: str, ascending: bool):
        _logger.info("ACTION:Traverse - Populating an ordinal hop")

    @classmethod
    def symmetric_hop(cls, cname: str):
        _logger.info("ACTION:Traverse - Populating a circular symmetric hop")

    @classmethod
    def asymmetric_circular_hop(cls, cname: str, side: str):
        _logger.info("ACTION:Traverse - Populating an asymmetric circular hop")

    @classmethod
    def from_symmetric_association_class(cls, rnum: str):
        _logger.info("ACTION:Traverse - Populating a from symmetric assoc class hop")

    @classmethod
    def from_asymmetric_association_class(cls, side: str):
        """
        :param side: Perspective side (T or P)
        :return:
        """
        _logger.info("ACTION:Traverse - Populating a from asymmetric assoc class hop")

    @classmethod
    def to_association_class(cls, number: int, rnum: str, to_class: str, attrs: Optional[Dict]):
        _logger.info("ACTION:Traverse - Populating a to association class hop")
        Relvar.insert(mmdb, tr=tr_Traverse, relvar='To_Association_Class_Hop', tuples=[
            To_Association_Class_Hop_i(Number=number, Path=cls.name, Domain=cls.domain)
        ])
        Relvar.insert(mmdb, tr=tr_Traverse, relvar='Association_Class_Hop', tuples=[
            Association_Class_Hop_i(Number=number, Path=cls.name, Domain=cls.domain)
        ])
        Relvar.insert(mmdb, tr=tr_Traverse, relvar='Association_Hop', tuples=[
            Association_Hop_i(Number=number, Path=cls.name, Domain=cls.domain)
        ])
        Relvar.insert(mmdb, tr=tr_Traverse, relvar='Hop', tuples=[
            Hop_i(Number=number, Path=cls.name, Domain=cls.domain, Rnum=rnum, Class_step=to_class)
        ])

    @classmethod
    def straight_hop(cls, number: int, rnum: str, to_class: str, attrs: Optional[Dict] = None):
        """
        Populate an instance of Straight HopArgs

        :param number:  Value (1, 2, 3... ) establishing order within a Path, See Hop.Number in the class model
        :param to_class: Hop over to this class
        :param rnum: Across this association
        :param attrs:  Unused, but required in signature
        """
        _logger.info("ACTION:Traverse - Populating a straight hop")
        Relvar.insert(mmdb, tr=tr_Traverse, relvar='Straight_Hop', tuples=[
            Straight_Hop_i(Number=number, Path=cls.name, Domain=cls.domain)
        ])
        Relvar.insert(mmdb, tr=tr_Traverse, relvar='Association_Hop', tuples=[
            Association_Hop_i(Number=number, Path=cls.name, Domain=cls.domain)
        ])
        Relvar.insert(mmdb, tr=tr_Traverse, relvar='Hop', tuples=[
            Hop_i(Number=number, Path=cls.name, Domain=cls.domain, Rnum=rnum, Class_step=to_class)
        ])

    @classmethod
    def to_superclass_hop(cls):
        _logger.info("ACTION:Traverse - Populating a to superclass hop")

    @classmethod
    def to_subclass_hop(cls, sub_class: str):
        _logger.info("ACTION:Traverse - Populating a to subclass hop")

    @classmethod
    def is_assoc_class(cls, cname: str, rnum: str) -> bool:
        """
        Returns true
        :param cname: Class to investigate
        :param rnum: Class participates in this association
        :return: True of the class is an association class formalizing the specified association
        """
        r = f"Class:<{cname}>, Rnum:<{rnum}>, Domain:<{cls.domain}>"
        return bool(Relation.restrict(mmdb, restriction=r, relation="Association_Class").body)

    @classmethod
    def is_reflexive(cls, rnum: str) -> int:
        """
        Is this a reflexive association and, if so, how many perspectives does it have?
        An association with both a T and P perspective is an asymmetric association while
        an association with a single S perspective is a symmetric association

        :param rnum: The association rnum to inspect
        :return: Zero if non-reflexive, 1 if symmetric and 2 if assymmetric reflexive
        """
        # Get all perspectives defined on rnum
        R = f"Rnum:<{rnum}>, Domain:<{cls.domain}>"
        perspectives = Relation.restrict(mmdb, restriction=R, relation="Perspective")
        if not perspectives.body:
            # Every association relationship defines at least one perspective
            raise UndefinedAssociation(rnum, cls.domain)
        vclasses = Relation.project(mmdb, attributes=('Viewed_class',)).body
        # Reflexive if there is both viewed classes are the same (only 1)
        # So, if reflexive, return 1 (S - Symmetric) or 2 (T,P - Assymetric), otherwise 0, non-reflexive
        return len(perspectives.body) if len(vclasses) == 1 else 0

    @classmethod
    def reachable_classes(cls, rnum: str) -> Set[str]:
        """
        Return a set of all classes reachable on the provided relationship

        :param rnum:
        :return:
        """
        reachable_classes = set()
        R = f"Rnum:<{rnum}>, Domain:<{cls.domain}>"
        refs = Relation.restrict(mmdb, restriction=R, relation="Reference").body
        for ref in refs:
            reachable_classes.add(ref['To_class'])
            reachable_classes.add(ref['From_class'])
        return reachable_classes

    @classmethod
    def resolve_ordinal_perspective(cls, perspective: str) -> bool:
        # Search for ordinal rel with the supplied perspective
        # TODO: Update metamodel with two additional identifiers
        R = f"Ranked_class:<{cls.class_cursor}>, Domain:<{cls.domain}>, " \
            f"(Ascending_perspective:<{perspective}> OR Descending_perspective:<{perspective}>)"
        orel = Relation.restrict(mmdb, restriction=R, relation="Ordinal_Relationship").body[0]
        if not orel:
            return False
        cls.rel_cursor = orel['Rnum']
        cls.ordinal_hop(cname=cls.class_cursor, ascending=orel['Ascending_perspective'] == perspective)
        return True

    @classmethod
    def hop_generalization(cls, refs: List[Dict[str, str]]):
        """
        Populate a Generalization HopArgs

        :param refs:
        :return:
        """
        # If hopping from a superclass, all subclass references will be provided as refs
        # otherwise we are hopping from one of the subclasses and only one ref from that subclass is provided
        # The to class for each ref must be the superclass, so we just grab the first (possibly only) ref
        super_class = refs[0]['To_class']
        if len(refs) > 1:
            # We are hopping from the super_class to a subclass
            P = ("From_class",)
            sub_tuples = Relation.project(mmdb, attributes=P, relation="rhop").body
            subclasses = {s['From_class'] for s in sub_tuples}
            # The subclass must be specified in the next hop
            cls.path_index += 1
            next_hop = cls.path.hops[cls.path_index]
            if next_hop.name not in subclasses:
                raise NoSubclassInHop(superclass=super_class, rnum=cls.rel_cursor, domain=cls.domain)
            cls.class_cursor = next_hop.name
            cls.to_subclass_hop(sub_class=cls.class_cursor)
            return
        else:
            # # Superclass to subclass
            cls.class_cursor = super_class
            cls.to_superclass_hop()
            return

    @classmethod
    def hop_association(cls, refs: List[Dict[str, str]]):
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
                    # Add a straight hop to the hop list and update the class_cursor to either the to or from class
                    # whichever does not match the class_cursor

                    # Update multiplicity for this hop
                    # We need to look up the Perspective to get the multiplicity
                    # Since this is an R ref (no association class) we just need to specify the
                    # rnum, domain, and viewed class which will be the updated class cursor
                    cls.class_cursor = to_class if to_class != cls.class_cursor else from_class
                    R = f"Rnum:<{cls.rel_cursor}>, Domain:<{cls.domain}>, Viewed_class:<{cls.class_cursor}>"
                    result = Relation.restrict(mmdb, relation='Perspective', restriction=R)
                    if not result.body:
                        # TODO: raise exception
                        return False
                    cls.mult = MaxMult.ONE if result.body[0]['Multiplicity'] == '1' else MaxMult.MANY
                    cls.hops.append(
                        Hop(hoptype=cls.straight_hop, to_class=cls.class_cursor, rnum=cls.rel_cursor, attrs=None))
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
                    # Update multiplicty
                    # First check multiplicity on to_class perspective (same as ref)
                    R = f"Rnum:<{cls.rel_cursor}>, Domain:<{cls.domain}>, Side:<{ref}>"
                    result = Relation.restrict(mmdb, relation='Perspective', restriction=R)
                    if not result.body:
                        # TODO: raise exception
                        return False
                    # Set multiplicity based on the perspective
                    cls.mult = MaxMult.ONE if result.body[0]['Multiplicity'] == '1' else MaxMult.MANY
                    # If multiplicity has been set to 1, but associative multiplicty is M, we need to set it as M
                    R = f"Rnum:<{cls.rel_cursor}>, Domain:<{cls.domain}>, Class:<{cls.class_cursor}>"
                    result = Relation.restrict(mmdb, relation='Association_Class', restriction=R)
                    if not result.body:
                        # TODO: raise exception
                        return False
                    associative_mult = result.body[0]['Multiplicity']
                    # Associative mult of M overrides a single mult
                    cls.mult = MaxMult.MANY if associative_mult == 'M' else cls.mult

                    cls.name += cls.class_cursor + '/'
                    cls.hops.append(
                        Hop(hoptype=cls.to_association_class, to_class=cls.class_cursor, rnum=cls.rel_cursor,
                            attrs=None))
                    return
                elif next_hop.name == to_class:
                    # Asymmetric reflexive hop requires a perspective phrase
                    raise NeedPerspectiveToHop(cls.rel_cursor, domain=cls.domain)

                else:
                    # Get the To class of the other (T or P) reference
                    other_ref_name = 'P' if ref == 'T' else 'T'
                    R = f"Ref:<{other_ref_name}>, Rnum:<{cls.rel_cursor}>, Domain:<{cls.domain}>"
                    other_ref = Relation.restrict(restriction=R, relation="Reference").body
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
                R = f"Viewed_class:<{cls.class_cursor}>, Rnum:<{cls.rel_cursor}>, Domain:<{cls.domain}>"
                Relation.restrict(mmdb, relation='Perspective', restriction=R)
                P = ('Side',)
                side = Relation.project(mmdb, attributes=P).body[0]['Side']
                cls.from_asymmetric_association_class(side=side)
                return
            else:
                # The next hop needs to be a perspective
                cls.resolve_perspective(phrase=next_hop.name)
                return

    @classmethod
    def resolve_perspective(cls, phrase: str) -> bool:
        """
        Populate hop across the association perspective

        :param phrase:  Perspective phrase text such as 'travels along'
        """
        # Find phrase and ensure that it is on an association that involves the class cursor
        R = f"Phrase:<{phrase}>, Domain:<{cls.domain}>"
        r_result = Relation.restrict(mmdb, relation='Perspective', restriction=R)
        if not r_result.body:
            return False
        P = ('Side', 'Rnum', 'Viewed_class')
        p_result = Relation.project(mmdb, attributes=P)
        side, rnum, viewed_class = map(p_result.body[0].get, P)
        cls.rel_cursor = rnum

        # The next hop may be a class name that matches the viewed class
        # If so, we can move the path index forward so that we don't process that class as a separate hop
        try:
            next_hop = cls.path.hops[cls.path_index + 1]
            if next_hop.name == viewed_class:
                cls.path_index += 1
        except (IndexError, AttributeError) as e:
            # We're already processing the last hop in the path, so don't bother advancing the path index or the
            # next hop is an rnum and not a name in which case we certainly don't want to advance the path index
            pass

        # We found the perspective
        # Now we decide which kind of hop to populate
        # We start by asking, "Is this association reflexive?"
        if symmetry := cls.is_reflexive(rnum):
            # Symmetry is zero if non-reflexive, otherwise 1:symmetric, 2:asymmetric
            # So it must be either 1 or 2
            if cls.class_cursor == viewed_class:
                # The class_cursor is one of the participating classes, i.e. not the association class
                # So it is a Circular HopArgs from-to the same class
                if symmetry == 1:
                    # Populate a symmetric hop
                    cls.symmetric_hop(viewed_class)
                else:
                    # Populate an asymmetric hop
                    cls.asymmetric_circular_hop(viewed_class, side)
                return True  # Circular hop populated
            else:
                # The class_cursor must be the association class
                if symmetry == 1:
                    cls.from_symmetric_association_class(rnum)
                else:
                    cls.from_asymmetric_association_class(side)
                return True  # From assoc class hop populated
        else:  # Non-reflexive association (non-circular hop)
            # We are either hopping from the association class to a viewed class or
            # from the other participating class to the viewed class
            if cls.is_assoc_class(cname=cls.class_cursor, rnum=rnum):
                cls.from_asymmetric_association_class(side)
            else:
                cls.class_cursor = viewed_class
                # TODO: Supply params below
                cls.straight_hop()
            return True  # Non-reflexive hop to a participating class

    @classmethod
    def build_path(cls, input_instance_flow: Flow_ap, path: PATH_a,
                   activity_data: Activity_ap) -> (str, Flow_ap):
        """
        Step through a path populating it along the way.

        :param input_instance_flow: This is the source instance flow where the path begins
        :param path: Parsed Scrall representing a Path
        :param activity_data:
        :return: The Traverse Action ID and the output instance flow id, its Class Type name and its maximum instance
        multiplicity, 1 or M
        """
        cls.path = path
        cls.anum = activity_data.anum
        cls.input_instance_flow = input_instance_flow
        cls.class_cursor = input_instance_flow.tname  # Validation cursor is on this class now
        cls.domain = activity_data.domain
        cls.name = "/"  # The path text forms path name value
        cls.activity_path = activity_data.activity_path
        cls.scrall_text = activity_data.scrall_text
        cls.mult = input_instance_flow.max_mult

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

        # We have an open transaction for the Statement superclass
        # We must first add each HopArgs population to the transaction before
        # determining the path_name, source, and destination flows which make it possible
        # to add the Path and Traverse Statement population

        # Valdiate path continuity
        # Step through the path validating each relationship, phrase, and class
        # Ensure that each step is reachable on the class model
        cls.path_index = 0
        while cls.path_index < len(path.hops) - 1:
            hop = path.hops[cls.path_index]

            if type(hop).__name__ == 'N_a':
                # This should be a perspective since flow names get eaten in the relationship hop handlers
                # and a path cannot begin with a class name
                # (any class name prefixing a path will have been processed to populate a labeled instance flow earlier)
                if not cls.resolve_perspective(phrase=hop.name) and not cls.resolve_ordinal_perspective(
                        perspective=hop.name):
                    raise UnexpectedClassOrPerspectiveInPath(name=hop.name, path=path)

            elif type(hop).__name__ == 'R_a':
                cls.rel_cursor = hop.rnum
                cls.name += cls.rel_cursor + '/'
                # This is either an Association, Generalization, or Ordinal Relationship
                # Determine the type and call the corresponding hop populator

                # First we look for any References to or from the class cursor
                R = f"(From_class:<{cls.class_cursor}> OR To_class:<{cls.class_cursor}>), Rnum:<{hop.rnum}>, " \
                    f"Domain:<{cls.domain}>"
                if Relation.restrict(mmdb, restriction=R, relation="Reference").body:
                    P = ('Ref', 'From_class', 'To_class')
                    refs = Relation.project(mmdb, attributes=P, svar_name='rhop').body

                    # Generalization
                    if refs[0]['Ref'] == 'G':
                        cls.hop_generalization(refs)
                    else:
                        cls.hop_association(refs)
                else:
                    # The perspective must be specified in the next hop
                    cls.path_index += 1
                    cls.resolve_ordinal_perspective(perspective=cls.path.hops[cls.path_index].name)

            cls.path_index += 1

        if cls.dest_class != cls.class_cursor:
            # Path does not reach destination
            pass

        # Now we can populate the path
        cls.populate()
        # Relvar.printall(mmdb)

        return cls.action_id, Flow_ap(fid=cls.dest_fid, content=Content.INSTANCE, tname=cls.dest_class,
                                      max_mult=cls.mult)
