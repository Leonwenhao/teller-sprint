"""XBRL and other validation layers consumed by `Agent.ask`.

Modules in this package are called only during result assembly; they must
not perform network I/O and must not raise unhandled exceptions into the
agent loop. Every validator returns a typed result with an `available`
flag and an abstention `reason` when it cannot answer.
"""
