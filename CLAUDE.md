# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

`xuml-populate` reads a human-readable **Executable UML (Shlaer-Mellor variant)** system — expressed as a folder tree of markdown-style text files — and populates the **Shlaer-Mellor Metamodel** (itself a modeled schema) into an in-memory TclRAL relational database. The output is a serialized `mmdb_<system>.ral` text file plus a `mmdb_<system>.txt` human-readable dump. Downstream Blueprint tools (Model Executor, code generators) consume the `.ral` file.

The core idea: the metamodel is *itself* a class model. Populating a user model means inserting instances into metamodel classes (`Class`, `Attribute`, `Relationship`, `State`, `Action`, `Flow`, …) while the relational constraints of the metamodel enforce that the user model is well-formed.

## Commands

```bash
# Run the populator on a system package (folder must be in cwd)
modeldb -s elevator                 # populate model structure only
modeldb -s elevator -A              # -A/--actions: also parse & populate Scrall action text
modeldb -s elevator -v              # verbose: print full mmdb to stdout
modeldb -s elevator -L              # keep the modeldb.log diagnostic file (deleted by default)
modeldb -V                          # print version

# Sample systems live under input/ (e.g. input/elevator, input/sequins)

# Tests (pytest; pythonpath=src is set in pytest.ini)
pytest
pytest tests/test_parse.py
pytest tests/test_parse.py::test_ops_pdf          # single test
pytest tests/test_parse.py -k goto-floor          # single parametrized case

# Version bump (updates pyproject.toml + src/xuml_populate/__init__.py, commits & tags)
bump2version patch      # or minor / major
```

The console entry point `modeldb` maps to `xuml_populate.__main__:main`. Running `python -m xuml_populate` works too.

## Input package layout

A "system" is a folder tree. See `README.md` for the full spec. Key points:

- `system/domain/subsystem/class-model/<subsystem>.xcm` — the class model. The `.xcm` filename **must** match the subsystem folder name; other `.xcm` files are ignored.
- `subsystem/methods/<class>/<method>.mtd` — class methods, grouped in a folder per class.
- `subsystem/state-machines/*.xsm` — lifecycles (named by class) and assigners (named by association, e.g. `R53.xsm`).
- `subsystem/external/external.yaml` + `mark.yaml` — external entities (proxies for classes) and their events/operations, plus marking directives.
- `domain/types.yaml` — maps domain types (Speed, Pressure) to database primitive types. Stop-gap until a real typing domain exists.

`system.yaml` at the system root lists all domains (modeled and "realized"/external).

## Architecture

### Two phases: parse, then populate

`System.__init__` (`src/xuml_populate/system.py`) walks the package tree and **parses** every file into a nested `self.content` dict keyed by domain → subsystem → {class_model, methods, state_models, external}. Parsing is delegated entirely to external Model Integration parser packages — **this repo does not implement parsers**:

- `xcm-parser` → class models, `xsm-parser` → state machines, `mtd-parser` → methods, `op-parser` → external operations, `scrall` → action language (Scrall).

**Gotcha:** the `op-parser` *distribution* installs an importable package named `op2_parser`, so `system.py` correctly does `from op2_parser.op_parser import OpParser`. The mismatch between the dependency name (`op-parser`) and the import name (`op2_parser`) is intentional — do not "fix" the import to match the dependency name.

`System.populate()` then opens the TclRAL session via `pyral` (`mi-pyral`), loads the empty metamodel schema from `src/xuml_populate/populate/mmdb.ral`, and populates each domain.

### Population pipeline (`populate/domain.py`)

`Domain.__init__` runs a deliberately ordered pipeline. Order matters because of cross-references and metamodel constraints:

1. Migrate the Domain from "Realized" to "Modeled"; insert Subsystems.
2. Classes → Relationships (per subsystem).
3. Methods (signatures only) → State models.
4. `Attribute.ResolveAttrTypes` — resolve attribute types after all classes exist (types may be class or scalar).
5. `Lineage.Derive` — compute generalization lineage.
6. External entities / explicit external services, then implicit state-entry external events (driven by `mark.yaml`).
7. **Action population in two passes** (only when `-A`/`parse_actions=True`): first pass populates each Method's activities except Method-Call parameter inputs; second pass (`post_process`) resolves Method Calls once every Method's output signature is known. State activities are processed last.

The two-pass design exists because a Method Call Action needs the *callee's* output type/flow, which may not be populated yet on the first pass.

### The `_i` named-tuple convention

`populate/mmclass_nt.py` defines one `namedtuple` per metamodel class, suffixed `_i` ("instance"), e.g. `Class_i`, `Attribute_i`, `State_Activity_i`. Its field list mirrors the attributes of the corresponding metamodel class in `mmdb.ral`. **This file is auto-generated when the metamodel is rebuilt — do not hand-edit it.** To insert an instance you build the matching `_i` tuple and call `Relvar.insert(...)`.

### pyral / TclRAL patterns

All database work goes through `pyral`:
- `Relvar.insert / deleteone / printall` for tuples.
- `Transaction.open(db, name=...)` / `Transaction.execute(...)` wrap multi-insert operations that must satisfy constraints atomically. Transaction names are module-level constants (e.g. `tr_Modeled_Domain`).
- `Relation.*` for queries during population.
- The database name is the constant `mmdb = "mmdb"` in `config.py`, imported everywhere.

### Actions subsystem (`populate/actions/`)

The largest and most complex area, active only under `-A`. It turns parsed **Scrall** action text into metamodel Action instances (traverse, select, restrict, create, delete, read/write, signal, switch, computation, method/operation call, etc.). `statement.py` dispatches a parsed statement to the right action populator; `activity.py` populates the enclosing Activity and wires up data Flows between actions. `actions/expressions/` handles instance-set / scalar / table expressions and restriction conditions. `actions/aparse_types.py` holds the shared `NamedTuple` types (e.g. `Flow_ap`, `ActivityAP`, `Boundary_Actions`) passed between action populators.

### Debugging

- `utility.print_mmdb()` dumps the full db to `mmdb_debug.txt`; guarded by `if __debug__` and imported throughout.
- Logging config is `src/xuml_populate/log.conf`; the log file `modeldb.log` is auto-deleted on exit unless `-L` is passed.
- `documentation/technotes/` contains data-flow-diagram PDFs/Graffle files documenting specific model activities (useful reference when reasoning about action population).

## Conventions

- Python ≥ 3.11, `src/` layout. Metamodel/model element names contain spaces (e.g. `"Modeled Domain"`, `"Realized Domain"`); relvar names and transaction names use those literal strings, while Python identifiers use underscores. `names.snake()` converts spaces → underscores.
- File names differ from model element names by case/delimiters (`elevator-management` ↔ `Elevator Management`); the real name comes from the parse, filenames are only convenience keys.