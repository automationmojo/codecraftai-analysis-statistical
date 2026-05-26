# automojo-analysis-statistical -- Implementation Roadmap

This roadmap turns the reference designs in `source/examples/` (the `sasstep*`
modules) into a production Python package under
`source/packages/automojo/analysis/statistical/`. The reference modules are the
oracle: every phase below validates production output against them, then they
remain as executable specification artifacts (not consumed at runtime).

## Guiding Principles

1. **SAS-fidelity is the contract.** Behavior matches the SAS DATA-step model.
   Missing-value ordering, KEEP/DROP/RENAME projection, BY-group `first.`/
   `last.`, RETAIN, LAG/DIF, format application, and NUMERIC-by-precision
   routing must all match the reference output, row for row.
2. **One class per file.** Class `FooBar` lives in `foobar.py` (lowercase, no
   underscores). No leading-underscore "private" classes; if it deserves a class,
   it deserves a public name.
3. **Storage is `num + char`.** `decimal` is a declare-only opt-in. Formats /
   informats are the extension point for new representations.
4. **Readers are the seam for inputs.** New input sources (database, raw text,
   parquet, etc.) are added as readers; the engine never branches on input mode.
5. **Vectorization is an optimization, never a redefinition.** Any fast path
   must match the row-loop result.
6. **`testbase` only.** Each new module gets matching tests under
   `source/testroots/automojo/tests/singlehost/analysis/statistical/...`.

## Target Package Layout

```
source/packages/automojo/analysis/statistical/
    __init__.py
    missing/
        missing.py                    # Missing
        missingfactory.py             # MISSING constant + missing() helper
    types/
        typehandler.py                # TypeHandler
        typeregistry.py               # TypeRegistry (replaces the TYPES dict)
        numcoercer.py                 # NumCoercer
        charcoercer.py                # CharCoercer
        decimalcoercer.py             # DecimalCoercer
        constants.py                  # NUM, CHAR, DECIMAL name constants
    formats/
        formatspec.py                 # FormatSpec (parser)
        formatregistry.py             # FormatRegistry
        informatregistry.py           # InformatRegistry
        dollarformat.py               # DollarFormat
        commaformat.py                # CommaFormat
        dateformat.py                 # DateFormat
        charformat.py                 # CharFormat
        dateinformat.py               # DateInformat
        dollarinformat.py             # DollarInformat
        commainformat.py              # CommaInformat
    readers/
        reader.py                     # Reader (abstract base)
        peekable.py                   # Peekable iterator
        setreader.py                  # SetReader
        mergereader.py                # MergeReader
    engine/
        phase.py                      # Phase enum
        slot.py                       # Slot
        recordframe.py                # RecordFrame
        lagqueue.py                   # LagQueue
        statefulfunctions.py          # StatefulFunctions (LAG/DIF host)
        observationengine.py          # ObservationEngine
    database/
        cursorrowstream.py            # CursorRowStream
        databasereader.py             # DatabaseReader
        numericresolver.py            # NumericResolver
        typemap.py                    # TypeMap container
        dialect.py                    # Dialect base
        oracledialect.py              # OracleDialect
        postgresqldialect.py          # PostgreSqlDialect
        mysqldialect.py               # MySqlDialect
        sqlserverdialect.py           # SqlServerDialect
        dialectdeclaration.py         # DialectDeclaration
    ir/
        unsupportederror.py           # UnsupportedError
        astlowerer.py                 # AstLowerer
        binopmap.py                   # BinOpMap
        compareopmap.py               # CompareOpMap
        boolopmap.py                  # BoolOpMap
        classifier.py                 # Classifier
        irinterpreter.py              # IrInterpreter
        logiccompiler.py              # LogicCompiler
        nodes/
            irnode.py                 # IrNode (base)
            constnode.py              # ConstNode
            colnode.py                # ColNode
            autonode.py               # AutoNode
            firstlastnode.py          # FirstLastNode
            binopnode.py              # BinOpNode
            comparenode.py            # CompareNode
            boolopnode.py             # BoolOpNode
            lagnode.py                # LagNode
            difnode.py                # DifNode
            assignnode.py             # AssignNode
            ifnode.py                 # IfNode
            outputnode.py             # OutputNode
            deletenode.py             # DeleteNode
    execution/
        arithmeticops.py              # ArithmeticOps
        compareops.py                 # CompareOps
        columnbuilder.py              # ColumnBuilder
        vectorevaluator.py            # VectorEvaluator
        scheduler.py                  # Scheduler
        compiledstep.py               # CompiledStep
    columnar/
        columnframe.py                # ColumnFrame
        columnarstep.py               # ColumnarStep
    report/
        line.py                       # Line
        report.py                     # Report
        crossrowlabeler.py            # CrossRowLabeler
        reportbuilder.py              # ReportBuilder
```

