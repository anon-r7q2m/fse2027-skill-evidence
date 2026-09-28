import json

def _infer_kind(event, state):
    k = event.get("kind")
    if k:
        return k
    if not state and "issue" in event and "tracked_paths" in event:
        return "begin"
    if "files" in event:
        return "files_ready"
    if "status" in event:
        return "model_result"
    return None

def _id_from_event(event):
    return {
        "run_id": event.get("run_id"),
        "base_commit": event.get("base_commit"),
        "base_snapshot_ref": event.get("base_snapshot_ref"),
    }

def _check_identity(event, state):
    if "id" not in state:
        return
    for k, v in state["id"].items():
        ev = event.get(k)
        if ev is not None and v is not None and ev != v:
            raise ValueError("PROTOCOL_REJECTED: wrong identity")

def _effect(state, kind, extra):
    rid = "req-%d" % state["next_req"]
    state["next_req"] += 1
    eff = {
        "kind": kind,
        "run_id": state["id"]["run_id"],
        "base_commit": state["id"]["base_commit"],
        "base_snapshot_ref": state["id"]["base_snapshot_ref"],
        "request_id": rid,
    }
    eff.update(extra)
    return eff

def _model_effect(state, purpose, prompt):
    eff = _effect(state, "model_request", {"purpose": purpose, "prompt": prompt})
    state["pending"] = {"kind": "model_request", "purpose": purpose, "request_id": eff["request_id"]}
    return eff

def _read_effect(state, paths):
    eff = _effect(state, "read_files", {"paths": paths})
    state["pending"] = {"kind": "read_files", "request_id": eff["request_id"]}
    return eff

def _handoff(state, status, reason, selected_files, localized_files, locations):
    eff = _effect(state, "localization_handoff", {
        "status": status,
        "reason": reason,
        "selected_files": selected_files,
        "localized_files": localized_files,
        "locations": locations,
    })
    state["phase"] = "terminal"
    state["pending"] = {"kind": "terminal", "request_id": eff["request_id"]}
    return eff

def _receipt_check(event, state, expected_kind):
    p = state.get("pending")
    if not p or p.get("kind") != expected_kind:
        raise ValueError("PROTOCOL_REJECTED: stale receipt")
    rk = _infer_kind(event, state)
    if rk != ("files_ready" if expected_kind == "read_files" else "model_result"):
        raise ValueError("PROTOCOL_REJECTED: receipt kind")
    if "request_id" in event and event["request_id"] != p["request_id"]:
        raise ValueError("PROTOCOL_REJECTED: stale receipt")
    if expected_kind == "model_request" and event.get("purpose") is not None and event.get("purpose") != p.get("purpose"):
        raise ValueError("PROTOCOL_REJECTED: receipt kind")

def _json_parse(text):
    try:
        return json.loads(text)
    except Exception:
        return None

def _parse_paths(text, tracked):
    obj = _json_parse(text)
    if not isinstance(obj, dict) or set(obj.keys()) != {"paths"} or not isinstance(obj["paths"], list):
        return None
    seen = set()
    out = []
    tracked_set = set(tracked)
    for x in obj["paths"]:
        if not isinstance(x, str):
            return None
        if x in tracked_set and x not in seen:
            seen.add(x)
            out.append(x)
            if len(out) == 3:
                break
    return out

def _line_count(s):
    return len(s.splitlines())

def _parse_locations(text, available_map):
    obj = _json_parse(text)
    if not isinstance(obj, dict) or set(obj.keys()) != {"locations"} or not isinstance(obj["locations"], list):
        return None
    if not obj["locations"]:
        return []
    out = []
    seen = set()
    for item in obj["locations"]:
        if not isinstance(item, dict) or set(item.keys()) != {"path", "start", "end"}:
            return None
        path = item["path"]
        start = item["start"]
        end = item["end"]
        if not isinstance(path, str) or not isinstance(start, int) or isinstance(start, bool) or not isinstance(end, int) or isinstance(end, bool):
            return None
        if path not in available_map:
            return None
        n = _line_count(available_map[path]["content"])
        if start < 1 or end < start or end > n:
            return None
        key = (path, start, end)
        if key not in seen:
            seen.add(key)
            out.append({"path": path, "start": start, "end": end})
    return out

def _paths_prompt(issue, tracked_paths):
    head = (
        "Select up to three repository-relative paths most relevant to the issue.\n"
        "Return only JSON exactly like {\"paths\":[\"a.py\"]}.\n"
        "Issue:\n" + issue + "\nTracked paths:\n"
    )
    budget = 950000 - len(head.encode("utf-8"))
    parts = []
    used = 0
    for p in tracked_paths:
        frag = p + "\n"
        b = len(frag.encode("utf-8"))
        if used + b > budget:
            break
        parts.append(frag)
        used += b
    return head + "".join(parts)

def _numbered(path, content):
    lines = content.splitlines()
    body = "".join("%d: %s\n" % (i + 1, line) for i, line in enumerate(lines))
    return "FILE %s\n%s" % (path, body)

