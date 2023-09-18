""" instance_set.py """

import logging
from typing import TYPE_CHECKING
from xuml_populate.populate.actions.traverse_action import TraverseAction
from xuml_populate.populate.mm_class import MMclass
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.actions.select_action import SelectAction
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content, Activity_ap, Boundary_Actions
from pyral.relation import Relation
from pyral.transaction import Transaction
from xuml_populate.exceptions.action_exceptions import NoClassOrInstanceFlowForInstanceSetName, \
    SelectionOnScalarFlow

if TYPE_CHECKING:
    from tkinter import Tk

_logger = logging.getLogger(__name__)


class InstanceSet:
    """
    Entry point for breaking down a parsed Instance Set
    """

    component_flow = None
    initial_action = None
    final_action = None

    @classmethod
    def process(cls, mmdb: 'Tk', input_instance_flow: Flow_ap, iset_components, activity_data: Activity_ap) -> (
            str, str, Flow_ap):
        """

        :param mmdb:
        :param input_instance_flow:
        :param iset_components:
        :param activity_data:
        :return: The initial action id, the final action id and the output instance flow
        """
        cls.initial_action = None
        cls.final_action = None
        cls.component_flow = input_instance_flow  # This will be input to the first component
        domain = activity_data.domain
        anum = activity_data.anum
        first_action = True  # We use this to recognize the initial action
        for count, comp in enumerate(iset_components):
            # We use the count to recognize the final action
            match type(comp).__name__:
                case 'PATH_a':
                    # Process the path to create the traverse action and obtain the resultant output instance flow
                    aid, cls.component_flow = TraverseAction.build_path(mmdb, input_instance_flow=cls.component_flow,
                                                                        path=comp, activity_data=activity_data)
                    # Data flow to/from actions within the instance_set
                    if first_action:
                        # For the first component, there can be dflow input from another action
                        cls.initial_action = aid
                        first_action = False  # The first action has been encountered and recognized as initial
                    if count == len(iset_components)-1:
                        # For the last component, there can be no dflow output to another action
                        cls.final_action = aid
                case 'N_a':
                    # Check to see if it is a class name
                    if MMclass.exists(cname=comp.name, domain=domain):
                        # An encountered class name on the RHS is the source of a multiple instance flow
                        # We create that and set it as the current RHS input flow
                        Transaction.open(mmdb)  # Multiple instance flow from class
                        class_flow_id = Flow.populate_instance_flow(mmdb, cname=comp.name, activity=anum,
                                                                    domain=domain, label=None)
                        cls.component_flow = Flow_ap(fid=class_flow_id, content=Content.INSTANCE,
                                                     tname=comp.name, max_mult=MaxMult.MANY)
                        Transaction.execute()
                        _logger.info(f"INSERT Class instance flow (assignment): ["
                                     f"{domain}:{comp.name}:{activity_data.activity_path.split(':')[-1]}:{class_flow_id}]")
                    else:
                        # Look for a labeled instance flow
                        R = f"Name:<{comp.name}>, Activity:<{anum}>, Domain:<{domain}>"
                        label_result = Relation.restrict(mmdb, relation='Labeled_Flow', restriction=R)
                        if label_result.body:
                            # It's a labeled flow, but it must be an instance flow to support selection
                            fid = label_result.body[0]['ID']
                            R = f"ID:<{fid}>, Activity:<{anum}>, Domain:<{domain}>"
                            if_result = Relation.restrict(mmdb, relation='Instance_Flow', restriction=R)
                            if if_result.body:
                                # Okay, it's an instance flow. Now we need the multiplicity on that flow
                                ctype = if_result.body[0]['Class']
                                many_if_result = Relation.restrict(mmdb, relation='Multiple_Instance_Flow',
                                                                   restriction=R)
                                m = MaxMult.MANY if many_if_result.body else MaxMult.ONE
                                cls.component_flow = Flow_ap(fid=fid, content=Content.INSTANCE, tname=ctype, max_mult=m)
                            else:
                                fid = label_result.body[0]['ID']
                                R = f"ID:<{fid}>, Activity:<{anum}>, Domain:<{domain}>"
                                rf_result = Relation.restrict(mmdb, relation='Relation_Flow', restriction=R)
                                if rf_result.body:
                                    # It's a table flow. Now we need the multiplicity on that flow
                                    ttype = rf_result.body[0]['Type']
                                    ntuples = Relation.restrict(mmdb, relation='Table_Flow',
                                                                       restriction=R)
                                    m = MaxMult.MANY if ntuples.body else MaxMult.ONE
                                    cls.component_flow = Flow_ap(fid=fid, content=Content.TABLE, tname=ttype,
                                                                 max_mult=m)
                                    pass
                                else:
                                    # It's a Scalar Flow
                                    # TODO: Support labeled table flow selection
                                    raise SelectionOnScalarFlow(path=activity_data.activity_path,
                                                                     text=activity_data.scrall_text, x=iset_components.X)
                        else:
                            raise NoClassOrInstanceFlowForInstanceSetName(path=activity_data.activity_path,
                                                                          text=activity_data.scrall_text,
                                                                          x=iset_components.X)
                case 'Selection_a':
                    # Process to populate a select action, the output type does not change
                    # since we are selecting on a known class
                    aid, cls.component_flow = SelectAction.populate(
                        mmdb, input_instance_flow=cls.component_flow, select_agroup=comp, activity_data=activity_data)

                    cls.final_action = aid
        return cls.initial_action, cls.final_action, cls.component_flow
