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

| Option | Long form | Description                                                                                                                             |
| --- | --- |-----------------------------------------------------------------------------------------------------------------------------------------|
| `-s` | `--system` | Name of the system package to load. The package is a folder in the current working directory with the structure described below.        |
| `-A` | `--actions` | Do not parse and populate any action language (Scrall) text. With this flag, action text is retained but not parsed into the metamodel. |
| `-v` | `--verbose` | Print progress and the populated metamodel to the console.                                                                              |
| `-L` | `--log` | Keep the `modeldb.log` diagnostic log file. By default the log is deleted when the program exits.                                       |
| `-D` | `--debug` | Run in debug mode.                                                                                                                      |
| `-V` | `--version` | Print the installed version and exit.                                                                                                   |

If you don't want the action language parsed and populated, you can suppress it with the -A option. You might want to do this if you just want to validate your class and state models without worrying about the action language yet.
By default, `modeldb` populates the model structure (classes, relationships, states, and so on). Add `-A`
when you also want the action language parsed and populated, for example when preparing a model for execution:

`% modeldb -s elevator-case-study -A`


## System structure

Each system is defined in a single package broken down into standard hierarchy of folders.

Here is a partial layout for The Elevator Case Study as an example:

    elevator // system name
        elevator-management // domain name
            elevator // subsystem name (coincidentally matches system name)
                class-model  // must contain a single .xcm file for the subsystem
                    elevator.xcm // must exist, and no more than one .xcm file
                    elevator.pdf // any other files in this folder are not processed
                    elevator.mls
                external // external entities, each a proxy for some class, this folder is optional
                    external.yaml  // defines all external entities, synch and asynch services
                    mark.yaml // implicit bridging, if any (implicit state entry events, for example)
                methods // methods for all classes in the subsystem
                    cabin // methods defined on the 'cabin' class (must be a modeled class name)
                        count-stops-oneway.mtd
                        count-stops-roundtrip.mtd
                        estimate-delay.mtd
                        ping.mtd
                        ping-both-ways.mtd
                    bank-level
                        choose-shaft.mtd
                    // no other classes define methods in this subsystem
                state-machines // lifecycles and assigners for this subsystem
                    aslev.xsm
                    blev.xsm
                    cabin.xsm // lifecycles named by class, assigners by association
                    door.xsm
                    floor-service.xsm
                    R53.xsm
                    transfer.xsm
                    class-collaboration-diagram.pdf  // optional and not processed
                    layouts  // optional subfolder with diagrams and layout sheets, not processed
            // no other subsystem folders in this example, but there can be, each structured like elevator above
            // this next types folder is optional for now, but you'll need it in the future
            // it defines model level data types for the entire domain
            types
                // content is not processed by modeldb, but it is processed downstream
        // more elevator system domain files will be added such as transport and sio (signal i/o)
        // for now, though, the elevator example only models a single domain

Here is a summary of the system skelton:

    system
        domain
            subsystem1
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
            types
                // content of this folder ignored by this command, but processed downstream
        domain2
        ...

### Notes:

Additional files such as class model PDFs and other documentation can be present in the subfolders. Only the
recognized files (xcm, mtd, etc) will be processed.
   
Each modeled domain has its own folder and each domain requires at least one subsystem folder.

Within a subsystem folder there is a class-model subfolder with one class model expressed as an .xcm (executable class model) file.

The following folders are necessary only if they contain model content:

* external – you can't wire this domain to any others, or stub it out in the debugger if you don't specify it
* methods – class methods each in a folder matching the class name with each method in a separate .mtd file
* state-machines – each state machine, assigner or lifecycle, in its own .xsm (executable state machine) file

The types folder resolves model level types and supported type operations like `Distance`, `Speed`, etc. to base types
and base type operations. We don't need to process these at this stage, so you can ignore this folder here.

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