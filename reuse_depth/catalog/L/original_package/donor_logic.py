import ast
import io
import re
import tokenize
from collections import OrderedDict

import libcst as cst
import libcst.matchers as m


file_content_template = """
### File: {file_name} ###
{file_content}
"""

file_content_in_block_template = """
### File: {file_name} ###
```python
{file_content}
```
"""

obtain_relevant_code_combine_top_n_prompt = """
Please review the following GitHub problem description and relevant files, and provide a set of locations that need to be edited to fix the issue.
The locations can be specified as class names, function or method names, or exact line numbers that require modification.

### GitHub Problem Description ###
{problem_statement}

###
{file_contents}

###

Please provide the class name, function or method name, or the exact line numbers that need to be edited.
The possible location outputs should be either "class", "function" or "line".

### Examples:
```
full_path1/file1.py
line: 10
class: MyClass1
line: 51

full_path2/file2.py
function: MyClass2.my_method
line: 12

full_path3/file3.py
function: my_function
line: 24
line: 156
```

Return just the location(s) wrapped with ```.
"""

obtain_relevant_code_combine_top_n_no_line_number_prompt = """
Please review the following GitHub problem description and relevant files, and provide a set of locations that need to be edited to fix the issue.
The locations can be specified as class, method, or function names that require modification.

### GitHub Problem Description ###
{problem_statement}

###
{file_contents}

###

Please provide the class, method, or function names that need to be edited.
### Examples:
```
full_path1/file1.py
function: my_function1
class: MyClass1

full_path2/file2.py
function: MyClass2.my_method
class: MyClass3

full_path3/file3.py
function: my_function2
```

Return just the location(s) wrapped with ```.
"""

obtain_relevant_functions_and_vars_from_compressed_files_prompt_more = """
Please look through the following GitHub Problem Description and the Skeleton of Relevant Files.
Identify all locations that need inspection or editing to fix the problem, including directly related areas as well as any potentially related global variables, functions, and classes.
For each location you provide, either give the name of the class, the name of a method in a class, the name of a function, or the name of a global variable.

### GitHub Problem Description ###
{problem_statement}

### Skeleton of Relevant Files ###
{file_contents}

###

Please provide the complete set of locations as either a class name, a function name, or a variable name.
Note that if you include a class, you do not need to list its specific methods.
You can include either the entire class or don't include the class name and instead include specific methods in the class.
### Examples:
```
full_path1/file1.py
function: my_function_1
class: MyClass1
function: MyClass2.my_method

full_path2/file2.py
variable: my_var
function: MyClass3.my_method

full_path3/file3.py
function: my_function_2
function: my_function_3
function: MyClass4.my_method_1
class: MyClass5
```

Return just the locations wrapped with ```.
"""

repair_relevant_file_instruction = """
Below are some code segments, each from a relevant file. One or more of these files may contain bugs.
"""

repair_prompt_combine_topn_parser_adapted = """
We are currently solving the following issue within our repository. Here is the issue text:
--- BEGIN ISSUE ---
{problem_statement}
--- END ISSUE ---

{repair_relevant_file_instruction}
--- BEGIN FILE ---
```
{content}
```
--- END FILE ---

Please generate `edit_file` commands to fix the issue.

Return exactly one ```python ... ``` block containing 1 to 64 literal calls in this inherited parser domain:

edit_file('path', start, end, 'replacement text')

Rules:
- use the exact spelling `edit_file(`
- use only literal string and decimal integer arguments
- use positional arguments only; no keywords
- paths must be literal paths for files that were read at the base
- `start` and `end` are ORIGINAL 1-based line numbers from the numbered context above
- every range must satisfy 1 <= start <= end <= the original file line count
- ranges for the same file must not overlap
- do not include comments, variables, semicolons, or extra statements
- do not include the substring `edit_file(` inside any string literal
- preserve indentation exactly in replacement text

Wrap only the commands in one ```python ... ``` block.
""".strip()


def build_filtered_tree(tracked_paths):
    structure = {}
    filtered_paths = []
    for path in tracked_paths:
        if not _keep_path(path):
            continue
        filtered_paths.append(path)
        current = structure
        parts = path.split("/")
        for index, part in enumerate(parts):
            if index == len(parts) - 1:
                current.setdefault(part, {})
            else:
                current = current.setdefault(part, {})
    return structure, filtered_paths


