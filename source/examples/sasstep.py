"""
sasstep -- a reference implementation of the SAS DATA-step execution model.

Correctness oracle, not the fast path. See DESIGN.md for the architecture.

This revision closes the variable-tracking gaps:
  * typed slots: each variable carries (type, length, format, informat), not
    just a value -- so character truncation/padding and value formatting work;
  * an EXTENSIBLE converter layer (formats + informats), which is SAS's actual
    extension mechanism -- dates/currency/etc. are num + a format, never a type;
  * a small, defaulted type registry (num/char) with a hook for custom storage
    types -- clean-room fork only; off by default to preserve SAS fidelity;
  * the special-missing family (._ , . , .A-.Z) with SAS ordering;
  * KEEP / DROP / RENAME as an output projection.

The register file is now its own object, RecordFrame; ObservationEngine owns one
and drives it through the implicit loop.
"""
from __future__ import annotations

import re
import sys
from abc import ABC, abstractmethod
from collections import deque
from datetime import date, timedelta
from enum import Enum, auto
from typing import Any, Callable, Iterable, Iterator, Optional

__all__ = [
    "Missing", "MISSING", "missing", "Phase",
    "Reader", "SetReader", "MergeReader",
    "RecordFrame", "ObservationEngine",
    "register_type", "register_format", "register_informat",
    "NUM", "CHAR",
]


# ============================================================================
# Missing values: plain (.), underscore (._), and special (.A-.Z).
# Ordering (SAS): ._  <  .  <  .A < .B < ... < .Z  <  every real number.
# ============================================================================
class Missing:
    __slots__ = ("tag",)
    _cache: dict = {}

    def __new__(cls, tag: str = ""):
        if tag not in cls._cache:
            obj = super().__new__(cls)
            obj.tag = tag
            cls._cache[tag] = obj
        return cls._cache[tag]

    def _order(self) -> int:
        if self.tag == "_": return -2
        if self.tag == "":  return -1
        return ord(self.tag) - ord("A")          # 0..25 for .A-.Z

    def __repr__(self):
        return "._" if self.tag == "_" else ("." + self.tag)

    def __eq__(self, other):
        return isinstance(other, Missing) and other.tag == self.tag

    def __lt__(self, other):
        if isinstance(other, Missing):
            return self._order() < other._order()
        return True                               # any missing < any number

    def __le__(self, other): return self == other or self < other
    def __gt__(self, other): return not self.__le__(other)
    def __ge__(self, other): return not self.__lt__(other)
    def __hash__(self): return hash(("__missing__", self.tag))


MISSING = Missing("")          # the plain numeric missing, "."
def missing(tag: str = "") -> Missing:
    """Get a missing value: missing() -> . ; missing('_') -> ._ ; missing('A') -> .A"""
    return Missing(tag.upper() if tag.isalpha() else tag)


# ============================================================================
# Storage types: a tiny registry. SAS core == num + char. Custom types are a
# clean-room fork extension (declare-only; not inferred).
# ============================================================================
NUM, CHAR = "num", "char"


class TypeHandler:
    def __init__(self, name: str, coerce: Callable[[Any, int], Any],
                 missing_value: Any, default_length: int):
        self.name = name
        self.coerce = coerce                      # (value, length) -> stored value
        self.missing = missing_value
        self.default_length = default_length


TYPES: dict[str, TypeHandler] = {}
def register_type(handler: TypeHandler): TYPES[handler.name] = handler


def _coerce_num(value, length):
    if isinstance(value, Missing): return value
    if isinstance(value, bool):    return 1 if value else 0
    if isinstance(value, (int, float)): return value      # native kept (SAS: float64)
    try:    return float(value)
    except (TypeError, ValueError):
        return MISSING                            # permissive: bad numeric -> missing


def _coerce_char(value, length):
    if isinstance(value, Missing): return ""      # char missing == blank
    s = value if isinstance(value, str) else format_value(value, None)
    return s[:length]                             # fixed length: silent truncation


register_type(TypeHandler(NUM, _coerce_num, MISSING, 8))
register_type(TypeHandler(CHAR, _coerce_char, "", 1))


def _infer_type(value) -> str:
    return CHAR if isinstance(value, str) else NUM


# ============================================================================
# Converters: formats (value -> text) and informats (text -> value). THIS is the
# SAS extension point. Register your own to teach the engine new representations.
# A format spec is like "DOLLAR8.2" / "DATE9." / "8.2" / "$10." -> (name,w,d).
# ============================================================================
FORMATS: dict[str, Callable[[Any, Optional[int], Optional[int]], str]] = {}
INFORMATS: dict[str, Callable[[str, Optional[int]], Any]] = {}
def register_format(name, fn):   FORMATS[name.upper()] = fn
def register_informat(name, fn): INFORMATS[name.upper()] = fn

