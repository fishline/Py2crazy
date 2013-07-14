Py2crazy
========

Py2crazy is CPython 2.7.5 hacked to support finer-grained tracing and debugging.

I've implemented three main features:

1. Each instruction in compiled Python bytecode now maps to a precise line number
and range of column numbers corresponding to the source code snippet that produced that bytecode.

2. Peephole optimizations are disabled so that bytecodes match source
code more closely.

3. Debuggers now call the trace function at (roughly) each executed
bytecode rather than each new executed line.


### Why would anyone do this?

I created Py2crazy to support finer-grained expression-level tracing
in [Online Python Tutor](http://pythontutor.com). This [wiki
page](https://github.com/pgbovine/OnlinePythonTutor/blob/master/v3/docs/project-ideas.md#hack-cpython-to-enable-sub-expression-level-tracing)
discusses some of the design rationale.

To illustrate:

- Running Online Python Tutor with Py2crazy provides fine-grained
<a href="http://pythontutor.com/visualize.html#code=def+foo()%3A%0A++return+True%0A%0Ax+%3D+3%0Ay+%3D+5%0A%0Aif+foo()+and+(x+%2B+y+%3E+7)%3A%0A++print+'YES'%0Aelse%3A%0A++print+'NO'&mode=display&cumulative=false&heapPrimitives=false&drawParentPointers=false&textReferences=false&showOnlyOutputs=false&py=2crazy&curInstr=0">expression-level stepping</a>.

- In contrast, running with regular Python 2.7 supports only
<a href="http://pythontutor.com/visualize.html#code=def+foo()%3A%0A++return+True%0A%0Ax+%3D+3%0Ay+%3D+5%0A%0Aif+foo()+and+(x+%2B+y+%3E+7)%3A%0A++print+'YES'%0Aelse%3A%0A++print+'NO'&mode=display&cumulative=false&heapPrimitives=false&drawParentPointers=false&textReferences=false&showOnlyOutputs=false&py=2&curInstr=0">line-level stepping</a>
like in an ordinary `pdb` style debugger.


### Precise line and column information in bytecodes

Here's an illustration of the first (and most significant) feature. If you compile this code

    x = 5
    y = 13
    if (x + 5 > 7) and (y - 3 == 10):
        print 'You win'

with regular Python 2.7.5 and disassemble it, you get roughly the following bytecode:
![compiled with Python](screenshots/python-regular-example.png)

Note that each bytecode instruction maps to one line of source code.

In contrast, if you compile this code with Py2crazy and disassemble, you can see that each bytecode
maps to not only a line, but also a precise range of columns within that line (highlighted in yellow):

![compiled with Py2crazy](screenshots/py2crazy-example.png)

This level of detail makes it possible to create much more fine-grained tracing and debugging tools!


### How do you view line and column number information?

Compile Py2crazy and then run the special
"Super Disassembler" ([Python-2.7.5/lib/super_dis.py](https://github.com/pgbovine/Py2crazy/blob/master/Python-2.7.5/Lib/super_dis.py))
module on a Python source file to see detailed line/number column information:

    Py2crazy/Python-2.7.5/python -m super_dis test.py

Most terminals support colors, so you should be able to see the yellow highlights.

Note that `super_dis.py` works only with Py2crazy, not with regular Python.


### How does Py2crazy debugger stepping differ from regular Python stepping?

Normally, the debugger (`pdb`) registers a tracing function into the
regular CPython interpreter and steps through the target program roughly
one line at a time.

However, when run in Py2crazy, `pdb` steps roughly one bytecode
instruction at a time, which provides much finer-grained tracing.

To illustrate the difference, run `pdb` on a test file in both regular
Python and Py2crazy:

    Py2crazy/Python-2.7.5/python -m pdb test.py


### Why disable peephole optimizations?

To make the Python source code and compiled bytecode correspond more
closely to one another, which helps in tracing and debugging
applications.


### What did you change in CPython 2.7.5?

Check out the Git repo and run

    git diff d36dfc8ffaf5337adb96bd582e0733fe2ffe3f02

to see diffs against a fresh Python 2.7.5 source distribution.

Although you might find some ideas in Py2crazy to be useful, its design
is ultimately driven by pedagogical goals, not by industrial-strength
debugging goals. For instance, efficiency wasn't a major concern.


### Footer

Created on 2013-07-03 by [Philip Guo](http://www.pgbovine.net/)
(philip@pgbovine.net)

Special thanks to [Ned Batchelder](http://nedbatchelder.com/) for inspiring this project, and for providing technical guidance.