def build_structure_string(tree):
    return show_project_structure(tree)


def _keep_path(path):
    if not path.endswith(".py"):
        return False
    for part in path.split("/"):
        if part.startswith("test"):
            return False
    return True


def show_project_structure(structure, spacing=0):
    pp_string = ""

    for key, value in structure.items():
        if "." in key and ".py" not in key:
            continue
        if "." in key:
            pp_string += " " * spacing + str(key) + "\n"
        else:
            pp_string += " " * spacing + str(key) + "/" + "\n"
        if "classes" not in value:
            pp_string += show_project_structure(value, spacing + 4)

    return pp_string


def parse_file_selection(raw_output, filtered_paths):
    model_found_files = _parse_model_return_lines(raw_output)
    files = [(path,) for path in filtered_paths]
    return correct_file_paths(model_found_files, files)


def _parse_model_return_lines(content):
    if content:
        return content.strip().split("\n")


def correct_file_paths(model_found_files, files):
    found_files = []
    if model_found_files:
        for model_file in model_found_files:
            for file_content in files:
                file = file_content[0]
                if model_file == file:
                    found_files.append(file)
        return found_files
    else:
        return []


def parse_location_response(raw_output, file_names):
    model_found_locs = extract_code_blocks(raw_output)
    separated = extract_locs_for_files(model_found_locs, file_names, keep_old_order=False)
    ordered = OrderedDict()
    for key, value in separated.items():
        ordered[key] = list(value)
    return ordered


def map_to_rows(file_to_locs):
    return [{"path": path, "locations": list(locs)} for path, locs in file_to_locs.items()]


def rows_to_map(rows):
    ordered = OrderedDict()
    for row in rows:
        ordered[row["path"]] = list(row["locations"])
    return ordered


def build_related_prompt(issue, file_names, base_files, compress_assign=False):
    file_contents = _ordered_repo_files(base_files, file_names)
    compressed_file_contents = {
        fn: get_skeleton(code, compress_assign=compress_assign)
        for fn, code in file_contents.items()
    }
    contents = [
        file_content_in_block_template.format(file_name=fn, file_content=code)
        for fn, code in compressed_file_contents.items()
    ]
    merged = "".join(contents)
    return obtain_relevant_functions_and_vars_from_compressed_files_prompt_more.format(
        problem_statement=issue,
        file_contents=merged,
    ).strip()


def build_fine_prompt(issue, file_names, coarse_locs, base_files, config):
    structure = _structure_for_sources(base_files)
    files, _, _ = get_full_file_paths_and_classes_and_functions(structure)

    file_contents = OrderedDict()
    for filepath in file_names:
        content = None
        for file_content in files:
            if file_content[0] == filepath:
                content = "\n".join(file_content[1])
                if filepath not in file_contents:
                    file_contents[filepath] = content
                break
        assert content is not None, "file not found"

    cropped = OrderedDict()
    for fn in file_names:
        if fn in coarse_locs:
            cropped[fn] = coarse_locs[fn]

    topn_content, _ = construct_topn_file_context(
        cropped,
        file_names,
        file_contents,
        structure,
        context_window=config["context_window"],
        loc_interval=True,
        fine_grain_loc_only=False,
        add_space=config["add_space"],
        sticky_scroll=config["sticky_scroll"],
        no_line_number=config["no_line_number"],
    )
    template = (
        obtain_relevant_code_combine_top_n_no_line_number_prompt
        if config["no_line_number"]
        else obtain_relevant_code_combine_top_n_prompt
    )
    return (
        template.format(problem_statement=issue, file_contents=topn_content).strip(),
        topn_content,
    )