_SPEC = re.compile(r"^(\$?[A-Za-z]*)(\d+)?\.?(\d+)?$")

def _parse_spec(spec: Optional[str]):
    if not spec: return "", None, None
    m = _SPEC.match(spec)
    if not m: return "", None, None
    name, w, d = m.group(1).upper(), m.group(2), m.group(3)
    return name, (int(w) if w else None), (int(d) if d else None)

def format_value(value, spec: Optional[str]) -> str:
    """Apply a format spec to a value (the PUT operation)."""
    if isinstance(value, Missing): return repr(value)
    name, w, d = _parse_spec(spec)
    fn = FORMATS.get(name)
    if fn is None:                                # default (BEST. / $.)
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)
    return fn(value, w, d)

def input_value(text: str, spec: Optional[str]) -> Any:
    """Apply an informat to raw text (the INPUT operation)."""
    name, w, _ = _parse_spec(spec)
    fn = INFORMATS.get(name)
    return fn(text, w) if fn else text

# --- a few built-ins, to demonstrate the registry (not exhaustive) ---------
_MONTHS = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"]
_EPOCH = date(1960, 1, 1)

register_format("DOLLAR", lambda v, w, d: f"${v:,.{d or 0}f}")
register_format("COMMA",  lambda v, w, d: f"{v:,.{d or 0}f}")
register_format("DATE",   lambda v, w, d: (_EPOCH + timedelta(days=int(v))).strftime(
    f"%d{_MONTHS[(_EPOCH + timedelta(days=int(v))).month - 1]}%Y").replace(
    (_EPOCH + timedelta(days=int(v))).strftime("%b").upper(),
    _MONTHS[(_EPOCH + timedelta(days=int(v))).month - 1]))
register_format("$",      lambda v, w, d: str(v).ljust(w or len(str(v)))[: (w or len(str(v)))])

register_informat("DATE",   lambda t, w: (
    date(int(t[5:9]), _MONTHS.index(t[2:5].upper()) + 1, int(t[0:2])) - _EPOCH).days)
register_informat("DOLLAR", lambda t, w: float(t.replace("$", "").replace(",", "")))
register_informat("COMMA",  lambda t, w: float(t.replace(",", "")))


# ============================================================================
# Implicit-loop phases
# ============================================================================
class Phase(Enum):
    TOP_OF_STEP = auto(); READ = auto(); EXECUTE = auto(); BOTTOM = auto(); DONE = auto()


# ============================================================================
# Readers (the READ-phase strategies) -- unchanged contract
# ============================================================================
class _Peekable:
    def __init__(self, it): self._it = iter(it); self._buf = deque(); self._eof = False
    def _fill(self):
        if not self._buf and not self._eof:
            try: self._buf.append(next(self._it))
            except StopIteration: self._eof = True
    def peek(self): self._fill(); return self._buf[0] if self._buf else None
    def pop(self):
        self._fill()
        if not self._buf: raise StopIteration
        return self._buf.popleft()


class Reader(ABC):
    """Every reader returns (row, in_flags, cur_key, next_key)."""
    @abstractmethod
    def has_more(self) -> bool: ...
    @abstractmethod
    def next_obs(self): ...


class SetReader(Reader):
    def __init__(self, source, by=None):
        self._src = _Peekable(source); self._by = by or []
    def _key(self, r): return tuple(r.get(b) for b in self._by) if r is not None else None
    def has_more(self): return self._src.peek() is not None
    def next_obs(self):
        row = self._src.pop()
        return row, {}, self._key(row), self._key(self._src.peek())


class MergeReader(Reader):
    def __init__(self, sources, by, in_flags=None):
        self._cur = {n: _Peekable(s) for n, s in sources.items()}
        self._by = by; self._in = in_flags or {}
        self._work = {}; self._group = None; self._active = False
    def _key(self, r): return tuple(r.get(b) for b in self._by)
    def _min_front(self):
        ks = [self._key(c.peek()) for c in self._cur.values() if c.peek() is not None]
        return min(ks) if ks else None
    def has_more(self): return self._active or self._min_front() is not None
    def next_obs(self):
        if not self._active:
            g = self._min_front()
            if g is None: raise StopIteration
            self._group = g; self._active = True
            for k in list(self._work): self._work[k] = MISSING
        in_result = {}
        for name, cur in self._cur.items():
            front = cur.peek()
            matched = front is not None and self._key(front) == self._group
            if name in self._in: in_result[self._in[name]] = 1 if matched else 0
            if matched:
                for k, v in cur.pop().items(): self._work[k] = v
        for b, v in zip(self._by, self._group): self._work[b] = v
        cur_key = self._group
        still = any(c.peek() is not None and self._key(c.peek()) == self._group
                    for c in self._cur.values())
        if still: next_key = self._group
        else: self._active = False; next_key = self._min_front()
        return dict(self._work), in_result, cur_key, next_key