def _locations_prompt(issue, files):
    intro = (
        "Identify the most relevant line ranges for the issue using only the provided files.\n"
        "Return only JSON exactly like {\"locations\":[{\"path\":\"a.py\",\"start\":1,\"end\":2}]}.\n"
        "Use valid 1-based inclusive line numbers and only the given file paths.\n"
        "Issue:\n" + issue + "\nFiles:\n"
    )
    budget = 950000 - len(intro.encode("utf-8"))
    parts = []
    used = 0
    for f in files:
        frag = _numbered(f["path"], f["content"])
        b = len(frag.encode("utf-8"))
        if used + b > budget:
            if not parts:
                frag = frag.encode("utf-8")[:max(0, budget)].decode("utf-8", "ignore")
                parts.append(frag)
            break
        parts.append(frag)
        used += b
    return intro + "\n".join(parts)

def handle(event, state):
    if state is None:
        state = {}
    kind = _infer_kind(event, state)
    if state.get("phase") == "terminal":
        raise ValueError("PROTOCOL_REJECTED: terminal reuse")
    if not state:
        if kind != "begin":
            raise ValueError("PROTOCOL_REJECTED: wrong identity")
        tracked = event.get("tracked_paths")
        if not isinstance(tracked, list):
            raise ValueError("PROTOCOL_REJECTED: wrong identity")
        state = {
            "id": _id_from_event(event),
            "phase": "await_paths",
            "next_req": 1,
            "pending": None,
            "issue": event.get("issue", ""),
            "tracked_paths": tracked,
            "selected_files": [],
            "available_files": [],
        }
        eff = _model_effect(state, "paths", _paths_prompt(state["issue"], tracked))
        return {"state": state, "effects": [eff]}

    _check_identity(event, state)

    if kind == "begin":
        raise ValueError("PROTOCOL_REJECTED: terminal reuse")

    if state["phase"] == "await_paths":
        _receipt_check(event, state, "model_request")
        status = event.get("status")
        if status == "output_failed":
            eff = _handoff(state, "NO_LOCALIZATION", "model output failed during path selection", [], [], [])
            return {"state": state, "effects": [eff]}
        if status != "completed":
            eff = _handoff(state, "NO_LOCALIZATION", "path selection did not complete", [], [], [])
            return {"state": state, "effects": [eff]}
        paths = _parse_paths(event.get("text", ""), state["tracked_paths"])
        if not paths:
            eff = _handoff(state, "NO_LOCALIZATION", "no valid selected files", [], [], [])
            return {"state": state, "effects": [eff]}
        state["selected_files"] = paths
        state["phase"] = "await_files"
        eff = _read_effect(state, paths)
        return {"state": state, "effects": [eff]}

    if state["phase"] == "await_files":
        _receipt_check(event, state, "read_files")
        files = event.get("files")
        if not isinstance(files, list):
            raise ValueError("PROTOCOL_REJECTED: receipt kind")
        paths = [f.get("path") for f in files if isinstance(f, dict)]
        if paths != state["selected_files"]:
            raise ValueError("PROTOCOL_REJECTED: stale receipt")
        available = []
        for f in files:
            if not isinstance(f, dict):
                raise ValueError("PROTOCOL_REJECTED: receipt kind")
            if f.get("status") == "available":
                if not isinstance(f.get("content"), str) or f.get("mode") not in ("100644", "100755"):
                    raise ValueError("PROTOCOL_REJECTED: receipt kind")
                available.append({
                    "path": f["path"],
                    "content": f["content"],
                    "mode": f["mode"],
                })
        state["available_files"] = available
        if not available:
            eff = _handoff(state, "NO_LOCALIZATION", "selected files unavailable", state["selected_files"], [], [])
            return {"state": state, "effects": [eff]}
        state["phase"] = "await_locations"
        eff = _model_effect(state, "locations", _locations_prompt(state["issue"], available))
        return {"state": state, "effects": [eff]}

    if state["phase"] == "await_locations":
        _receipt_check(event, state, "model_request")
        status = event.get("status")
        if status == "output_failed":
            eff = _handoff(state, "NO_LOCALIZATION", "model output failed during localization", state["selected_files"], [], [])
            return {"state": state, "effects": [eff]}
        if status != "completed":
            eff = _handoff(state, "NO_LOCALIZATION", "localization did not complete", state["selected_files"], [], [])
            return {"state": state, "effects": [eff]}
        avail = {f["path"]: f for f in state["available_files"]}
        locations = _parse_locations(event.get("text", ""), avail)
        if not locations:
            eff = _handoff(state, "NO_LOCALIZATION", "no valid locations", state["selected_files"], [], [])
            return {"state": state, "effects": [eff]}
        localized_files = []
        seen = set()
        for loc in locations:
            if loc["path"] not in seen:
                seen.add(loc["path"])
                localized_files.append(loc["path"])
        eff = _handoff(state, "LOCALIZED", "localized relevant lines", state["selected_files"], localized_files, locations)
        return {"state": state, "effects": [eff]}

    raise ValueError("PROTOCOL_REJECTED: stale receipt")
