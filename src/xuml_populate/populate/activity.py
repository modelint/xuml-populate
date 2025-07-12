"""
activity.py – Populate an Activity
"""

# System
import logging
from typing import NamedTuple


# Model Integration
from pyral.relvar import Relvar
from pyral.relation import Relation
from scrall.parse.parser import ScrallParser

# xUML Populate
from xuml_populate.pop_types import SMType
from xuml_populate.config import mmdb
from xuml_populate.populate.flow import Flow
from xuml_populate.populate.method_activity import MethodActivity
from xuml_populate.populate.state_activity import StateActivity
from xuml_populate.populate.element import Element
from xuml_populate.populate.actions.aparse_types import ActivityAP
from xuml_populate.populate.mmclass_nt import (Activity_i, Asynchronous_Activity_i, State_Activity_i,
                                               Synchronous_Activity_i, Lifecycle_Activity_i,
                                               Multiple_Assigner_Activity_i, Single_Assigner_Activity_i)

_logger = logging.getLogger(__name__)

# Temporarily silence the noisy scrall visitor logger
null_handler = logging.NullHandler()
# print(logging.root.manager.loggerDict.keys())
slogger = logging.getLogger("scrall.parse.visitor")
slogger.handlers.clear()
slogger.addHandler(null_handler)
slogger.propagate = False


