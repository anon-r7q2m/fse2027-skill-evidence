import ast
import json

COMMON_ID_FIELDS = ("run_id", "base_commit", "base_snapshot_ref")
MAX_CANDIDATE_BYTES = 262144


def _reject(msg):
    raise ValueError("PROTOCOL_REJECTED: " + msg)


def _copy_identity(event):
    return {k: event[k] for k in COMMON_ID_FIELDS if k in event}


def _check_identity(event, state):
    ident = state.get("identity", {})
    for k, v in ident.items():
        if event.get(k) != v:
            _reject("identity mismatch for " + k)


def _next_request_id(state):
    n = int(state.get("next_request_num", 1))
    state["next_request_num"] = n + 1
    return str(n)


def _set_pending(state, effect, receipt_kind):
    state["pending"] = {
        "request_id": effect["request_id"],
        "receipt_kind": receipt_kind,
    }


def _consume_pending(event, state):
    pending = state.get("pending")
    if not isinstance(pending, dict):
        _reject("missing pending receipt")
    rid = event.get("request_id")
    if not isinstance(rid, str) or not rid:
        _reject("missing request_id")
    if rid != pending.get("request_id"):
        _reject("stale or foreign request_id")
    if event.get("kind") != pending.get("receipt_kind"):
        _reject("unexpected receipt kind")
    state.pop("pending", None)


def _make_effect(kind, payload, state):
    eff = {"kind": kind, "request_id": _next_request_id(state)}
    eff.update(state["identity"])
    eff.update(payload)
    return eff


def _count_occurrences(text, sub):
    count = 0
    start = 0
    while True:
        i = text.find(sub, start)
        if i < 0:
            return count
        count += 1
        start = i + 1


def _files_by_path(files):
    out = {}
    for f in files:
        p = f.get("path")
        if not isinstance(p, str) or not p or p in out:
            _reject("invalid files")
        out[p] = {"content": f.get("content"), "mode": f.get("mode")}
    return out


def _hint_paths(locations):
    out = set()
    if isinstance(locations, list):
        for loc in locations:
            if isinstance(loc, dict) and isinstance(loc.get("path"), str):
                out.add(loc["path"])
    return out


def _build_prompt(issue, files, locations):
    parts = [
        "Issue:",
        issue if isinstance(issue, str) else "",
        "",
        "Hint locations (JSON):",
        json.dumps(locations, ensure_ascii=False, separators=(",", ":")),
        "",
        "Files:",
    ]
    for f in files:
        parts.append(f"--- {f['path']} ({f['mode']}) ---")
        parts.append(f["content"])
    parts.append("")
    parts.append("Return the smallest valid fix as ordered exact-string edits.")
    return "\n".join(parts)


def _parse_completed_sample(text):
    try:
        obj = json.loads(text)
    except Exception:
        return None, "malformed JSON"
    if not isinstance(obj, dict) or set(obj.keys()) != {"edits"} or not isinstance(obj["edits"], list) or not obj["edits"]:
        return None, "invalid edit payload"
    edits = obj["edits"]
    for e in edits:
        if not isinstance(e, dict) or set(e.keys()) != {"path", "old_text", "new_text"}:
            return None, "invalid edit payload"
        if not isinstance(e["path"], str) or not e["path"]:
            return None, "invalid edit path"
        if not isinstance(e["old_text"], str) or not isinstance(e["new_text"], str):
            return None, "invalid edit text"
        if e["old_text"] == "":
            return None, "empty old_text"
    return edits, None


def _apply_sample(sample, files, locations):
    idx = sample.get("sample_index")
    status = sample.get("status")
    if status != "completed":
        return {"sample_index": idx, "status": "rejected", "reason": "sample not completed", "files": [], "rank": None}

    edits, err = _parse_completed_sample(sample.get("text"))
    if err:
        return {"sample_index": idx, "status": "rejected", "reason": err, "files": [], "rank": None}

    base = _files_by_path(files)
    current = {p: rec["content"] for p, rec in base.items()}
    touched = []
    touched_set = set()

    for e in edits:
        path = e["path"]
        if path not in current:
            return {"sample_index": idx, "status": "rejected", "reason": "unknown path", "files": [], "rank": None}
        now = current[path]
        old = e["old_text"]
        occ = _count_occurrences(now, old)
        if occ == 0:
            return {"sample_index": idx, "status": "rejected", "reason": "old_text not found", "files": [], "rank": None}
        if occ != 1:
            return {"sample_index": idx, "status": "rejected", "reason": "old_text ambiguous", "files": [], "rank": None}
        pos = now.find(old)
        current[path] = now[:pos] + e["new_text"] + now[pos + len(old):]
        if path not in touched_set:
            touched.append(path)
            touched_set.add(path)

    ordered_touched = [f["path"] for f in files if f["path"] in touched_set]
    out_files = []
    total_bytes = 0
    for path in ordered_touched:
        before = base[path]["content"]
        after = current[path]
        try:
            ast.parse(after, filename=path)
        except SyntaxError:
            return {"sample_index": idx, "status": "rejected", "reason": "python syntax error", "files": [], "rank": None}
        total_bytes += len(before.encode("utf-8")) + len(after.encode("utf-8"))
        out_files.append({"path": path, "before": before, "after": after})

    if total_bytes > MAX_CANDIDATE_BYTES:
        return {"sample_index": idx, "status": "rejected", "reason": "candidate too large", "files": [], "rank": None}

    hint = _hint_paths(locations)
    overlap = sum(1 for p in ordered_touched if p in hint)
    delta = sum(abs(len(f["after"]) - len(f["before"])) for f in out_files)
    rank = [-overlap, len(out_files), delta, total_bytes, idx]
    return {"sample_index": idx, "status": "accepted", "reason": "valid ordered edits", "files": out_files, "rank": rank}