def build_repair_prompt(issue, file_names, fine_locs, base_files, config):
    structure = _structure_for_sources(base_files)
    files, _, _ = get_full_file_paths_and_classes_and_functions(structure)

    file_contents = OrderedDict()
    for filepath in file_names:
        content = None
        for file_content in files:
            if file_content[0] == filepath:
                content = "\n".join(file_content[1])
                if filepath not in file_contents:
                    file_contents[filepath] = content
                break
        assert content is not None, "file not found"

    cropped = OrderedDict()
    for fn in file_names:
        if fn in fine_locs:
            cropped[fn] = fine_locs[fn]

    topn_content, _ = construct_topn_file_context(
        cropped,
        file_names,
        file_contents,
        structure,
        context_window=config["context_window"],
        loc_interval=True,
        fine_grain_loc_only=False,
        add_space=config["add_space"],
        sticky_scroll=config["sticky_scroll"],
        no_line_number=False,
    )
    prompt = repair_prompt_combine_topn_parser_adapted.format(
        repair_relevant_file_instruction=repair_relevant_file_instruction,
        problem_statement=issue,
        content=topn_content.rstrip(),
    ).strip()
    return prompt, topn_content


def _ordered_repo_files(base_files, filepaths):
    structure = _structure_for_sources(base_files)
    files, _, _ = get_full_file_paths_and_classes_and_functions(structure)

    file_contents = OrderedDict()
    for filepath in filepaths:
        content = None
        for file_content in files:
            if file_content[0] == filepath:
                content = "\n".join(file_content[1])
                if filepath not in file_contents:
                    file_contents[filepath] = content
                break
        assert content is not None, "file not found"

    return file_contents


def check_contains_valid_loc(file_to_locs, base_files):
    structure = _structure_for_sources(base_files)
    files, _, _ = get_full_file_paths_and_classes_and_functions(structure)

    file_contents = OrderedDict()
    for filepath in file_to_locs.keys():
        content = None
        for file_content in files:
            if file_content[0] == filepath:
                content = "\n".join(file_content[1])
                if filepath not in file_contents:
                    file_contents[filepath] = content
                break
        assert content is not None, "file not found"

    for pred_file, locs in file_to_locs.items():
        line_locs, _ = transfer_arb_locs_to_locs(
            locs,
            structure,
            pred_file,
            0,
            True,
            False,
            file_content=file_contents[pred_file] if pred_file in file_contents else "",
        )

        if len(line_locs) > 0:
            return True

    return False


def parse_python_file(file_path, file_content=None):
    if file_content is None:
        try:
            with open(file_path, "r") as file:
                file_content = file.read()
                parsed_data = ast.parse(file_content)
        except Exception:
            return [], [], ""
    else:
        try:
            parsed_data = ast.parse(file_content)
        except Exception:
            return [], [], ""

    class_info = []
    function_names = []
    class_methods = set()

    for node in ast.walk(parsed_data):
        if isinstance(node, ast.ClassDef):
            methods = []
            for n in node.body:
                if isinstance(n, ast.FunctionDef):
                    methods.append(
                        {
                            "name": n.name,
                            "start_line": n.lineno,
                            "end_line": n.end_lineno,
                            "text": file_content.splitlines()[n.lineno - 1 : n.end_lineno],
                        }
                    )
                    class_methods.add(n.name)
            class_info.append(
                {
                    "name": node.name,
                    "start_line": node.lineno,
                    "end_line": node.end_lineno,
                    "text": file_content.splitlines()[node.lineno - 1 : node.end_lineno],
                    "methods": methods,
                }
            )
        elif isinstance(node, ast.FunctionDef) and not isinstance(
            node, ast.AsyncFunctionDef
        ):
            if node.name not in class_methods:
                function_names.append(
                    {
                        "name": node.name,
                        "start_line": node.lineno,
                        "end_line": node.end_lineno,
                        "text": file_content.splitlines()[node.lineno - 1 : node.end_lineno],
                    }
                )

    return class_info, function_names, file_content.splitlines()


def get_full_file_paths_and_classes_and_functions(structure, current_path=""):
    files = []
    classes = []
    functions = []
    for name, content in structure.items():
        if isinstance(content, dict):
            if (
                "functions" not in content.keys()
                and "classes" not in content.keys()
                and "text" not in content.keys()
            ) or not len(content.keys()) == 3:
                next_path = f"{current_path}/{name}" if current_path else name
                (
                    sub_files,
                    sub_classes,
                    sub_functions,
                ) = get_full_file_paths_and_classes_and_functions(content, next_path)
                files.extend(sub_files)
                classes.extend(sub_classes)
                functions.extend(sub_functions)
            else:
                next_path = f"{current_path}/{name}" if current_path else name
                files.append((next_path, content["text"]))
                if "classes" in content:
                    for clazz in content["classes"]:
                        classes.append(
                            {
                                "file": next_path,
                                "name": clazz["name"],
                                "start_line": clazz["start_line"],
                                "end_line": clazz["end_line"],
                                "methods": [
                                    {
                                        "name": method["name"],
                                        "start_line": method["start_line"],
                                        "end_line": method["end_line"],
                                    }
                                    for method in clazz.get("methods", [])
                                ],
                            }
                        )
                if "functions" in content:
                    for function in content["functions"]:
                        function["file"] = next_path
                        functions.append(function)
        else:
            next_path = f"{current_path}/{name}" if current_path else name
            files.append(next_path)
    return files, classes, functions


