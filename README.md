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
maps each bytecode instruction to a pair of line and column numbers.


### Why would anyone do this?

I created Py2crazy to support finer-grained sub-expression-level tracing
for [Online Python Tutor](http://pythontutor.com). This [wiki
page](https://github.com/pgbovine/OnlinePythonTutor/blob/master/v3/docs/project-ideas.md#hack-cpython-to-enable-sub-expression-level-tracing)
discusses some of the rationale behind its design.

Although you might find some ideas in Py2crazy to be useful, its design
is ultimately driven by pedagogical goals, not by industrial-strength
debugging goals. Enjoy!


### How does Py2crazy debugger stepping differ from regular Python stepping?

Normally, the debugger (`pdb`) registers a tracing function into the
regular CPython interpreter and steps through the target program roughly
one line at a time.

However, when run in Py2crazy, `pdb` steps roughly one bytecode
instruction at a time, which provides much finer-grained tracing.

To illustrate the difference, run `pdb` on a test file in both regular
Python and Py2crazy:

    python -m pdb test.py


### Why disable peephole optimizations?

To make the Python source code and compiled bytecode correspond more
closely to one another, which helps in tracing and debugging
applications.


### How do you see line/column number information?

The line/column information is stored in a `code.co_coltab` field within
each compiled code object. This field is a dict mapping each bytecode
instruction offset to a pair of line and column numbers that (roughly)
corresponds to that instruction. (The mapping isn't nearly perfect, but
it's still better than nothing!)

Run the customized `dis` module within the Py2crazy distribution on any
test Python program.

    python -m dis test.py

You'll see not only line numbers (like in regular Python) but also an
extra tuple with line and column numbers alongside each bytecode
instruction.

Here's some example disassembly from the following line with line/column
number mappings, and the corresponding points in the source code.

    Source code line 7:
    "if foo() and (x + y > 7):"

    (7, 3)          21 LOAD_NAME                0 (foo)  if foo() and (x + y > 7):
                                                            ^
    (7, 3)          24 CALL_FUNCTION            0        if foo() and (x + y > 7):
                                                            ^
    (7, 3)          27 JUMP_IF_FALSE_OR_POP    43        if foo() and (x + y > 7):
                                                            ^
    (7, 14)         30 LOAD_NAME                1 (x)    if foo() and (x + y > 7):
                                                                       ^
    (7, 18)         33 LOAD_NAME                2 (y)    if foo() and (x + y > 7):
                                                                           ^
    (7, 16)         36 BINARY_ADD                        if foo() and (x + y > 7):
                                                                         ^
    (7, 22)         37 LOAD_CONST               3 (7)    if foo() and (x + y > 7):
                                                                               ^
    (7, 20)         40 COMPARE_OP               4 (>)    if foo() and (x + y > 7):
                                                                             ^
    (7, 20)    >>   43 POP_JUMP_IF_FALSE       54        if foo() and (x + y > 7):
                                                                             ^


### Changelog

Created on 2013-07-03 by [Philip Guo](http://www.pgbovine.net/)
(philip@pgbovine.net)

