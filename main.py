import tree_sitter_python as tspython
from tree_sitter import Language, Parser

PY_LANGUAGE = Language(tspython.language())

parser = Parser(PY_LANGUAGE)

filename = "test.py"

with open(filename, "rb") as f:
    data = f.read()
    tree = parser.parse(data)

    root_node = tree.root_node

    print(str(root_node))
