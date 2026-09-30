import re

STATUSES = ("PASSED", "FAILED", "ERROR", "SKIPPED", "XFAIL", "XPASS", "MISSING")
_SEV = {
    "ERROR": 6,
    "FAILED": 5,
    "XPASS": 4,
    "SKIPPED": 3,
    "XFAIL": 2,
    "PASSED": 1,
    "MISSING": 0,
}

_PYTEST_RESULT_RE = re.compile(
    r"^(?P<id>.+?)\s+"
    r"(?P<st>PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)\b"
    r"(?:\s+\[[^\]]+\])?"
    r"(?:\s+.*)?$"
)
_PYTEST_COLLECTION_RE = re.compile(r"^(?:collecting \.\.\. )?collected (\d+) items?$")
_PYTEST_SUMMARY_COUNT_RE = re.compile(
    r"(\d+)\s+(passed|failed|error|errors|skipped|xfailed|xpassed)\b"
)
_UNITTEST_RAN_RE = re.compile(r"^Ran (\d+) tests? in ")
_UNITTEST_TERM_RE = re.compile(r"^(OK|FAILED)(?: \((.*)\))?$")
_TRACEBACK_FILE_RE = re.compile(r'^\s*File "([^"]+)", line (\d+), in .+$')
_DETAIL_HEADER_RE = re.compile(r"^(FAIL|ERROR): (.+)$")
_EXCEPTION_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*): (.*)$")


def _worst(vals):
    return max(vals, key=lambda x: _SEV.get(x, -1)) if vals else "MISSING"


def _counts():
    return {k: 0 for k in STATUSES}


def _looks_test_id(s):
    s = s.strip()
    if not s:
        return False
    if s.startswith(
        ("FAIL:", "ERROR:", "Traceback", "AssertionError:", "OK", "FAILED", "Ran ")
    ):
        return False
    if " ... " in s:
        return False
    if set(s) <= {"-", "="}:
        return False
    if re.match(r"^\S+\s+\([^)]+\)$", s):
        return True
    return s.startswith("test")


def _looks_pytest_id(s):
    s = s.strip()
    if not s:
        return False
    if s.startswith("="):
        return False
    return ("::" in s) or s.endswith(".py") or s.startswith("test")


def _u_status(s):
    if s == "ok":
        return "PASSED"
    if s == "FAIL":
        return "FAILED"
    if s == "ERROR":
        return "ERROR"
    if s.startswith("skipped"):
        return "SKIPPED"
    if s == "expected failure":
        return "XFAIL"
    if s == "unexpected success":
        return "XPASS"
    return None


def _parse_kvs(payload):
    out = {}
    if not payload:
        return out
    for part in payload.split(","):
        part = part.strip()
        if "=" not in part:
            out[part] = None
        else:
            k, v = part.split("=", 1)
            out[k.strip()] = int(v.strip()) if v.strip().isdigit() else None
    return out


def _owner_from_detail_id(tid):
    tid = tid.strip()
    m = re.match(r"^(.+?\s+\([^)]+\))(?:\s+.*|\s*\(.*\))?$", tid)
    return m.group(1) if m else tid


def _record_status(raw, test_id, status):
    raw.setdefault(test_id, []).append(status)


