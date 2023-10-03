"""
activity.py – Populate an Activity
"""

import logging
from pyral.relvar import Relvar
from pyral.relation import Relation
from xuml_populate.populate.element import Element
from scrall.parse.parser import ScrallParser
from xuml_populate.populate.actions.aparse_types import Activity_ap, Boundary_Actions
from xuml_populate.populate.xunit import ExecutionUnit
from xuml_populate.exceptions.action_exceptions import ActionException
from xuml_populate.populate.mmclass_nt import Activity_i, Asynchronous_Activity_i, \
    State_Activity_i, Synchronous_Activity_i

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
    def populate_method(cls, mmdb: str, tr: str, action_text: str, cname: str, method: str,
                        subsys: str, domain: str) -> str:
        """
        Populate Synchronous Activity for Method

        :param mmdb: The metamodel db name
        :param tr: The name of the open transaction
        :param cname: The class name
        :param method: The method name
        :param action_text: Unparsed scrall text
        :param subsys: The subsystem name
        :param domain: The domain name
        :return: The Activity number (Anum)
        """
        cls.domain = domain
        Anum = cls.populate(mmdb, tr=tr, action_text=action_text, subsys=subsys, domain=domain, synchronous=True)
        if cname not in cls.methods:
            cls.methods[cname] = {
                method: {'anum': Anum, 'domain': domain, 'text': action_text, 'parse': None}}
        else:
            cls.methods[cname][method]['anum'] = Anum
            cls.methods[cname][method]['domain'] = domain
            cls.methods[cname][method]['text'] = action_text
        # Parse the scrall and save for later population
        cls.methods[cname][method]['parse'] = ScrallParser.parse_text(scrall_text=action_text, debug=False)
        return Anum

    @classmethod
    def populate_operation(cls, mmdb: str, tr: str, action_text: str, ee: str, subsys: str, domain: str,
                           synchronous: bool) -> str:
        """
        Populate Operation Activity

        :param action_text:
        :param ee:
        :param subsys:
        :param domain:
        :param synchronous:
        :param mmdb:
        :return:
        """
        Anum = cls.populate(mmdb, tr=tr, action_text=action_text, subsys=subsys, domain=domain, synchronous=synchronous)
        cls.operations[ee] = ScrallParser.parse_text(scrall_text=action_text, debug=False)
        return Anum

    @classmethod
    def populate(cls, mmdb: str, tr: str, action_text: str, subsys: str, domain: str,
                 synchronous: bool) -> str:
        """
        Populate an Activity

        :param mmdb: The metamodel db name
        :param tr: The name of the open transaction
        :param action_text: Unparsed scrall text
        :param subsys: The subsystem name
        :param domain: The domain name
        :param synchronous: True if Activity is synchronous
        :return: The Activity number (Anum)
        """
        Anum = Element.populate_unlabeled_subsys_element(mmdb, tr=tr, prefix='A', subsystem=subsys, domain=domain)
        Relvar.insert(mmdb, tr=tr, relvar='Activity', tuples=[
            Activity_i(Anum=Anum, Domain=domain)
        ])
        if synchronous:
            Relvar.insert(mmdb, tr=tr, relvar='Synchronous_Activity', tuples=[
                Synchronous_Activity_i(Anum=Anum, Domain=domain)
            ])
        else:
            Relvar.insert(mmdb, tr=tr, relvar='Asynchronous_Activity', tuples=[
                Asynchronous_Activity_i(Anum=Anum, Domain=domain)
            ])
        return Anum

    @classmethod
    def populate_state(cls, mmdb: str, tr: str, state: str, state_model: str, actions: str,
                       subsys: str, domain: str) -> str:
        """
        :param mmdb:
        :param state:
        :param state_model:
        :param actions:
        :param subsys:
        :param domain:
        :return:
        """

        # Parse scrall in this state and add it to temporary sm dictionary
        action_text = ''.join(actions) + '\n'
        if state_model not in cls.sm:
            cls.sm[state_model] = {}
        parsed_activity = ScrallParser.parse_text(scrall_text=action_text, debug=False)
        cls.sm[state_model][state] = parsed_activity  # To subsys_parse parsed actions for debugging
        # cls.populate_activity(text=action_text, pa=parsed_activity)

        # Create the Susbystem Element and obtain a unique Anum
        Anum = cls.populate(mmdb, tr=tr, action_text=action_text, subsys=subsys, domain=domain, synchronous=False)
        Relvar.insert(mmdb, tr=tr, relvar='State_Activity', tuples=[
            State_Activity_i(Anum=Anum, State=state, State_model=state_model, Domain=domain)
        ])
        return Anum

    @classmethod
    def process_execution_units(cls, mmdb: str):
        """
        Process each Scrall Execution Unit for all Activities (Method, State, and Synchronous Operation)
        """
        # Populate each (Method) Activity
        for class_name, method_data in cls.methods.items():
            for method_name, activity_data in method_data.items():

                _logger.info(f"Populating method execution units: {class_name}.{method_name}")
                # Look up signature
                R = f"Method:<{method_name}>, Class:<{class_name}>, Domain:<{cls.domain}>"
                result = Relation.restrict(mmdb, relation='Method_Signature', restriction=R)
                if not result.body:
                    # TODO: raise exception here
                    pass
                signum = result.body[0]['SIGnum']

                # Look up xi flow
                R = f"Name:<{method_name}>, Class:<{class_name}>, Domain:<{cls.domain}>"
                result = Relation.restrict(mmdb, relation='Method', restriction=R)
                if not result.body:
                    # TODO: raise exception here
                    pass
                xi_flow_id = result.body[0]['Executing_instance_flow']
                method_path = f"{cls.domain}:{class_name}:{method_name}.mtd"

                aparse = activity_data['parse']
                activity_data = Activity_ap(anum=activity_data['anum'], domain=cls.domain,
                                            cname=class_name, sname=None, eename=None,
                                            xiflow=xi_flow_id, activity_path=method_path, scrall_text=aparse[1])
                seq_flows = {}
                seq_labels = set()
                for xunit in aparse[0]:
                    match type(xunit).__name__:
                        case 'Execution_Unit_a':
                            boundary_actions = ExecutionUnit.process_method_statement_set(
                                mmdb=mmdb, activity_data=activity_data, statement_set=xunit.statement_set)
                        case 'Output_Flow_a':
                            ExecutionUnit.process_synch_output(mmdb=mmdb, activity_data=activity_data, synch_output=xunit)
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

    # @classmethod
    # def process_statements(cls, mmdb: 'Tk'):
    #     """
    #     Process each Scrall statement in the Method
    #     """
    #     # Populate all method activities
    #     for cname, method_data in cls.methods.items():
    #         for method, activity_data in method_data.items():
    #             _logger.info(f"Populating anum for method: {cname}.{method}")
    #             aparse = activity_data['parse']
    #             for a in aparse[0]:
    #                 Statement.populate_method(mmdb=mmdb, cname=cname, method=method, anum=activity_data['anum'],
    #                                           domain=activity_data['domain'], aparse=a, scrall_text=aparse[1])
    #
    #     pass
    # Populate all state activities
    # Populate all operation activities