def line_wrap_content(
    content,
    context_intervals=None,
    add_space=False,
    no_line_number=False,
    sticky_scroll=False,
):
    def is_scope(line):
        return line.startswith("class ") or line.strip().startswith("def ")

    lines = content.split("\n")
    new_lines = []
    if context_intervals is None or context_intervals == []:
        context_intervals = [(0, len(lines))]

    prev_scopes = []
    line_format = "{line}"
    if not no_line_number:
        line_format = "{line_number}|{line}" if not add_space else "{line_number}| {line} "
    for interval in context_intervals:
        min_line, max_line = interval

        if min_line != 0:
            new_lines.append("...")

        scopes = []
        for i, line in enumerate(lines):
            if sticky_scroll:
                if is_scope(line):
                    indent_level = len(line) - len(line.lstrip())
                    while scopes and scopes[-1]["indent_level"] >= indent_level:
                        scopes.pop()
                    scopes.append(
                        {"line": line, "line_number": i, "indent_level": indent_level}
                    )

            if min_line != -1 and i < min_line - 1:
                continue
            if sticky_scroll and i == min_line - 1:
                last_scope_line = None
                for j, scope_line in enumerate(scopes):
                    if (
                        len(prev_scopes) > j
                        and prev_scopes[j]["line_number"] == scope_line["line_number"]
                    ):
                        continue
                    if i == scope_line["line_number"]:
                        continue
                    new_lines.append(
                        line_format.format(
                            line_number=scope_line["line_number"] + 1,
                            line=scope_line["line"],
                        )
                    )
                    last_scope_line = scope_line["line_number"]
                if last_scope_line is not None and last_scope_line < i - 1:
                    new_lines.append("...")

            new_lines.append(line_format.format(line_number=i + 1, line=line))
            if max_line != -1 and i >= max_line - 1:
                break
        prev_scopes = scopes

    if max_line != len(lines):
        new_lines.append("...")

    return "\n".join(new_lines)


def merge_intervals(intervals):
    if not intervals:
        return []

    intervals.sort(key=lambda interval: interval[0])
    merged_intervals = [intervals[0]]

    for current in intervals[1:]:
        last = merged_intervals[-1]
        if current[0] <= last[1]:
            merged_intervals[-1] = (last[0], max(last[1], current[1]))
        else:
            merged_intervals.append(current)

    return merged_intervals


