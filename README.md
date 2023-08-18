# xuml-populate

This package transforms human readable text files describing an Executable UML model of a system into
a populated metamodel database. With your models loaded into this database it is now possible to produce
a variety of useful artifacts to support model execution and verification, code generation and anything else
that performs detailed analyis on the model components and their relationships.

The text files are expressed in an easy to read markdown format so you can browse through the classes, relationships,
states and transitions, actions and all other model components.

Here we support the Shlaer-Mellor variant of Executable UML exclusively.

## Input to the populator

Each modeled domain is in its own folder further broken down into one or more subsystem folders.
Each subsystem folder has the following structure using the elevator case study as an example system:

    elevator-management
        Elevator
            external
                CABIN
                    arrived-at-floor.op
                    goto-floor.op
            methods
                Cabin
                    Ping.mtd
                    ...
                ...
            state-machines
                cabin.xsm
                transfer.xsm
                ...
            Elevator.xcm
        types.yaml

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