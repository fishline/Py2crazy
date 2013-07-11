import ast

#TEST_STR = 'res = apple + banana * carrot'
#TEST_STR = '_,_ = apple + banana * carrot'
TEST_STR = '`"repr of a string"`'


# Consult Parser/Python.asdl for full AST description

# Tested by running MyVisitor on a bunch of files from the Python
# standard library, starting with Lib/ast.py.
# Also test on the Online Python Tutor test suite as well.


# start_col - starting column to highlight
# extent - number of characters to highlight starting at start_col
# NOTE THAT start_col might not equal col_offset, since we might want to
# highlight a larger portion of the expression not rooted at col_offset.
# The classic example is:
#
# x + y
#
# For the BinOp expression, col_offset is 2 (the location of the '+'
# operator), but start_col is 0, and extent is 5, which highlights the
# entirety of 'x + y' while pointing the cursor at the '+' smack dab in
# the middle.


# The hope is that this visitor doesn't have to be perfect, since
# Py2crazy stops only on each unique line/column combo, so some of these
# AST types might be "shadowed" by one of its children with start_col and
# extent info, even if it doesn't get a start_col and extent to itself.


# NOPs
NOP_CLASSES = [ast.expr_context, ast.cmpop, ast.boolop,
               ast.unaryop, ast.operator,
               ast.Module, ast.Interactive, ast.Expression,
               ast.arguments, ast.keyword, ast.alias
               ast.excepthandler,
               ast.Dict, ast.Set, ast.List, ast.Tuple,
               ast.If, ast.With, ast.GeneratorExp,
               ast.comprehension,
               ast.BoolOp,
               ast.ListComp, ast.DictComp, ast.SetComp,
               ast.IfExp,
               ast.UnaryOp,
               ast.Slice, ast.ExtSlice, ast.Ellipsis,
               ast.Print]


