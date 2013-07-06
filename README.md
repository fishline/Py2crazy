Py2crazy
========

Py2crazy is CPython 2.7.5 hacked to support finer-grained tracing and
debugging.

Specifically, I've implemented three main features:

1. Debuggers now call the trace function at (roughly) each executed
bytecode rather than each new executed line.

2. Peephole optimizations are disabled so that bytecodes match source
code more closely.

3. Code objects now contain a new field called `code.co_coltab`, which
maps each bytecode instruction to a pair of line and column numbers, for
more precise debugging information.

