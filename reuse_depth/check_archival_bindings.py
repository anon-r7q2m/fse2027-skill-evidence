"""Check published record bindings without executing packages or study code.

This checks an existing scripted AP entry, not provider authenticity, every
package branch, task correctness, scoring, or the missing first failed entry.
"""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AP = ROOT / 'aider_ap'
RECORDS = AP / 'records'


def load(path):
    return json.loads(path.read_bytes())


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def require(condition, label):
    if not condition:
        raise ValueError(label)


def git_object(kind, content):
    return hashlib.sha1(f'{kind} {len(content)}\0'.encode() + content).hexdigest()


def one_file_tree(path, text):
    require('/' not in path, 'This archived fixture has one root-level file')
    blob = git_object('blob', text.encode())
    tree = b'100644 ' + path.encode() + b'\0' + bytes.fromhex(blob)
    return git_object('tree', tree)


def check_callbacks(folders):
    previous = None
    for index, name in enumerate(folders):
        folder = RECORDS / name
        incoming = load(folder / 'input.json')
        outgoing = load(folder / 'output.json')
        invocation = load(folder / 'invocation.json')
        require(digest_bytes(canonical(incoming)) == invocation['input_sha256'], 'Callback input identity: ' + name)
        require(invocation['worker_start'] == index and invocation['worker_stop'] == index + 1, 'Recorded worker range: ' + name)
        if previous is not None:
            require(previous['state'] == incoming['state'], 'Callback state continuity: ' + name)
        previous = outgoing