def _parse_unittest(text):
    lines = text.splitlines()
    raw = {}
    details = {}
    diags = []
    nstatus = 0

    pending = []

    def add_pending(test_id):
        nonlocal pending
        if pending:
            diags.append("overlapping_unfinished_parents")
        pending.append(test_id)

    def resolve_pending(status):
        nonlocal pending, nstatus
        if len(pending) == 1:
            _record_status(raw, pending[0], status)
            nstatus += 1
            pending = []
        elif not pending:
            diags.append("orphan_standalone_unittest_status")
        else:
            diags.append("ambiguous_standalone_unittest_status")

    roster_end = len(lines)
    for idx, ln in enumerate(lines):
        if (
            re.fullmatch(r"-{6,}", ln)
            or re.fullmatch(r"={6,}", ln)
            or _UNITTEST_RAN_RE.match(ln)
        ):
            roster_end = idx
            break

    for ln in lines[:roster_end]:
        stripped = ln.strip()
        standalone = _u_status(stripped) if " ... " not in ln else None
        if standalone is not None:
            resolve_pending(standalone)
            continue

        if " ... " in ln:
            left, right = ln.rsplit(" ... ", 1)
            left = left.strip()
            right = right.strip()
            inline_status = _u_status(right)
            if _looks_test_id(left):
                if inline_status is not None:
                    if pending:
                        diags.append("overlapping_unfinished_parents")
                    _record_status(raw, left, inline_status)
                    nstatus += 1
                else:
                    add_pending(left)
            elif inline_status is not None and pending:
                resolve_pending(inline_status)
            else:
                continue
            continue

        if _looks_test_id(stripped):
            add_pending(stripped)
            continue

    if pending:
        diags.append("unfinished_unittest_result_line")

    j = 0
    while j < len(lines):
        if not re.fullmatch(r"={6,}", lines[j]):
            j += 1
            continue
        if j + 1 >= len(lines):
            break
        header = _DETAIL_HEADER_RE.match(lines[j + 1])
        if not header:
            j += 1
            continue

        kind = "FAILED" if header.group(1) == "FAIL" else "ERROR"
        tid = _owner_from_detail_id(header.group(2))
        block = []
        k = j + 2
        while k < len(lines):
            if re.fullmatch(r"={6,}", lines[k]) or _UNITTEST_RAN_RE.match(lines[k]):
                break
            block.append(lines[k])
            k += 1

        frames = []
        exc = None
        msg = None
        for idx, ln in enumerate(block):
            fm = _TRACEBACK_FILE_RE.match(ln)
            if fm:
                src = block[idx + 1].strip() if idx + 1 < len(block) else ""
                frames.append(
                    {
                        "file": fm.group(1),
                        "line": int(fm.group(2)),
                        "source": src,
                    }
                )
            em = _EXCEPTION_RE.match(ln.strip())
            if em:
                exc, msg = em.group(1), em.group(2)

        details.setdefault(tid, []).append(
            {
                "kind": kind,
                "frames": frames,
                "exception": exc,
                "message": msg,
            }
        )
        j = k

    ran_matches = [
        (ix, _UNITTEST_RAN_RE.match(ln))
        for ix, ln in enumerate(lines)
        if _UNITTEST_RAN_RE.match(ln)
    ]
    if len(ran_matches) != 1:
        diags.append("missing_or_duplicate_unittest_ran_summary")
        ran = None
        ridx = None
    else:
        ridx, mm = ran_matches[0]
        ran = int(mm.group(1))

    terms = []
    if ridx is not None:
        for ln in lines[ridx + 1 :]:
            s = ln.strip()
            if _UNITTEST_TERM_RE.match(s):
                terms.append(s)

    if len(terms) != 1:
        diags.append("missing_or_duplicate_unittest_terminal_summary")
        term = None
    else:
        term = terms[0]

    if ran is not None and ran != nstatus:
        diags.append("unittest_ran_count_mismatch")

    obs = {}
    rawc = _counts()
    dup = False
    conf = False
    for tid, sts in raw.items():
        for st in sts:
            rawc[st] += 1
        if len(sts) > 1:
            dup = True
        if len(set(sts)) > 1:
            conf = True
        obs[tid] = _worst(sts)
    if dup:
        diags.append("duplicate_test_ids")
    if conf:
        diags.append("conflicting_test_statuses")

    if term is not None:
        m = _UNITTEST_TERM_RE.match(term)
        if not m:
            diags.append("invalid_unittest_terminal_summary")
        else:
            kind = m.group(1)
            kv = _parse_kvs(m.group(2))
            mp = {
                "failures": "FAILED",
                "errors": "ERROR",
                "skipped": "SKIPPED",
                "expected failures": "XFAIL",
                "unexpected successes": "XPASS",
            }
            for k, st in mp.items():
                if k in kv and kv[k] != rawc.get(st, 0):
                    diags.append("unittest_terminal_count_mismatch_" + k.replace(" ", "_"))
            bad = rawc["FAILED"] + rawc["ERROR"] + rawc["XPASS"]
            if kind == "OK" and bad:
                diags.append("unittest_ok_terminal_with_nonpassing_tests")
            if kind == "FAILED" and bad == 0:
                diags.append("unittest_failed_terminal_without_failures")

    return {
        "native_complete": not diags,
        "diagnostics": diags,
        "observed": obs,
        "failure_details": details,
        "saw_summary": ran is not None and term is not None and nstatus > 0,
    }


def _parse_pytest(text):
    lines = text.splitlines()
    raw = {}
    diags = []
    nstatus = 0

    collection_counts = []
    terminal_summaries = []

    for ln in lines:
        s = ln.strip()

        cm = _PYTEST_COLLECTION_RE.fullmatch(s)
        if cm:
            collection_counts.append(int(cm.group(1)))
        elif s.startswith("collecting ..."):
            diags.append("unfinished_pytest_collection")
        elif re.search(r"\bcollected\b", s) and re.search(r"\berror\b", s, re.I):
            diags.append("pytest_collection_error")

        rm = _PYTEST_RESULT_RE.match(s)
        if rm and _looks_pytest_id(rm.group("id")):
            _record_status(raw, rm.group("id"), rm.group("st"))
            nstatus += 1

        if s.startswith("=") and s.endswith("=") and _PYTEST_SUMMARY_COUNT_RE.search(s):
            terminal_summaries.append(s.strip("=").strip())

    if len(collection_counts) > 1:
        diags.append("duplicate_pytest_collection_summary")
        collected = None
    elif len(collection_counts) == 1:
        collected = collection_counts[0]
    else:
        collected = None

    if len(terminal_summaries) != 1:
        diags.append("missing_or_duplicate_pytest_terminal_summary")
        summary = None
    else:
        summary = terminal_summaries[0]

    if collected is not None and collected != nstatus:
        diags.append("pytest_collected_count_mismatch")

    obs = {}
    rawc = _counts()
    dup = False
    conf = False
    for tid, sts in raw.items():
        for st in sts:
            rawc[st] += 1
        if len(sts) > 1:
            dup = True
        if len(set(sts)) > 1:
            conf = True
        obs[tid] = _worst(sts)
    if dup:
        diags.append("duplicate_test_ids")
    if conf:
        diags.append("conflicting_test_statuses")

    if summary is not None:
        seen = {
            "PASSED": 0,
            "FAILED": 0,
            "ERROR": 0,
            "SKIPPED": 0,
            "XFAIL": 0,
            "XPASS": 0,
        }
        for n, word in _PYTEST_SUMMARY_COUNT_RE.findall(summary):
            n = int(n)
            mp = {
                "passed": "PASSED",
                "failed": "FAILED",
                "error": "ERROR",
                "errors": "ERROR",
                "skipped": "SKIPPED",
                "xfailed": "XFAIL",
                "xpassed": "XPASS",
            }
            seen[mp[word]] += n
        for st in ("PASSED", "FAILED", "ERROR", "SKIPPED", "XFAIL", "XPASS"):
            if seen[st] != rawc[st]:
                diags.append("pytest_terminal_count_mismatch_" + st)

    return {
        "native_complete": not diags,
        "diagnostics": diags,
        "observed": obs,
        "failure_details": {},
        "saw_summary": summary is not None and nstatus > 0,
    }


