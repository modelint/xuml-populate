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
    State_Activity_i, Signature_i, Parameter_i

if TYPE_CHECKING:
    from tkinter import Tk

class Activity:
    """
    Create a State Model relation
    """
    _logger = logging.getLogger(__name__)

    sm = {} # For debugging purposes, delete once we get action semantics populated

    @classmethod
    def populate_state(cls, mmdb: 'Tk', state: str, state_model: str, actions: str,
                       subsys_name: str, domain_name: str) -> str:
        """Constructor"""


        action_text = '\n'.join(actions)+'\n'
        if state_model not in cls.sm:
            cls.sm[state_model] = {}
        cls.sm[state_model][state] = cls.parse(action_text) # To record parsed actions for debugging

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
        # Read the test file
        test_file_dir = Path(__file__).parent.parent / "test" / "scrall"
        # test_file_path = test_file_dir / "all_examples.scrall"
        # test_file_path = test_file_dir / "test_example.scrall"
        # test_file_path = test_file_dir / "cabin.scrall"
        # test_file_path = test_file_dir / "transfer.scrall"
        # test_text = open(test_file_path, 'r').read() + "\n"
        # result = ScrallParser.parse(scrall_text=test_text, debug=True)
        result = ScrallParser.parse(scrall_text=actions, debug=False)
        return result
