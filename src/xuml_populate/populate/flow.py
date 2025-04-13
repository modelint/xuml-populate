"""
flow.py – Populate a Flow in PyRAL
"""

import logging
from xuml_populate.config import mmdb
from pyral.relvar import Relvar
from pyral.relation import Relation
from pyral.transaction import Transaction
from typing import Optional, Set, List, Dict
from xuml_populate.populate.actions.table import Table
from xuml_populate.exceptions.action_exceptions import FlowException, ControlFlowHasNoTargetActions
from xuml_populate.populate.mmclass_nt import Data_Flow_i, Flow_i, \
    Multiple_Instance_Flow_i, Single_Instance_Flow_i, Instance_Flow_i, \
    Control_Flow_i, Non_Scalar_Flow_i, Scalar_Flow_i, Relation_Flow_i, Labeled_Flow_i, Unlabeled_Flow_i, \
    Tuple_Flow_i, Table_Flow_i, Control_Dependency_i
from xuml_populate.populate.actions.aparse_types import Flow_ap, MaxMult, Content

# TODO: Add Table and Control Flow population

_logger = logging.getLogger(__name__)

# Transaction
tr_Inst_Flow = "Instance Flow"
tr_Rel_Flow = "Relation Flow"
tr_Scalar_Flow = "Scalar Flow"


