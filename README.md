# Executable UML Repository Populator

This package populates a Shlaer-Mellor Executable UML metamodel repository with your modeled system. Here, we'll use the Elevator Case Study system as an example.

The two inputs are: 1) an empty metmaodel repository and 2) your modeled (or partially modeled) system. The populator outputs a metamodel database populated with your system. For our example, we'll populate the elevator system into the repository.

### Input 1: An empty metamodel repository

Use [makexumlrepo command](https://github.com/modelint/make-xuml-repo) to generate the empty metamodel repository and
pass that as one of the inputs to the `modeldb` command as shown in the Command Usage section below. The empty repo will be namd `mmdb.ral` in our example.

### Input 2: Your modeled system

The modeled system is a structured hierarchy of folders containing text files representing your models. You can think of this as a system package. You just feed the name of the top level system folder as input to the command line.

## Command usage

`% modeldb -s elevator`

The top level of the elevator system package named `elevator` is in the local directory for this example and we've specified the path with the `-s` option. If the `mmdb.ral` file is present in the local directory, you don't need to specify it on the command line. Otherwise, use the -m option to supply the path.

The above command will output a file named `mmdb_elevator.ral`. This optional naming convention can be read right to left as _elevator populated into mmdb_. Later, when you populate your system with scenario specific data, you can continue the convention with  `mmdb_elevator_threeshafts` reading _threeshafts populated into elevator system populated into the metamodel db_.

If all goes well, your system is loaded into the repository. Often, all will not go well, and that is likely because there are errors in your models. If any Shlaer-Mellor Executable UML modeling rules are broken, the system models won't populate. The errors will tell you what's wrong so that you can make the necessary fixes before trying again. Rather than using complex checking algorithms, we rely on the power of the metamodel itself as a tightly constrained database to detect and report model errors.

When you finally succeed, you know that your models are syntatically correct. They still might not work when you try to run them, (just like syntatically correct code) but that's another set of problems that you can resolve with the appropriate tools downstream, such as the [MDB](https://github.com/modelint/model-debugger) (model debugger) and [MX](https://github.com/modelint/model-execution) (model execution engine).

### Command line options

| Option | Long form | Description |
| --- | --- | --- |
| `-s` | `--system` | Name of the system package to load. The package is a folder in the current working directory with the structure described below. |
| `-A` | `--actions` | Parse and populate all action language (Scrall) text. Without this flag, action text is retained but not parsed into the metamodel. |
| `-v` | `--verbose` | Print progress and the populated metamodel to the console. |
| `-L` | `--log` | Keep the `modeldb.log` diagnostic log file. By default the log is deleted when the program exits. |
| `-D` | `--debug` | Run in debug mode. |
| `-V` | `--version` | Print the installed version and exit. |

By default, `modeldb` populates only the model structure (classes, relationships, states, and so on). Add `-A`
when you also want the action language parsed and populated, for example when preparing a model for execution:

`% modeldb -s elevator-case-study -A`


## System structure

This package transforms human readable text files describing an Executable UML model of a system into
a populated metamodel database. With your models loaded into this database it is now possible to produce
a variety of useful artifacts to support model execution and verification, code generation and anything else
that performs detailed analyis on the model components and their relationships.

The text files are expressed in an easy to read markdown format so you can browse through the classes, relationships,
states and transitions, actions and all other model components.

Here we support the Shlaer-Mellor variant of Executable UML exclusively.

Each system is defined in a single package broken down into standard hierarchy of folders like so:

    system
        domain
            subsystem
                class-model
                    classmodel.xcm
                types.yaml
                methods
                    class1
                        m1.mtd
                        ...
                    class2
                        m1.mtd
                        ...
                    ...
                state-machines
                    s1.xsm
                    ...
                external
                    external.yaml
                    mark.yaml
            subsystem2
            ...
        domain2
        ...

Additional files such as class model PDFs and other documentation can be present in the subfolders. Only the
needed files (xcm, mtd, etc) will be processed.
   
Here is a partial layout for The Elevator Case Study as an example:


    elevator-case-study // system
        elevator-management // application domain
            elevator // All defined in one subsystem
                class-model
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

Within a subsystem folder there is a class-model subfolder with one class model expressed as an .xcm (executable class model) file.

The following folders are optional:

* external – external entities and their operations, one subfolder per external entity
* methods – class methods each in a folder matching the class name with each method in a separate .mtd file
* state-machines – each state machine, assigner or lifecycle, in its own .xsm (executable state machine) file

Also within a domain you have a types.yaml file which specifies each domain specific type (Pressure, Speed, etc) and selects
a corresponding system (database) type. This is a stop gap measure as we have not yet provided a more robust typing
domain, so, for now we settle with what our database has to offer (int, string, float, etc). Unltimately, though,
a full featured typing facility will support a variety of types and operations on those types as well as a type
definition system. Note that the typing facility can be, but need not necessarily be a modeled domain.

## Installation

This package is published on [PyPI](https://pypi.org/project/xuml-populate/) and requires Python 3.11 or later.

    % pip install xuml-populate

Installing from within a virtual environment is recommended:

    % python3 -m venv .venv
    % source .venv/bin/activate
    % pip install xuml-populate

The install pulls in all required Blueprint parser and database dependencies automatically
(`xcm-parser`, `xsm-parser`, `mtd-parser`, `op-parser`, `scrall`, `mi-pyral`, `pyyaml`).

Once installed, the `modeldb` command is available on your path:

    % modeldb -V

To upgrade to the latest release:

    % pip install --upgrade xuml-populate