# ============================================================================
# RecordFrame -- the Program Data Vector: a typed register file for one obs.
# Holds per-variable (type, length, format, informat, value, retain) and owns
# the reset/retain rule and coercion. This is the object the engine advances.
# ============================================================================
class Slot:
    __slots__ = ("stype", "length", "fmt", "informat", "value", "retain")
    def __init__(self, stype, length, fmt=None, informat=None, retain=False):
        self.stype = stype; self.length = length
        self.fmt = fmt; self.informat = informat
        self.retain = retain
        self.value = TYPES[stype].missing if stype == NUM else ""


class RecordFrame:
    def __init__(self):
        self._slots: dict[str, Slot] = {}        # insertion order == PDV order

    # -- declaration / typing --
    def declare(self, name, stype=NUM, length=None, fmt=None, informat=None,
                retain=False, init=None):
        length = length if length is not None else TYPES[stype].default_length
        slot = Slot(stype, length, fmt, informat, retain)
        if init is not None:
            slot.value = TYPES[stype].coerce(init, length)
        self._slots[name] = slot
        return slot

    # -- value access with coercion --
    def get(self, name): 
        s = self._slots.get(name); return s.value if s else MISSING
    def set(self, name, value):
        slot = self._slots.get(name)
        if slot is None:                          # auto-create on first assignment
            st = _infer_type(value) if not isinstance(value, Missing) else NUM
            length = len(value) if (st == CHAR and isinstance(value, str)) \
                else TYPES[st].default_length
            slot = self.declare(name, st, length)
        slot.value = TYPES[slot.stype].coerce(value, slot.length)

    # -- retain / reset (the load-bearing rule) --
    def mark_retained(self, name):
        if name in self._slots: self._slots[name].retain = True
    def reset_non_retained(self):
        for slot in self._slots.values():
            if not slot.retain:
                slot.value = TYPES[slot.stype].missing if slot.stype == NUM else ""
    def load(self, row):                          # source read: set + retain
        for k, v in row.items():
            self.set(k, v); self._slots[k].retain = True

    # -- formatting (PUT) --
    def formatted(self, name, spec=None):
        s = self._slots.get(name)
        if s is None: return repr(MISSING)
        return format_value(s.value, spec if spec is not None else s.fmt)

    # -- output projection (KEEP / DROP / RENAME) --
    def snapshot(self, keep=None, drop=None, rename=None):
        rename = rename or {}
        out = {}
        for name, slot in self._slots.items():
            if keep is not None and name not in keep: continue
            if drop and name in drop: continue
            out[rename.get(name, name)] = slot.value
        return out


# ============================================================================
# Stateful functions -- LAG/DIF, call-site-keyed FIFO queues
# ============================================================================
class _StatefulFunctions:
    _lagq: dict
    def _site(self, tag, depth):
        f = sys._getframe(depth); return (tag, f.f_code.co_filename, f.f_lineno)
    def lag(self, value, n=1, site=None):
        if site is None: site = self._site("LAG", 2)
        key = (site, n)
        q = self._lagq.get(key)
        if q is None:
            q = deque([MISSING] * n, maxlen=n); self._lagq[key] = q
        front = q[0]; q.append(value); return front
    def dif(self, value, n=1):
        site = self._site("DIF", 2)
        prev = self.lag(value, n, site=site)
        if isinstance(prev, Missing) or isinstance(value, Missing): return MISSING
        return value - prev