class Flow:
    """
    Populate relevant Flow relvars
    """
    flow_id_ctr = {}  # Manage flow id numbering per anum:domain

    @classmethod
    def populate_switch_output(cls, label: str, ref_flow: Flow_ap, anum: str, domain: str) -> Flow_ap:
        """
        The output of a Data Flow Switch is a new Data Flow that matches all properties of any Data Flow providing
        input to the Data Flow Switch.  (all inputs have identical properties, so the ref_flow can be any one of the
        input flows)

        :param label: Switch output flows are always labeled
        :param ref_flow: The reference flow is any of the inputs to the switch
        :param anum: The activity number
        :param domain: The domain name
        :return: A summary of the newly populated switch output Data Flow
        """
        match ref_flow.content:
            case Content.INSTANCE:
                return cls.populate_instance_flow(cname=ref_flow.tname, anum=anum, domain=domain, label=label,
                                                  single=(ref_flow.max_mult == MaxMult.ONE))
            case Content.RELATION:
                return cls.populate_relation_flow_by_reference(ref_flow=ref_flow, anum=anum, domain=domain, label=label)
            case Content.SCALAR:
                return cls.populate_scalar_flow(scalar_type=ref_flow.tname, anum=anum, domain=domain, label=label)
            case _:
                raise FlowException

    @classmethod
    def compatible(cls, flows: List[Flow_ap]) -> bool:
        """
        Ensure that all flows in the given list have the same content, type, and multiplicity.
        If so, return true

        :param flows:
        :return: True if all flows are compatible
        """
        assert len(flows) > 1
        # Set reference properties
        c = flows[0].content
        t = flows[0].tname
        m = flows[0].max_mult
        for f in flows[1:]:
            # Compare to reference properties
            if f.content != c or f.tname != t or f.max_mult != m:
                return False
        return True

    @classmethod
    def find_labeled_ns_flow(cls, name: str, anum: str, domain: str) -> Optional[Flow_ap]:
        """
        Given a name, find a Non Scalar Flow labeled with that name and return its summary.

        Nothing is returned if there is no such flow.

        :param name: A name that should match a Labeled Flow
        :param anum: The activity number
        :param domain: The domain name
        :return:
        """
        fid = cls.find_labeled_flow(name=name, anum=anum, domain=domain)
        if not fid:
            return None
        # Is it an Instance Flow?
        R = f"ID:<{fid}>, Activity:<{anum}>, Domain:<{domain}>"
        if_result = Relation.restrict(mmdb, relation='Instance_Flow', restriction=R)
        if if_result.body:
            # Okay, it's an instance flow. Now we need the multiplicity on that flow
            ctype = if_result.body[0]['Class']
            many_if_result = Relation.restrict(mmdb, relation='Multiple_Instance_Flow', restriction=R)
            m = MaxMult.MANY if many_if_result.body else MaxMult.ONE
            return Flow_ap(fid=fid, content=Content.INSTANCE, tname=ctype, max_mult=m)

        # Is it a Relation Flow?
        R = f"ID:<{fid}>, Activity:<{anum}>, Domain:<{domain}>"
        rf_result = Relation.restrict(mmdb, relation='Relation_Flow', restriction=R)
        if rf_result.body:
            # It's a Relation Flow. Tuple or Table?
            ttype = rf_result.body[0]['Type']
            ntuples = Relation.restrict(mmdb, relation='Table_Flow', restriction=R)
            m = MaxMult.MANY if ntuples.body else MaxMult.ONE
            return Flow_ap(fid=fid, content=Content.RELATION, tname=ttype, max_mult=m)

    @classmethod
    def find_labeled_scalar_flow(cls, name: str, anum: str, domain: str) -> Optional[Flow_ap]:
        """
        Given a name, find a Scalar Flow labeled with that name and return its summary.

        Nothing is returned if there is no such flow.

        :param name: Name that matches a Labled Flow
        :param anum: The activity number
        :param domain: The domain name
        :return: A flow summary or None if no such labeled flow is defined
        """
        fid = cls.find_labeled_flow(name=name, anum=anum, domain=domain)
        if not fid:
            return None
        R = f"ID:<{fid}>, Activity:<{anum}>, Domain:<{domain}>"
        result = Relation.restrict(mmdb, relation='Scalar_Flow', restriction=R)
        if result.body:
            return Flow_ap(fid=fid, content=Content.SCALAR, tname=result.body[0]['Type'], max_mult=None)
        else:
            return None

    @classmethod
    def find_labeled_flow(cls, name: str, anum: str, domain: str) -> Optional[str]:
        """
        Return the fid of a Labeled Flow if it is defined

        :param name: Flow Name
        :param anum: Activity number
        :param domain: Domain name
        :return: flow id (fid) or None if not found
        """
        R = f"Name:<{name}>, Activity:<{anum}>, Domain:<{domain}>"
        result = Relation.restrict(mmdb, relation='Labeled_Flow', restriction=R)
        if not result.body:
            return None
        else:
            return result.body[0]['ID']

    @classmethod
    def populate_control_flow(cls, tr: str, enabled_actions: Set[str], anum: str, domain: str,
                              label: Optional[str] = None) -> str:
        """
        Populate a new Control Flow.

        Since a Control Flow must feed an Action, it populates inside the provided transaction
        and does not open and close its own like Data Flows.

        :return: The flow id
        """
        flow_id = cls.populate_flow(tr=tr, anum=anum, domain=domain, label=label)
        Relvar.insert(mmdb, tr=tr, relvar='Control_Flow', tuples=[
            Control_Flow_i(ID=flow_id, Activity=anum, Domain=domain)
        ])
        # Populate one or more targets of each Control Flow
        if len(enabled_actions) < 1:
            _logger.error(f"Control flow requires at least one target action")
            raise ControlFlowHasNoTargetActions
        for a in enabled_actions:
            Relvar.insert(mmdb, tr=tr, relvar='Control_Dependency', tuples=[
                Control_Dependency_i(Control_flow=flow_id, Action=a, Activity=anum, Domain=domain)
            ])
        return flow_id

    @classmethod
    def populate_table_flow_from_class(cls, cname: str, anum: str, domain: str) -> Flow_ap:
        """

        :return:
        """
        pass

    @classmethod
    def lookup_data(cls, fid: str, anum: str, domain: str) -> Flow_ap:
        """
        Given a Data Flow identifier (fid, anum, domain), determine the flow content, tname, and maxmult

        Raise exception if no such Data Flow

        :param fid: Flow ID of a Data Flow
        :param anum: The activity number
        :param domain: The domain name
        :return: A flow summary for the supplied ID
        """
        # First verify that the fid corresponds to some Data Flow instance
        R = f"ID:<{fid}>, Activity:<{anum}>, Domain:<{domain}>"
        result = Relation.restrict(mmdb, relation='Data_Flow', restriction=R)
        if not result.body:
            # Either fid not defined or it is a Control Flow
            raise FlowException

        # Is Non Scalar or Scalar Flow?
        R = f"ID:<{fid}>, Activity:<{anum}>, Domain:<{domain}>"
        result = Relation.restrict(mmdb, relation='Non_Scalar_Flow', restriction=R)
        if result.body:
            # It is a Non Scalar Flow
            R = f"ID:<{fid}>, Activity:<{anum}>, Domain:<{domain}>"
            result = Relation.restrict(mmdb, relation='Instance_Flow', restriction=R)
            if result.body:
                # It's an Instance Flow
                tname = result.body[0]['Type']
                R = f"ID:<{fid}>, Activity:<{anum}>, Domain:<{domain}>"
                result = Relation.restrict(mmdb, relation='Multiple_Instance_Flow', restriction=R)
                max_mult = MaxMult.MANY if result.body else MaxMult.ONE
                return Flow_ap(fid=fid, content=Content.INSTANCE, tname=tname, max_mult=max_mult)
            else:
                # Must be a Table Flow
                R = f"ID:<{fid}>, Activity:<{anum}>, Domain:<{domain}>"
                result = Relation.restrict(mmdb, relation='Relation_Flow', restriction=R)
                tname = result.body[0]['Type']
                R = f"ID:<{fid}>, Activity:<{anum}>, Domain:<{domain}>"
                result = Relation.restrict(mmdb, relation='Table_Flow', restriction=R)
                max_mult = MaxMult.MANY if result.body else MaxMult.ONE
                return Flow_ap(fid=fid, content=Content.RELATION, tname=tname, max_mult=max_mult)
        else:
            # It's a Scalar Flow
            R = f"ID:<{fid}>, Activity:<{anum}>, Domain:<{domain}>"
            result = Relation.restrict(mmdb, relation='Scalar_Flow', restriction=R)
            tname = result.body[0]['Type']
            return Flow_ap(fid=fid, content=Content.SCALAR, tname=tname, max_mult=None)

    @classmethod
    def populate_data_flow_by_type(cls, label: Optional[str], mm_type: str, anum: str,
                                   domain: str, activity_tr: str = None) -> Flow_ap:
        """
        Populate an instance of Data Flow and determine its subclasses based on the supplied
        Class, Scalar, or Table Type.

        :param label:
        :param mm_type: A Class, Scalar, or Table Type
        :param anum:
        :param domain:
        :param activity_tr: Incorporate this in the activity population transaction if provided
        :return: The generated flow id
        """
        tr = tr_Inst_Flow if not activity_tr else activity_tr
        # For now we distinguish only between class and scalar types
        # Is the type a Class Type?
        R = f"Name:<{mm_type}>, Domain:<{domain}>"
        r_result = Relation.restrict(db=mmdb, relation='Class', restriction=R)
        if r_result.body:
            # It's a class type, create a multiple instance flow
            flow = cls.populate_instance_flow(cname=mm_type, anum=anum, domain=domain, label=label,
                                              activity_tr=tr)
        else:
            # It's a scalar type
            flow = cls.populate_scalar_flow(scalar_type=mm_type, anum=anum, domain=domain,
                                            label=label, activity_tr=tr)
        return flow

    @classmethod
    def populate_scalar_flow(cls, scalar_type: str, anum: str, domain: str, label: Optional[str] = None,
                             activity_tr: str = None) -> Flow_ap:
        """
        Populate an instance of Scalar flow

        :param scalar_type: The name of the Scalar (Type)
        :param anum: The anum of the enclosing Activity
        :param domain: The name of the domain
        :param label: If provided, a labeled flow is populated
        :param activity_tr: Incorporate this in the activity population transaction if provided
        :return: A Flow_ap summary of the key flow characteristics
        """
        tr = tr_Inst_Flow if not activity_tr else activity_tr
        # See comment in populate_instance_flow
        if not activity_tr:
            Transaction.open(db=mmdb, name=tr)

        flow_id = cls.populate_data_flow(tr=tr, anum=anum, domain=domain, label=label)
        Relvar.insert(db=mmdb, tr=tr, relvar='Scalar_Flow', tuples=[
            Scalar_Flow_i(ID=flow_id, Activity=anum, Domain=domain, Type=scalar_type)
        ])
        if not activity_tr:
            Transaction.execute(db=mmdb, name=tr)

        return Flow_ap(fid=flow_id, content=Content.SCALAR, tname=scalar_type, max_mult=None)

    @classmethod
    def populate_instance_flow(cls, cname: str, anum: str, domain: str, label: Optional[str] = None,
                               single: bool = False, activity_tr: str = None) -> Flow_ap:
        """
        Populate an instance of Scalar flow

        :param cname: The class name which establishes the Type
        :param label: If provided, a labeled flow is populated
        :param anum: The anum of the enclosing Activity
        :param domain: The name of the domain
        :param single: If true, Single vs Multiple Instance Flow which is assumed by default
        :param activity_tr: Incorporate this in the activity population transaction if provided
        :return: A Flow_ap summary of the key flow characteristics
        """
        # When an Activity is being populated, it may require certain Flows, the 'me' initial
        # executing instance Flow, for example. In this case, the Activity has a transaction open
        # and, until this outer transaction closes, the Activity does not yet exist. In this case,
        # we use the activity transaction, otherwise we create a new one locally
        tr = tr_Inst_Flow if not activity_tr else activity_tr
        if not activity_tr:
            Transaction.open(db=mmdb, name=tr)

        flow_id = cls.populate_non_scalar_flow(tr=tr, anum=anum, domain=domain, label=label)
        Relvar.insert(db=mmdb, tr=tr, relvar='Instance_Flow', tuples=[
            Instance_Flow_i(ID=flow_id, Activity=anum, Domain=domain, Class=cname)
        ])
        if single:
            max_mult = MaxMult.ONE
            Relvar.insert(db=mmdb, tr=tr, relvar='Single_Instance_Flow', tuples=[
                Single_Instance_Flow_i(ID=flow_id, Activity=anum, Domain=domain)
            ])
        else:
            max_mult = MaxMult.MANY
            Relvar.insert(db=mmdb, tr=tr, relvar='Multiple_Instance_Flow', tuples=[
                Multiple_Instance_Flow_i(ID=flow_id, Activity=anum, Domain=domain)
            ])

        if not activity_tr:
            Transaction.execute(db=mmdb, name=tr)

        return Flow_ap(fid=flow_id, content=Content.INSTANCE, tname=cname, max_mult=max_mult)

    @classmethod
    def populate_non_scalar_flow(cls, tr: str, anum: str, domain: str, label: Optional[str] = None) -> str:
        """
        Populate an instance of Non Scalar flow (called by subclass only)

        :param tr:  The transaction specific to Flow subclass
        :param anum: The activity number
        :param domain: The domain name
        :param label: An optional label
        :return: The Flow ID
        """
        fid = cls.populate_data_flow(tr=tr, anum=anum, domain=domain, label=label)
        Relvar.insert(db=mmdb, tr=tr, relvar='Non_Scalar_Flow', tuples=[
            Non_Scalar_Flow_i(ID=fid, Activity=anum, Domain=domain)
        ])
        return fid

    @classmethod
    def populate_data_flow(cls, tr: str, anum: str, domain: str, label: Optional[str] = None) -> str:
        """
        """
        fid = cls.populate_flow(tr=tr, anum=anum, domain=domain, label=label)
        Relvar.insert(db=mmdb, tr=tr, relvar='Data_Flow', tuples=[
            Data_Flow_i(ID=fid, Activity=anum, Domain=domain)
        ])
        return fid

    @classmethod
    def populate_relation_flow(cls, table_name: str, anum: str, domain: str, is_tuple: bool,
                               label: Optional[str] = None) -> Flow_ap:
        """
        Given an existing Table, populate a Relation Flow

        :param table_name: Name of an existing Table
        :param anum:
        :param domain:
        :param is_tuple:
        :param label:
        :return: Summary of the populated flow
        """
        flow_id = cls.populate_non_scalar_flow(tr=tr_Rel_Flow, anum=anum, domain=domain, label=label)
        Relvar.insert(db=mmdb, tr=tr_Rel_Flow, relvar='Relation_Flow', tuples=[
            Relation_Flow_i(ID=flow_id, Activity=anum, Domain=domain, Type=table_name)
        ])
        if is_tuple:
            Relvar.insert(db=mmdb, tr=tr_Rel_Flow, relvar='Tuple_Flow', tuples=[
                Tuple_Flow_i(ID=flow_id, Activity=anum, Domain=domain)
            ])
        else:
            Relvar.insert(db=mmdb, tr=tr_Rel_Flow, relvar='Table_Flow', tuples=[
                Table_Flow_i(ID=flow_id, Activity=anum, Domain=domain)
            ])
        return Flow_ap(fid=flow_id, content=Content.RELATION, tname=table_name,
                       max_mult=MaxMult.ONE if is_tuple else MaxMult.MANY)

    @classmethod
    def populate_relation_flow_by_reference(cls, ref_flow: Flow_ap, anum: str, domain: str,
                                            label: Optional[str] = None) -> Flow_ap:
        """
        Given an existing Relation Flow, create another with the same properties.

        This is useful in the Switch Action for creating the output of a Data Flow Switch which must match
        the input.

        :param ref_flow: A Relation Flow summary
        :param label: optional label
        :param anum: The anum number
        :param domain: The domain name
        :return: Summary of duplicated flow
        """
        # Since we are making a copy, we know that the Table (Type) must already exist, so we skip the Table creation
        # / verification step and just populate the Relation Flow.
        Transaction.open(db=mmdb, name=tr_Rel_Flow)
        rflow = cls.populate_relation_flow(table_name=ref_flow.tname, anum=anum, domain=domain,
                                           is_tuple=(ref_flow.max_mult == MaxMult.ONE), label=label)
        Transaction.execute(db=mmdb, name=tr_Rel_Flow)
        return rflow

    @classmethod
    def populate_relation_flow_by_header(cls, table_header: Dict[str, str], anum: str, domain: str, max_mult: MaxMult,
                                         label: Optional[str] = None) -> Flow_ap:
        """
        Populate a Relation Flow as either a Table or Tuple Flow typed with either an existing Table,
        if there is a header match, or a newly created Table.

        :param table_header: The table header as a dict of attribute name;type pairs
        :param anum: Activity number (anum)
        :param domain: The domain name
        :param max_mult: Max number of tuples
        :param label: Optional name of flow
        :return: The newly populated Relation Flow
        """
        Transaction.open(mmdb, tr_Rel_Flow)
        # Populate the table if it does not aleady exist
        table_name = Table.populate(tr=tr_Rel_Flow, table_header=table_header, domain=domain)
        rflow = cls.populate_relation_flow(table_name=table_name, anum=anum, domain=domain,
                                           is_tuple=(max_mult == MaxMult.ONE), label=label)
        Transaction.execute(mmdb, tr_Rel_Flow)
        return rflow

    @classmethod
    def populate_flow(cls, tr: str, anum: str, domain: str, label: Optional[str] = None) -> str:
        """
        Called only by a subclass Flow populator, populate a Flow of the subclass with an optional label.

        :param tr: The open transaction specific to the Flow subclass
        :param anum: The anum
        :param domain: The domain name
        :param label: An optional label
        :return: The Flow ID (fid)
        """
        """
        Populate Flow instance and optional Label
        """
        # Each anum requires a new flow id counter
        activity_id = f'{domain}:{anum}'  # combine attributes to get id
        if activity_id not in cls.flow_id_ctr.keys():
            cls.flow_id_ctr[activity_id] = 0

        # Populate Flow instance
        cls.flow_id_ctr[activity_id] += 1  # Increment the flow id counter for this anum
        fid = f"F{cls.flow_id_ctr[activity_id]}"
        Relvar.insert(db=mmdb, tr=tr, relvar='Flow', tuples=[
            Flow_i(ID=fid, Activity=anum, Domain=domain)
        ])

        # If a label has been defined, populate it
        if label:
            Relvar.insert(db=mmdb, tr=tr, relvar='Labeled_Flow', tuples=[
                Labeled_Flow_i(Name=label, ID=fid, Activity=anum, Domain=domain)
            ])
        else:
            Relvar.insert(db=mmdb, tr=tr, relvar='Unlabeled_Flow', tuples=[
                Unlabeled_Flow_i(ID=fid, Activity=anum, Domain=domain)
            ])

        return fid
