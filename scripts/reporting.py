"""Offline assertions, exact reproduction requests, and a static report viewer."""
import base64
import collections
import hashlib
import html
import json
from pathlib import Path
import shlex

ROOT = Path(__file__).resolve().parents[1]
WARNING = 'Experimental, commissioned as a test of the IMD swarm. It may not work as described. Read the code, start with small amounts, no warranty.'


def parsed(record):
    try:
        return json.loads(record['response']['body'])
    except (KeyError, ValueError):
        return None


def evaluate(case, record):
    if record is None:
        return 'NOT RUN', 'No saved response.'
    if 'transport_error' in record:
        return 'INCONCLUSIVE', 'Transport error: ' + record['transport_error']
    r = record['response']; status = r['status']; data = parsed(record)
    e = case['expect']; mode = e.get('mode'); errors = []
    if status == 429 or status >= 500:
        return 'INCONCLUSIVE', f'HTTP {status}; provider/rate failure cannot establish the input rule.'
    blockers = data.get('blockers', []) if isinstance(data, dict) else []
    details = json.dumps(blockers, ensure_ascii=False)
    detail = (data.get('detail', '') if isinstance(data, dict) else '')
    summary = f'HTTP {status}'
    if isinstance(data, dict) and data.get('error'):
        summary += '; ' + str(data['error']) + (': '+str(detail) if detail else '')
    if blockers:
        summary += '; blockers=' + details
    if mode == 'observe':
        return 'OBSERVED', summary + '; documentation does not specify the exact outcome.'
    if mode == 'schema_reject':
        # A refusal must actually identify the relevant field, not an unrelated blocker.
        aliases = e.get('aliases', [e.get('field', '')])
        text = str(detail) + ' ' + details
        refused = (status in (400, 413, 422) or bool(blockers))
        relevant = any(x.lower() in text.lower() for x in aliases)
        if refused and relevant:
            return 'PASS', summary
        if refused:
            return 'INCONCLUSIVE', summary + '; refusal did not identify the tested field.'
        return 'FAIL', summary + '; documented invalid input was not refused.'
    if mode == 'schema_accept':
        if status == 200:
            # This checks structural acceptance only, not admission or evaluator agreement.
            return 'PASS', summary + '; outer input schema accepted; this does not assert admission.'
        return 'FAIL', summary + '; documented boundary did not pass the input schema.'
    if mode == 'range' and status == 400:
        return 'PASS', summary + '; out-of-range query rejected.'
    if mode == 'facts':
        facts={f.get('id'):f for f in data.get('facts',[])} if isinstance(data,dict) else {}
        for key in e['required_missing']:
            f=facts.get(key,{})
            if f.get('required') is not True or f.get('state') != 'missing' or not any(b.get('code')=='missing_fact' and b.get('fact')==key for b in blockers):
                errors.append('missing required fact/blocker '+key)
    if mode == 'blocker':
        matched = bool(blockers) and e.get('contains', '') in details
        if not matched: errors.append('expected blocker '+repr(e.get('contains', '')))
    if mode in ('no_blocker', 'facts') and status != 200:
        errors.append('expected HTTP 200')
    if e.get('json') and data is None:
        errors.append('expected valid JSON')
    if mode == 'no_blocker' and e.get('contains', '') in details:
        errors.append('unexpected '+e['contains'])
    if mode == 'runtime':
        text = json.dumps(data)
        if all(x in text for x in e['contains']):
            return 'FAIL', summary + '; historical runtime record contains the documented step and path_violation.'
        return 'INCONCLUSIVE', summary + '; expected historical runtime evidence absent.'
    if 'status' in e and status != e['status']:
        errors.append(f'expected HTTP {e["status"]}')
    if 'error' in e and (not isinstance(data,dict) or data.get('error') != e['error']):
        errors.append('expected error '+e['error'])
    for key in e.get('keys', []):
        if not isinstance(data,dict) or key not in data:errors.append('missing '+key)
    for key,val in e.get('equals', {}).items():
        if not isinstance(data,dict) or data.get(key, object()) != val: errors.append('unexpected '+key)
    if 'item_keys' in e:
        key, keys = e['item_keys']; rows=data.get(key) if isinstance(data,dict) else None
        if not isinstance(rows,list):errors.append('missing array '+key)
        else:
            for itemkey in keys:
                missing=[i for i,row in enumerate(rows) if not isinstance(row,dict) or itemkey not in row]
                if missing:errors.append(f'{key} rows missing {itemkey}: '+str(missing[:5]))
            if not rows:return 'INCONCLUSIVE', summary + '; empty array cannot establish item shape.'
    if 'only_item_keys' in e:
        key, keys = e['only_item_keys'];rows=data.get(key) if isinstance(data,dict) else None
        if not isinstance(rows,list) or any(set(row)!=set(keys) for row in rows):errors.append('fields projection differs')
    if 'array_max' in e:
        key, maximum=e['array_max'];rows=data.get(key) if isinstance(data,dict) else None
        if not isinstance(rows,list):errors.append('missing array '+key)
        elif len(rows)>maximum:errors.append(f'{len(rows)} rows exceeds {maximum}')
        elif maximum>1 and len(rows)<maximum:summary+='; sparse sample: clamp upper bound only, exact clamp not proven'
    if 'cors' in e:
        headers={k.lower():v for k,v in r['headers']}
        allow=headers.get('access-control-allow-origin')
        present=allow in ('*', 'https://example.org')
        if present != e['cors']:errors.append('unexpected Access-Control-Allow-Origin='+repr(allow))
    return ('FAIL', summary+'; '+'; '.join(errors)) if errors else ('PASS', summary)


