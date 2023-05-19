"""
activity.py – Populate an activity instance in PyRAL
"""

import logging
from pathlib import Path
from PyRAL.relvar import Relvar
from class_model_dsl.populate.element import Element
from class_model_dsl.parse.scrall_parser import ScrallParser
from typing import TYPE_CHECKING
from class_model_dsl.populate.pop_types import Activity_i, Asynchronous_Activity_i,\
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
    def populate_method(cls, mmdb: 'Tk', action_text:str, class_name: str, subsys_name: str, domain_name: str) -> str:
        """
        Populate Synchronous Activity for Method
        :param mmdb:
        :param action_text: Unparsed scrall text
        :param class_name:
        :param subsys_name:
        :param domain_name:
        :return: Anum
        """
        Anum = cls.populate_synchronous(mmdb, action_text, subsys_name, domain_name)
        cls.methods[class_name] = cls.parse(action_text)
        return Anum

    @classmethod
    def populate_operation(cls, mmdb: 'Tk', action_text:str, ee_name: str, subsys_name: str, domain_name: str) -> str:
        """
        Populate Synchronous Activity for Operation

        :param mmdb:
        :param action_text:
        :param ee_name:
        :param subsys_name:
        :param domain_name:
        :return:
        """
        Anum = cls.populate_synchronous(mmdb, action_text, subsys_name, domain_name)
        cls.operations[ee_name] = cls.parse(action_text)
        return Anum

    @classmethod
    def populate_synchronous(cls, mmdb: 'Tk', action_text:str, subsys_name: str, domain_name: str) -> str:
        """
        Populate a Synchronous Activity (Method or Operation)

        :param mmdb:
        :param action_text:
        :param subsys_name:
        :param domain_name:
        :return:
        """
        # Rather than combine synch and asynch into one population method we keep these separate because
        # at soem point we may add the creation of an optional synchronous output in this method
        Anum = Element.populate_unlabeled_subsys_element(mmdb,
                                                         prefix='A',
                                                         subsystem_name=subsys_name, domain_name=domain_name)
        Relvar.insert(relvar='Activity', tuples=[
            Activity_i(Anum=Anum, Domain=domain_name, Actions=action_text)
        ])
        Relvar.insert(relvar='Synchronous_Activity', tuples=[
            Synchronous_Activity_i(Anum=Anum, Domain=domain_name)
        ])
        return Anum


    @classmethod
    def populate_state(cls, mmdb: 'Tk', state: str, state_model: str, actions: str,
                       subsys_name: str, domain_name: str) -> str:
        """Constructor"""


        # Parse scrall in this state and add it to temporary sm dictionary
        action_text = '\n'.join(actions)+'\n'
        if state_model not in cls.sm:
            cls.sm[state_model] = {}
        parsed_activity = cls.parse(action_text)
        cls.sm[state_model][state] = parsed_activity # To record parsed actions for debugging
        # cls.populate_activity(text=action_text, pa=parsed_activity)

        # Create the Susbystem Element and obtain a unique Anum
        Anum = Element.populate_unlabeled_subsys_element(mmdb,
                                                         prefix='A',
                                                         subsystem_name=subsys_name, domain_name=domain_name)
        Relvar.insert(relvar='Activity', tuples=[
            Activity_i(Anum=Anum, Domain=domain_name, Actions=action_text)
        ]) # TODO: Action text must be passed to an Action Language parser to obtain Action semantics
        Relvar.insert(relvar='Asynchronous_Activity', tuples=[
            Asynchronous_Activity_i(Anum=Anum, Domain=domain_name)
        ])
        Relvar.insert(relvar='State_Activity', tuples=[
            State_Activity_i(Anum=Anum, State=state, State_model=state_model, Domain=domain_name)
        ])
        return Anum

    @classmethod
    def parse(cls, actions, debug=False):
        action_text = '\n'.join(actions)+'\n'
        # Read the test file
        test_file_dir = Path(__file__).parent.parent / "test" / "scrall"
        # test_file_path = test_file_dir / "all_examples.scrall"
        # test_file_path = test_file_dir / "test_example.scrall"
        # test_file_path = test_file_dir / "cabin.scrall"
        # test_file_path = test_file_dir / "transfer.scrall"
        # test_text = open(test_file_path, 'r').read() + "\n"
        # result = ScrallParser.parse(scrall_text=test_text, debug=True)
        result = ScrallParser.parse(scrall_text=action_text, debug=False)
        return result
