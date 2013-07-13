"""A "Super" Python Bytecode Disassembler for Py2crazy"""
# Created by Philip Guo on 2013-07-12
# based on coverage.py/lab/disgen.py by Ned Batchelder
# https://bitbucket.org/ned/coveragepy

import sys
import types
import collections

import ast_extents
import inspect

from opcode import *
from opcode import __all__ as _opcodes_all

__all__ = ["dis", "disassemble", "distb", "disco",
           "findlinestarts", "findlabels"] + _opcodes_all
del _opcodes_all

def dis(x=None, filename=None, source=None):
    extent_map = ast_extents.create_extent_map(source)
    source_lines = source.splitlines()

    child_code = set()
    for disline in disgen(x):
        if disline.code_obj:
            child_code.add(disline.code_obj)
        if disline.first and disline.offset > 0:
            print('')
        print(format_dis_line(disline, source_lines, extent_map))

    # recurse (TODO: how to avoid infinite loops?)
    for c in child_code:
        if c.co_filename == filename and c.co_name != '<genexpr>':
            print
            print 'Disassembling function', c.co_name
            dis(c, filename, source)


YELLOW_BG = '\033[43m'
BLACK_FG = '\033[30m'
STOP_FG = '\033[39m'
STOP_BG = '\033[49m'

def highlight(s):
  return YELLOW_BG + BLACK_FG + s + STOP_FG + STOP_BG

def format_dis_line(disline, source_lines, extent_map):
    lc = (disline.lineno, disline.column)
    cod_line = source_lines[disline.lineno - 1]

    if disline.first:
        lineno = '%3d' % disline.lineno
    else:
        lineno = '   '

    if lc in extent_map:
      start_col, extent = extent_map[lc]
    else:
      # boring defaults
      start_col, extent = disline.column, 1

    cod_line = cod_line[:start_col] + \
               highlight(cod_line[start_col:start_col+extent]) + \
               cod_line[start_col+extent:]

    if disline.target:
        label = ">>"
    else:
        label = "  "
    return "%s %s %4r %-20s %s" % (lineno, label, disline.offset, disline.opcode, cod_line)

def disgen(x=None):
    """Disassemble methods, functions, or code.

    With no argument, disassemble the last traceback.

    """
    if x is None:
        return distb()
    if hasattr(x, 'im_func'):
        x = x.im_func
    if hasattr(x, 'func_code'):
        x = x.func_code
    if hasattr(x, 'co_code'):
        return disassemble(x)
    else:
        raise TypeError(
            "don't know how to disassemble %s objects" %
            type(x).__name__
        )

def distb(tb=None):
    """Disassemble a traceback (default: last traceback)."""
    if tb is None:
        try:
            tb = sys.last_traceback
        except AttributeError:
            raise RuntimeError("no last traceback to disassemble")
        while tb.tb_next: 
            tb = tb.tb_next
    return disassemble(tb.tb_frame.f_code, tb.tb_lasti)

DisLine = collections.namedtuple(
    'DisLine',
    "lineno column first target offset opcode oparg argstr code_obj"
    )

def disassemble(co, lasti=-1):
    """Disassemble a code object."""
    code = co.co_code
    labels = findlabels(code)
    linestarts = dict(findlinestarts(co))
    n = len(code)
    i = 0
    extended_arg = 0
    free = None

    dislines = []
    lineno = linestarts[0]

    while i < n:
        op = byte_from_code(code, i)
        first = i in linestarts
        if first:
            lineno = linestarts[i]

        #if i == lasti: print '-->',
        #else: print '   ',
        target = i in labels
        offset = i
        opcode = opname[op]

        try:
            line_dup, column = co.co_coltab[i]
        except KeyError:
            # when there's an error, punt to column 0
            line_dup, column = lineno, 0
        assert lineno == line_dup

        code_obj = None # is this loading a code object that we should
                        # maybe recurse into?

        i = i+1
        if op >= HAVE_ARGUMENT:
            oparg = byte_from_code(code, i) + byte_from_code(code, i+1)*256 + extended_arg
            extended_arg = 0
            i = i+2
            if op == EXTENDED_ARG:
                extended_arg = oparg*65536
            if op in hasconst:
                c = co.co_consts[oparg]
                argstr = '(' + repr(c) + ')'
                if inspect.iscode(c):
                    code_obj = c
            elif op in hasname:
                argstr = '(' + co.co_names[oparg] + ')'
            elif op in hasjabs:
                argstr = '(-> ' + repr(oparg) + ')'
            elif op in hasjrel:
                argstr = '(-> ' + repr(i + oparg) + ')'
            elif op in haslocal:
                argstr = '(' + co.co_varnames[oparg] + ')'
            elif op in hascompare:
                argstr = '(' + cmp_op[oparg] + ')'
            elif op in hasfree:
                if free is None:
                    free = co.co_cellvars + co.co_freevars
                argstr = '(' + free[oparg] + ')'
            else:
                argstr = ""
        else:
            oparg = None
            argstr = ""

        yield DisLine(lineno=lineno, column=column,
                      first=first, target=target,
                      offset=offset,
                      opcode=opcode, oparg=oparg,
                      argstr=argstr,
                      code_obj=code_obj)


def byte_from_code(code, i):
    byte = code[i]
    if not isinstance(byte, int):
        byte = ord(byte)
    return byte

def findlabels(code):
    """Detect all offsets in a byte code which are jump targets.

    Return the list of offsets.

    """
    labels = []
    n = len(code)
    i = 0
    while i < n:
        op = byte_from_code(code, i)
        i = i+1
        if op >= HAVE_ARGUMENT:
            oparg = byte_from_code(code, i) + byte_from_code(code, i+1)*256
            i = i+2
            label = -1
            if op in hasjrel:
                label = i+oparg
            elif op in hasjabs:
                label = oparg
            if label >= 0:
                if label not in labels:
                    labels.append(label)
    return labels

def findlinestarts(code):
    """Find the offsets in a byte code which are start of lines in the source.

    Generate pairs (offset, lineno) as described in Python/compile.c.

    """
    byte_increments = [byte_from_code(code.co_lnotab, i) for i in range(0, len(code.co_lnotab), 2)]
    line_increments = [byte_from_code(code.co_lnotab, i) for i in range(1, len(code.co_lnotab), 2)]

    lastlineno = None
    lineno = code.co_firstlineno
    addr = 0
    for byte_incr, line_incr in zip(byte_increments, line_increments):
        if byte_incr:
            if lineno != lastlineno:
                yield (addr, lineno)
                lastlineno = lineno
            addr += byte_incr
        lineno += line_incr
    if lineno != lastlineno:
        yield (addr, lineno)

def _test():
    """Simple test program to disassemble a file."""
    if sys.argv[1:]:
        if sys.argv[2:]:
            sys.stderr.write("usage: python dis.py [-|file]\n")
            sys.exit(2)
        fn = sys.argv[1]
        if not fn or fn == "-":
            fn = None
    else:
        fn = None
    if fn is None:
        f = sys.stdin
    else:
        f = open(fn)
    source = f.read()
    if fn is not None:
        f.close()
    else:
        fn = "<stdin>"
    code = compile(source, fn, "exec")
    print 'Disassembling top-level module in', fn
    dis(code, fn, source)

if __name__ == "__main__":
    _test()
