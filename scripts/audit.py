#!/usr/bin/env python3
"""Public IMD documentation probes; Python standard library only."""
import argparse
import base64
import fcntl
import hashlib
import json
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
WARNING = 'Experimental, commissioned as a test of the IMD swarm. It may not work as described. Read the code, start with small amounts, no warranty.'
ORIGIN = 'https://example.org'
MAX_CALLS = 290  # Ten calls reserved for initial documentation/bootstrap discovery.
INTERVAL = 2.1

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def validate_request(case):
    url = urllib.parse.urlsplit(case['url'])
    if url.scheme != 'https' or url.netloc not in {'api.imd.fun', 'explorer.imd.fun', 'imd.fun'}:
        raise ValueError('Only fixed public IMD HTTPS origins are permitted')
    if url.fragment or url.username or url.password:
        raise ValueError('Unexpected URL component')
    method = case['method']
    if method == 'POST':
        if url.netloc != 'api.imd.fun' or url.path != '/requests/check' or url.query:
            raise ValueError('POST is permitted only to api.imd.fun/requests/check')
    elif method != 'GET':
        raise ValueError('Only GET and POST /requests/check are permitted')
    if any(x in urllib.parse.unquote(url.path).lower().split('/') for x in ('quote', 'submit', 'import')):
        raise ValueError('Quote, submit and import routes are forbidden')
    allowed = {'origin', 'content-type', 'accept', 'user-agent'}
    if any(k.lower() not in allowed for k in case.get('headers', {})):
        raise ValueError('Credentials and arbitrary headers are forbidden')


def body_bytes(case):
    if 'body_text' in case:
        return case['body_text'].encode('utf-8')
    if 'body' in case:
        return json.dumps(case['body'], ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    return None


def run(cases, output, select):
    output.mkdir(parents=True, exist_ok=True)
    # One shared lock and ledger for every live invocation, even with another output path.
    state_dir = ROOT / 'results'
    state_dir.mkdir(exist_ok=True)
    with (state_dir / 'session.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state_path = state_dir / 'session.json'
        state = json.loads(state_path.read_text()) if state_path.exists() else {'calls': 0, 'last_finished': 0}
        opener = urllib.request.build_opener(NoRedirect())
        for case in cases:
            if select and case['id'] not in select:
                continue
            path = output / (case['id'] + '.json')
            if path.exists():
                continue
            validate_request(case)
            if state['calls'] >= MAX_CALLS:
                raise SystemExit('Call budget exhausted; no further network request made')
            time.sleep(max(0, INTERVAL - (time.time() - state['last_finished'])))
            body = body_bytes(case)
            headers = {'User-Agent': 'IMD-public-docs-audit/1.0', 'Accept': 'application/json'}
            if body is not None:
                headers['Content-Type'] = 'application/json'
            headers.update(case.get('headers', {}))
            req = urllib.request.Request(case['url'], data=body, method=case['method'], headers=headers)
            record = {'id': case['id'], 'started_at': time.time(), 'request': {'method': case['method'], 'url': case['url'], 'headers': dict(req.header_items()), 'body': body.decode('utf-8') if body is not None else None}}
            state['calls'] += 1
            # Count attempts before I/O, including timeouts and interrupted requests.
            state['last_finished'] = time.time()
            state_path.write_text(json.dumps(state, indent=2) + '\n')
            try:
                try:
                    response = opener.open(req, timeout=60)
                except urllib.error.HTTPError as exc:
                    response = exc
                with response:
                    raw = response.read()
                    record['response'] = {'status': response.status, 'headers': list(response.headers.items()), 'body_base64': base64.b64encode(raw).decode(), 'body_sha256': hashlib.sha256(raw).hexdigest(), 'body': raw.decode('utf-8', errors='replace')}
            except (OSError, urllib.error.URLError) as exc:
                record['transport_error'] = str(exc)
            finally:
                record['finished_at'] = time.time()
                state['last_finished'] = record['finished_at']
                state_path.write_text(json.dumps(state, indent=2) + '\n')
                path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
            print(case['id'], record.get('response', {}).get('status', 'TRANSPORT_ERROR'), flush=True)


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=WARNING, epilog='No dependencies. Default is offline; --live explicitly enables public calls. Global budget: 290 attempts plus 10 discovery calls reserved. At least 2.1 seconds after each response; no redirects or retries.')
    parser.add_argument('--live', action='store_true', help='Run missing probes against live API')
    parser.add_argument('--cases', type=Path, default=ROOT / 'claims.json', help='Claim/probe manifest')
    parser.add_argument('--results', type=Path, default=ROOT / 'results' / 'probes')
    parser.add_argument('--only', help='Comma-separated probe IDs (still uses shared budget)')
    parser.add_argument('--verify', action='store_true', help='Validate saved bytes, coverage and spacing offline')
    args = parser.parse_args()
    cases = json.loads(args.cases.read_text())
    for case in cases:
        validate_request(case)
    if args.live:
        run(cases, args.results, set(args.only.split(',')) if args.only else None)
    from reporting import report, verify
    if args.results.resolve() == (ROOT / 'results' / 'probes').resolve():
        report(cases, args.results)
    else:
        print('Alternate results saved/read; the reviewed campaign report is unchanged.')
    if args.verify:
        verify(cases, args.results)

if __name__ == '__main__':
    main()