def transfer_arb_locs_to_locs(
    locs,
    structure,
    pred_file,
    context_window=10,
    loc_interval=False,
    fine_grain_only=False,
    remove_line=False,
    file_content="",
    verbose=False,
):
    if structure is None:
        class_info, function_names, file_lines = parse_python_file("", file_content)
        structure = {}
        structure[pred_file] = {
            "classes": class_info,
            "functions": function_names,
            "text": file_lines,
        }

    files, classes, functions = get_full_file_paths_and_classes_and_functions(structure)

    line_loc = []
    if isinstance(locs, str):
        locs = [locs]
    global_vars = parse_global_var_from_code(file_content)
    unrecognized_locs = []

    for model_pred_locs in locs:
        current_class_name = ""
        for loc in model_pred_locs.splitlines():
            if loc.startswith("class: ") and "." not in loc:
                loc = loc[len("class: ") :].strip()
                relevant_class = [
                    clazz
                    for clazz in classes
                    if clazz["file"] == pred_file and clazz["name"] == loc
                ]

                if len(relevant_class) == 0:
                    unrecognized_locs.append(loc)
                else:
                    line_loc.append(
                        (relevant_class[0]["start_line"], relevant_class[0]["end_line"])
                    )
                    current_class_name = loc

            elif loc.startswith("function: ") or "." in loc:
                loc = loc.split(":", 1)[-1].strip()

                if "." in loc:
                    method_name = loc.split(".")[1]
                    class_name = loc.split(".")[0]

                    relevant_class = [
                        clazz
                        for clazz in classes
                        if clazz["file"] == pred_file and clazz["name"] == class_name
                    ]
                    if len(relevant_class) == 0:
                        unrecognized_locs.append(loc)
                    else:
                        relevant_method = [
                            method
                            for method in relevant_class[0]["methods"]
                            if method["name"] == method_name
                        ]
                        if len(relevant_method) == 0:
                            unrecognized_locs.append(loc)
                        else:
                            line_loc.append(
                                (
                                    relevant_method[0]["start_line"],
                                    relevant_method[0]["end_line"],
                                )
                            )

                else:
                    relevant_function = [
                        function
                        for function in functions
                        if function["file"] == pred_file and function["name"] == loc
                    ]
                    if len(relevant_function) == 0:
                        if current_class_name != "":
                            relevant_class = [
                                clazz
                                for clazz in classes
                                if clazz["file"] == pred_file
                                and clazz["name"] == current_class_name
                            ]
                            relevant_method = [
                                method
                                for method in relevant_class[0]["methods"]
                                if method["name"] == loc
                            ]
                            if len(relevant_method) == 0:
                                unrecognized_locs.append(loc)
                            else:
                                line_loc.append(
                                    (
                                        relevant_method[0]["start_line"],
                                        relevant_method[0]["end_line"],
                                    )
                                )
                        else:
                            relevant_method = []
                            for clazz in classes:
                                if clazz["file"] == pred_file:
                                    relevant_method.extend(
                                        [
                                            method
                                            for method in clazz["methods"]
                                            if method["name"] == loc
                                        ]
                                    )

                            if len(relevant_method) == 1:
                                line_loc.append(
                                    (
                                        relevant_method[0]["start_line"],
                                        relevant_method[0]["end_line"],
                                    )
                                )
                    else:
                        line_loc.append(
                            (
                                relevant_function[0]["start_line"],
                                relevant_function[0]["end_line"],
                            )
                        )
            elif loc.startswith("line: "):
                if remove_line:
                    continue
                line_tokens = loc[len("line: ") :].strip().split()
                if len(line_tokens) == 0:
                    continue
                loc = line_tokens[0]
                try:
                    line_loc.append((int(loc), int(loc)))
                except Exception:
                    continue
            elif loc.startswith("variable:"):
                vars_ = loc[len("variable:") :].strip().split()
                for v in vars_:
                    if v in global_vars:
                        line_loc.append(
                            (global_vars[v]["start_line"], global_vars[v]["end_line"])
                        )
            else:
                if loc.strip():
                    unrecognized_locs.append(loc)

    if fine_grain_only:
        filtered_line_loc = []
        for st, en in line_loc:
            if filtered_line_loc:
                last_st, last_en = filtered_line_loc[-1]
                if last_st <= st and en <= last_en:
                    filtered_line_loc.pop()
            filtered_line_loc.append((st, en))
        line_loc = filtered_line_loc

    for file_content_item in files:
        if file_content_item[0] == pred_file:
            content = file_content_item[1]
            break

    if len(line_loc) == 0:
        return [], []

    if verbose:
        for _ in unrecognized_locs:
            pass

    if loc_interval:
        contextual_line_loc = []
        for loc in line_loc:
            max_line = max(min(loc[1] + context_window, len(content)), 0)
            min_line = min(max(loc[0] - context_window, 0), len(content))
            contextual_line_loc.append((min_line, max_line))

        return line_loc, merge_intervals(contextual_line_loc)
    else:
        max_line = min(max([loc[1] for loc in line_loc]) + context_window, len(content))
        min_line = max(min([loc[0] for loc in line_loc]) - context_window, 0)

        return line_loc, [(min_line, max_line)]


