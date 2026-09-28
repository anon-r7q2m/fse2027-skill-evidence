import ast
import io
import tokenize


def get_functions(tree):
    functions = {}

    class FunctionVisitor(ast.NodeVisitor):
        def __init__(self):
            self.parents = []

        def visit(self, node):
            self.parents.append(node)
            super().visit(node)
            self.parents.pop()

        def visit_FunctionDef(self, node):
            if not any(isinstance(parent, ast.ClassDef) for parent in self.parents):
                functions[node.name] = ast.unparse(node)
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node):
            if not any(isinstance(parent, ast.ClassDef) for parent in self.parents):
                functions[node.name] = ast.unparse(node)
            self.generic_visit(node)

    class ClassVisitor(ast.NodeVisitor):
        def visit_ClassDef(self, node):
            class_name = node.name
            for body_item in node.body:
                if isinstance(body_item, ast.FunctionDef) or isinstance(
                    body_item, ast.AsyncFunctionDef
                ):
                    functions[f"{class_name}.{body_item.name}"] = ast.unparse(body_item)
            self.generic_visit(node)

    FunctionVisitor().visit(tree)
    ClassVisitor().visit(tree)
    return functions


def is_just_new_function(code1, code2):
    tree1 = ast.parse(code1)
    tree2 = ast.parse(code2)

    functions1 = get_functions(tree1)
    functions2 = get_functions(tree2)

    if len(set(list(functions1.keys())) - set(list(functions2.keys()))) > 0:
        return False

    for func in functions1:
        if functions1[func] != functions2[func]:
            return False

    if len(set(list(functions2.keys())) - set(list(functions1.keys()))) > 0:
        return True

    return False


def remove_comments_and_docstrings(source):
    io_obj = io.StringIO(source)
    out = ""
    prev_toktype = tokenize.INDENT
    last_lineno = -1
    last_col = 0
    for tok in tokenize.generate_tokens(io_obj.readline):
        token_type = tok[0]
        token_string = tok[1]
        start_line, start_col = tok[2]
        end_line, end_col = tok[3]
        if start_line > last_lineno:
            last_col = 0
        if start_col > last_col:
            out += " " * (start_col - last_col)
        if token_type == tokenize.COMMENT:
            pass
        elif token_type == tokenize.STRING:
            if prev_toktype != tokenize.INDENT:
                if prev_toktype != tokenize.NEWLINE:
                    if start_col > 0:
                        out += token_string
        else:
            out += token_string
        prev_toktype = token_type
        last_col = end_col
        last_lineno = end_line
    out = "\n".join(l for l in out.splitlines() if l.strip())
    return out


def _normalize_code(code: str) -> str:
    try:
        node = ast.parse(code)
        return ast.unparse(node)
    except Exception:
        return code


def prepare_normalization_files(files: list[dict]) -> tuple[list[dict], list[dict]]:
    normalized_files = []
    flags = []

    for row in files:
        old_content = _normalize_code(row["before"])
        new_content = _normalize_code(row["after"])

        try:
            stripped_old = remove_comments_and_docstrings(old_content)
            ast.parse(stripped_old)
            stripped_new = remove_comments_and_docstrings(new_content)
            ast.parse(stripped_new)
        except Exception:
            stripped_old = old_content
            stripped_new = new_content

        normalized_files.append(
            {"path": row["path"], "before": stripped_old, "after": stripped_new}
        )
        flags.append(
            {
                "path": row["path"],
                "flag": is_just_new_function(stripped_old, stripped_new),
            }
        )

    return normalized_files, flags


def build_normalized_key(diff_files: list[dict], flags: list[dict]) -> str:
    flag_by_path = {row["path"]: bool(row["flag"]) for row in flags}
    normalized_diff = ""

    for row in diff_files:
        diff = row["diff"]
        if flag_by_path.get(row["path"], False):
            diff = "\n".join(
                line
                for line in diff.splitlines()
                if line.startswith("-") or line.startswith("+")
            )
        normalized_diff += diff

    return normalized_diff
