"""
anum.py – Populate an Activity
"""

# System
import logging
from typing import NamedTuple

# Model Integration
from pyral.relvar import Relvar
from pyral.relation import Relation
from scrall.parse.parser import ScrallParser

# xUML Populate
from xuml_populate.config import mmdb
from xuml_populate.populate.method_activity import MethodActivity
from xuml_populate.populate.element import Element
from xuml_populate.populate.actions.aparse_types import Activity_ap
from xuml_populate.populate.mmclass_nt import (Activity_i, Asynchronous_Activity_i, State_Activity_i,
                                               Synchronous_Activity_i)

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
        :param parse_actions:
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
        cls.methods[cname][method]['parse'] = ScrallParser.parse_text(scrall_text=action_text, debug=False)
        pass
        # if parse_actions:
        #     cls.methods[cname][method]['parse'] = ScrallParser.parse_text(scrall_text=action_text, debug=False)
        # else:
        #     cls.methods[cname][method]['parse'] = None
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
        :param tr:  Name of the transaction
        :param state: State name
        :param state_model:  State model name
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

                ma = MethodActivity(name=method_name, class_name=class_name, method_data=method_data,
                                    activity_data=activity_data, domain=cls.domain)
        pass

    # TODO: Populate all state activities
    # TODO: Populate all operation activities
