import ast

TEST_STR = 'res = apple + banana * carrot'
#TEST_STR = '_,_ = apple + banana * carrot'

# TODO: Look at Parser/Python.asdl for full AST description


class MyVisitor(ast.NodeVisitor):
  # This shit runs top-down, so we might need to run several times to fixpoint
  def __init__(self):
    self.incomplete = False
    ast.NodeVisitor.__init__(self)

  def reset(self):
    self.incomplete = False

  def add_attrs(self, node):
    if 'extent' not in node._attributes:
      node._attributes = node._attributes + ('start_col', 'extent',)


  def generic_visit(self, node):
    #print '>', ast.dump(node)
    ast.NodeVisitor.generic_visit(self, node)

  def visit_Name(self, node):
    self.add_attrs(node)
    node.start_col = node.col_offset
    node.extent = len(node.id)

  def visit_BinOp(self, node):
    if not hasattr(node.left, 'start_col') or \
       not hasattr(node.right, 'start_col'):
      self.incomplete = True
    else:
      self.add_attrs(node)
      node.start_col = node.left.start_col
      node.extent = (node.right.start_col + node.right.extent - node.start_col)

    self.generic_visit(node)

  def visit_Assign(self, node):
    self.generic_visit(node)
    # go from the FIRST target to the beginning of value
    if not hasattr(node.targets[0], 'start_col') or \
       not hasattr(node.value, 'start_col'):
      self.incomplete = True
    else:
      self.add_attrs(node)
      node.start_col = node.targets[0].start_col
      node.extent = (node.value.start_col - node.start_col)


v = MyVisitor()

m = ast.parse(TEST_STR)


# TODO: crap this infinite loops whenever information is incomplete, so
# think of a more robust solution that propagates values UPWARDS on
# demand rather than downward
i = 1
while True:
  print 'Round', i
  v.reset()
  v.visit(m)
  i += 1
  print ast.dump(m, annotate_fields=True, include_attributes=True)
  print
  if not v.incomplete:
    break

'''
Module(
  body=[
    Assign(
      targets=[
        Tuple(elts=[Name(id='_', ctx=Store(), lineno=1, col_offset=0, start_col=0, extent=1), Name(id='_', ctx=Store(), lineno=1, col_offset=2, start_col=2, extent=1)], ctx=Store(), lineno=1, col_offset=0)
      ],
      value=
        BinOp(left=Name(id='apple', ctx=Load(), lineno=1, col_offset=6, start_col=6, extent=5), op=Add(), right=BinOp(left=Name(id='banana', ctx=Load(), lineno=1, col_offset=14, start_col=14, extent=6), op=Mult(), right=Name(id='carrot', ctx=Load(), lineno=1, col_offset=23, start_col=23, extent=6), lineno=1, col_offset=21, start_col=14, extent=15), lineno=1, col_offset=12, start_col=6, extent=23), lineno=1, col_offset=0)
  ]
)
'''
