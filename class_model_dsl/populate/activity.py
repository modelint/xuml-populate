"""
activity.py – Populate an activity instance in PyRAL
"""

import logging
from pathlib import Path
from PyRAL.relvar import Relvar
from class_model_dsl.populate.element import Element
# from class_model_dsl.parse.scrall_parser import ScrallParser
from class_model_dsl.test.scrall.path_inst.scrall_parser import ScrallParser
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

    @classmethod
    def populate_state(cls, mmdb: 'Tk', state: str, state_model: str, actions: str,
                       subsys_name: str, domain_name: str) -> str:
        """Constructor"""

        cls.parse(actions)

        # Create the Susbystem Element and obtain a unique Anum
        Anum = Element.populate_unlabeled_subsys_element(mmdb,
                                                         prefix='A',
                                                         subsystem_name=subsys_name, domain_name=domain_name)
        action_text = '\n'.join(actions) # Activity is parsed as a list of strings, convert to a single string
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
        test_file_dir = Path(__file__).parent.parent / "test" / "scrall" / "path_inst"
        test_file_path = test_file_dir / "path-inst.scrall"
        test_text = open(test_file_path, 'r').read() + "\n"

        # test_text = "TRAN.Goto floor(\n      floor : Height,\n   direction\n  )\n"
        # test_text = "Cabin at destination( floor : Height, direction ) -> /R53/Transfer\n"
        # test_text = "Cabin at destination( floor : Height, dir : Direction ) -> /R53/Transfer\n"
        # test_text = "Cabin at destination( floor : Height, dir : Direction ) -> /R53/Transfer\n"
        # test_text = "Cabin at destination() -> /R53/Transfer\n"
        print(test_text)
        result = ScrallParser.parse(scrall_text=test_text, debug=True)
        pass
