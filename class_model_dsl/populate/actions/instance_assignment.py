"""
instance_assignment.py – Break an instance set generator into one or more components
"""

import logging
from typing import TYPE_CHECKING, Set, Dict, List, Optional
from class_model_dsl.populate.actions.traverse_action import TraverseAction
from class_model_dsl.populate.actions.select_action import SelectAction
from class_model_dsl.populate.mm_class import MMclass
from class_model_dsl.populate.flow import Flow

from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction

from collections import namedtuple

Iflow = namedtuple("Iflow", "id cname")
"""Instance flow descriptor"""
Tflow = namedtuple("Tflow", "id table_type")
"""Table flow descriptor"""

if TYPE_CHECKING:
    from tkinter import Tk

_logger = logging.getLogger(__name__)

class InstanceAssignment:
    """
    Break down a Scrall instance assignment statement into action semantics and populate them

    The lhs (left hand side) will be a labeled Instance Flow. It may or may not have an explicit Class Type.
    The card (cardinality) is either 1c or Mc (one or many conditional). It determines whether the lhs Instance
    Flow is Single or Multiple.

    The rhs (right hand side) is an expression that outputs an instance set of some Class Type. If the lhs is
    explicitly typed, we throw an exception if the rhs and lhs types do not match.

    For now we limit the expression to a chain of the following components:
        * create action
        * traversal action
        * instance flow
        * method or operation output of Class Type
        * selection output

    We say 'chain' since the output of one can feed into the input of the next yielding a final output at the end
    of the chain. It is this final output that determines the type (or type conflict) with the lhs Instance Flow

    We say 'for now' because this chain does not yet take into account instance set operations (add, subtract, union,
    etc). The Scrall syntax will later be udpated to accommodate such expressions.
    """

    input_flow = None

    @classmethod
    def process(cls, mmdb: 'Tk', anum:str, cname:str, domain:str, inst_assign_parse, xi_flow_id:str, signum:str):
        """
        Given a parsed instance set expression, populate each component action
        and return the resultant Class Type name

        We'll need an initial flow and we'll need to create intermediate instance flows to connect the components.
        The final output flow must be an instance flow. The associated Class Type determines the type of the
        assignment which must match any explicit type.

        :param mmdb: The metamodel db
        :param cname: The class (for an operation it is the proxy class)
        :param domain: In this domain
        :param anum: The Activity Number
        :param inst_assign_parse: A parsed instance assignment
        :param xi_flow_id: The ID of the executing instance flow (the instance executing this activity)
        :param signum: The signature number so we can look up any input parameters
        """
        lhs = inst_assign_parse.lhs
        card = inst_assign_parse.card
        rhs = inst_assign_parse.rhs
        ctype = cname # Initialize with the instance/ee class
        input_flow = Iflow(id=xi_flow_id, cname=cname)

        for c in rhs.components:
            match type(c).__name__:
                case 'PATH_a':
                    # Process the path to create the traverse action and obtain the resultant Class Type name
                    ctype = TraverseAction.build_path(mmdb, anum=anum, source_class=ctype, source_flow=input_flow.id,
                                                      domain=domain, path=c)
                case 'N_a':
                    # Check to see if it is a class name
                    if MMclass.exists(cname=c.name, domain=domain):
                        # An encountered class name on the RHS is the source of a multiple instance flow
                        # We create that and set it as the current RHS input flow
                        Transaction.open(mmdb)
                        cls.input_flow = Iflow(id=Flow.populate_instance_flow(
                            mmdb, cname=c.name, activity=anum, domain=domain, label=None), cname=c.name)
                        Transaction.execute()
                    else:
                        # Look for a labeled instance flow
                        R = f"Name:<{c.name}>, Activity:<{anum}>, Domain:<{domain}>"
                        result = Relation.restrict3(mmdb, relation='Label', restriction=R)
                        if result.body:
                            # Labeled flow found
                            cls.input_flow = result.body[0]['Flow']
                        else:
                            pass
                case 'Selection_a':
                    # Process to populate a select action, the output type does not change
                    # since we are selecting on a known class
                    SelectAction.populate(mmdb, input_flow=cls.input_flow, select_agroup=c, domain=domain)


        # Process LHS after all components have been processed
        output_flow_label = lhs.name.name
        if lhs.exp_type and lhs.exp_type != ctype:
            # Raise assignment type mismatch exception
            pass
        Transaction.open(mmdb)
        Flow.populate_instance_flow(mmdb, cname=ctype, activity=anum, domain=domain,label=output_flow_label,
                                    single=True if card == '1c' else False)
        Transaction.execute()
        Relvar.printall(mmdb)
