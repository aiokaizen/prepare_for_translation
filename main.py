import tree_sitter_python as tspython
from tree_sitter import Language, Parser

INDENT_SIZE = 4
SKIPPED_TYPES = [
    "import_from_statement",
]


def loop_children(root_node, indent=0):
    indent_str = indent * INDENT_SIZE * " "
    if indent >= 3:
        return
    if indent == 0:
        print(
            f"{indent_str}start_point: {root_node.start_point} | "
            f"type: {root_node.type} | "
            f"end_point: {root_node.end_point}\n"
        )
    for i in range(len(root_node.children)):
        child = root_node.children[i]
        print(f"{i} | Child type:", child.type)
        if child.type in SKIPPED_TYPES:
            print(f"SKIPPED!! | {child.child_count}")
            i += child.child_count
            continue
        print(
            f"{indent_str}start_point: {child.start_point} | "
            f"type: {child.type} | "
            f"end_point: {child.end_point}\n"
        )
        if child.children:
            loop_children(child, indent + 1)


def main():
    PY_LANGUAGE = Language(tspython.language())

    parser = Parser(PY_LANGUAGE)

    filename = "test.py"

    with open(filename, "rb") as f:
        data = f.read()
        tree = parser.parse(data)

        root_node = tree.root_node
        print("dir:", dir(root_node))
        loop_children(root_node)

        # print(str(root_node))


if __name__ == "__main__":
    main()