def main():
    provenance = load(ROOT / 'PROVENANCE.json')
    for record in provenance['records']:
        data = (ROOT / record['path']).read_bytes()
        require(digest_bytes(data) == record['publication_sha256'], 'Publication file identity: ' + record['path'])
        if record['representation'] == 'original_bytes':
            require(record['publication_sha256'] == record['original_sha256'], 'Original byte identity: ' + record['path'])
    catalog = load(ROOT / 'CATALOG_INSPECTION.json')['classes']
    identities = {}
    for entry in catalog:
        folder = ROOT / 'catalog' / entry['class'] / 'original_package'
        actual = {name: digest_bytes((folder / name).read_bytes()) for name in entry['file_sha256']}
        require(actual == entry['file_sha256'], 'Original module inventory: ' + entry['class'])
        identity = digest_bytes(canonical(actual))
        require(identity == entry['computed_file_map_digest'], 'Package file-map identity: ' + entry['class'])
        identities[entry['class']] = identity
    for key in ('A', 'P'):
        sealed = load(AP / f'{key}_original_seal.json')['finals']['direct']
        entry = next(x for x in catalog if x['class'] == key)
        require(sealed['package_files'] == entry['file_sha256'], key + ' original seal file map')
        require(sealed['package_sha256'] == identities[key], key + ' original seal package identity')

    a_names = ['architect/' + x for x in ('01_begin_architect', '02_architect_result', '03_editor_result')]
    p_names = ['P2/' + x for x in ('01_begin_samples', '02_sample_batch_ready', '03_candidate_batch_ready', '04_normalized_batch_ready')]
    check_callbacks(a_names)
    check_callbacks(p_names)
    handoff = load(RECORDS / a_names[1] / 'output.json')['effects'][0]
    advice = load(RECORDS / a_names[1] / 'input.json')['event']['text']
    p_begin = load(RECORDS / p_names[0] / 'input.json')['event']
    editor = load(RECORDS / 'editor_begin.json')
    require(advice == handoff['task_text'] == editor['issue'] == p_begin['issue'], 'Exact advice reaches original P input')
    require(handoff['cur_messages'] == [] and handoff['done_messages'] == [], 'Fresh histories in handoff')
    selection = load(RECORDS / p_names[-1] / 'output.json')['effects'][0]
    require(selection['counts'] == {'admitted': 4, 'attempted': 4, 'distinct_keys': 2, 'distinct_trees': 2, 'eligible': 4, 'winning_votes': 3}, 'Four admitted / three winning archived samples')
    for sample in selection['samples']:
        index = sample['sample_index']
        file = load(RECORDS / f'materialization/{index}/files.json')[0]
        require(one_file_tree(file['path'], file['after']) == sample['snapshot_ref'], 'Actual materialized tree: ' + str(index))
        require(one_file_tree(file['path'], file['before']) == p_begin['base_snapshot_ref'], 'Same base materialization: ' + str(index))
        receipt = load(RECORDS / f'P2/diff/{index}.json')['receipt']
        require(receipt['snapshot_ref'] == sample['snapshot_ref'], 'Normalization tree identity: ' + str(index))
        require(receipt['files'][0]['diff'] == sample['normalized_key'], 'Original normalization receipt: ' + str(index))
    tree = selection['vote']['snapshot_ref']
    capture = RECORDS / 'snapshots/capture_002'
    manifest = load(capture / 'capture_manifest.json')
    endpoint = load(RECORDS / 'endpoints.json')
    publication = endpoint['policies']['AP']['publication']
    terminal_input = load(RECORDS / a_names[-1] / 'input.json')['event']
    terminal = load(RECORDS / a_names[-1] / 'output.json')['effects'][0]
    require(tree == manifest['final_tree'] == publication['final_tree'] == terminal_input['snapshot_ref'] == terminal['final_snapshot_ref'], 'Vote/capture/publication/A terminal tree identity')
    require(digest_bytes((capture / 'agent.patch').read_bytes()) == manifest['patch']['sha256'] == publication['patch_sha256'], 'Actual patch bytes identity')
    require(digest_bytes((capture / 'capture_manifest.json').read_bytes()) == publication['manifest_sha256'], 'Original capture manifest identity')
    require(publication['recapture'] is False, 'Original capture published without recapture')
    selected_file = load(RECORDS / 'materialization/1/files.json')[0]
    require(selected_file['after'].startswith('\n'), 'Preserve the actual leading blank line')
    require(terminal['calls_used'] == 5 and terminal['usage'] == {'input_tokens': 500, 'output_tokens': 100}, 'Synthetic scripted account, not measured model cost')
    cleanup = load(RECORDS / 'cleanup.json')
    require(cleanup['cleanup_confirmed'] and not cleanup['errors'], 'Archived cleanup receipt')
    for index, worker in enumerate(cleanup['workers']['A']):
        require(worker['package_sha256'] == identities['A'], 'A worker package identity')
        require(worker['input_sha256'] == digest_bytes(canonical(load(RECORDS / a_names[index] / 'input.json'))), 'A worker input binding')
        require(worker['output_sha256'] == digest_bytes(canonical(load(RECORDS / a_names[index] / 'output.json'))), 'A worker output binding')
        require(worker['status'] == 'COMPLETED' and worker['return_code'] == 0 and worker['cleanup_confirmed'], 'A archived worker exit/cleanup')
    session = load(RECORDS / 'P2/session.json')
    require(session['package_sha256'] == identities['P'], 'P session package identity')
    parent = load(AP / 'parent_wait.json')
    require(parent['return_code'] == 0 and not parent['timed_out'] and not parent['process_group_remaining'], 'Archived original parent wait')
    both = load(AP / 'both_entries_terminal.json')
    require(both['actual_model_requests'] == both['benchmark_starts'] == both['scorer_starts'] == 0, 'Historical scripted entry counts')
    print(json.dumps({'status': 'PUBLISHED_ARCHIVAL_BINDINGS_CONSISTENT', 'catalog_classes': len(catalog), 'package_callbacks': 7, 'selected_tree': tree, 'new_package_executions': 0, 'new_model_benchmark_or_grader_calls': 0, 'provider_authenticity_or_task_correctness_certified': False}))


if __name__ == '__main__':
    main()
