"""Materialize independent test byte recipes. Not imported by production code."""
import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
PREP = ROOT / 'expectations/mvp01/v0.1/additional-cases.json'
PREP_SHA = '34a92d1a8dd8039b20cbf380985d63c47189b6d86fd9c96fa04d77c9f768d40b'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    out = Path(args.out).resolve()
    if not out.is_relative_to((ROOT / 'fixtures/mvp01').resolve()):
        parser.error('materialize only under fixtures/mvp01 with a fresh version directory')
    data = PREP.read_bytes()
    if digest(data) != PREP_SHA:
        raise ValueError('Independent preimplementation recipe changed')
    recipes = json.loads(data)['xpt_fixtures']
    # Build and validate everything before creating the delivery directory.
    built = {}
    for name, recipe in recipes.items():
        seed = (ROOT / recipe['base_path']).resolve()
        if not seed.is_relative_to(ROOT / 'artifacts/TASK-001/gate1-v0.1'):
            raise ValueError('Seed must resolve inside the approved package')
        raw = seed.read_bytes()
        if digest(raw) != recipe['base_sha256']:
            raise ValueError('Approved seed mismatch')
        header = bytearray(raw)
        for edit in recipe['edits']:
            offset, length = edit['offset'], edit['length']
            value = bytes.fromhex(edit['replacement_hex'])
            if len(value) != length or offset < 0 or offset + length > len(header):
                raise ValueError('Invalid fixed-length manufacturing edit')
            header[offset:offset + length] = value
        payload = bytes.fromhex(recipe['payload_pattern_hex']) * recipe['payload_repeat']
        content = bytes(header) + payload + b' ' * recipe['ascii_padding_bytes']
        if len(content) != recipe['bytes'] or digest(content) != recipe['sha256']:
            raise ValueError('Independent byte recipe mismatch: ' + name)
        if len(payload) % recipe['row_width']:
            raise ValueError('Manufacturing payload is not whole rows')
        built[name] = (content, len(payload) // recipe['row_width'])
    out.mkdir(parents=True, exist_ok=False)
    records = []
    for name, (content, count) in built.items():
        path = out / (name + '.xpt')
        path.write_bytes(content)
        if digest(path.read_bytes()) != recipes[name]['sha256']:
            raise ValueError('Written byte mismatch')
        records.append({'file': path.name, 'sha256': digest(content), 'bytes': len(content),
                        'manufactured_record_count': count, 'member': 'VS', 'test_only': True})
    provenance = {'source_id': 'TEST-MANUFACTURE-M01-001', 'test_only': True,
                  'purpose': 'Independent recipe materialization, no engine execution or business approval',
                  'recipe_path': PREP.relative_to(ROOT).as_posix(), 'recipe_sha256': PREP_SHA,
                  'builder_sha256': digest(Path(__file__).read_bytes()), 'files': records}
    save(out / 'manufacturing-record.json', provenance)
    provenance_sha = digest((out / 'manufacturing-record.json').read_bytes())
    save(out / 'read-context.json', {'schema_version': 'mvp01-read-context-0.1', 'study_id': 'SYN001',
         'family': 'SDTM', 'test_only': True, 'declarations': [
             {'declaration_id': 'TEST-READ-' + name, 'source_sha256': row['sha256'], 'member': 'VS',
              'encoding': 'utf-8' if name in ['utf8', 'invalid_utf8', 'nbsp', 'scale10000'] else 'ascii',
              'record_count': row['manufactured_record_count'], 'provided_by': 'TEST_FIXTURE_MANUFACTURER',
              'provenance': {'source_id': provenance['source_id'], 'source_sha256': provenance_sha,
                             'locator': '/files/' + str(index)}} for index, (name, row) in enumerate(zip(built, records))]})
    save(out / 'manifest.json', {'scope': '8 independent synthetic XPT byte fixtures; no engine tested',
         'files': [{'path': p.name, 'sha256': digest(p.read_bytes()), 'bytes': p.stat().st_size} for p in sorted(out.iterdir())],
         'excludes_self': True})
    print(json.dumps({'out': out.relative_to(ROOT).as_posix(), 'materialized': len(records),
                      'independent_hash_matches': len(records), 'engine_cases_executed': 0}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
