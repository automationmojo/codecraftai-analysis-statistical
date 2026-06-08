==========================
Examples
==========================

This folder contains two kinds of files:

**Reference engine modules** (``sasstep*.py``)
    Faithful Python renderings of the SAS DATA-step execution model that act
    as the documented correctness oracle for the production package. They are
    *not* meant to be imported by user code. The production package mirrors
    every behavior in ``source/packages/ccai/analysis/statistical/`` and
    pins parity against these modules via the ``oracle`` test subtree.

**Usage examples** (``example_*.py``)
    Runnable scripts that demonstrate the production package's public surface.
    Each script is self-contained -- run any one as
    ``python example_NN_*.py`` after running ``poetry install``. The eight
    examples cover, in order:

    01. by-group accumulation (the canonical SAS DATA step in Python),
    02. match-merge with ``IN=`` flags,
    03. ``LAG`` / ``DIF`` stateful functions,
    04. KEEP / DROP / RENAME output projection,
    05. database source over SQLite,
    06. dialect-named declarations and precision routing,
    07. ``CompiledStep`` vector / hybrid / fallback paths with timing,
    08. columnar pipeline and pandas export,
    09. migration / optimization advisor,
    10. registering a custom format class.

Each example prints labeled output and ends cleanly so you can run them in a
terminal and copy-paste fragments into your own code. They mirror the worked
ports in :doc:`../../userguide/20-07-porting-sas-jobs-to-python`.