# ============================================================================
# ObservationEngine -- the implicit-loop iterator; owns a RecordFrame.
# ============================================================================
class ObservationEngine(_StatefulFunctions):
    def __init__(self, reader, logic, by=None, retain=None, declare=None,
                 keep=None, drop=None, rename=None):
        self._reader = reader; self._logic = logic; self._by = by or []
        self._frame = RecordFrame()
        if hasattr(reader, "declarations"):       # source-supplied schema (e.g. DB cursor)
            for d in reader.declarations():
                self._frame.declare(**d)
        for d in (declare or []):                 # explicit decls override the source
            self._frame.declare(**d)
        for name, init in (retain or {}).items():
            slot = self._frame._slots.get(name)
            if slot is not None:
                slot.retain = True
                slot.value = TYPES[slot.stype].coerce(init, slot.length)
            else:
                st = _infer_type(init) if not isinstance(init, Missing) else NUM
                self._frame.declare(name, st, retain=True, init=init)
        self._keep, self._drop, self._rename = keep, drop, rename

        self._prev_key = None
        self.first = {}; self.last = {}; self.in_ = {}
        self.n = 0; self.eof = False
        self._lagq = {}
        self._outbuf = deque(); self._explicit_output = False; self._deleted = False
        self.phase = Phase.TOP_OF_STEP

    # variable access delegates to the frame
    def __getitem__(self, k): return self._frame.get(k)
    def __setitem__(self, k, v): self._frame.set(k, v)
    @property
    def frame(self): return self._frame
    def put(self, name, spec=None): return self._frame.formatted(name, spec)

    def output(self):
        self._outbuf.append(self._frame.snapshot(self._keep, self._drop, self._rename))
        self._explicit_output = True
    def delete(self): self._deleted = True

    def __iter__(self): return self
    def __next__(self):
        while not self._outbuf: self._tick()
        return self._outbuf.popleft()

    def _flags(self, cur_key, next_key):
        for i, b in enumerate(self._by):
            pfx = cur_key[: i + 1]
            self.first[b] = self._prev_key is None or self._prev_key[: i + 1] != pfx
            self.last[b] = next_key is None or next_key[: i + 1] != pfx
        self._prev_key = cur_key

    def _tick(self):
        if self.phase is Phase.DONE: raise StopIteration
        # TOP OF STEP
        self._frame.reset_non_retained()
        self._explicit_output = False; self._deleted = False
        # READ
        if not self._reader.has_more():
            self.phase = Phase.DONE; raise StopIteration
        row, in_flags, cur_key, next_key = self._reader.next_obs()
        self.n += 1
        self._frame.load(row)
        self.in_ = in_flags
        self.eof = not self._reader.has_more()
        self._flags(cur_key, next_key)
        # EXECUTE
        self._logic(self)
        # BOTTOM
        if not self._deleted and not self._explicit_output:
            self._outbuf.append(self._frame.snapshot(self._keep, self._drop, self._rename))


# ============================================================================
# Self-test
# ============================================================================
if __name__ == "__main__":
    def show(title, rows):
        print(f"\n# {title}")
        for r in rows:
            print("  " + "  ".join(f"{k}={v}" for k, v in r.items()))

    # (1) by-group accumulate  -- unchanged behavior
    sales = [
        {"region": "East", "customer": "A", "amount": 10},
        {"region": "East", "customer": "A", "amount": 15},
        {"region": "East", "customer": "B", "amount": 7},
        {"region": "West", "customer": "C", "amount": 20},
        {"region": "West", "customer": "C", "amount": 5},
    ]
    def accumulate(p):
        if p.first["customer"]: p["total"] = 0
        p["total"] = p["total"] + p["amount"]
        if p.last["customer"]: p.output()
    show("by-group accumulate",
         list(ObservationEngine(SetReader(sales, by=["region", "customer"]),
              accumulate, by=["region", "customer"], retain={"total": 0})))

    # (2) match-merge -- unchanged behavior
    A = [{"id": 1, "a": 10}, {"id": 1, "a": 20}, {"id": 2, "a": 30}]
    B = [{"id": 1, "b": 100}, {"id": 2, "b": 200}, {"id": 2, "b": 300}]
    mr = MergeReader({"A": A, "B": B}, by=["id"], in_flags={"A": "inA", "B": "inB"})
    def passthrough(p): p["inA"], p["inB"] = p.in_["inA"], p.in_["inB"]
    show("match-merge", list(ObservationEngine(mr, passthrough, by=["id"])))

    # (3) lag / dif -- unchanged behavior
    def lags(p):
        p["lag_all"] = p.lag(p["x"]); p["dif_all"] = p.dif(p["x"])
        if p["x"] % 2 == 1: p["lag_odd"] = p.lag(p["x"])
    show("lag / dif", list(ObservationEngine(SetReader([{"x": v} for v in (1,2,3,4,5)]), lags)))

    # (4) NEW: typed char truncation + formats (PUT)
    def typed(p):
        p["label"] = p["name"]                    # CHAR(3): truncates
        p["shown_amt"] = p.put("amt", "DOLLAR10.2")
        p["shown_dt"] = p.put("dt", "DATE9.")
    rows = [{"name": "HELLO", "amt": 1234.5, "dt": 0},
            {"name": "HI", "amt": 9.0, "dt": 366}]
    show("typed char + formats",
         list(ObservationEngine(SetReader(rows), typed,
              declare=[{"name": "label", "stype": CHAR, "length": 3}])))

    # (5) NEW: special missing values + SAS ordering
    vals = [3, missing("A"), missing("_"), 1, MISSING, missing("B")]
    print("\n# special missings, sorted ascending")
    print("  ", sorted(vals))

    # (6) NEW: KEEP / DROP / RENAME projection
    def proj(p): p["doubled"] = p["x"] * 2
    show("keep/drop/rename (keep x->n, doubled)",
         list(ObservationEngine(SetReader([{"x": 5}, {"x": 8}]), proj,
              keep=["x", "doubled"], rename={"x": "n"})))
