# Blueprint MBSE Repository Populator

This package transforms human readable text files describing an Executable UML model of a system into
a populated metamodel database. With your models loaded into this database it is now possible to produce
a variety of useful artifacts to support model execution and verification, code generation and anything else
that performs detailed analyis on the model components and their relationships.

The text files are expressed in an easy to read markdown format so you can browse through the classes, relationships,
states and transitions, actions and all other model components.

Here we support the Shlaer-Mellor variant of Executable UML exclusively.

## Command usage

`% modeldb -s elevator-case-study`

Assuming your system is named 'elevator-case-study' and is in the current working directory with the internal structure defined below, will output a file named `mmdb_elevator-case-study.ral`. This *.ral file is a text file serialization of a TclRAL database.

Your user model is loaded into the Shlaer-Mellor Metamodel and, if there are no errors, you know you have a Shlaer-Mellor Executable Model that doesn't break any of the rules defined by the metamodel.

You can load and view it using TclRAL or PyRAL or feed it to other downstream Blueprint tools such as the
Model Executor which among its tasks will generate a user model database.


## Input to the populator

Each system is defined in a single package broken down into standard hierarchy of folders like so:

    system
        domain
            subsystem
                classmodel.xcm
                types.yaml
                methods
                    m1.mtd
                    m2.mtd
                    ...
                state-machines
                    s1.xsm
                    ...
                external
                    EE
                        op1.op
                        ...
            subsystem2
            ...
        domain2
        ...
   
Here is a partial layout for The Elevator Case Study as an example:


    elevator-case-study // system
        elevator-management // application domain
            elevator // All defined in one subsystem
                elevator.xcm // the class model
                methods // methods for all classes in subsystem
                    cabin // methods on 'cabin' class
                        ping.mtd // the ping method
                        ...
                    ...
                state-machines // lifecycles and assigners for this subsystem
                    cabin.xsm // lifecycles named by class, assigners by association
                    transfer.xsm
                    R53.xsm // assigner state machine on association R53
                    ...
                external // external entities, each a proxy for some class
                    CABIN // proxy for 'cabin' class
                        arrived-at-floor.op // two ee operations
                        goto-floor.op
            types.yaml // data types for all subsystems in domain
        transport // two more domains (not broken down yet)
        signal io

Each modeled domain has its own folder. Above we just see one for the Elevator Managment domain.

Each domain requires at least one subsystem folder. Here we see only one and that is the Elevator domain.

Within a subsystem folder there is one class model expressed as an .xcm (executable class model) file.

The folders are optional and are:

* external – external entities and their operations, one subfolder per external entity
* methods – class methods each in a folder matching the class name with each method in a separate .mtd file
* state-machines – each state machine, assigner or lifecycle, in its own .xsm (executable state machine) file

Also within a domain you have a types.yaml file which specifies each domain specific type (Pressure, Speed, etc) and selects
a corresponding system (database) type. This is a stop gap measure as we have not yet provided a more robust typing
domain, so, for now we settle with what our database has to offer (int, string, float, etc). Unltimately, though,
a full featured typing facility will support a variety of types and operations on those types as well as a type
definition system. Note that the typing facility can be, but need not necessarily be a modeled domain.