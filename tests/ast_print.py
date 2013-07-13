import ast, sys

print ast.dump(ast.parse(open(sys.argv[1]).read()), include_attributes=True)
