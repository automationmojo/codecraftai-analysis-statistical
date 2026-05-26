"""
sasstep_columnar -- columnar output for the fully-vectorizable path.

The benchmark in sasstep_exec showed the truth: for a pure transform the
arithmetic was already cheap; building one Python dict per row dominated. So the
fix is not faster arithmetic -- it's NOT MATERIALIZING ROWS. A ColumnFrame holds
results as arrays and yields row dicts only on demand. A pipeline of vectorizable
steps then stays columnar end to end, paying O(columns) array ops instead of
O(rows) dict builds.

ColumnarStep.run_columnar accepts either rows or a ColumnFrame, so vectorized
steps chain directly array-to-array with zero materialization between them.
Hybrid/fallback steps still go through the row loop (they must) and are wrapped
back into a ColumnFrame for a uniform return type.
"""
from __future__ import annotations
import numpy as np

from sasstep_exec import CompiledStep, _veval, _columns, _scalar


class ColumnFrame:
    """Columnar result: {name: ndarray}. Rows are materialized lazily."""
    def __init__(self, columns, n, order):
        self._cols = columns; self._n = n; self._order = list(order)

    @property
    def columns(self): return list(self._order)
    def __len__(self): return self._n
    def array(self, name): return self._cols[name]

    def __getitem__(self, key):
        if isinstance(key, str):
            return self._cols[key]                          # column (no materialization)
        if isinstance(key, int):
            return {k: _scalar(self._cols[k][key]) for k in self._order}  # one row
        raise TypeError(key)

    def __iter__(self):                                     # lazy row materialization
        for i in range(self._n):
            yield {k: _scalar(self._cols[k][i]) for k in self._order}

    def to_dicts(self): return list(self)
    def head(self, k=5): return [self[i] for i in range(min(k, self._n))]
    def to_pandas(self):
        import pandas as pd
        return pd.DataFrame({k: self._cols[k] for k in self._order})
    def to_arrow(self):
        import pyarrow as pa
        return pa.table({k: self._cols[k] for k in self._order})

    @classmethod
    def from_dicts(cls, rows):
        if not rows:
            return cls({}, 0, [])
        order = list(rows[0].keys())
        cols = {k: np.array([r.get(k) for r in rows]) for k in order}
        return cls(cols, len(rows), order)


class ColumnarStep(CompiledStep):
    def run_columnar(self, data) -> ColumnFrame:
        # accept a ColumnFrame (chain array-to-array) or a list of row dicts
        if isinstance(data, ColumnFrame):
            order = data.columns
            cols = {k: data.array(k) for k in order}
            n = len(data)
            rows = None
        else:
            rows = list(data)
            if not rows:
                return ColumnFrame({}, 0, [])
            order = list(rows[0].keys())
            cols = _columns(rows)
            n = len(rows)

        path, batch, loop = self.plan(order)

        if path == "vector":                                # no row materialization at all
            order = list(order)
            for s in batch:
                v = _veval(s.expr, cols)
                cols[s.target] = v if np.ndim(v) else np.full(n, v)
                if s.target not in order:
                    order.append(s.target)
            return ColumnFrame(cols, n, order)

        # hybrid / fallback must use the row loop; wrap result back to columnar
        src = rows if rows is not None else list(data)
        return ColumnFrame.from_dicts(self.run(src))


if __name__ == "__main__":
    import time
    from sasstep import ObservationEngine, SetReader

    def reference(rows, logic, **kw):
        return list(ObservationEngine(SetReader(list(rows), by=kw.get("by", [])),
                                      logic, **kw))

    def transform(pdv):
        pdv["gross"] = pdv["qty"] * pdv["price"]
        pdv["net"] = pdv["gross"] * (1 - pdv["disc"])
        pdv["tax"] = pdv["net"] * 0.2
        pdv["total"] = pdv["net"] + pdv["tax"]

    # ---- correctness: columnar materialized == reference -------------------
    small = [{"qty": 2, "price": 60.0, "disc": 0.1},
             {"qty": 1, "price": 200.0, "disc": 0.0}]
    cf = ColumnarStep(transform).run_columnar(small)
    print("# columnar.to_dicts() == reference:", cf.to_dicts() == reference(small, transform))
    print("# columns kept as arrays:", cf.columns)

    # ---- pipeline: two vector steps chain array-to-array, no materialization
    def step2(pdv):
        pdv["margin"] = pdv["net"] / pdv["gross"]
        pdv["after_tax_pct"] = pdv["total"] / pdv["gross"]
    cf1 = ColumnarStep(transform).run_columnar(small)
    cf2 = ColumnarStep(step2).run_columnar(cf1)             # consumes ColumnFrame directly
    print("# chained pipeline columns:", cf2.columns)
    print("# chained row 0:", cf2[0])

    # ---- benchmark: 500k rows, pure transform ------------------------------
    N = 500_000
    big = [{"qty": i % 7 + 1, "price": float(i % 100 + 1), "disc": (i % 5) / 10.0}
           for i in range(N)]
    t0 = time.perf_counter(); r_ref = reference(big, transform); t1 = time.perf_counter()
    step = ColumnarStep(transform)
    t2 = time.perf_counter(); cfb = step.run_columnar(big); t3 = time.perf_counter()
    t4 = time.perf_counter(); _ = cfb.to_dicts(); t5 = time.perf_counter()

    ref_t, col_t, mat_t = t1 - t0, t3 - t2, t5 - t4
    print(f"\n# benchmark on {N:,} rows (pure transform)")
    print(f"  reference engine (dicts) : {ref_t:7.3f}s")
    print(f"  columnar (arrays only)   : {col_t:7.3f}s   ({ref_t / col_t:6.1f}x faster)")
    print(f"  + materialize to dicts   : {mat_t:7.3f}s   (only if a consumer needs rows)")
    print(f"  columnar correct vs ref  : {cfb[0] == r_ref[0] and cfb[N-1] == r_ref[N-1]}")

    # ---- export -------------------------------------------------------------
    df = cfb.to_pandas()
    print(f"\n# to_pandas(): {df.shape[0]:,} rows x {df.shape[1]} cols; head net values:",
          list(df['net'].head(3)))