The test tree mirrors this exactly, rooted at
`source/testroots/automojo/tests/singlehost/analysis/statistical/`.

## Dependencies

The package consumes the following `automojo-*` packages via URL syntax in
`pyproject.toml` (same style as `automojo-interop`):

* `automojo-errors` -- for shared exception types (`ConfigurationError`,
  `SemanticError`, `NotSupportedError`). Replaces the local `Unsupported`
  reference symbol with a domain-specific `UnsupportedError` that extends
  `NotSupportedError`.
* `automojo-testbase` -- the test framework used to validate every module.
* `automojo-xmodules` -- shared utility/cross-module helpers used across the
  automojo suite (lazy import helpers, logger plumbing).

Third-party runtime: `numpy` for the vectorized executor and columnar path.
Optional drivers (`psycopg`, `pymysql`, `oracledb`, `pyodbc`) are NOT direct
dependencies; the `DatabaseReader` wraps any PEP 249 cursor a caller hands in.

## Phases

### Phase 0 -- Scaffolding (foundational)
- Fix `pyproject.toml`: `packages = [{include="automojo", from="source/packages"}]`,
  and add the URL-style automojo dependencies.
- Create the package namespace `automojo/analysis/statistical/__init__.py` and
  each sub-package `__init__.py` (empty namespace markers).
- Create `source/testroots/automojo/__testroot__.py` (`ROOT_TYPE = "testbase"`),
  with `tests/`, `testshared/`, and the singlehost test tree skeleton.

### Phase 1 -- Engine Core (correctness oracle, no DB / no IR)
Port `sasstep.py` into per-class files.

Modules: `missing/*`, `types/*`, `formats/*`, `readers/{reader,peekable,
setreader,mergereader}.py`, `engine/{phase,slot,recordframe,lagqueue,
statefulfunctions,observationengine}.py`.

Tests against the reference engine for:
- BY-group `first.`/`last.` over single & nested BY vars.
- RETAIN + sum-style accumulation; reset-per-group.
- Match-merge: positional, `IN=`, retain-on-exhaustion, later-dataset-wins.
- `LAG_n` / `DIF_n` including conditional and multi-site queues.
- Typed slots: CHAR truncation/length; format application (PUT).
- Missing-value ordering (`._ < . < .A..Z <` numbers).
- KEEP / DROP / RENAME projection.

Exit criterion: every reference example in `source/examples/sasstep.py`
`__main__` is reproducible from the new package with identical output.

### Phase 2 -- Database Readers
Port `sasstep_db.py` into per-class files. `DecimalCoercer` registers the
`decimal` storage type. `Dialect` becomes a base class with one subclass per
RDBMS, each providing a `TypeMap` and a `NAME_TABLE` of dialect-named types.
`DialectDeclaration` replaces the `dialect_declare` function.

Tests:
- sqlite3 end-to-end (a `DatabaseReader` produces identical output to a
  hand-built `SetReader` over the same rows).
- Precision routing: `NUMERIC(8,2)` -> `num`; `NUMERIC(38,2)` -> `decimal`.
- Same column declared across all four dialects yields identical declarations.
- Unmappable dialect types (`JSONB`) raise at declare time.
- Dialect-named declaration: string form and object form route through the
  same resolver.

Exit criterion: every reference example in `source/examples/sasstep_db.py`
`__main__` is reproducible.

### Phase 3 -- IR Front End
Port `sasstep_ir.py`. IR nodes each become their own dataclass file under
`ir/nodes/`. `AstLowerer` replaces the `_Lowerer` class. `Classifier` exposes
`classify(stmts)` and `summarize(stmts)`. `IrInterpreter` is the faithful
oracle for IR output. `LogicCompiler.compile(logic)` returns
`(callable, mode)`. `UnsupportedError` extends `automojo.errors.exceptions.
NotSupportedError`.

Tests:
- Lowering of every supported AST shape (constants, columns, autos,
  first./last., binops, compares, boolops, calls to lag/dif, assigns, ifs,
  output/delete) produces the expected IR.
- Unsupported shapes (comprehensions, calls outside lag/dif, dynamic index)
  raise `UnsupportedError`.
- Classifier marks vectorizable vs sequential statements correctly.
- `IrInterpreter` output equals reference-engine output for every supported
  fixture (the IR-as-oracle property).

Exit criterion: every reference example in `source/examples/sasstep_ir.py`
`__main__` is reproducible.

