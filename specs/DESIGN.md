# sasstep — design note

A reference implementation of the SAS DATA-step execution model in Python.
Its job is **correctness, not speed**: the oracle a future fast path is validated
against, and the fallback engine for the parts of a step that can't be vectorized.

## The model

The DATA step is a row-at-a-time procedural machine with three pieces:

- **Program Data Vector (PDV)** — the working register set for the current row.
  Implemented as `RecordFrame`: a typed register file (per variable: type,
  length, format, informat, value, retain flag).
- **Implicit loop** — the driver: reset → read → execute → output → repeat.
  Implemented as `ObservationEngine`, which owns a `RecordFrame` and *is* the
  iterator over output rows.
- **Cross-row state rules** — what makes it more than a map over rows.

Because one input observation can yield zero rows (subsetting `IF`/`delete`) or
many (multiple `output()` calls), `__next__` drains an output buffer before
advancing the machine. The phases (`Phase` enum) make the state machine explicit.

## The load-bearing rule

Top-of-step reset, in `ObservationEngine._tick` / `RecordFrame.reset_non_retained`:

| variable origin            | behavior at top of step          |
|----------------------------|----------------------------------|
| source vars (SET / MERGE)  | retained; next read overwrites   |
| assigned vars              | reset to missing                 |
| declared `retain`          | retained, keep value             |
| automatic (`_N_`, first./last., end=, IN=) | engine-managed   |

Get this wrong and every real program is subtly wrong. Every state feature
(RETAIN, sum statement, LAG/DIF) is a variation on "which slots survive this."

## Findings

**1. READ is the seam.** The only phase that changes shape across input modes.
Every `Reader` returns `(row, in_flags, cur_key, next_key)`, so the loop driver
never branches on input mode and `first.`/`last.` is computed once, in the
engine. `MERGE` (a multi-cursor sub-state-machine) and database sources both
plug in as readers with zero changes to `_tick`.

**2. Features split into two kinds, only one expensive.** *Control-flow* features
(MERGE, OUTPUT, BY transitions) touch loop structure → live in/behind a `Phase`.
*State* features (RETAIN, sum, LAG/DIF) only need a durable home across the reset
boundary → the long-lived engine provides it for free, no new phase.

**3. Types are two; converters are the extension point.** SAS storage types are
just num + char. Dates/currency/etc. are num + a **format** (out) or **informat**
(in). So `register_format`/`register_informat` are the SAS-faithful way to teach
new representations. A `register_type` hook exists for clean-room storage types
(e.g. `decimal`) but is declare-only and off by default, to preserve fidelity.

## Verified semantics

- BY-group `first.`/`last.` over sorted input, nested across multiple BY vars.
- `RETAIN` + sum-style accumulation; reset-per-group via `if first.x`.
- Match-merge: positional (not cartesian); `IN=`; retain-on-exhaustion within a
  group; missing-when-absent (no cross-group leak); later-dataset-wins.
- `LAG_n`/`DIF_n` as execution-tied, call-site-keyed FIFO queues (incl. conditional).
- Typed slots: char truncation/length; `format` (PUT) display without mutating
  storage; the special-missing family (`._ < . < .A..Z <` numbers).
- KEEP / DROP / RENAME output projection.

## Database sources (sasstep_db.py)

A relational source is a **Reader**, not an engine change — the SAS/ACCESS-engine
analogue. `DatabaseReader` wraps any PEP 249 cursor, streams rows lazily via
`fetchmany`, and self-describes its schema through `declarations()`, which the
engine applies to type the frame.

The only per-database artifact is a **type map** from the driver's type code to
`(engine_type, length, format)`. Drivers disagree on what a type code *is*
(psycopg OIDs, PyMySQL FIELD_TYPE ints, oracledb DbType objects, pyodbc Python
types) but the map shape is identical. Maps provided for postgresql / mysql /
oracle / sqlserver.

- **Precision**: `NUMERIC`/`NUMBER` beyond ~15 digits routes to the `decimal`
  type (float64 would silently lose digits — a defect for money/clinical data).
- **Unmappable types** (json, arrays, uuid, blob): no num/char home → explicit
  policy (stringify / custom type / reject). `dialect_declare` *rejects* by default.
- **Dialect-named declaration**: declare in a database's own terms; both forms
  resolve through one `_resolve_named` core (so they can't drift), and promise a
  storage mapping ONLY — never the dialect's runtime semantics (rounding, fixed
  scale, collation). Clean-room convenience; SAS itself discards dialect on read.
  - *string form*: `dialect_declare("salary", "NUMBER(38,2)", "oracle")`.
  - *object form*: `Oracle.VARCHAR2(30)`, `Postgres.NUMERIC(8,2)`, `MySQL.DATETIME`,
    `SQLServer.MONEY` — namespaced `Dialect` objects whose attributes are typed
    constructors. Validate eagerly (a typo like `Oracle.VRACHAR2` raises at the
    point of use), and bare names work uncalled (`Oracle.DATE` == `Oracle.DATE()`).
    `cols(name=Oracle.VARCHAR2(3), salary=Oracle.NUMBER(38,2))` builds a declare
    list; identifier-named columns only, else `TypeRef.named("Order Date")`.
  - Four dialects supported (`Oracle`, `Postgres`, `MySQL`, `SQLServer`), defined
    once each by canonical type name in `NAME_TABLES`; the read-path code maps
    (`POSTGRESQL`/`MYSQL`/`ORACLE_BY_NAME`/`SQLSERVER`) derive from the same names.
  - `NUMERIC`/`NUMBER`/`DECIMAL`/`MONEY` route to `num` or `decimal` by precision.
    Unmappable types (`JSONB`, arrays, `uuid`, blobs) are *rejected* at declare
    time, not silently coerced.
- Push `ORDER BY`/`WHERE` into SQL (DB sorts/filters better; MergeReader requires
  sorted input — mind cross-database collation on merges). NULL → MISSING is
  clean, but SQL three-valued logic doesn't survive the crossing.

## Known gaps (deliberate, not bugs)

- **UPDATE**: a different reader (apply-non-missing-only, master/transaction).
- **PROC SORT**: MergeReader assumes sorted input; no sort/NOTSORTED path yet.
- **Permissive runtime**: bad numerics become MISSING, but `_ERROR_`/log
  semantics aren't fully modeled; strict-vs-permissive is still a clean fork.
- **Raw INPUT**: informats exist and are registered, but no column/text INPUT
  reader wires them in yet.
- **Decimal arithmetic in logic**: storage is exact, but mixing `Decimal` and
  `float` in user logic is the user's concern (no auto-promotion).
- **Same-line LAG/DIF**: keyed by source line; two on one line collide (`site=`
  overrides). An IR would remove the caveat.
- **Numeric representation**: native Python numbers kept (int stays int) rather
  than SAS's uniform float64 — immaterial to modeled semantics; documented.

## Where this sits

Reference interpreter (build-plan Phases 0–3) plus database ingestion. Next
structural step is an **IR**: lower user logic to inspectable nodes to classify
statements as vectorizable (no cross-row state) vs sequential (retained reads,
first./last., LAG). Vectorizable spans fuse into columnar ops; the sequential
residual runs through this engine. The IR also retires the same-line LAG caveat.

## Module map

- `sasstep.py` — engine core: Missing family, types/converters, Reader/SetReader/
  MergeReader, RecordFrame, ObservationEngine, LAG/DIF.
- `sasstep_db.py` — database readers: DatabaseReader, per-dialect type maps,
  the `decimal` type, dialect-named declaration.