class Activity:
    """
    Create an Activity relation
    """
    # These dictionaries are for debugging purposes, delete once we get action semantics populated
    sm = {}
    # methods = {}
    operations = {}
    domain = None

    @classmethod
    def valid_param(cls, pname: str, activity: ActivityAP):
        # TODO: Verify that the parameter is in the signature of the specified activity with exception if not
        pass

    @classmethod
    def populate_operation(cls, tr: str, action_text: str, ee: str, subsys: str, domain: str,
                           synchronous: bool) -> str:
        """
        Populate Operation Activity

        :param tr:
        :param action_text:
        :param ee:
        :param subsys:
        :param domain:
        :param synchronous:
        :return:
        """
        Anum = cls.populate(tr=tr, action_text=action_text, subsys=subsys, domain=domain, synchronous=synchronous)
        cls.operations[ee] = ScrallParser.parse_text(scrall_text=action_text, debug=False)
        return Anum

    @classmethod
    def populate(cls, tr: str, action_text: str, subsys: str, domain: str,
                 synchronous: bool) -> str:
        """
        Populate an Activity

        :param tr: The name of the open transaction
        :param action_text: Unparsed scrall text
        :param subsys: The subsystem name
        :param domain: The domain name
        :param synchronous: True if Activity is synchronous
        :return: The Activity number (Anum)
        """
        Anum = Element.populate_unlabeled_subsys_element(tr=tr, prefix='A', subsystem=subsys, domain=domain)
        Relvar.insert(db=mmdb, tr=tr, relvar='Activity', tuples=[
            Activity_i(Anum=Anum, Domain=domain)
        ])
        if synchronous:
            Relvar.insert(db=mmdb, tr=tr, relvar='Synchronous Activity', tuples=[
                Synchronous_Activity_i(Anum=Anum, Domain=domain)
            ])
        else:
            Relvar.insert(db=mmdb, tr=tr, relvar='Asynchronous Activity', tuples=[
                Asynchronous_Activity_i(Anum=Anum, Domain=domain)
            ])
        return Anum

    @classmethod
    def populate_state(cls, tr: str, state: str, state_model: str, sm_type: SMType, actions: str,
                       subsys: str, domain: str, parse_actions: bool) -> str:
        """
        :param tr:  Name of the transaction
        :param state: State name
        :param state_model:  State model name
        :param sm_type:  Lifecycle, Single or Multiple assigner
        :param actions:
        :param subsys:
        :param domain:
        :param parse_actions:
        :return: Anum
        """

        # Parse scrall in this state and add it to temporary sm dictionary
        action_text = ''.join(actions) + '\n'
        if state_model not in cls.sm:
            cls.sm[state_model] = {}
        if parse_actions:
            parsed_activity = ScrallParser.parse_text(scrall_text=action_text, debug=False)
        else:
            parsed_activity = None
        # cls.populate_activity(text=action_text, pa=parsed_activity)

        # Create the Susbystem Element and obtain a unique Anum
        Anum = cls.populate(tr=tr, action_text=action_text, subsys=subsys, domain=domain, synchronous=False)
        cls.sm[state_model][state] = {'anum': Anum, 'sm_type': sm_type, 'parse': parsed_activity[0],
                                      'text': action_text, 'domain': domain}
        Relvar.insert(db=mmdb, tr=tr, relvar='State_Activity', tuples=[
            State_Activity_i(Anum=Anum, Domain=domain)
        ])
        match sm_type:
            case SMType.LIFECYCLE:
                # Populate the executing instance (me) flow
                xi_flow = Flow.populate_instance_flow(cname=state_model, anum=Anum, domain=domain,
                                                      label='me', single=True, activity_tr=tr)
                Relvar.insert(db=mmdb, tr=tr, relvar='Lifecycle_Activity', tuples=[
                    Lifecycle_Activity_i(Anum=Anum, Domain=domain, Executing_instance_flow=xi_flow.fid)
                ])
            case SMType.MA:
                # Populate the executing instance (me) flow
                partition_flow = Flow.populate_instance_flow(cname=state_model, anum=Anum, domain=domain,
                                                             label='partition_instance', single=True, activity_tr=tr)
                Relvar.insert(db=mmdb, tr=tr, relvar='Multiple_Assigner_Activity', tuples=[
                    Multiple_Assigner_Activity_i(Anum=Anum, Domain=domain,
                                                 Partitioning_instance_flow=partition_flow.fid)
                ])
            case SMType.SA:
                Single_Assigner_Activity_i(Anum=Anum, Domain=domain)
        return Anum

    @classmethod
    def pop_xunits(cls, activity_obj):

        signum = None
        xi_flow_id = None
        pi_flow_id = None
        activity_path = None
        domain = activity_obj.domain

        match type(activity_obj).__name__:
            case 'Method':
                _logger.info(f"Populating method execution units: {activity_obj.class_name}.{activity_obj.name}")
                # Look up signature
                R = f"Method:<{activity_obj.name}>, Class:<{activity_obj.class_name}>, Domain:<{domain}>"
                method_sig_r = Relation.restrict(db=mmdb, relation='Method Signature', restriction=R)
                if not method_sig_r.body:
                    # TODO: raise exception here
                    pass
                signum = method_sig_r.body[0]['SIGnum']

                # Look up xi flow
                R = f"Name:<{activity_obj.name}>, Class:<{activity_obj.class_name}>, Domain:<{domain}>"
                method_r = Relation.restrict(db=mmdb, relation='Method', restriction=R)
                if not method_r.body:
                    # TODO: raise exception here
                    pass
                xi_flow_id = method_r.body[0]['Executing_instance_flow']
                activity_path = f"{domain}:{activity_obj.class_name}:{activity_obj.name}.mtd"
                pass
            case 'State':
                _logger.info(f"Populating state activity execution units: {activity_obj.state_model}")
                # Look up signature
                R = f"State_model:<{activity_obj.state_model}>, Domain:<{activity_obj.domain}>"
                state_sig_r = Relation.restrict(db=mmdb, relation='State Signature', restriction=R)
                if not state_sig_r.body:
                    # TODO: raise exception here
                    pass
                signum = state_sig_r.body[0]['SIGnum']

                match activity_obj.sm_type:
                    case SMType.LIFECYCLE:
                        # Look up the executign instance (xi) flow
                        R = f"Anum:<{activity_obj.anum}>, Domain:<{domain}>"
                        result = Relation.restrict(db=mmdb, relation='Lifecycle Activity', restriction=R)
                        if not result.body:
                            # TODO: raise exception here
                            pass
                        xi_flow_id = result.body[0]['Executing_instance_flow']
                    case SMType.MA:
                        # Look up the partitioning instance (pi) flow
                        R = f"Anum:<{activity_obj.anum}>, Domain:<{domain}>"
                        result = Relation.restrict(db=mmdb, relation='Multiple Assigner Activity', restriction=R)
                        if not result.body:
                            # TODO: raise exception here
                            pass
                        pi_flow_id = result.body[0]['Paritioning_instance_flow']
                    case SMType.SA:
                        pass  # No xi or pi flow (rnum only, no associated instance)

                activity_path = f"{domain}:{activity_obj.state_model}.xsm"
                activity_detail = ActivityAP(anum=activity_obj.anum, domain=domain,
                                             cname=None, sname=activity_obj.state_name, state_model=activity_obj.state_model,
                                             smtype=activity_obj.sm_type, eename=None, opname=None,
                                             xiflow=xi_flow_id, piflow=pi_flow_id,
                                             activity_path=activity_obj, scrall_text=activity_obj.activity_text)

            case _:
                pass

        # aparse = self.activity_data['parse']
        # activity_detail = ActivityAP(anum=self.activity_data['anum'], domain=self.domain,
        #                               cname=self.class_name, sname=None, state_model=None, smtype=None, eename=None,
        #                               opname=self.name, xiflow=xi_flow_id, piflow=None,
        #                               activity_path=method_path, scrall_text=aparse[1])
        #
        # # seq_flows = {}  TODO: We don't appear to use these
        # # seq_labels = set()
        #
        # # Here we process each statement set in the Method (Activity)
        # for count, xunit in enumerate(aparse[0]):  # Use count for debugging
        #     c = count + 1
        #     if type(xunit.statement_set.statement).__name__ == 'Output_Flow_a':
        #         # This is the statement set that returns the Method's value
        #         ExecutionUnit.process_synch_output(activity_data=activity_detail,
        #                                            synch_output=xunit.statement_set.statement)
        #     else:
        #         # This is a statement set that does not return the Method's value
        #         boundary_actions = ExecutionUnit.process_method_statement_set(
        #             activity_data=activity_detail, statement_set=xunit.statement_set)
        #
        #     # Process any input or output tokens
        #     # if output_tk not in seq_flows:
        #     # Get a set of terminal actions
        #     # seq_flows[output_tk] = {'from': [terminal_actions], 'to': []}
        # pass

    @classmethod
    def process_execution_units(cls):
        """
        Process each Scrall Execution Unit for all Activities (Method, State, and Synchronous Operation)
        """
        # Populate each State Activity
        for state_model, sm in cls.sm.items():
            for state_name, activity_parse in sm.items():
                sa = StateActivity(state_name=state_name, state_model=state_model,
                                   activity_data=activity_parse, domain=cls.domain)
                pass

    # TODO: Populate all operation activities