### Phase 4 -- Hybrid Executor
Port `sasstep_exec.py`. `Scheduler.schedule(stmts, source_cols)` performs the
forward dataflow split into `(batch, loop)`. `VectorEvaluator` evaluates IR
expressions over `numpy` arrays. `CompiledStep.run(rows)` dispatches across
`vector | hybrid | fallback`.

Tests:
- Fully-vectorizable transforms produce output equal to the reference engine.
- Hybrid plans (vector arithmetic + sequential spine) produce output equal to
  the reference engine.
- Fallback (unsupported logic) routes to the reference engine unchanged.
- Forward-dataflow demotion: a "vectorizable" statement reading a loop-only
  value moves to the loop.

Exit criterion: reference benchmarks in `sasstep_exec.py` `__main__` are
reproducible; vectorized path is bit-equal to reference output.

### Phase 5 -- Columnar Output
Port `sasstep_columnar.py`. `ColumnFrame` wraps `{name: ndarray}` with lazy row
materialization, `to_pandas()`, `to_arrow()`, head/iter/index access.
`ColumnarStep` chains array-to-array across pure-vector pipeline steps with
zero per-row materialization between them.

Tests:
- `ColumnFrame.to_dicts()` equals reference-engine output.
- Two-step pipeline (`step1.run_columnar(rows) -> step2.run_columnar(cf1)`)
  exposes the produced columns.
- Optional `to_pandas` / `to_arrow` round-trips (skipped at runtime when
  pandas / pyarrow are not importable; `testbase` skip semantics).

### Phase 6 -- Migration & Optimization Advisor
Port `sasstep_report.py`. `Line` and `Report` are dataclasses. `ReportBuilder.
report(logic, source_cols, retain)` returns a `Report`. `CrossRowLabeler`
walks an IR expression and labels cross-row sources.

Tests:
- A fully-vectorizable transform reports `vector` path with all lines `batch`.
- A mixed step reports correct counts of `irreducible`, `tool-limited`,
  `dependency`, and `cardinality` categories.
- A fallback reports `fallback` with a human-readable cause.

### Phase 7 -- Public API & Documentation
- Curate `automojo/analysis/statistical/__init__.py` to expose the public
  surface: `ObservationEngine`, `SetReader`, `MergeReader`, `DatabaseReader`,
  `Missing`, `MISSING`, `missing()`, `Phase`, `register_format`,
  `register_informat`, `register_type`, `CompiledStep`, `ColumnarStep`,
  `ColumnFrame`, `report`, dialect-named declaration helpers, and the storage
  type constants.
- Userguide pages under `userguide/`:
  - `20-00-overview-and-mental-model.rst`
  - `20-01-engine-core-and-pdv.rst`
  - `20-02-readers-and-by-groups.rst`
  - `20-03-database-sources-and-dialects.rst`
  - `20-04-ir-classification-and-vectorization.rst`
  - `20-05-columnar-output.rst`
  - `20-06-migration-advisor.rst`
  - `20-07-porting-sas-jobs-to-python.rst` -- worked examples that pair a SAS
    snippet with the Python port and the assertion that proves equivalence.

### Phase 8 -- Known Gaps from DESIGN.md (deferred but explicit)
Each of these has its own milestone branch when picked up:
- UPDATE reader (apply-non-missing-only; master/transaction model).
- PROC SORT (no sort/NOTSORTED path yet; MergeReader currently assumes sorted).
- Strict-vs-permissive runtime mode and `_ERROR_` / log semantics.
- Raw INPUT (informats wired into a column/text input reader).
- IR-level fix for same-line LAG/DIF site collision.

## Cross-Cutting Concerns

* **Aspects pattern** -- the engine and readers expose behavior controls
  (timeouts, retries on flaky DB cursors, logging verbosity) only through an
  `Aspects` parameter. No behavior-modifying decorators.
* **Error semantics** -- `SemanticError` is never caught. Configuration-shape
  errors raise `ConfigurationError` from `automojo-errors`. Domain-specific
  unsupported logic raises `UnsupportedError`.
* **Logging** -- use `automojo-xmodules` logger plumbing once Phase 1 is
  green; before then, the engine has no logging (the reference engine doesn't
  either, and adding it before validation would muddy the oracle comparison).

## Test Strategy Summary

Every milestone produces (a) production modules under `source/packages/...`,
(b) `testbase` resource factories under `testshared`, and (c) `test_*.py`
files under `tests/singlehost/...` that mirror the source paths. The reference
modules under `source/examples/` remain as the executable oracle and are
imported in tests only via a fixture that loads them out-of-tree.