def _normalize_four(rows, name):
    if not isinstance(rows, list) or len(rows) != 4:
        _reject("expected four " + name)
    by_index = {}
    for row in rows:
        if not isinstance(row, dict):
            _reject("invalid " + name)
        i = row.get("sample_index")
        if i not in (1, 2, 3, 4) or i in by_index:
            _reject("invalid " + name)
        by_index[i] = row
    return [by_index[i] for i in (1, 2, 3, 4)]


def handle(event, state):
    if not isinstance(event, dict) or not isinstance(state, dict):
        _reject("invalid input")
    if state.get("phase") == "done":
        _reject("terminal reuse")

    phase = state.get("phase")
    if phase is None:
        if event.get("kind") != "begin":
            _reject("expected begin")
        if state:
            _reject("nonempty initial state")
        files = event.get("files")
        if not isinstance(files, list) or not (0 < len(files) <= 3):
            _reject("invalid begin files")
        for f in files:
            if not isinstance(f, dict):
                _reject("invalid begin files")
            if not isinstance(f.get("path"), str) or not f["path"]:
                _reject("invalid begin files")
            if not isinstance(f.get("content"), str) or f["content"] == "":
                _reject("invalid begin files")
            if f.get("mode") not in ("100644", "100755"):
                _reject("invalid begin files")

        new_state = {
            "phase": "await_samples",
            "identity": _copy_identity(event),
            "next_request_num": 1,
            "issue": event.get("issue", ""),
            "files": files,
            "locations": event.get("locations", []),
            "limits": event.get("limits", {}),
        }
        effect = _make_effect(
            "sample_batch",
            {
                "instructions": (
                    "Return only strict JSON with exactly "
                    '{"edits":[{"path":"file.py","old_text":"...","new_text":"..."}]}. '
                    "Use ordered exact-string replacements against the supplied files. "
                    "old_text must be non-empty and match exactly once in the current evolving file text. "
                    "No markdown or commentary."
                ),
                "prompt": _build_prompt(new_state["issue"], files, new_state["locations"]),
            },
            new_state,
        )
        _set_pending(new_state, effect, "samples_ready")
        return {"state": new_state, "effects": [effect]}

    _check_identity(event, state)

    if phase == "await_samples":
        _consume_pending(event, state)
        files = state["files"]
        locations = state.get("locations", [])
        samples = _normalize_four(event.get("samples"), "samples")
        evaluated = [_apply_sample(s, files, locations) for s in samples]
        rows = [
            {
                "sample_index": r["sample_index"],
                "status": r["status"],
                "reason": r["reason"],
                "files": r["files"] if r["status"] == "accepted" else [],
            }
            for r in evaluated
        ]
        new_state = dict(state)
        new_state["phase"] = "await_captures"
        new_state["candidates"] = evaluated
        effect = _make_effect("candidates", {"samples": rows}, new_state)
        _set_pending(new_state, effect, "captures_ready")
        return {"state": new_state, "effects": [effect]}

    if phase == "await_captures":
        _consume_pending(event, state)
        captures = _normalize_four(event.get("samples"), "captures")
        cand_by_idx = {c["sample_index"]: c for c in state.get("candidates", [])}
        best = None
        for row in captures:
            idx = row["sample_index"]
            cand = cand_by_idx.get(idx)
            if cand is None:
                _reject("missing candidate")
            status = row.get("status")
            snap = row.get("snapshot_ref")
            if cand["status"] == "accepted":
                if status != "accepted":
                    _reject("capture status mismatch")
                if snap is None:
                    continue
                rank = cand["rank"]
                if best is None or rank < best["rank"]:
                    best = {"sample_index": idx, "rank": rank}
            else:
                if status != "rejected":
                    _reject("capture status mismatch")
                if snap is not None:
                    _reject("rejected capture with snapshot")
        new_state = dict(state)
        new_state["phase"] = "done"
        new_state.pop("pending", None)
        effect = _make_effect(
            "selection",
            {
                "sample_index": None if best is None else best["sample_index"],
                "reason": "no accepted captured candidate" if best is None else "best valid localized edit candidate",
            },
            new_state,
        )
        return {"state": new_state, "effects": [effect]}

    _reject("unknown phase")
