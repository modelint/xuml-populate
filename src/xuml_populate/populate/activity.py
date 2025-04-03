"""
anum.py – Populate an Activity
"""

# System
import logging

# Model Integration
from pyral.relvar import Relvar
from pyral.relation import Relation
from scrall.parse.parser import ScrallParser

# xUML Populate
from xuml_populate.config import mmdb
from xuml_populate.populate.element import Element
from xuml_populate.populate.actions.aparse_types import Activity_ap, Boundary_Actions
from xuml_populate.populate.xunit import ExecutionUnit
from xuml_populate.exceptions.action_exceptions import ActionException
from xuml_populate.populate.mmclass_nt import (Activity_i, Asynchronous_Activity_i, State_Activity_i,
                                               Synchronous_Activity_i)

_logger = logging.getLogger(__name__)

class Activity:
    """
    Create an Activity relation
    """
    # These dictionaries are for debugging purposes, delete once we get action semantics populated
    sm = {}
    methods = {}
    operations = {}
    domain = None

    @classmethod
    def valid_param(cls, pname: str, activity: Activity_ap):
        # TODO: Verify that the parameter is in the signature of the specified activity with exception if not
        pass

    @classmethod
    def populate_method(cls, tr: str, action_text: str, cname: str, method: str,
                        subsys: str, domain: str, parse_actions: bool) -> str:
        """
        Populate Synchronous Activity for Method

        :param tr: The name of the open transaction
        :param cname: The class name
        :param method: The method name
        :param action_text: Unparsed scrall text
        :param subsys: The subsystem name
        :param domain: The domain name
        :return: The Activity number (Anum)
        """
        cls.domain = domain
        Anum = cls.populate(tr=tr, action_text=action_text, subsys=subsys, domain=domain, synchronous=True)
        if cname not in cls.methods:
            cls.methods[cname] = {
                method: {'anum': Anum, 'domain': domain, 'text': action_text, 'parse': None}}
        else:
            cls.methods[cname][method] = {'anum': Anum, 'domain': domain, 'text': action_text, 'parse': None}
        # Parse the scrall and save for later population
        if parse_actions:
            cls.methods[cname][method]['parse'] = ScrallParser.parse_text(scrall_text=action_text, debug=False)
        else:
            cls.methods[cname][method]['parse'] = None
        return Anum

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
            Relvar.insert(db=mmdb, tr=tr, relvar='Synchronous_Activity', tuples=[
                Synchronous_Activity_i(Anum=Anum, Domain=domain)
            ])
        else:
            Relvar.insert(db=mmdb, tr=tr, relvar='Asynchronous_Activity', tuples=[
                Asynchronous_Activity_i(Anum=Anum, Domain=domain)
            ])
        return Anum

    @classmethod
    def populate_state(cls, tr: str, state: str, state_model: str, actions: str,
                       subsys: str, domain: str, parse_actions: bool) -> str:
        """
        :param tr:
        :param state:
        :param state_model:
        :param actions:
        :param subsys:
        :param domain:
        :param parse_actions:
        :return:
        """

        # Parse scrall in this state and add it to temporary sm dictionary
        action_text = ''.join(actions) + '\n'
        if state_model not in cls.sm:
            cls.sm[state_model] = {}
        if parse_actions:
            parsed_activity = ScrallParser.parse_text(scrall_text=action_text, debug=False)
        else:
            parsed_activity = None
        cls.sm[state_model][state] = parsed_activity  # To subsys_parse parsed actions for debugging
        # cls.populate_activity(text=action_text, pa=parsed_activity)

        # Create the Susbystem Element and obtain a unique Anum
        Anum = cls.populate(tr=tr, action_text=action_text, subsys=subsys, domain=domain, synchronous=False)
        Relvar.insert(db=mmdb, tr=tr, relvar='State_Activity', tuples=[
            State_Activity_i(Anum=Anum, State=state, State_model=state_model, Domain=domain)
        ])
        return Anum

    @classmethod
    def process_execution_units(cls):
        """
        Process each Scrall Execution Unit for all Activities (Method, State, and Synchronous Operation)
        """
        # Populate each (Method) Activity
        for class_name, method_data in cls.methods.items():
            for method_name, activity_data in method_data.items():

                _logger.info(f"Populating method execution units: {class_name}.{method_name}")
                # Look up signature
                R = f"Method:<{method_name}>, Class:<{class_name}>, Domain:<{cls.domain}>"
                result = Relation.restrict(db=mmdb, relation='Method_Signature', restriction=R)
                if not result.body:
                    # TODO: raise exception here
                    pass
                signum = result.body[0]['SIGnum']

                # Look up xi flow
                R = f"Name:<{method_name}>, Class:<{class_name}>, Domain:<{cls.domain}>"
                result = Relation.restrict(db=mmdb, relation='Method', restriction=R)
                if not result.body:
                    # TODO: raise exception here
                    pass
                xi_flow_id = result.body[0]['Executing_instance_flow']
                method_path = f"{cls.domain}:{class_name}:{method_name}.mtd"

                aparse = activity_data['parse']
                activity_data = Activity_ap(anum=activity_data['anum'], domain=cls.domain,
                                            cname=class_name, sname=None, eename=None, opname=method_name,
                                            xiflow=xi_flow_id, activity_path=method_path, scrall_text=aparse[1])
                seq_flows = {}
                seq_labels = set()
                # for xunit in aparse[0]:
                for count, xunit in enumerate(aparse[0]):  # Use count for debugging
                    c = count+1
                    # print(f"Processing statement: {c}")
                    match type(xunit).__name__:
                        case 'Execution_Unit_a':
                            boundary_actions = ExecutionUnit.process_method_statement_set(
                                activity_data=activity_data, statement_set=xunit.statement_set)
                        case 'Output_Flow_a':
                            ExecutionUnit.process_synch_output(activity_data=activity_data, synch_output=xunit)
                            pass
                        case _:
                            _logger.error(f"Execution unit [{xunit}] is neither a statement set nor a "
                                              f"synch output flow")
                            raise ActionException
                    # Obtain set of initial and terminal action ids

                    # Process any input or output tokens
                    # if output_tk not in seq_flows:
                    # Get a set of terminal actions
                    # seq_flows[output_tk] = {'from': [terminal_actions], 'to': []}
                    pass

        pass
    # TODO: Populate all state activities
    # TODO: Populate all operation activities