def construct_topn_file_context(
    file_to_locs,
    pred_files,
    file_contents,
    structure,
    context_window,
    loc_interval=True,
    fine_grain_loc_only=False,
    add_space=False,
    sticky_scroll=False,
    no_line_number=True,
):
    file_loc_intervals = dict()
    topn_content = ""

    for pred_file, locs in file_to_locs.items():
        content = file_contents[pred_file]
        line_locs, context_intervals = transfer_arb_locs_to_locs(
            locs,
            structure,
            pred_file,
            context_window,
            loc_interval,
            fine_grain_loc_only,
            file_content=file_contents[pred_file] if pred_file in file_contents else "",
        )

        if len(line_locs) > 0:
            file_loc_content = line_wrap_content(
                content,
                context_intervals,
                add_space=add_space,
                no_line_number=no_line_number,
                sticky_scroll=sticky_scroll,
            )
            topn_content += f"### {pred_file}\n{file_loc_content}\n\n\n"
            file_loc_intervals[pred_file] = context_intervals

    return topn_content, file_loc_intervals


def check_syntax(code):
    if not isinstance(code, list):
        code = [code]

    for c in code:
        if not c.strip():
            return False
        try:
            ast.parse(c)
        except SyntaxError:
            return False
    return True


def remove_empty_lines(code):
    lines = code.splitlines()
    filtered_lines = [line for line in lines if line.strip() != ""]
    return "\n".join(filtered_lines)


def check_code_differ_by_just_empty_lines(codes, prev_codes):
    if not isinstance(codes, list):
        codes = [codes]
        prev_codes = [prev_codes]

    normalized_code1 = ""
    normalized_code2 = ""

    for code, prev_code in zip(codes, prev_codes):
        normalized_code1 += remove_empty_lines(code)
        normalized_code2 += remove_empty_lines(prev_code)

    return normalized_code1 == normalized_code2


def extract_code_blocks(text):
    pattern = r"```\n(.*?)\n```"
    matches = re.findall(pattern, text, re.DOTALL)
    if len(matches) == 0:
        if "```" in text:
            return [text.split("```", 1)[-1].strip()]
    return matches


def extract_locs_for_files(locs, file_names, keep_old_order=False):
    if keep_old_order:
        results = {fn: [] for fn in file_names}
    else:
        results = {}
    current_file_name = None
    for loc in locs:
        for line in loc.splitlines():
            if line.strip().endswith(".py"):
                current_file_name = line.strip()
            elif line.strip() and any(
                line.startswith(w)
                for w in ["line:", "function:", "class:", "variable:"]
            ):
                if current_file_name in file_names:
                    if current_file_name not in results:
                        results[current_file_name] = []
                    results[current_file_name].append(line)
                else:
                    pass

    for file_name in file_names:
        if file_name not in results:
            results[file_name] = []

    return {fn: ["\n".join(results[fn])] for fn in results.keys()}


class CompressTransformer(cst.CSTTransformer):
    DESCRIPTION = str = "Replaces function body with ..."
    replacement_string = '"__FUNC_BODY_REPLACEMENT_STRING__"'

    def __init__(self, keep_constant=True, keep_indent=False):
        self.keep_constant = keep_constant
        self.keep_indent = keep_indent

    def leave_Module(self, original_node, updated_node):
        new_body = [
            stmt
            for stmt in updated_node.body
            if m.matches(stmt, m.ClassDef())
            or m.matches(stmt, m.FunctionDef())
            or (
                self.keep_constant
                and m.matches(stmt, m.SimpleStatementLine())
                and m.matches(stmt.body[0], m.Assign())
            )
        ]
        return updated_node.with_changes(body=new_body)

    def leave_ClassDef(self, original_node, updated_node):
        new_body = [
            stmt
            for stmt in updated_node.body.body
            if not (
                m.matches(stmt, m.SimpleStatementLine())
                and m.matches(stmt.body[0], m.Expr())
                and m.matches(stmt.body[0].value, m.SimpleString())
            )
        ]
        return updated_node.with_changes(body=cst.IndentedBlock(body=new_body))

    def leave_FunctionDef(self, original_node, updated_node):
        if not self.keep_indent:
            new_expr = cst.Expr(value=cst.SimpleString(value=self.replacement_string))
            new_body = cst.IndentedBlock((new_expr,))
            return updated_node.with_changes(body=new_body)
        else:
            new_expr = [
                cst.Expr(value=cst.SimpleString(value=self.replacement_string)),
            ]
            return updated_node.with_changes(
                body=cst.IndentedBlock(body=[cst.SimpleStatementLine(body=new_expr)])
            )