def _parse(parser, text):
    if parser == "django_verbose":
        return _parse_unittest(text)
    if parser == "pytest_verbose":
        return _parse_pytest(text)
    return {
        "native_complete": False,
        "diagnostics": ["unsupported_parser"],
        "observed": {},
        "failure_details": {},
        "saw_summary": False,
    }


def _combined_text(stdout, stderr):
    if not stdout:
        return stderr
    if not stderr:
        return stdout
    return stdout + ("" if stdout.endswith("\n") else "\n") + stderr


def _with_selected(parsed, name):
    out = dict(parsed)
    out["selected_stream"] = name
    return out


def _ambiguous_combo(combo):
    out = dict(combo)
    out["diagnostics"] = list(combo.get("diagnostics", [])) + ["ambiguous_stream_order"]
    out["native_complete"] = False
    out["selected_stream"] = "stdout_then_stderr"
    return out


def parse_native_log(parser, stdout, stderr):
    stdout = stdout if isinstance(stdout, str) else ""
    stderr = stderr if isinstance(stderr, str) else ""

    if stdout and not stderr:
        return _with_selected(_parse(parser, stdout), "stdout")
    if stderr and not stdout:
        return _with_selected(_parse(parser, stderr), "stderr")
    if not stdout and not stderr:
        return _with_selected(_parse(parser, ""), "empty")

    a = _parse(parser, stdout)
    b = _parse(parser, stderr)
    combo = _parse(parser, _combined_text(stdout, stderr))

    complete = []
    if a["native_complete"]:
        complete.append("stdout")
    if b["native_complete"]:
        complete.append("stderr")
    if combo["native_complete"]:
        complete.append("stdout_then_stderr")

    if len(complete) == 1:
        chosen = complete[0]
        if chosen == "stdout":
            return _with_selected(a, "stdout")
        if chosen == "stderr":
            return _with_selected(b, "stderr")
        return _with_selected(combo, "stdout_then_stderr")

    if len(complete) > 1:
        if (
            "stdout" in complete
            and "stdout_then_stderr" in complete
            and "stderr" not in complete
            and a["observed"] == combo["observed"]
            and a["failure_details"] == combo["failure_details"]
        ):
            return _with_selected(a, "stdout")
        if (
            "stderr" in complete
            and "stdout_then_stderr" in complete
            and "stdout" not in complete
            and b["observed"] == combo["observed"]
            and b["failure_details"] == combo["failure_details"]
        ):
            return _with_selected(b, "stderr")
        return _ambiguous_combo(combo)

    if combo["saw_summary"] and not a["saw_summary"] and not b["saw_summary"]:
        return _with_selected(combo, "stdout_then_stderr")
    if a["saw_summary"] and not b["saw_summary"]:
        return _with_selected(a, "stdout")
    if b["saw_summary"] and not a["saw_summary"]:
        return _with_selected(b, "stderr")
    if a["saw_summary"] and b["saw_summary"] and stdout != stderr:
        return _ambiguous_combo(combo)

    return _with_selected(combo, "stdout_then_stderr")


def matches_expected_assertion(test_id, observed_status, row, parsed):
    if row.get("disposition") != "EXPECTED_CHANGE" or observed_status != "FAILED":
        return False

    want = row.get("assertion")
    if not isinstance(want, dict):
        return False

    ds = parsed.get("failure_details", {}).get(test_id, [])
    if len(ds) != 1:
        return False

    d = ds[0]
    if (
        d.get("kind") != "FAILED"
        or d.get("exception") != want.get("exception")
        or d.get("message") != want.get("message")
    ):
        return False

    frames = d.get("frames") or []
    if len(frames) != 1:
        return False

    f = frames[0]
    return (
        f.get("file") == want.get("file")
        and f.get("line") == want.get("line")
        and (f.get("source") or "").strip() == (want.get("source") or "").strip()
    )
