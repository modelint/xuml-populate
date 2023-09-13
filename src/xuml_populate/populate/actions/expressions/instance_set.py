""" instance_set.py """

import logging
from typing import TYPE_CHECKING, Set, Dict, List, Optional
from xuml_populate.populate.actions.traverse_action import TraverseAction
from xuml_populate.populate.mm_class import MMclass
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.actions.select_action import SelectAction
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content, Activity_ap
from pyral.relation import Relation
from pyral.transaction import Transaction
from xuml_populate.exceptions.action_exceptions import NoClassOrInstanceFlowForInstanceSetName,\
    SelectionOnNonInstanceFlow

if TYPE_CHECKING:
    from tkinter import Tk

_logger = logging.getLogger(__name__)


class InstanceSet:
    """
    Entry point for breaking down a parsed Instance Set
    """

    component_flow = None

    @classmethod
    def process(cls, mmdb: 'Tk', input_instance_flow: Flow_ap, iset_components, activity_data: Activity_ap) -> Flow_ap:
        """

        :param mmdb:
        :param input_instance_flow:
        :param iset_components:
        :param activity_data:
        :return:
        """
        cls.component_flow = input_instance_flow  # This will be input to the first component
        domain = activity_data.domain
        anum = activity_data.anum
        for c in iset_components:
            match type(c).__name__:
                case 'PATH_a':
                    # Process the path to create the traverse action and obtain the resultant Class Type name
                    cls.component_flow = TraverseAction.build_path(mmdb, input_instance_flow=cls.component_flow,
                                                                   path=c, activity_data=activity_data)
                case 'N_a':
                    # Check to see if it is a class name
                    if MMclass.exists(cname=c.name, domain=domain):
                        # An encountered class name on the RHS is the source of a multiple instance flow
                        # We create that and set it as the current RHS input flow
                        Transaction.open(mmdb)  # Multiple instance flow from class
                        class_flow_id = Flow.populate_instance_flow(mmdb, cname=c.name, activity=anum,
                                                                    domain=domain, label=None)
                        cls.component_flow = Flow_ap(fid=class_flow_id, content=Content.INSTANCE,
                                                     tname=c.name, max_mult=MaxMult.MANY)
                        Transaction.execute()
                        _logger.info(f"INSERT Class instance flow (assignment): ["
                                     f"{domain}:{c.name}:{activity_data.activity_path.split(':')[-1]}:{class_flow_id}]")
                    else:
                        # Look for a labeled instance flow
                        R = f"Name:<{c.name}>, Activity:<{anum}>, Domain:<{domain}>"
                        label_result = Relation.restrict(mmdb, relation='Labeled_Flow', restriction=R)
                        if label_result.body:
                            # It's a labeled flow, but it must be an instance flow to support selection
                            fid = label_result.body[0]['ID']
                            R = f"ID:<{fid}>, Activity:<{anum}>, Domain:<{domain}>"
                            if_result = Relation.restrict(mmdb, relation='Instance_Flow', restriction=R)
                            if if_result.body:
                                # Okay, it's an instance flow. Now we need the multiplicity on that flow
                                ctype = if_result.body[0]['Class']
                                many_if_result = Relation.restrict(mmdb, relation='Multiple_Instance_Flow', restriction=R)
                                m = MaxMult.MANY if many_if_result.body else MaxMult.ONE
                                cls.component_flow = Flow_ap(fid=fid, content=Content.INSTANCE, tname=ctype, max_mult=m)
                            else:
                                # It's either a table or scalar flow. Scalar's don't support selection.
                                # Selection on tables will be supported, but not yet
                                # TODO: Support labeled table flow selection
                                raise SelectionOnNonInstanceFlow(path=activity_data.activity_path,
                                                                 text=activity_data.scrall_text, x=iset_components.X)
                        else:
                            raise NoClassOrInstanceFlowForInstanceSetName(path=activity_data.activity_path,
                                                                          text=activity_data.scrall_text,
                                                                          x=iset_components.X)
                case 'Selection_a':
                    # Process to populate a select action, the output type does not change
                    # since we are selecting on a known class
                    cls.component_flow = SelectAction.populate(
                        mmdb, input_instance_flow=cls.component_flow, anum=anum, select_agroup=c, domain=domain,
                        activity_path=activity_data.activity_path, scrall_text=activity_data.scrall_text)

        return cls.component_flow
