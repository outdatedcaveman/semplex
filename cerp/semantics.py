"""Semantic domain for fragment F0: total Boolean functions on a finite,
named, ordered variable set.

A TruthTable *is* the extensional meaning [[C]] of an artifact in F0.
Assignment index i encodes var j as bit (n-1-j) of i, so var[0] is the MSB.

This module is the "main" interpreter stack. It is deliberately separate
from cerp.kernel; the two are cross-checked in tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterator


@dataclass(frozen=True)
class TruthTable:
    vars: tuple
    bits: int  # bit i set  <=>  f(assignment i) == 1

    @property
    def n(self) -> int:
        return len(self.vars)

    @property
    def size(self) -> int:
        return 1 << self.n

    @classmethod
    def from_function(cls, vars, fn: Callable[[dict], int]) -> "TruthTable":
        vars = tuple(vars)
        bits = 0
        for i, env in enumerate(assignments(vars)):
            if fn(env):
                bits |= 1 << i
        return cls(vars, bits)

    @classmethod
    def const(cls, vars, value: int) -> "TruthTable":
        return cls(tuple(vars), ((1 << (1 << len(vars))) - 1) if value else 0)

    def __call__(self, env: dict) -> int:
        return (self.bits >> self.index(env)) & 1

    def at(self, i: int) -> int:
        return (self.bits >> i) & 1

    def index(self, env: dict) -> int:
        i = 0
        for v in self.vars:
            i = (i << 1) | env[v]
        return i

    def env(self, i: int) -> dict:
        n = self.n
        return {v: (i >> (n - 1 - j)) & 1 for j, v in enumerate(self.vars)}

    def ones(self) -> Iterator[int]:
        b, i = self.bits, 0
        while b:
            if b & 1:
                yield i
            b >>= 1
            i += 1

    def count(self) -> int:
        return bin(self.bits).count("1")

    def __and__(self, o): return self._bin(o, self.bits & o.bits)
    def __or__(self, o): return self._bin(o, self.bits | o.bits)
    def __xor__(self, o): return self._bin(o, self.bits ^ o.bits)
    def __invert__(self): return TruthTable(self.vars, self.bits ^ ((1 << self.size) - 1))

    def _bin(self, o, bits):
        if o.vars != self.vars:
            raise ValueError("variable sets differ")
        return TruthTable(self.vars, bits)

    def support(self) -> frozenset:
        """Variables the function actually depends on (over the full domain)."""
        out = set()
        for j, v in enumerate(self.vars):
            mask = 1 << (self.n - 1 - j)
            if any(self.at(i) != self.at(i ^ mask) for i in range(self.size) if not i & mask):
                out.add(v)
        return frozenset(out)


def assignments(vars) -> Iterator[dict]:
    n = len(vars)
    for i in range(1 << n):
        yield {v: (i >> (n - 1 - j)) & 1 for j, v in enumerate(vars)}
