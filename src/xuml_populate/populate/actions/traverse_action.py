"""
traverse_action.py – Populate a traverse action instance in PyRAL
"""

# System
import logging
from typing import Set, Dict, List, NamedTuple, Callable
from enum import Enum

# Model Integration
from scrall.parse.visitor import PATH_a
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

# XUML_Populate
from xuml_populate.config import mmdb
from xuml_populate.populate.actions.action import Action
from xuml_populate.populate.flow import Flow
from xuml_populate.exceptions.action_exceptions import (UndefinedRelationship, IncompletePath,
                                                        NoDestinationInPath, UndefinedClass,
                                                        RelationshipUnreachableFromClass, HopToUnreachableClass,
                                                        MissingTorPrefInAssociativeRel, NoSubclassInHop,
                                                        SubclassNotInGeneralization, PerspectiveNotDefined,
                                                        UndefinedAssociation, NeedPerspectiveOrClassToHop,
                                                        NeedPerspectiveToHop, UnexpectedClassOrPerspectiveInPath)
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content, Activity_ap
from xuml_populate.populate.mmclass_nt import (Action_i, Traverse_Action_i, Path_i, Hop_i, Association_Class_Hop_i,
                                               Circular_Hop_i, Symmetric_Hop_i, Asymmetric_Circular_Hop_i,
                                               Ordinal_Hop_i, Straight_Hop_i,
                                               From_Asymmetric_Association_Class_Hop_i,
                                               From_Symmetric_Association_Class_Hop_i, To_Association_Class_Hop_i,
                                               Perspective_Hop_i, Generalization_Hop_i, To_Subclass_Hop_i,
                                               To_Superclass_Hop_i, Association_Hop_i)
from xuml_populate.populate.actions.hop_types import (AggregationType, Hop, SymmetricHop, AsymmetricCircularHop,
                                                      OrdinalHop, FromAsymAssocHop)

_logger = logging.getLogger(__name__)

# Transactions
tr_Traverse = "Traverse Action"