# This shit runs top-down, so we might need to run several times to fixpoint
class MyVisitor(ast.NodeVisitor):
  def __init__(self):
    ast.NodeVisitor.__init__(self)


  def add_attrs(self, node):
    if 'extent' not in node._attributes:
      node._attributes = node._attributes + ('start_col', 'extent',)

  # this should NEVER be called, since all cases should be exhaustively handled
  def generic_visit(self, node):
    # exception: let these pass through unscathed, since we NOP on them
    for c in NOP_CLASSES:
      if isinstance(node, c):
        # recurse normally into children (if any)
        self.visit_children(node)
        return

    assert False, node.__class__


  # copied from Lib/ast.py generic_visit
  def visit_children(self, node):
      for field, value in ast.iter_fields(node):
          if isinstance(value, list):
              for item in value:
                  if isinstance(item, ast.AST):
                      self.visit(item)
          elif isinstance(value, ast.AST):
              self.visit(value)

  # always end with a call to self.visit_children(node)
  # (unless you know you're a terminal node)
  # TODO: encapsulate in a decorator


  def visit_Expr(self, node):
    if hasattr(node.value, 'extent'):
      self.add_attrs(node)
      node.start_col = node.value.start_col
      node.extent = node.value.extent
    self.visit_children(node)

  def visit_Subscript(self, node):
    if hasattr(node.slice, 'extent'):
      self.add_attrs(node)
      node.start_col = node.slice.start_col
      node.extent = node.slice.extent
    self.visit_children(node)

  def visit_Index(self, node):
    if hasattr(node.value, 'extent'):
      self.add_attrs(node)
      node.start_col = node.value.start_col
      node.extent = node.value.extent
    self.visit_children(node)


  def visit_Attribute(self, node):
    self.add_attrs(node)
    node.start_col = node.col_offset
    node.extent = len(node.attr) + 1 # extra for dot
    self.visit_children(node)

  def visit_Call(self, node):
    if hasattr(node.func, 'extent'):
      self.add_attrs(node)
      node.start_col = node.func.start_col
      node.extent = node.func.extent
    self.visit_children(node)

  def visit_Compare(self, node):
    '''
	     -- need sequences for compare to distinguish between
	     -- x < 4 < 3 and (x < 4) < 3
	     | Compare(expr left, cmpop* ops, expr* comparators)
    '''
    leftmost = node.left
    rightmost = node.comparators[-1]
    if hasattr(leftmost, 'extent') and hasattr(rightmost, 'extent'):
      self.add_attrs(node)
      node.start_col = leftmost.col_offset
      node.extent = rightmost.col_offset + rightmost.extent - leftmost.col_offset
    self.visit_children(node)

  def visit_BinOp(self, node):
    if hasattr(node.left, 'extent') and hasattr(node.right, 'extent'):
      self.add_attrs(node)
      node.start_col = node.left.start_col
      node.extent = (node.right.start_col + node.right.extent - node.start_col)
    self.visit_children(node)

  def visit_Assign(self, node):
    if hasattr(node.targets[0], 'extent') and hasattr(node.value, 'extent'):
      self.add_attrs(node)
      node.start_col = node.targets[0].start_col
      node.extent = (node.value.start_col + node.value.extent - node.start_col)
    self.visit_children(node)

  def visit_AugAssign(self, node):
    if hasattr(node.target, 'extent') and hasattr(node.value, 'extent'):
      self.add_attrs(node)
      node.start_col = node.target.start_col
      node.extent = (node.value.start_col + node.value.extent - node.start_col)
    self.visit_children(node)

  def visit_Repr(self, node):
    if hasattr(node.value, 'extent'):
      self.add_attrs(node)
      node.start_col = node.col_offset
      node.extent = len(node.value) + 2 # add 2 for surrounding backquotes
    self.visit_children(node)


  # TODO: abstract out this recurring pattern ...
  def visit_FunctionDef(self, node):
    self.add_attrs(node)
    node.start_col = node.col_offset
    node.extent = len('def')
    self.visit_children(node)

  def visit_ClassDef(self, node):
    self.add_attrs(node)
    node.start_col = node.col_offset
    node.extent = len('class')
    self.visit_children(node)

  def visit_Raise(self, node):
    self.add_attrs(node)
    node.start_col = node.col_offset
    node.extent = len('raise')
    self.visit_children(node)

  def visit_Assert(self, node):
    self.add_attrs(node)
    node.start_col = node.col_offset
    node.extent = len('assert')
    self.visit_children(node)

  def visit_TryExcept(self, node):
    self.add_attrs(node)
    node.start_col = node.col_offset
    node.extent = len('try')
    self.visit_children(node)

  def visit_TryFinally(self, node):
    self.add_attrs(node)
    node.start_col = node.col_offset
    node.extent = len('try')
    self.visit_children(node)

  def visit_ExceptHandler(self, node):
    self.add_attrs(node)
    node.start_col = node.col_offset
    node.extent = len('except')
    self.visit_children(node)

  def visit_Global(self, node):
    self.add_attrs(node)
    node.start_col = node.col_offset
    node.extent = len('global')
    self.visit_children(node)

  def visit_Lambda(self, node):
    self.add_attrs(node)
    node.start_col = node.col_offset
    node.extent = len('lambda')
    self.visit_children(node)

  def visit_Exec(self, node):
    self.add_attrs(node)
    node.start_col = node.col_offset
    node.extent = len('exec')
    self.visit_children(node)

  def visit_For(self, node):
    self.add_attrs(node)
    node.start_col = node.col_offset
    node.extent = len('for')
    self.visit_children(node)

  def visit_While(self, node):
    self.add_attrs(node)
    node.start_col = node.col_offset
    node.extent = len('for')
    self.visit_children(node)

  def visit_Pass(self, node):
    self.add_attrs(node)
    node.start_col = node.col_offset
    node.extent = len('pass')
    self.visit_children(node)

  def visit_Break(self, node):
    self.add_attrs(node)
    node.start_col = node.col_offset
    node.extent = len('break')
    self.visit_children(node)

  def visit_Continue(self, node):
    self.add_attrs(node)
    node.start_col = node.col_offset
    node.extent = len('continue')
    self.visit_children(node)

  def visit_Delete(self, node):
    self.add_attrs(node)
    node.start_col = node.col_offset
    node.extent = len('del')
    self.visit_children(node)

  def visit_Return(self, node):
    self.add_attrs(node)
    node.start_col = node.col_offset
    node.extent = len('return')
    self.visit_children(node)

  def visit_Import(self, node):
    self.add_attrs(node)
    node.start_col = node.col_offset
    node.extent = len('import')
    self.visit_children(node)

  def visit_ImportFrom(self, node):
    self.add_attrs(node)
    node.start_col = node.col_offset
    node.extent = len('from')
    self.visit_children(node)

  def visit_Yield(self, node):
    self.add_attrs(node)
    node.start_col = node.col_offset
    node.extent = len('yield')
    self.visit_children(node)


  # terminal nodes
  def visit_Str(self, node):
    # TODO: doesn't work for multi-line strings, or triple-quoted
    # strings, etc.
    # (some weird strings have col_offset as -1, so ignore those
    if node.col_offset >= 0:
      self.add_attrs(node)
      node.start_col = node.col_offset
      node.extent = len(node.s) + 2 # add 2 for quotes

  def visit_Name(self, node):
    self.add_attrs(node)
    node.start_col = node.col_offset
    node.extent = len(node.id)

  def visit_Num(self, node):
    # TODO: don't do anything for floats since we don't know exactly
    # how long they are when printed in the original source code!
    if isinstance(node.n, int) or isinstance(node.n, long):
      self.add_attrs(node)
      node.start_col = node.col_offset
      node.extent = len(str(node.n))


v = MyVisitor()

import sys
m = ast.parse(open(sys.argv[1]).read())

v.visit(m)
print ast.dump(m, annotate_fields=True, include_attributes=True)


# TODO: crap this infinite loops whenever information is incomplete, so
# think of a more robust solution that propagates values UPWARDS on
# demand rather than downward
# NB: I think this needs to run only H times, where H is the height of
# the full AST tree.
#i = 1
#while True:
#  print 'Round', i
#  v.visit(m)
#  i += 1
#  print ast.dump(m, annotate_fields=True, include_attributes=True)
#  print
#  if not v.incomplete:
#    break

