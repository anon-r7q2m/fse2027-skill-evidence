"""Strict syntax-failure linkage; raw frames stay inside the evaluator."""

import re

SYNTAX_CLASSES = ("SyntaxError", "IndentationError", "TabError")
START = ">>>>> Start Test Output"
END = ">>>>> End Test Output"


def exception_site(raw):
    """Return one unambiguous syntax site internally, or reject without its text."""
    start = raw.find(START)
    end = raw.find(END, start + len(START))
    if start < 0 or end < 0:
        return None
    body = raw[start + len(START) : end]
    if (
        body.count("Traceback (most recent call last):") != 1
        or "During handling of the above exception" in body
        or "direct cause of the following exception" in body
    ):
        return None
    endings = list(re.finditer(r"(?m)^([A-Za-z_][A-Za-z_0-9.]*(?:Error|Exception)):", body))
    if len(endings) != 1 or endings[0].group(1) not in SYNTAX_CLASSES:
        return None
    ending_line_end = body.find("\n", endings[0].end())
    if ending_line_end >= 0 and body[ending_line_end + 1 :].strip():
        return None
    trace_start = body.index("Traceback (most recent call last):")
    before = body[trace_start : endings[0].start()]
    frames = list(re.finditer(r'^\s*File "([^"\n]+)", line (\d+)(?:, in [^\n]+)?$', before, re.M))
    if not frames:
        return None
    frame = frames[-1]
    path = frame.group(1)
    if not path.startswith("/testbed/"):
        return None
    relative = path[len("/testbed/") :]
    if not relative.endswith(".py") or ".." in relative.split("/"):
        return None
    # Traceback followed by an ordinary source line and caret is allowed.
    # Another frame/exception or unrelated text after the syntax ending is not.
    return {"path": relative, "line": int(frame.group(2)), "exception_class": endings[0].group(1)}