def command(record, body_path):
    req = record['request']
    parts=['curl', '--max-time', '60', '--request', req['method']]
    for key,val in req['headers'].items():parts += ['--header', key+': '+val]
    if req['body'] is not None:parts += ['--data-binary', '@'+body_path]
    parts += [req['url']]
    return ' '.join(shlex.quote(p) for p in parts)


def report(cases, directory):
    outcomes=[]; requests=ROOT/'results'/'requests'; requests.mkdir(parents=True,exist_ok=True)
    rows=[];cors=[];mismatches=[]
    for c in cases:
        path=directory/(c['id']+'.json');r=json.loads(path.read_text()) if path.exists() else None
        status,reason=evaluate(c,r)
        outcome={'id':c['id'],'status':status,'reason':reason,'docs':c['docs']}
        outcomes.append(outcome)
        esc=lambda s:str(s).replace('|','\\|').replace('\n',' ')
        evidence=f'[raw](results/probes/{c["id"]}.json)' if r else '—'
        rows.append(f'| {c["id"]} | [{esc(c["claim"])}]({c["docs"]}) | {status} | {esc(reason)} | {evidence} |')
        if r:
            req=r['request']; bp=f'results/requests/{c["id"]}.json'
            if req['body'] is not None:(ROOT/bp).write_text(req['body'])
            if c.get('headers',{}).get('Origin'):
                headers={k.lower():v for k,v in r.get('response',{}).get('headers',[])}
                cors.append(f'| {c["id"]} | `{req["method"]} {req["url"]}` | {r.get("response",{}).get("status","error")} | `{headers.get("access-control-allow-origin","absent")}` |')
            if status=='FAIL':
                mismatches += [f'### {c["id"]}',f'Documented claim: [{c["claim"]}]({c["docs"]})',f'Observed: {reason}',f'Exact request (from repository root; each curl is a live call and bypasses the runner budget, so wait at least 2 seconds and account for it):\n\n```sh\n{command(r,bp)}\n```',f'Full response, headers and timestamps: [{c["id"]}](results/probes/{c["id"]}.json).']
    counts=collections.Counter(x['status'] for x in outcomes)
    (ROOT/'results'/'outcomes.json').write_text(json.dumps(outcomes,indent=2)+'\n')
    table='| Probe | Claim and docs section | Result | Observation | Evidence |\n|---|---|---|---|---|\n'+'\n'.join(rows)
    (ROOT/'claims.md').write_text(WARNING+'\n\n# Documented behavior checklist\n\nEach row is one fixed request; positive schema probes establish only schema acceptance, not eventual admission. Expectations and exact request bodies are in [claims.json](claims.json). OBSERVED marks exploratory inputs for which the docs do not prescribe a precise outcome. INCONCLUSIVE and NOT RUN are not passes.\n\n'+table+'\n')
    notes=(ROOT/'report-notes.md').read_text() if (ROOT/'report-notes.md').exists() else ''
    records=[json.loads(p.read_text()) for p in directory.glob('*.json')]
    times=sorted(r['started_at'] for r in records)
    interval=min((b-a for a,b in zip(times,times[1:])),default=0)
    summary=', '.join(f'{k}: {v}' for k,v in sorted(counts.items()))
    text=WARNING+'\n\n# IMD public API documentation audit\n\n'+summary+f'. Saved probes: {len(records)}. Minimum recorded start-to-start spacing: {interval:.3f} seconds.\n\n'+notes+'\n\n## Every tested claim\n\n'+table+'\n\n## Exact requests for mismatches\n\n'+'\n\n'.join(mismatches)+'\n\n## CORS observations\n\nAll rows below sent `Origin: https://example.org`. An absent header does not make a server-to-server request fail. No OPTIONS/preflight calls were made; a GET header observation does not establish full browser POST support. Error responses are distinguished by status. Documentation says selected routes permit CORS ([Base URLs](https://imd.fun/docs/#base)).\n\n| Probe | Request | Status | Access-Control-Allow-Origin |\n|---|---|---|---|\n'+'\n'.join(cors)+'\n'
    (ROOT/'report.md').write_text(text)
    # No JS, external assets or network calls. Escaping prevents response data becoming HTML.
    page='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Experimental IMD docs audit</title><style>body{max-width:1000px;margin:2rem auto;padding:0 1rem;font:16px/1.5 system-ui}aside{padding:1rem;background:#fff1ce;border:2px solid #875d00}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style><body><aside role="note">'+html.escape(WARNING)+'</aside><h1>IMD public API documentation audit</h1><p>'+html.escape(summary)+'</p><p><a href="report.md">Report and exact reproductions</a> · <a href="claims.md">Claims</a> · <a href="claims.json">Machine-readable probes</a> · <a href="README.md">Run instructions</a></p><pre>'+html.escape(notes)+'</pre></body></html>\n'
    (ROOT/'index.html').write_text(page)
    print(summary)


