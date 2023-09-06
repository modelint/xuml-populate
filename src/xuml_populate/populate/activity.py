"""
anum.py – Populate an anum instance in PyRAL
"""

import logging
from pyral.relvar import Relvar
from xuml_populate.populate.element import Element
from scrall.parse.parser import ScrallParser
from xuml_populate.populate.exec_unit import ExecutionUnit
# from xuml_populate.populate.statement import Statement
from typing import TYPE_CHECKING
from xuml_populate.populate.mmclass_nt import Activity_i, Asynchronous_Activity_i,\
    State_Activity_i, Synchronous_Activity_i

if TYPE_CHECKING:
    from tkinter import Tk

class Activity:
    """
    Create an Activity relation
    """
    _logger = logging.getLogger(__name__)

    # These dictionaries are for debugging purposes, delete once we get action semantics populated
    sm = {}
    methods = {}
    operations = {}

    @classmethod
    def populate_method(cls, mmdb: 'Tk', action_text: str, class_name: str, method_name: str, subsys_name: str, domain_name: str) -> str:
        """
        Populate Synchronous Activity for Method
        :param method_name:
        :param mmdb:
        :param action_text: Unparsed scrall text
        :param class_name:
        :param subsys_name:
        :param domain_name:
        :return: Anum
        """
        Anum = cls.populate(mmdb, action_text, subsys_name, domain_name, synchronous=True)
        if class_name not in cls.methods:
            cls.methods[class_name] = {method_name: {'anum': Anum, 'domain': domain_name, 'text': action_text, 'parse': None}}
        else:
            cls.methods[class_name][method_name]['anum'] = Anum
            cls.methods[class_name][method_name]['domain'] = domain_name
            cls.methods[class_name][method_name]['text'] = action_text
        # Parse the scrall and save for later population
        cls.methods[class_name][method_name]['parse'] = ScrallParser.parse_text(scrall_text=action_text, debug=False)
        return Anum

    @classmethod
    def populate_operation(cls, mmdb: 'Tk', action_text:str, ee_name: str, subsys_name: str, domain_name: str,
                           synchronous: bool) -> str:
        """
        Populate Operation Activity

        :param action_text:
        :param ee_name:
        :param subsys_name:
        :param domain_name:
        :param synchronous:
        :param mmdb:
        :return:
        """
        Anum = cls.populate(mmdb, action_text, subsys_name, domain_name, synchronous)
        cls.operations[ee_name] = ScrallParser.parse_text(scrall_text=action_text, debug=False)
        return Anum

    @classmethod
    def populate(cls, mmdb: 'Tk', action_text:str, subsys_name: str, domain_name: str,
                 synchronous: bool) -> str:
        """
        Populate an Activity Operation

        :param mmdb:
        :param action_text:
        :param subsys_name:
        :param domain_name:
        :param synchronous:
        :return:
        """
        Anum = Element.populate_unlabeled_subsys_element(mmdb,
                                                         prefix='A',
                                                         subsystem_name=subsys_name, domain_name=domain_name)
        Relvar.insert(relvar='Activity', tuples=[
            Activity_i(Anum=Anum, Domain=domain_name)
        ])
        if synchronous:
            Relvar.insert(relvar='Synchronous_Activity', tuples=[
                Synchronous_Activity_i(Anum=Anum, Domain=domain_name)
            ])
        else:
            Relvar.insert(relvar='Asynchronous_Activity', tuples=[
                Asynchronous_Activity_i(Anum=Anum, Domain=domain_name)
            ])
        return Anum

    @classmethod
    def populate_state(cls, mmdb: 'Tk', state: str, state_model: str, actions: str,
                       subsys_name: str, domain_name: str) -> str:
        """
        :param mmdb:
        :param state:
        :param state_model:
        :param actions:
        :param subsys_name:
        :param domain_name:
        :return:
        """

        # Parse scrall in this state and add it to temporary sm dictionary
        action_text = ''.join(actions) + '\n'
        if state_model not in cls.sm:
            cls.sm[state_model] = {}
        parsed_activity = ScrallParser.parse_text(scrall_text=action_text, debug=False)
        cls.sm[state_model][state] = parsed_activity # To subsys_parse parsed actions for debugging
        # cls.populate_activity(text=action_text, pa=parsed_activity)

        # Create the Susbystem Element and obtain a unique Anum
        Anum = cls.populate(mmdb, action_text, subsys_name, domain_name, synchronous=False)
        Relvar.insert(relvar='State_Activity', tuples=[
            State_Activity_i(Anum=Anum, State=state, State_model=state_model, Domain=domain_name)
        ])
        return Anum

    @classmethod
    def process_execution_units(cls, mmdb: 'Tk'):
        """
        Process each Scrall Execution Unit in the Method
        """
        # Populate all method activities
        for class_name, method_data in cls.methods.items():
            for method_name, activity_data in method_data.items():
                cls._logger.info(f"Populating anum for method: {class_name}.{method_name}")
                aparse = activity_data['parse']
                for xunit in aparse[0]:
                    ExecutionUnit.process_method(mmdb=mmdb, cname=class_name, method=method_name,
                                                 anum=activity_data['anum'], xunit=xunit,
                                                 domain=activity_data['domain'], scrall_text=aparse[1])
        pass

    # @classmethod
    # def process_statements(cls, mmdb: 'Tk'):
    #     """
    #     Process each Scrall statement in the Method
    #     """
    #     # Populate all method activities
    #     for class_name, method_data in cls.methods.items():
    #         for method_name, activity_data in method_data.items():
    #             cls._logger.info(f"Populating anum for method: {class_name}.{method_name}")
    #             aparse = activity_data['parse']
    #             for a in aparse[0]:
    #                 Statement.populate_method(mmdb=mmdb, cname=class_name, method=method_name, anum=activity_data['anum'],
    #                                           domain=activity_data['domain'], aparse=a, scrall_text=aparse[1])
    #
    #     pass
        # Populate all state activities
        # Populate all operation activities