class GlobalVariableVisitor(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (cst.metadata.PositionProvider,)

    def __init__(self):
        self.global_assigns = []

    def leave_Module(self, original_node):
        assigns = []
        for stmt in original_node.body:
            if m.matches(stmt, m.SimpleStatementLine()) and m.matches(
                stmt.body[0], m.Assign()
            ):
                start_pos = self.get_metadata(cst.metadata.PositionProvider, stmt).start
                end_pos = self.get_metadata(cst.metadata.PositionProvider, stmt).end
                assigns.append([stmt, start_pos, end_pos])
        self.global_assigns.extend(assigns)


def parse_global_var_from_code(file_content):
    try:
        tree = cst.parse_module(file_content)
    except Exception:
        return file_content

    wrapper = cst.metadata.MetadataWrapper(tree)
    visitor = GlobalVariableVisitor()
    wrapper.visit(visitor)

    global_assigns = {}
    for assign_stmt, start_pos, end_pos in visitor.global_assigns:
        for t in assign_stmt.body:
            try:
                targets = [t.targets[0].target.value]
            except Exception:
                try:
                    targets = t.targets[0].target.elements
                    targets = [x.value.value for x in targets]
                except Exception:
                    targets = []
            for target_var in targets:
                global_assigns[target_var] = {
                    "start_line": start_pos.line,
                    "end_line": end_pos.line,
                }
    return global_assigns


class _AssignVisitor(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (cst.metadata.PositionProvider,)

    def __init__(self):
        self.assigns = []

    def leave_Assign(self, original_node):
        stmt = original_node
        start_pos = self.get_metadata(cst.metadata.PositionProvider, stmt).start
        end_pos = self.get_metadata(cst.metadata.PositionProvider, stmt).end
        self.assigns.append([stmt, start_pos, end_pos])


def remove_lines(raw_code, remove_line_intervals):
    new_code = ""
    for i, line in enumerate(raw_code.splitlines()):
        if not any(start <= i + 1 <= end for start, end in remove_line_intervals):
            new_code += line + "\n"
        if any(start == i + 1 for start, _ in remove_line_intervals):
            new_code += "...\n"
    return new_code


def compress_assign_stmts(raw_code, total_lines=30, prefix_lines=10, suffix_lines=10):
    try:
        tree = cst.parse_module(raw_code)
    except Exception:
        return raw_code

    wrapper = cst.metadata.MetadataWrapper(tree)
    visitor = _AssignVisitor()
    wrapper.visit(visitor)

    remove_line_intervals = []
    for stmt in visitor.assigns:
        if stmt[2].line - stmt[1].line > total_lines:
            remove_line_intervals.append(
                (stmt[1].line + prefix_lines, stmt[2].line - suffix_lines)
            )
    return remove_lines(raw_code, remove_line_intervals)


def get_skeleton(
    raw_code,
    keep_constant=True,
    keep_indent=False,
    compress_assign=False,
    total_lines=30,
    prefix_lines=10,
    suffix_lines=10,
):
    try:
        tree = cst.parse_module(raw_code)
    except Exception:
        return raw_code

    transformer = CompressTransformer(keep_constant=keep_constant, keep_indent=True)
    modified_tree = tree.visit(transformer)
    code = modified_tree.code

    if compress_assign:
        code = compress_assign_stmts(
            code,
            total_lines=total_lines,
            prefix_lines=prefix_lines,
            suffix_lines=suffix_lines,
        )

    if keep_indent:
        code = code.replace(CompressTransformer.replacement_string + "\n", "...\n")
        code = code.replace(CompressTransformer.replacement_string, "...\n")
    else:
        pattern = f"\\n[ \\t]*{CompressTransformer.replacement_string}"
        replacement = "\n..."
        code = re.sub(pattern, replacement, code)

    return code


def _structure_for_sources(base_files):
    structure = {}

    for row in base_files:
        path = row["path"]
        content = row["content"]
        class_info, function_names, file_lines = parse_python_file("", content)

        current = structure
        parts = path.split("/")
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        current[parts[-1]] = {
            "classes": class_info,
            "functions": function_names,
            "text": file_lines,
        }

    return structure
