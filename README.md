Experimental, commissioned as a test of the IMD swarm. It may not work as described. Read the code, start with small amounts, no warranty.

# IMD public API documentation audit

A dependency-free, bounded comparison of [IMD's API documentation](https://imd.fun/docs/) with public GET routes and free `POST /requests/check` responses. Includes real requests, raw responses, reproducible mismatches, and offline checks. No wallet, authentication token, quote, submission, import, or payment is needed.

Start with [report.md](report.md), [the claim checklist](claims.md), or open [index.html](index.html) locally. The site viewer is static and makes no network requests.

## Run offline

Requires Python 3.10+ on Linux/macOS (or WSL); all imports are standard library modules. No installation, package download, build step, or vendored dependency is necessary.

```sh
python3 scripts/audit.py --verify
python3 -m unittest discover -s tests -v
python3 scripts/audit.py --help
```

The default command **makes no network calls**. It regenerates the report, checklist, static viewer, exact POST body files, and machine-readable outcomes from the committed evidence. `--verify` additionally checks request correspondence, raw response hashes, spacing, and the budget. A successful verification means the artifacts are internally consistent; it does not certify the service or make failed claims pass.

## Run live

```sh
python3 scripts/audit.py --live
```

This resumes missing probes in `claims.json`, preserving saved responses. The delivered snapshot is complete, so this command skips its existing probes. To collect selected fresh evidence in another directory:

```sh
python3 scripts/audit.py --live --only docs-with-paths --results results/recheck
```

That command consumes the same remaining budget and saves fresh raw evidence without changing the reviewed campaign report. Use `--verify --results results/recheck` to check that alternate evidence offline. A complete new campaign needs its own explicitly authorized call budget; the tool deliberately provides no budget reset option. Do not remove the shared ledger to bypass this assignment's limit.

The runner serializes calls with a process lock, waits at least 2.1 seconds **after each response**, counts attempts before sending, follows no redirects, and makes no automatic retries. The shared `results/session.json` caps runner attempts at 290; another ten calls are reserved for initial discovery. Output-directory changes and `--only` do not reset the counter. HTTP errors, timeouts and interrupted attempts count. A different-origin browser header is sent only by designated CORS probes. Credentials and POST routes other than the control plane's `/requests/check` are rejected before I/O.

Exact curl requests for each failed assertion appear in the report. These are manual live calls outside the runner: account for them and space them at least two seconds apart. POST bytes are stored under `results/requests/`, including whitespace in the body-size probes.

## Files and interpretation

- `claims.json`: every fixed probe, its documentation section, expected outcome, method, URL, headers and payload. Dynamic resource IDs were chosen from captured public list responses and then frozen for reproducibility.
- `claims.md`: every probe's pass/fail, inconclusive or observational result, with evidence links.
- `scripts/audit.py`: guarded network runner; `scripts/reporting.py`: offline assertions and report generation.
- `results/probes/*.json`: request bytes, request/response timestamps, status, all returned headers, response text, lossless base64 body, and SHA-256. Raw HTTP framing is not captured.
- `results/outcomes.json`: derived assertions; `results/session.json`: cumulative runner budget. The report generator does not edit probe responses.
- `results/docs.html`, `docs.txt`, and `bootstrap.json`: documentation snapshot and early discovery ledger. One early HTTP 403 was counted but its body/timestamp were not captured; a later complete capture records the same route/origin refusal. The browser documentation read is separately reserved in the budget.
- `report-notes.md`: reviewed interpretation and coverage limits, included verbatim in the generated report and static viewer.
- `tests/`: offline tests of method restrictions, budget enforcement, pacing, evidence preservation and assertion behavior. Recorded local results are in `results/local-tests.txt` and `results/local-verification.txt`.

PASS on a schema-only probe does not mean a job would be admitted or complete. A check can return HTTP 200 with blockers; refusals inspect the body. Rate/provider failures are INCONCLUSIVE. OBSERVED means the docs do not specify a precise expected behavior. Existing runtime failures are historical evidence, not newly purchased executions. Fields in documentation examples are treated as required only where the route's field list promises them; extra fields are allowed.

The operator runs these checks to help maintainers align the docs, planner and runtime. The script changes only local evidence files; it requests no onchain state transition, charges no gas and creates no paid request. Availability and future responses depend on the IMD operator; snapshots describe only the recorded time and sampled resources.

Commissioned through paid IMD swarm requests.