def verify(cases, directory):
    from audit import validate_request, body_bytes
    ids=[c['id'] for c in cases];assert len(ids)==len(set(ids)), 'Duplicate probe IDs'
    records=[]
    for c in cases:
        validate_request(c)
        assert c['docs'].startswith('https://imd.fun/docs/#')
        p=directory/(c['id']+'.json')
        if not p.exists():continue
        r=json.loads(p.read_text());assert r['id']==c['id']
        assert r['request']['url']==c['url'] and r['request']['method']==c['method']
        b=body_bytes(c);assert r['request']['body']==(b.decode() if b is not None else None)
        if 'response' in r:
            raw=base64.b64decode(r['response']['body_base64'],validate=True)
            assert hashlib.sha256(raw).hexdigest()==r['response']['body_sha256']
            assert raw.decode('utf-8',errors='replace')==r['response']['body']
        assert r['started_at']<=r['finished_at'];records.append(r)
    assert set(p.stem for p in directory.glob('*.json'))==set(r['id'] for r in records),'Unmapped evidence'
    records.sort(key=lambda r:r['started_at'])
    for a,b in zip(records,records[1:]):assert b['started_at']-a['finished_at']>=2,(a['id'],b['id'])
    state=json.loads((ROOT/'results'/'session.json').read_text())
    assert len(records)<=state['calls']<=290
    print(f'Offline verification passed: {len(records)} saved records, {state["calls"]} counted attempts + 10 reserved discovery calls <= 300.')