class TraverseAction:
    """
    Create all relations for a Traverse Statement
    """

    def __init__(self):
        """

        """
        self.path_index = 0
        self.path = None
        self.name = None
        self.input_instance_flow = None
        self.id = None
        self.dest_class = None  # End of path
        self.class_cursor = None
        self.rel_cursor = None
        self.domain = None
        self.hops = []
        self.anum = None
        self.action_id = None
        self.mult = None  # Max mult of the current hop
        self.dest_fid = None
        self.activity_path = None
        self.scrall_text = None

    def build_path(self, input_instance_flow: Flow_ap, path: PATH_a, activity_data: Activity_ap) -> (str, Flow_ap):
        """
        Step through a path populating it along the way.

        :param input_instance_flow: This is the source instance flow where the path begins
        :param path: Parsed Scrall representing a Path
        :param activity_data:
        :return: The Traverse Action ID and the output instance flow id, its Class Type name and its maximum instance
        multiplicity, 1 or M
        """
        self.path = path
        self.hops = []
        self.anum = activity_data.anum
        self.input_instance_flow = input_instance_flow
        self.class_cursor = input_instance_flow.tname  # Validation cursor is on this class now
        self.domain = activity_data.domain
        self.name = "/"  # The path text forms path name value
        self.activity_path = activity_data.activity_path
        self.scrall_text = activity_data.scrall_text
        self.mult = input_instance_flow.max_mult

        # Verify adequate path length
        if len(path.hops) < 2:
            raise IncompletePath(path)
        # Path has at least 2 hop elements

        # Validate destination class at the end of the path
        terminal_hop = path.hops[-1]
        if type(terminal_hop).__name__ != 'N_a':
            # Destination class must a name
            raise NoDestinationInPath(path)
        self.dest_class = terminal_hop.name

        # Valdiate path continuity
        # Step through the path validating each relationship, phrase, and class
        # Ensure that each step is reachable on the class model
        self.path_index = 0
        while self.path_index < len(path.hops) - 1:
            hop = path.hops[self.path_index]

            if type(hop).__name__ == 'N_a':
                # This should be a perspective since flow names get eaten in the relationship hop handlers
                # and a path cannot begin with a class name
                # (any class name prefixing a path will have been processed to populate a labeled instance flow earlier)
                if not self.resolve_perspective(phrase=hop.name) and not self.resolve_ordinal_perspective(
                        perspective=hop.name):
                    raise UnexpectedClassOrPerspectiveInPath(name=hop.name, path=path)

            elif type(hop).__name__ == 'R_a':
                self.rel_cursor = hop.rnum
                self.name += self.rel_cursor + '/'
                # This is either an Association, Generalization, or Ordinal Relationship
                # Determine the type and call the corresponding hop populator

                # First we look for any References to or from the class cursor
                R = f"(From_class:<{self.class_cursor}> OR To_class:<{self.class_cursor}>), Rnum:<{hop.rnum}>, " \
                    f"Domain:<{self.domain}>"
                ref_r = Relation.restrict(db=mmdb, restriction=R, relation="Reference")
                if ref_r.body:
                    P = ('Ref', 'From_class', 'To_class')
                    refs = Relation.project(db=mmdb, attributes=P, svar_name='rhop').body

                    # Generalization
                    if refs[0]['Ref'] == 'G':
                        self.hop_generalization(refs=refs)
                    else:
                        self.hop_association(refs=refs)
                else:
                    # The perspective must be specified in the next hop
                    self.path_index += 1
                    self.resolve_ordinal_perspective(perspective=self.path.hops[self.path_index].name)

            self.path_index += 1

        if self.dest_class != self.class_cursor:
            # Path does not reach destination
            pass

        # Now we can populate the path
        self.populate()

        return self.action_id, Flow_ap(fid=self.dest_fid, content=Content.INSTANCE, tname=self.dest_class,
                                       max_mult=self.mult)

    def populate(self):
        """
        Populate the Traverse Statement, Path and all Hops
        """
        self.name = self.name.rstrip('/')  # Remove trailing '/' from the path name
        # Create a Traverse Action and Path
        Transaction.open(db=mmdb, name=tr_Traverse)
        _logger.info(f"OPEN > {mmdb}:{tr_Traverse}")
        self.action_id = Action.populate(tr=tr_Traverse, anum=self.anum, domain=self.domain, action_type="traverse")
        # Create the Traverse action destination flow (the output for R930)
        self.dest_fid = Flow.populate_instance_flow(cname=self.dest_class, anum=self.anum,
                                                    domain=self.domain, label=None,
                                                    single=True if self.mult == MaxMult.ONE else False).fid

        _logger.info(f"INSERT Traverse action output Flow: ["
                     f"{self.domain}:{self.dest_class}:{self.activity_path.split(':')[-1]}"
                     f":{self.dest_fid}]")
        Relvar.insert(db=mmdb, tr=tr_Traverse, relvar='Traverse_Action', tuples=[
            Traverse_Action_i(ID=self.action_id, Activity=self.anum, Domain=self.domain, Path=self.name,
                              Source_flow=self.input_instance_flow.fid, Destination_flow=self.dest_fid)
        ])
        Relvar.insert(db=mmdb, tr=tr_Traverse, relvar='Path', tuples=[
            Path_i(Name=self.name, Domain=self.domain, Dest_class=self.dest_class)
        ])

        # Get the next action ID
        # Then process each hop
        for number, h in enumerate(self.hops, start=1):
            # Call method to populate this particular kind of type of hop (straight, gen, to assoc, etc)
            params = vars(h).copy()
            params.pop("hoptype")
            params["number"] = number
            h.hoptype(**params)
            # h.hoptype(number=number, to_class=h.to_class, rnum=h.rnum)
        Transaction.execute(db=mmdb, name=tr_Traverse)
        _logger.info(f"EXECUTED > {mmdb}:{tr_Traverse}")

    def validate_rel(self, rnum: str):
        rel = f"Rnum:<{rnum}>, Domain:<{self.domain}>"
        if not Relation.restrict(db=mmdb, restriction=rel, relation="Relationship").body:
            _logger.error(f"Undefined Rnum {rnum} in Domain {self.domain}")
            raise UndefinedRelationship(rnum=rnum, domain=self.domain)

    def ordinal_hop(cls, cname: str, ascending: bool):
        _logger.info("ACTION:Traverse - Populating an ordinal hop")

    def symmetric_hop(cls, cname: str):
        _logger.info("ACTION:Traverse - Populating a circular symmetric hop")

    def asymmetric_circular_hop(self, cname: str, side: str):
        _logger.info("ACTION:Traverse - Populating an asymmetric circular hop")

    def from_symmetric_association_class(self, *, number: int, run: str, rnum: str):
        _logger.info("ACTION:Traverse - Populating a from symmetric assoc class hop")

    def from_asymmetric_association_class(self, *, number: int, rnum: str, to_class: str, side: str):
        """
        :param side: Perspective side (T or P)
        :return:
        """
        _logger.info("ACTION:Traverse - Populating a From Asymmetric Assoc Class Hop")
        Relvar.insert(db=mmdb, tr=tr_Traverse, relvar='From_Asymmetric_Association_Class_Hop', tuples=[
            From_Asymmetric_Association_Class_Hop_i(Number=number, Path=self.name, Domain=self.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Traverse, relvar='Association_Class_Hop', tuples=[
            Association_Class_Hop_i(Number=number, Path=self.name, Domain=self.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Traverse, relvar='Association_Hop', tuples=[
            Association_Hop_i(Number=number, Path=self.name, Domain=self.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Traverse, relvar='Hop', tuples=[
            Hop_i(Number=number, Path=self.name, Domain=self.domain, Rnum=rnum, Class_step=to_class)
        ])
        Relvar.insert(db=mmdb, tr=tr_Traverse, relvar='Perspective_Hop', tuples=[
            Perspective_Hop_i(Number=number, Path=self.name, Domain=self.domain, Side=side, Rnum=rnum)
        ])

    def to_association_class(self, *, number: int, rnum: str, to_class: str):
        """

        :param number:
        :param rnum:
        :param to_class:
        :return:
        """
        _logger.info("ACTION:Traverse - Populating a To Association Class Hop")
        Relvar.insert(db=mmdb, tr=tr_Traverse, relvar='To_Association_Class_Hop', tuples=[
            To_Association_Class_Hop_i(Number=number, Path=self.name, Domain=self.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Traverse, relvar='Association_Class_Hop', tuples=[
            Association_Class_Hop_i(Number=number, Path=self.name, Domain=self.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Traverse, relvar='Association_Hop', tuples=[
            Association_Hop_i(Number=number, Path=self.name, Domain=self.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Traverse, relvar='Hop', tuples=[
            Hop_i(Number=number, Path=self.name, Domain=self.domain, Rnum=rnum, Class_step=to_class)
        ])

    def straight_hop(self, *, number: int, rnum: str, to_class: str):
        """
        Populate an instance of Straight HopArgs

        :param number:  Value (1, 2, 3... ) establishing order within a Path, See Hop.Number in the class model
        :param to_class: Hop over to this class
        :param rnum: Across this association
        """
        _logger.info("ACTION:Traverse - Populating a straight hop")
        Relvar.insert(db=mmdb, tr=tr_Traverse, relvar='Straight_Hop', tuples=[
            Straight_Hop_i(Number=number, Path=self.name, Domain=self.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Traverse, relvar='Association_Hop', tuples=[
            Association_Hop_i(Number=number, Path=self.name, Domain=self.domain)
        ])
        Relvar.insert(db=mmdb, tr=tr_Traverse, relvar='Hop', tuples=[
            Hop_i(Number=number, Path=self.name, Domain=self.domain, Rnum=rnum, Class_step=to_class)
        ])

    def to_superclass_hop(self):
        _logger.info("ACTION:Traverse - Populating a to superclass hop")

    def to_subclass_hop(self, sub_class: str):
        _logger.info("ACTION:Traverse - Populating a to subclass hop")

    def is_assoc_class(self, cname: str, rnum: str) -> bool:
        """
        Returns true
        :param cname: Class to investigate
        :param rnum: Class participates in this association
        :return: True of the class is an association class formalizing the specified association
        """
        r = f"Class:<{cname}>, Rnum:<{rnum}>, Domain:<{self.domain}>"
        return bool(Relation.restrict(db=mmdb, restriction=r, relation="Association_Class").body)

    def is_reflexive(self, rnum: str) -> int:
        """
        Is this a reflexive association and, if so, how many perspectives does it have?
        An association with both a T and P perspective is an asymmetric association while
        an association with a single S perspective is a symmetric association

        :param rnum: The association rnum to inspect
        :return: Zero if non-reflexive, 1 if symmetric and 2 if assymmetric reflexive
        """
        # Get all perspectives defined on rnum
        R = f"Rnum:<{rnum}>, Domain:<{self.domain}>"
        perspectives = Relation.restrict(db=mmdb, restriction=R, relation="Perspective")
        if not perspectives.body:
            # Every association relationship defines at least one perspective
            raise UndefinedAssociation(rnum=rnum, domain=self.domain)
        vclasses = Relation.project(db=mmdb, attributes=('Viewed_class',)).body
        # Reflexive if there is both viewed classes are the same (only 1)
        # So, if reflexive, return 1 (S - Symmetric) or 2 (T,P - Assymetric), otherwise 0, non-reflexive
        return len(perspectives.body) if len(vclasses) == 1 else 0

    def reachable_classes(self, rnum: str) -> Set[str]:
        """
        Return a set of all classes reachable on the provided relationship

        :param rnum:
        :return:
        """
        reachable_classes = set()
        R = f"Rnum:<{rnum}>, Domain:<{self.domain}>"
        refs = Relation.restrict(db=mmdb, restriction=R, relation="Reference").body
        for ref in refs:
            reachable_classes.add(ref['To_class'])
            reachable_classes.add(ref['From_class'])
        return reachable_classes

    def resolve_ordinal_perspective(self, perspective: str) -> bool:
        # Search for ordinal rel with the supplied perspective
        # TODO: Update metamodel with two additional identifiers
        R = f"Ranked_class:<{self.class_cursor}>, Domain:<{self.domain}>, " \
            f"(Ascending_perspective:<{perspective}> OR Descending_perspective:<{perspective}>)"
        orel = Relation.restrict(db=mmdb, restriction=R, relation="Ordinal_Relationship").body[0]
        if not orel:
            return False
        self.rel_cursor = orel['Rnum']
        self.ordinal_hop(cname=self.class_cursor, ascending=orel['Ascending_perspective'] == perspective)
        return True

    def hop_generalization(self, refs: List[Dict[str, str]]):
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
            sub_tuples = Relation.project(db=mmdb, attributes=P, relation="rhop").body
            subclasses = {s['From_class'] for s in sub_tuples}
            # The subclass must be specified in the next hop
            self.path_index += 1
            next_hop = self.path.hops[self.path_index]
            if next_hop.name not in subclasses:
                raise NoSubclassInHop(superclass=super_class, rnum=self.rel_cursor, domain=self.domain)
            self.class_cursor = next_hop.name
            self.to_subclass_hop(sub_class=self.class_cursor)
            return
        else:
            # # Superclass to subclass
            self.class_cursor = super_class
            self.to_superclass_hop()
            return

    def hop_association(self, refs: List[Dict[str, str]]):
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
                    self.path_index += 1
                    self.resolve_perspective(phrase=self.path.hops[self.path_index])
                else:
                    # Add a straight hop to the hop list and update the class_cursor to either the to or from class
                    # whichever does not match the class_cursor

                    # Update multiplicity for this hop
                    # We need to look up the Perspective to get the multiplicity
                    # Since this is an R ref (no association class) we just need to specify the
                    # rnum, domain, and viewed class which will be the updated class cursor
                    self.class_cursor = to_class if to_class != self.class_cursor else from_class
                    R = f"Rnum:<{self.rel_cursor}>, Domain:<{self.domain}>, Viewed_class:<{self.class_cursor}>"
                    persp_r = Relation.restrict(db=mmdb, relation='Perspective', restriction=R)
                    if not persp_r.body:
                        # TODO: raise exception
                        return False
                    self.mult = MaxMult.ONE if persp_r.body[0]['Multiplicity'] == '1' else MaxMult.MANY
                    self.hops.append(
                        Hop(hoptype=self.straight_hop, to_class=self.class_cursor, rnum=self.rel_cursor))
                return

            if ref == 'T' or ref == 'P':
                # We are traversing an associative relationship
                # This means that we could be traversing to either the association class
                # or a straight hop to a participating class
                # We already know the association class as the from class. So we need to get both
                # to classes (same class may be on each side in a reflexive)
                # Then we look ahead for the next step which MUST be either a class name
                # or a perspective
                self.path_index += 1
                next_hop = self.path.hops[self.path_index]
                # The next hop must be either a class name or a perspective phrase on the current rel
                if type(next_hop).__name__ == 'R_a':
                    # In other words, it cannot be an rnum
                    raise NeedPerspectiveOrClassToHop(rnum=self.rel_cursor, domain=self.domain)
                # Is the next hop the association class?
                if next_hop.name == from_class:
                    self.class_cursor = from_class
                    # Update multiplicity
                    # First check multiplicity on to_class perspective (same as ref)
                    R = f"Rnum:<{self.rel_cursor}>, Domain:<{self.domain}>, Side:<{ref}>"
                    persp_r = Relation.restrict(db=mmdb, relation='Perspective', restriction=R)
                    if not persp_r.body:
                        # TODO: raise exception
                        return False
                    # Set multiplicity based on the perspective
                    self.mult = MaxMult.ONE if persp_r.body[0]['Multiplicity'] == '1' else MaxMult.MANY
                    # If multiplicity has been set to 1, but associative multiplicty is M, we need to set it as M
                    R = f"Rnum:<{self.rel_cursor}>, Domain:<{self.domain}>, Class:<{self.class_cursor}>"
                    assoc_class_r = Relation.restrict(db=mmdb, relation='Association_Class', restriction=R)
                    if not assoc_class_r.body:
                        # TODO: raise exception
                        return False
                    associative_mult = assoc_class_r.body[0]['Multiplicity']
                    # Associative mult of M overrides a single mult
                    self.mult = MaxMult.MANY if associative_mult == 'M' else self.mult

                    self.name += self.class_cursor + '/'
                    self.hops.append(
                        Hop(hoptype=self.to_association_class, to_class=self.class_cursor, rnum=self.rel_cursor)
                    )
                    return
                elif next_hop.name == to_class:
                    # Asymmetric reflexive hop requires a perspective phrase
                    raise NeedPerspectiveToHop(rnum=self.rel_cursor, domain=self.domain)

                else:
                    # Get the To class of the other (T or P) reference
                    other_ref_name = 'P' if ref == 'T' else 'T'
                    R = f"Ref:<{other_ref_name}>, Rnum:<{self.rel_cursor}>, Domain:<{self.domain}>"
                    other_ref = Relation.restrict(restriction=R, relation="Reference").body
                    if not other_ref:
                        # The model must be currupted somehow
                        raise MissingTorPrefInAssociativeRel(rnum=self.rel_cursor, domain=self.domain)
                    other_participating_class = other_ref[0]['To_class']
                    if next_hop.name == other_participating_class:
                        self.class_cursor = next_hop.name
                        self.straight_hop()
                        return
                    else:
                        # Next hop must be a perspective
                        self.resolve_perspective(phrase=next_hop.name)
                        return

        # T and P reference
        else:
            # Current hop is from an association class
            self.path_index += 1
            next_hop = self.path.hops[self.path_index]
            # Does the next hop match either of the participating classes
            particip_classes = {refs[0]['To_class'], refs[1]['To_class']}
            if next_hop.name in particip_classes:
                # The particpating class is explicitly named
                self.class_cursor = next_hop.name
                R = f"Viewed_class:<{self.class_cursor}>, Rnum:<{self.rel_cursor}>, Domain:<{self.domain}>"
                Relation.restrict(db=mmdb, relation='Perspective', restriction=R)
                P = ('Side',)
                side = Relation.project(db=mmdb, attributes=P).body[0]['Side']
                self.hops.append(
                    FromAsymAssocHop(hoptype=self.from_asymmetric_association_class, to_class=self.class_cursor,
                                     rnum=self.rel_cursor, side=side)
                )
                return
            else:
                # The next hop needs to be a perspective
                self.resolve_perspective(phrase=next_hop.name)
                return

    def resolve_perspective(self, phrase: str) -> bool:
        """
        Populate hop across the association perspective

        :param phrase:  Perspective phrase text such as 'travels along'
        """
        # Find phrase and ensure that it is on an association that involves the class cursor
        R = f"Phrase:<{phrase}>, Domain:<{self.domain}>"
        r_result = Relation.restrict(db=mmdb, relation='Perspective', restriction=R)
        if not r_result.body:
            return False
        P = ('Side', 'Rnum', 'Viewed_class')
        p_result = Relation.project(db=mmdb, attributes=P)
        side, rnum, viewed_class = map(p_result.body[0].get, P)
        self.rel_cursor = rnum

        # The next hop may be a class name that matches the viewed class
        # If so, we can move the path index forward so that we don't process that class as a separate hop
        try:
            next_hop = self.path.hops[self.path_index + 1]
            if next_hop.name == viewed_class:
                self.path_index += 1
        except (IndexError, AttributeError) as e:
            # We're already processing the last hop in the path, so don't bother advancing the path index or the
            # next hop is an rnum and not a name in which case we certainly don't want to advance the path index
            pass

        # We found the perspective
        # Now we decide which kind of hop to populate
        # We start by asking, "Is this association reflexive?"
        if symmetry := self.is_reflexive(rnum):
            # Symmetry is zero if non-reflexive, otherwise 1:symmetric, 2:asymmetric
            # So it must be either 1 or 2
            if self.class_cursor == viewed_class:
                # The class_cursor is one of the participating classes, i.e. not the association class
                # So it is a Circular HopArgs from-to the same class
                if symmetry == 1:
                    # Populate a symmetric hop
                    self.symmetric_hop(viewed_class)
                else:
                    # Populate an asymmetric hop
                    self.asymmetric_circular_hop(cname=viewed_class, side=side)
                return True  # Circular hop populated
            else:
                # The class_cursor must be the association class
                if symmetry == 1:
                    self.from_symmetric_association_class(rnum=rnum)
                else:
                    self.from_asymmetric_association_class(side=side)
                return True  # From assoc class hop populated
        else:  # Non-reflexive association (non-circular hop)
            # We are either hopping from the association class to a viewed class or
            # from the other participating class to the viewed class
            if self.is_assoc_class(cname=self.class_cursor, rnum=rnum):
                self.from_asymmetric_association_class(side=side)
            else:
                self.class_cursor = viewed_class
                # TODO: Supply params below
                self.straight_hop()
            return True  # Non-reflexive hop to a participating class
