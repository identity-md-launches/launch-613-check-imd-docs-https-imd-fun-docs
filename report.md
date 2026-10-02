Experimental, commissioned as a test of the IMD swarm. It may not work as described. Read the code, start with small amounts, no warranty.

# IMD public API documentation audit

FAIL: 12, INCONCLUSIVE: 1, OBSERVED: 7, PASS: 214. Saved probes: 234. Minimum recorded start-to-start spacing: 2.184 seconds.

## Findings for maintainers

The live API was reachable. The runner captured 234 probes on 2026-10-02, from 18:23:16 to 18:35:56 UTC. The control-plane version was `152d58c2d9cf5ddc34b4aec4a380d9c38889b475` ([version evidence](results/probes/version.json)); the saved docs footer identifies `3b96b1cc`, checked on 2026-10-01. These findings compare the captured documentation with that live deployment, not necessarily with the build the docs were last checked against. The five groups below account for the failed assertions; repeated boundary/direction probes are separate rows, not separate underlying bugs.

1. **Three skills contradict the documented step-path requirement.** [Job body → Each step](https://imd.fun/docs/#job-body) lists `write-readme-and-docs`, `deploy-script`, and `gas-and-size-report` among skills requiring explicit step paths. All three checked successfully without paths. All three returned `unplannable_steps` when supplied paths, explaining that the skill has its own budget. The other listed skills tested without paths were refused as expected. See `docs-no-paths`, `docs-with-paths`, `missing-paths-deploy-script`, `provided-paths-deploy-script`, and the two gas-report follow-ups. Please align the required-path list with the catalog, then ensure named outputs are compatible with a skill's effective allowance before accepting a plan.

   The known documentation runtime failure is also independently visible in public records. `GET /jobs/c2ba5413-a0fe-4e9a-9915-0e521c5bea2c` reports `state: blocked`, template `skill:write-readme-and-docs`, and `node write_readme_and_docs: path_violation`. Its node allows only `README.md` and `docs/**`. `GET /jobs/c2ba5413-a0fe-4e9a-9915-0e521c5bea2c/submissions` contains three failed attempts, each naming `artifacts/SEPOLIA-GUIDE.md` as an output outside those paths, with zero model turns. The docs put named outputs under `artifacts/` ([Job body → Starting source and files](https://imd.fun/docs/#job-body)). The current check accepts a documentation step with an `artifacts/README.md` output without paths, yet rejects the explicit paths that could cover it. **The current planning contradiction and historical runtime path failure are confirmed.** The historical job uses a single skill, not the new check's step array, and dates to September 27. This audit did not buy a new execution and cannot claim the current runtime was rerun or recover the historical paid input from these public records. See `docs-runtime`, `docs-runtime-submissions`, and `docs-runtime-result` for the exact GETs and original responses.

2. **The 16-path limit depends on path form.** [Job body → Each step](https://imd.fun/docs/#job-body) allows up to 16 repository-relative paths. With `implement-component`, 8 directory-like paths pass, but 9 and 16 produce `bad_path_count`. Sixteen `.md` paths pass. Sixteen paths ending in `/**` also pass as an exploratory control, although the docs do not define glob semantics. Inference: directory expansion may consume two internal allowance entries per supplied directory. The responses do not expose that implementation, so the report does not assert it as fact. Please apply the documented limit to user entries, or document how expansion changes it. Reproductions: `paths-8-directory`, `paths-9-directory`, `paths-count-16`, `paths-16-file`, `paths-16-glob`.

3. **Oracle list rows omit promised fields.** [Oracle](https://imd.fun/docs/#oracle) describes `panelSize` and `quorum` in each `/oracle/requests` row. Neither is present in either of the two sampled list entries. The detail route does return both. Please include them in list rows or move the documented fields to the detail response. Reproduction: `oracle-list`; comparison: `oracle-detail`.

4. **Oracle attestation lacks the CORS header advertised for oracle reads.** [Base URLs → CORS](https://imd.fun/docs/#base) describes oracle reads as CORS-enabled. With `Origin: https://example.org`, the list, counts, detail and pools GETs send `Access-Control-Allow-Origin: *`; the successful attestation GET sends no allow-origin header. Please add it to the attestation route or explicitly document the exception. Reproduction: `oracle-attestation`. This tests an actual successful attestation, not an unknown-ID error. It does not test an OPTIONS preflight.

5. **Explorer agent responses omit documented keys.** [Explorer](https://imd.fun/docs/#explorer) promises `jobs` and `lastAcceptedAt` for `/api/agents/:tokenId`. The successful response for seat 42 contains neither key. Please provide the fields (including an explicit null where appropriate), or update the response contract. Reproduction: `explorer-agent`.

## What matched and what remains limited

The checklist records every fixed probe, its docs section, exact expectation, outcome and raw evidence. Tested areas include job and research objective lengths, skill-id length, step objective and acceptance-criteria lengths/counts, path counts and relative-path refusals, step-key syntax, DAG requirements, missing paths for the listed skills, mutually exclusive selectors, source-pair requirements, input required fields, output locations, refused job/workflow fields, required launch facts, custom-token economics, oracle short-check boundaries, schedule runs/labels/cadence/refused fields, pagination, response keys and CORS. The check body accepts 16,384 bytes and refuses 16,385 with HTTP 413. This byte test uses JSON trailing whitespace, so it isolates the aggregate body limit from any individual string limit.

Missing launch name/symbol appear as required missing facts and matching `missing_fact` blockers. Refused job fields and planner problems usually appear inside HTTP 200 `blockers`, while structural validation usually returns HTTP 400. A check result is not a purchased job's admission result. Positive schema probes establish only the relevant outer schema boundary: an unknown 64-character skill still has an `unknown_skill` blocker; a 2,000-character meaningless oracle question can still be refused as ambiguous. Key syntax probes on a chain also encounter a separate rule requiring DAG shape for explicit keys.

Oversized GET searches (`q` of 201 characters) return HTTP 200 on jobs, oracle lists, and explorer search. Those docs specify a maximum but do not say whether the server rejects or truncates. These are **OBSERVED**, not claimed refusal failures: the all-`x` searches cannot distinguish truncation from ignoring the limit. Invalid publication page sizes return 400; pagination limits clamp where documented. Sparse result sets establish only an upper bound, not an exact clamp. `/ens` returns the documented general feature-off status 404, with `member_sites_closed` and wildcard CORS; the resolver config shape could not be tested while that feature was disabled ([Errors](https://imd.fun/docs/#errors), [Publications and sites](https://imd.fun/docs/#publications)).

CORS is recorded for each Origin-bearing probe in the matrix below. Wildcard headers were observed on hourly steps, swarm, oracle list/counts/detail/pools, schedule lists and disabled ENS. The request capabilities and OpenAPI routes, and POST check, refuse the unrelated Origin with 403 `origin_not_allowed`; without it, they work. Other sampled routes generally return responses without CORS headers. No OPTIONS, HEAD, WebSocket, signed, quote, submit, import or paid-execution calls were made. CORS observations concern these responses only, not every possible success/error branch.

One missing-paths probe for `gas-and-size-report` received 429. Its raw response remains INCONCLUSIVE. A separately named, later probe returned 200 without blockers and established the finding; this was a transport/rate follow-up, not an evaluator-consistency experiment. Live data may change on reproduction. No results were manufactured for inaccessible paths.

The audit checks public response key presence and selected row fields, not full schema/type conformance or every possible route branch. It does not verify payment settlement, fee transfers, signatures onchain, deployment, browser preflight, scheduled execution, cache expiration, external artifact integrity, private authorization, full paid-oracle input validation, or resource-dependent limits without suitable fixtures. Some GET routes are sampled with known resources and others with deliberately absent ones. Full paid-oracle fields are not assumed to be accepted by the explicitly shorter free check. Non-GET actions outside `/requests/check` cannot be tested within this assignment. There is no claim that all prose in the documentation has been exhaustively certified.

## Evidence and reproducibility

Raw responses are preserved with headers, timestamps, exact request bodies, lossless base64 bodies and SHA-256. `results/docs.html` is the documentation snapshot; `results/docs.txt` is a readable extraction. `claims.json` is the frozen request/expectation manifest. Use `python3 scripts/audit.py --verify` to reproduce the report offline and validate saved request/body correspondence, hashes, spacing and budget. Run `python3 -m unittest discover -s tests -v` for the offline runner/assertion checks. These are local checks, not independent certification.

The persistent ledger counts 234 runner attempts. Five early bootstrap attempts are listed in `results/bootstrap.json`, including one 403 whose timestamp/body were not retained; the repeated refusal has a complete capture. An initial browser documentation fetch (redirecting to `/docs/`) is also outside the runner. Reserving ten calls for all discovery yields a conservative total of **244 of 300**, leaving 56 runner calls. All runner calls are sequential and at least 2.1 seconds after the previous response. Initial bootstrap code also slept 2.1 seconds between calls; the missing early timestamp prevents independent spacing verification of that single transition. The initial browser read's redirect timing is not available. No live requests are needed to read or regenerate this deliverable.


## Every tested claim

| Probe | Claim and docs section | Result | Observation | Evidence |
|---|---|---|---|---|
| version | [GET /version returns the documented response fields; record cross-origin headers.](https://imd.fun/docs/#health) | PASS | HTTP 200 | [raw](results/probes/version.json) |
| health | [GET /health returns the documented response fields; record cross-origin headers.](https://imd.fun/docs/#health) | PASS | HTTP 200 | [raw](results/probes/health.json) |
| skills | [GET /skills returns the documented response fields; record cross-origin headers.](https://imd.fun/docs/#health) | PASS | HTTP 200 | [raw](results/probes/skills.json) |
| services | [Public GET is reachable and returns JSON for /services; the docs do not specify a complete top-level schema.](https://imd.fun/docs/#health) | PASS | HTTP 200 | [raw](results/probes/services.json) |
| hourly | [GET /steps/hourly returns the documented response fields; record cross-origin headers.](https://imd.fun/docs/#health) | PASS | HTTP 200 | [raw](results/probes/hourly.json) |
| jobs | [GET /jobs?limit=5 returns the documented response fields; record cross-origin headers.](https://imd.fun/docs/#jobs) | PASS | HTTP 200 | [raw](results/probes/jobs.json) |
| workflows | [GET /workflows?limit=2 returns the documented response fields; record cross-origin headers.](https://imd.fun/docs/#workflows) | PASS | HTTP 200 | [raw](results/probes/workflows.json) |
| oracle-list | [GET /oracle/requests?limit=2 returns the documented response fields; record cross-origin headers.](https://imd.fun/docs/#oracle) | FAIL | HTTP 200; requests rows missing panelSize: [0, 1]; requests rows missing quorum: [0, 1] | [raw](results/probes/oracle-list.json) |
| oracle-counts | [GET /oracle/counts returns the documented response fields; record cross-origin headers.](https://imd.fun/docs/#oracle) | PASS | HTTP 200 | [raw](results/probes/oracle-counts.json) |
| schedules | [GET /schedules?limit=2 returns the documented response fields; record cross-origin headers.](https://imd.fun/docs/#schedules) | PASS | HTTP 200 | [raw](results/probes/schedules.json) |
| panels | [Public GET is reachable and returns JSON for /research/panels?limit=1; the docs do not specify a complete top-level schema.](https://imd.fun/docs/#research) | PASS | HTTP 200 | [raw](results/probes/panels.json) |
| fuzz | [GET /fuzz/results?limit=1 returns the documented response fields; record cross-origin headers.](https://imd.fun/docs/#research) | PASS | HTTP 200 | [raw](results/probes/fuzz.json) |
| swarm | [GET /swarm returns the documented response fields; record cross-origin headers.](https://imd.fun/docs/#fleet) | PASS | HTTP 200 | [raw](results/probes/swarm.json) |
| workers | [GET /workers?fields=deviceKey returns the documented response fields; record cross-origin headers.](https://imd.fun/docs/#fleet) | PASS | HTTP 200 | [raw](results/probes/workers.json) |
| contributors | [Public GET is reachable and returns JSON for /contributors; the docs do not specify a complete top-level schema.](https://imd.fun/docs/#fleet) | PASS | HTTP 200 | [raw](results/probes/contributors.json) |
| seats | [GET /seats/records returns the documented response fields; record cross-origin headers.](https://imd.fun/docs/#fleet) | PASS | HTTP 200 | [raw](results/probes/seats.json) |
| owners | [GET /seats/owners returns the documented response fields; record cross-origin headers.](https://imd.fun/docs/#fleet) | PASS | HTTP 200 | [raw](results/probes/owners.json) |
| publications | [GET /publications?pageSize=1 returns the documented response fields; record cross-origin headers.](https://imd.fun/docs/#publications) | PASS | HTTP 200 | [raw](results/probes/publications.json) |
| publication-counts | [GET /publications/counts returns the documented response fields; record cross-origin headers.](https://imd.fun/docs/#publications) | PASS | HTTP 200 | [raw](results/probes/publication-counts.json) |
| sites | [GET /sites returns the documented response fields; record cross-origin headers.](https://imd.fun/docs/#publications) | PASS | HTTP 200 | [raw](results/probes/sites.json) |
| ens | [ENS disabled response is permitted by Errors (404 feature off); ENS responses still carry documented CORS.](https://imd.fun/docs/#base) | PASS | HTTP 404; member_sites_closed: this plane names no member sites | [raw](results/probes/ens.json) |
| launches | [GET /launches?limit=1 returns the documented response fields; record cross-origin headers.](https://imd.fun/docs/#launches) | PASS | HTTP 200 | [raw](results/probes/launches.json) |
| policies | [GET /launch/policies returns the documented response fields; record cross-origin headers.](https://imd.fun/docs/#launches) | PASS | HTTP 200 | [raw](results/probes/policies.json) |
| feedback | [Public GET is reachable and returns JSON for /feedback/batches?limit=1; the docs do not specify a complete top-level schema.](https://imd.fun/docs/#records) | PASS | HTTP 200 | [raw](results/probes/feedback.json) |
| explorer-version | [GET /version returns the documented response fields; record cross-origin headers.](https://imd.fun/docs/#explorer) | PASS | HTTP 200 | [raw](results/probes/explorer-version.json) |
| explorer-activity | [GET /api/activity returns the documented response fields; record cross-origin headers.](https://imd.fun/docs/#explorer) | PASS | HTTP 200 | [raw](results/probes/explorer-activity.json) |
| explorer-search | [GET /api/search?q=docs returns the documented response fields; record cross-origin headers.](https://imd.fun/docs/#explorer) | PASS | HTTP 200 | [raw](results/probes/explorer-search.json) |
| capabilities | [GET /requests/capabilities returns the documented response fields; record cross-origin headers.](https://imd.fun/docs/#paid) | PASS | HTTP 200 | [raw](results/probes/capabilities.json) |
| capabilities-origin | [GET /requests/capabilities returns the documented response fields; record cross-origin headers.](https://imd.fun/docs/#paid) | PASS | HTTP 403; origin_not_allowed | [raw](results/probes/capabilities-origin.json) |
| openapi | [GET /openapi.json returns the documented response fields; record cross-origin headers.](https://imd.fun/docs/#paid) | PASS | HTTP 200 | [raw](results/probes/openapi.json) |
| openapi-origin | [GET /openapi.json returns the documented response fields; record cross-origin headers.](https://imd.fun/docs/#paid) | PASS | HTTP 403; origin_not_allowed | [raw](results/probes/openapi-origin.json) |
| docs-no-paths | [write-readme-and-docs without step paths must be refused: paths are documented as required.](https://imd.fun/docs/#job-body) | FAIL | HTTP 200; documented invalid input was not refused. | [raw](results/probes/docs-no-paths.json) |
| docs-with-paths | [Documented step paths must not make write-readme-and-docs unplannable.](https://imd.fun/docs/#job-body) | FAIL | HTTP 200; blockers=[{"code": "unplannable_steps", "detail": "step 1 (write-readme-and-docs) declares its own budget, so the step may not also name paths"}]; unexpected unplannable_steps | [raw](results/probes/docs-with-paths.json) |
| check-baseline | [A valid job check returns action, kind, plan, facts, judged, blockers and suggestions.](https://imd.fun/docs/#paid) | PASS | HTTP 200 | [raw](results/probes/check-baseline.json) |
| check-origin | [Unrelated browser Origin is refused on request routes.](https://imd.fun/docs/#paid) | PASS | HTTP 403; origin_not_allowed | [raw](results/probes/check-origin.json) |
| objective-len-0 | [objective= is refused by the documented input rule.](https://imd.fun/docs/#job-body) | PASS | HTTP 400; invalid_request: objective: Too small: expected string to have >=1 characters | [raw](results/probes/objective-len-0.json) |
| objective-len-1 | [objective=x is inside the documented input bounds.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; outer input schema accepted; this does not assert admission. | [raw](results/probes/objective-len-1.json) |
| objective-len-8000 | [objective=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx… is inside the documented input bounds.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; outer input schema accepted; this does not assert admission. | [raw](results/probes/objective-len-8000.json) |
| objective-len-8001 | [objective=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx… is refused by the documented input rule.](https://imd.fun/docs/#job-body) | PASS | HTTP 400; invalid_request: objective: Too big: expected string to have <=8000 characters | [raw](results/probes/objective-len-8001.json) |
| skill-len-64 | [A 64-character skill identifier passes the length validator (catalog validity is separate).](https://imd.fun/docs/#job-body) | PASS | HTTP 200; blockers=[{"code": "unknown_skill", "detail": "no skill named \"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\""}]; outer input schema accepted; this does not assert admission. | [raw](results/probes/skill-len-64.json) |
| skill-len-65 | [skill=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx is refused by the documented input rule.](https://imd.fun/docs/#job-body) | PASS | HTTP 400; invalid_request: skill: Too big: expected string to have <=64 characters | [raw](results/probes/skill-len-65.json) |
| objective-missing | [objective is required.](https://imd.fun/docs/#job-body) | PASS | HTTP 400; invalid_request: objective: Invalid input: expected string, received undefined | [raw](results/probes/objective-missing.json) |
| refused-projectId | [projectId=11111111-1111-4111-8111-111111111111 is refused by the documented input rule.](https://imd.fun/docs/#continue) | PASS | HTTP 200; blockers=[{"code": "invalid_input", "detail": "a paid job starts a project of its own; parentJobId and projectId are not accepted"}] | [raw](results/probes/refused-projectId.json) |
| refused-deploymentLaunchId | [deploymentLaunchId=11111111-1111-4111-8111-111111111111 is refused by the documented input rule.](https://imd.fun/docs/#continue) | PASS | HTTP 200; blockers=[{"code": "invalid_input", "detail": "a paid job does not build against an existing launch"}] | [raw](results/probes/refused-deploymentLaunchId.json) |
| refused-parentJobId | [parentJobId=11111111-1111-4111-8111-111111111111 is refused by the documented input rule.](https://imd.fun/docs/#continue) | PASS | HTTP 200; blockers=[{"code": "invalid_input", "detail": "a paid job starts a project of its own; parentJobId and projectId are not accepted"}] | [raw](results/probes/refused-parentJobId.json) |
| refused-onchain | [onchain=True is refused by the documented input rule.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; blockers=[{"code": "invalid_input", "detail": "a launch is not covered by the job price; ask for launch.open instead"}] | [raw](results/probes/refused-onchain.json) |
| refused-chainId | [chainId=11155111 is refused by the documented input rule.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; blockers=[{"code": "invalid_input", "detail": "chainId names where a launch deploys; set onchain, or leave chainId out"}] | [raw](results/probes/refused-chainId.json) |
| refused-pairWith | [pairWith=eth is refused by the documented input rule.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; blockers=[{"code": "invalid_input", "detail": "pairWith names what a launch's pool pairs with; set onchain, or leave pairWith out"}] | [raw](results/probes/refused-pairWith.json) |
| exclusive-skill-template | [template=single is refused by the documented input rule.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; blockers=[{"code": "invalid_input", "detail": "name a template, a skill, or steps — not more than one"}] | [raw](results/probes/exclusive-skill-template.json) |
| exclusive-skill-steps | [steps=[{'skill': 'build-website'}] is refused by the documented input rule.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; blockers=[{"code": "invalid_input", "detail": "name a template, a skill, or steps — not more than one"}] | [raw](results/probes/exclusive-skill-steps.json) |
| research-objective-4000 | [objective=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx… is inside the documented input bounds.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; outer input schema accepted; this does not assert admission. | [raw](results/probes/research-objective-4000.json) |
| research-objective-4001 | [objective=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx… is refused by the documented input rule.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; blockers=[{"code": "invalid_input", "detail": "a research panel's question is at most 4000 characters, and this one is 4001: shorten it, or ask for a written report instead"}] | [raw](results/probes/research-objective-4001.json) |
| research-panelSize-0 | [panelSize=0 is refused by the documented input rule.](https://imd.fun/docs/#job-body) | PASS | HTTP 400; invalid_request: panelSize: Too small: expected number to be >=1 | [raw](results/probes/research-panelSize-0.json) |
| research-panelSize-1 | [panelSize=1 is inside the documented input bounds.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; outer input schema accepted; this does not assert admission. | [raw](results/probes/research-panelSize-1.json) |
| research-panelSize-9 | [panelSize=9 is inside the documented input bounds.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; outer input schema accepted; this does not assert admission. | [raw](results/probes/research-panelSize-9.json) |
| research-panelSize-10 | [panelSize=10 is refused by the documented input rule.](https://imd.fun/docs/#job-body) | PASS | HTTP 400; invalid_request: panelSize: Too big: expected number to be <=9 | [raw](results/probes/research-panelSize-10.json) |
| research-panelQuorum-0 | [panelQuorum=0 is refused by the documented input rule.](https://imd.fun/docs/#job-body) | PASS | HTTP 400; invalid_request: panelQuorum: Too small: expected number to be >=1 | [raw](results/probes/research-panelQuorum-0.json) |
| research-panelQuorum-1 | [panelQuorum=1 is inside the documented input bounds.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; outer input schema accepted; this does not assert admission. | [raw](results/probes/research-panelQuorum-1.json) |
| research-panelQuorum-9 | [panelQuorum=9 is inside the documented input bounds.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; outer input schema accepted; this does not assert admission. | [raw](results/probes/research-panelQuorum-9.json) |
| research-panelQuorum-10 | [panelQuorum=10 is refused by the documented input rule.](https://imd.fun/docs/#job-body) | PASS | HTTP 400; invalid_request: panelQuorum: Too big: expected number to be <=9 | [raw](results/probes/research-panelQuorum-10.json) |
| research-minCitations--1 | [minCitations=-1 is refused by the documented input rule.](https://imd.fun/docs/#job-body) | PASS | HTTP 400; invalid_request: minCitations: Too small: expected number to be >=0 | [raw](results/probes/research-minCitations--1.json) |
| research-minCitations-0 | [minCitations=0 is inside the documented input bounds.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; outer input schema accepted; this does not assert admission. | [raw](results/probes/research-minCitations-0.json) |
| research-minCitations-20 | [minCitations=20 is inside the documented input bounds.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; outer input schema accepted; this does not assert admission. | [raw](results/probes/research-minCitations-20.json) |
| research-minCitations-21 | [minCitations=21 is refused by the documented input rule.](https://imd.fun/docs/#job-body) | PASS | HTTP 400; invalid_request: minCitations: Too big: expected number to be <=20 | [raw](results/probes/research-minCitations-21.json) |
| step-objective-0 | [Step objective:  must be refused.](https://imd.fun/docs/#job-body) | PASS | HTTP 400; invalid_request: steps.0.objective: Too small: expected string to have >=1 characters | [raw](results/probes/step-objective-0.json) |
| step-objective-1 | [Step objective: x is within documented bounds.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; outer input schema accepted; this does not assert admission. | [raw](results/probes/step-objective-1.json) |
| step-objective-3000 | [Step objective: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx is within documented bounds.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; outer input schema accepted; this does not assert admission. | [raw](results/probes/step-objective-3000.json) |
| step-objective-3001 | [Step objective: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx must be refused.](https://imd.fun/docs/#job-body) | PASS | HTTP 400; invalid_request: steps.0.objective: Too big: expected string to have <=3000 characters | [raw](results/probes/step-objective-3001.json) |
| criteria-count-0 | [Step acceptanceCriteria: [] must be refused.](https://imd.fun/docs/#job-body) | PASS | HTTP 400; invalid_request: steps.0.acceptanceCriteria: Too small: expected array to have >=1 items | [raw](results/probes/criteria-count-0.json) |
| criteria-count-1 | [Step acceptanceCriteria: ['The page loads.'] is within documented bounds.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; outer input schema accepted; this does not assert admission. | [raw](results/probes/criteria-count-1.json) |
| criteria-count-8 | [Step acceptanceCriteria: ['The page loads.', 'The page loads.', 'The page loads.', 'The page loads.', 'The page loads.', 'The is within documented bounds.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; outer input schema accepted; this does not assert admission. | [raw](results/probes/criteria-count-8.json) |
| criteria-count-9 | [Step acceptanceCriteria: ['The page loads.', 'The page loads.', 'The page loads.', 'The page loads.', 'The page loads.', 'The must be refused.](https://imd.fun/docs/#job-body) | PASS | HTTP 400; invalid_request: steps.0.acceptanceCriteria: Too big: expected array to have <=8 items | [raw](results/probes/criteria-count-9.json) |
| criteria-length-0 | [Step acceptanceCriteria: [''] must be refused.](https://imd.fun/docs/#job-body) | PASS | HTTP 400; invalid_request: steps.0.acceptanceCriteria.0: Too small: expected string to have >=1 characters | [raw](results/probes/criteria-length-0.json) |
| criteria-length-500 | [Step acceptanceCriteria: ['xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx is within documented bounds.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; outer input schema accepted; this does not assert admission. | [raw](results/probes/criteria-length-500.json) |
| criteria-length-501 | [Step acceptanceCriteria: ['xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx must be refused.](https://imd.fun/docs/#job-body) | PASS | HTTP 400; invalid_request: steps.0.acceptanceCriteria.0: Too big: expected string to have <=500 characters | [raw](results/probes/criteria-length-501.json) |
| paths-count-1 | [Step paths: ['src/p0'] is within documented bounds.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; outer input schema accepted; this does not assert admission. | [raw](results/probes/paths-count-1.json) |
| paths-count-16 | [The documented maximum of 16 repository-relative step paths should not exceed the internal allowed-path count.](https://imd.fun/docs/#job-body) | FAIL | HTTP 200; blockers=[{"code": "bad_path_count", "detail": "expected between 1 and 16 allowed paths", "node": "implement_component"}]; unexpected bad_path_count | [raw](results/probes/paths-count-16.json) |
| paths-count-17 | [Step paths: ['src/p0', 'src/p1', 'src/p2', 'src/p3', 'src/p4', 'src/p5', 'src/p6', 'src/p7', 'src/p8', 'src/p9', must be refused.](https://imd.fun/docs/#job-body) | PASS | HTTP 400; invalid_request: steps.0.paths: Too big: expected array to have <=16 items | [raw](results/probes/paths-count-17.json) |
| path-relative | [Step paths: ['src/components'] is within documented bounds.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; outer input schema accepted; this does not assert admission. | [raw](results/probes/path-relative.json) |
| path-absolute | [Step paths: ['/tmp/example'] must be refused.](https://imd.fun/docs/#job-body) | PASS | HTTP 400; invalid_request: steps.0.paths.0: must be repository-relative | [raw](results/probes/path-absolute.json) |
| path-parent | [Step paths: ['../escape'] must be refused.](https://imd.fun/docs/#job-body) | PASS | HTTP 400; invalid_request: steps.0.paths.0: must not traverse upward | [raw](results/probes/path-parent.json) |
| path-nested-parent | [Explore src/../escape as a repository-relative path; docs do not define normalization or protected paths.](https://imd.fun/docs/#job-body) | OBSERVED | HTTP 400; invalid_request: steps.0.paths.0: must not traverse upward; documentation does not specify the exact outcome. | [raw](results/probes/path-nested-parent.json) |
| path-dot | [Explore . as a repository-relative path; docs do not define normalization or protected paths.](https://imd.fun/docs/#job-body) | OBSERVED | HTTP 200; documentation does not specify the exact outcome. | [raw](results/probes/path-dot.json) |
| path-git | [Explore .git/config as a repository-relative path; docs do not define normalization or protected paths.](https://imd.fun/docs/#job-body) | OBSERVED | HTTP 200; blockers=[{"code": "protected_path", "detail": "\".git/config\" is protected and can never be modified by a task", "node": "implement_component"}, {"code": "protected_path", "detail": "\".git/config/**\" is protected and can never be modified by a task", "node": "implement_component"}]; documentation does not specify the exact outcome. | [raw](results/probes/path-git.json) |
| step-key-a | [Step key: a is within documented bounds.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; blockers=[{"code": "unplannable_steps", "detail": "Explicit keys and dependencies require shape:dag"}]; outer input schema accepted; this does not assert admission. | [raw](results/probes/step-key-a.json) |
| step-key-length32 | [Step key: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa is within documented bounds.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; blockers=[{"code": "unplannable_steps", "detail": "Explicit keys and dependencies require shape:dag"}]; outer input schema accepted; this does not assert admission. | [raw](results/probes/step-key-length32.json) |
| step-key-length33 | [Step key: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa must be refused.](https://imd.fun/docs/#job-body) | PASS | HTTP 400; invalid_request: steps.0.key: Invalid string: must match pattern /^[a-z][a-z0-9_]{0,31}$/ | [raw](results/probes/step-key-length33.json) |
| step-key-A | [Step key: A must be refused.](https://imd.fun/docs/#job-body) | PASS | HTTP 400; invalid_request: steps.0.key: Invalid string: must match pattern /^[a-z][a-z0-9_]{0,31}$/ | [raw](results/probes/step-key-A.json) |
| step-key-1a | [Step key: 1a must be refused.](https://imd.fun/docs/#job-body) | PASS | HTTP 400; invalid_request: steps.0.key: Invalid string: must match pattern /^[a-z][a-z0-9_]{0,31}$/ | [raw](results/probes/step-key-1a.json) |
| step-key-length3 | [Step key: a-b must be refused.](https://imd.fun/docs/#job-body) | PASS | HTTP 400; invalid_request: steps.0.key: Invalid string: must match pattern /^[a-z][a-z0-9_]{0,31}$/ | [raw](results/probes/step-key-length3.json) |
| step-key-underscore | [Step key: a_b is within documented bounds.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; blockers=[{"code": "unplannable_steps", "detail": "Explicit keys and dependencies require shape:dag"}]; outer input schema accepted; this does not assert admission. | [raw](results/probes/step-key-underscore.json) |
| step-count-0 | [steps has 0 entries; documented 1–6.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; blockers=[{"code": "unplannable_steps", "detail": "a job needs at least one step"}] | [raw](results/probes/step-count-0.json) |
| step-count-1 | [steps has 1 entries; documented 1–6.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; outer input schema accepted; this does not assert admission. | [raw](results/probes/step-count-1.json) |
| step-count-6 | [steps has 6 entries; documented 1–6.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; outer input schema accepted; this does not assert admission. | [raw](results/probes/step-count-6.json) |
| step-count-7 | [steps has 7 entries; documented 1–6.](https://imd.fun/docs/#job-body) | PASS | HTTP 400; invalid_request: steps: Too big: expected array to have <=6 items | [raw](results/probes/step-count-7.json) |
| shape-required | [shape is required with steps.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; blockers=[{"code": "invalid_input", "detail": "steps need a shape to run in: chain, fan_out_join or dag"}] | [raw](results/probes/shape-required.json) |
| dag-missing-key | [DAG keys/dependencies must be explicit, acyclic, and join into one final step.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; blockers=[{"code": "unplannable_steps", "detail": "DAG steps need unique valid keys"}] | [raw](results/probes/dag-missing-key.json) |
| dag-missing-deps | [DAG keys/dependencies must be explicit, acyclic, and join into one final step.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; blockers=[{"code": "unplannable_steps", "detail": "DAG dependencies must name unique existing steps"}] | [raw](results/probes/dag-missing-deps.json) |
| dag-cycle | [DAG keys/dependencies must be explicit, acyclic, and join into one final step.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; blockers=[{"code": "unplannable_steps", "detail": "DAG must join all branches into one final step"}] | [raw](results/probes/dag-cycle.json) |
| dag-no-join | [DAG keys/dependencies must be explicit, acyclic, and join into one final step.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; blockers=[{"code": "unplannable_steps", "detail": "DAG must join all branches into one final step"}] | [raw](results/probes/dag-no-join.json) |
| missing-paths-implement-contract | [implement-contract requires explicit step paths.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; blockers=[{"code": "unplannable_steps", "detail": "step 1 (implement-contract) takes its paths from the job, so the step has to say what it writes in \"paths\""}] | [raw](results/probes/missing-paths-implement-contract.json) |
| missing-paths-implement-one-contract | [implement-one-contract requires explicit step paths.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; blockers=[{"code": "unplannable_steps", "detail": "step 1 (implement-one-contract) takes its paths from the job, so the step has to say what it writes in \"paths\""}] | [raw](results/probes/missing-paths-implement-one-contract.json) |
| missing-paths-implement-and-test | [implement-and-test requires explicit step paths.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; blockers=[{"code": "unplannable_steps", "detail": "step 1 (implement-and-test) takes its paths from the job, so the step has to say what it writes in \"paths\""}] | [raw](results/probes/missing-paths-implement-and-test.json) |
| missing-paths-implement-component | [implement-component requires explicit step paths.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; blockers=[{"code": "unplannable_steps", "detail": "step 1 (implement-component) takes its paths from the job, so the step has to say what it writes in \"paths\""}] | [raw](results/probes/missing-paths-implement-component.json) |
| missing-paths-write-foundry-tests | [write-foundry-tests requires explicit step paths.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; blockers=[{"code": "unplannable_steps", "detail": "step 1 (write-foundry-tests) takes its paths from the job, so the step has to say what it writes in \"paths\""}] | [raw](results/probes/missing-paths-write-foundry-tests.json) |
| missing-paths-refine-project | [refine-project requires explicit step paths.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; blockers=[{"code": "unplannable_steps", "detail": "step 1 (refine-project) takes its paths from the job, so the step has to say what it writes in \"paths\""}] | [raw](results/probes/missing-paths-refine-project.json) |
| missing-paths-deploy-script | [deploy-script requires explicit step paths.](https://imd.fun/docs/#job-body) | FAIL | HTTP 200; documented invalid input was not refused. | [raw](results/probes/missing-paths-deploy-script.json) |
| missing-paths-gas-and-size-report | [gas-and-size-report requires explicit step paths.](https://imd.fun/docs/#job-body) | INCONCLUSIVE | HTTP 429; provider/rate failure cannot establish the input rule. | [raw](results/probes/missing-paths-gas-and-size-report.json) |
| pair-required-repoUrl | [repoUrl=https://github.com/example/example is refused by the documented input rule.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; blockers=[{"code": "invalid_input", "detail": "repoUrl and baseCommit must be supplied together"}] | [raw](results/probes/pair-required-repoUrl.json) |
| pair-required-baseCommit | [baseCommit=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa is refused by the documented input rule.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; blockers=[{"code": "invalid_input", "detail": "repoUrl and baseCommit must be supplied together"}] | [raw](results/probes/pair-required-baseCommit.json) |
| references-count-8 | [references=['defi-native', 'defi-native', 'defi-native', 'defi-native', 'defi-native', 'defi-native',… is inside the documented input bounds.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; outer input schema accepted; this does not assert admission. | [raw](results/probes/references-count-8.json) |
| references-count-9 | [references=['defi-native', 'defi-native', 'defi-native', 'defi-native', 'defi-native', 'defi-native',… is refused by the documented input rule.](https://imd.fun/docs/#job-body) | PASS | HTTP 400; invalid_request: references: Too big: expected array to have <=8 items | [raw](results/probes/references-count-9.json) |
| contracts-count-4 | [contracts=['C0', 'C1', 'C2', 'C3'] is inside the documented input bounds.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; outer input schema accepted; this does not assert admission. | [raw](results/probes/contracts-count-4.json) |
| contracts-count-5 | [contracts=['C0', 'C1', 'C2', 'C3', 'C4'] is refused by the documented input rule.](https://imd.fun/docs/#job-body) | PASS | HTTP 400; invalid_request: contracts: Too big: expected array to have <=4 items | [raw](results/probes/contracts-count-5.json) |
| output-path-114 | [outputs=[{'name': 'report', 'path': 'artifacts/report.md', 'mediaType': 'text/markdown'}] is inside the documented input bounds.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; outer input schema accepted; this does not assert admission. | [raw](results/probes/output-path-114.json) |
| output-path-115 | [outputs=[{'name': 'report', 'path': 'report.md', 'mediaType': 'text/markdown'}] is refused by the documented input rule.](https://imd.fun/docs/#job-body) | PASS | HTTP 400; invalid_request: outputs.0.path: named outputs go under artifacts/; source files travel in the Git bundle | [raw](results/probes/output-path-115.json) |
| output-path-116 | [outputs=[{'name': 'report', 'path': 'artifacts/../report.md', 'mediaType': 'text/markdown'}] is refused by the documented input rule.](https://imd.fun/docs/#job-body) | PASS | HTTP 400; invalid_request: outputs.0.path: must be a normalized relative path | [raw](results/probes/output-path-116.json) |
| input-required-hash | [inputs=[{'name': 'report', 'path': 'artifacts/report.md', 'mediaType': 'text/markdown', 'bytes': … is refused by the documented input rule.](https://imd.fun/docs/#job-body) | PASS | HTTP 400; invalid_request: inputs.0.hash: Invalid input: expected string, received undefined | [raw](results/probes/input-required-hash.json) |
| input-required-mediaType | [inputs=[{'name': 'report', 'path': 'artifacts/report.md', 'hash': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa… is refused by the documented input rule.](https://imd.fun/docs/#job-body) | PASS | HTTP 400; invalid_request: inputs.0.mediaType: Invalid input: expected string, received undefined | [raw](results/probes/input-required-mediaType.json) |
| input-required-bytes | [inputs=[{'name': 'report', 'path': 'artifacts/report.md', 'hash': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa… is refused by the documented input rule.](https://imd.fun/docs/#job-body) | PASS | HTTP 400; invalid_request: inputs.0.bytes: Invalid input: expected number, received undefined | [raw](results/probes/input-required-bytes.json) |
| input-required-submissionHash | [inputs=[{'name': 'report', 'path': 'artifacts/report.md', 'hash': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa… is refused by the documented input rule.](https://imd.fun/docs/#job-body) | PASS | HTTP 400; invalid_request: inputs.0.submissionHash: Invalid input: expected string, received undefined | [raw](results/probes/input-required-submissionHash.json) |
| launch-missing-name | [Launch check requires token name/symbol, fixed token terms unless custom_token, and custom token economics.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; blockers=[{"code": "bad_path_count", "detail": "expected between 1 and 16 allowed paths", "node": "impl"}, {"code": "bad_path_count", "detail": "expected between 1 and 16 allowed paths", "node": "tests"}, {"code": "missing_fact", "fact": "token_name", "detail": "Token name: needed to mint the token."}, {"code": "missing_fact", "fact": "token_symbol", "detail": "Token symbol: needed to mint the token."}] | [raw](results/probes/launch-missing-name.json) |
| launch-nonstandard-token | [Launch check requires token name/symbol, fixed token terms unless custom_token, and custom token economics.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; blockers=[{"code": "bad_path_count", "detail": "expected between 1 and 16 allowed paths", "node": "impl"}, {"code": "bad_path_count", "detail": "expected between 1 and 16 allowed paths", "node": "tests"}, {"code": "launch_token", "detail": "Every launch deploys the same token: 1,000,000,000 with 18 decimals, minted once, transfers plain, with no fees, limits, pausing or minting, split 10% to the swarm, the other 90% is yours: 80% into the pool unless you choose otherwise, the rest to your wallet. This request asks for a different supply or decimals, which the launch would not deploy. Take it out and check again."}] | [raw](results/probes/launch-nonstandard-token.json) |
| launch-custom-without-economics | [Launch check requires token name/symbol, fixed token terms unless custom_token, and custom token economics.](https://imd.fun/docs/#job-body) | PASS | HTTP 200; blockers=[{"code": "invalid_input", "detail": "a custom token launch needs economics: poolBps, initialMarketCapWei and, unless the pool takes all of the requester's share, remainderTo"}] | [raw](results/probes/launch-custom-without-economics.json) |
| oracle-short | [Short oracle check drafts a complete request without payment.](https://imd.fun/docs/#oracle-body) | PASS | HTTP 200 | [raw](results/probes/oracle-short.json) |
| oracle-question-0 | [Oracle question boundary 0.](https://imd.fun/docs/#oracle-body) | PASS | HTTP 400; invalid_request: question: Too small: expected string to have >=1 characters | [raw](results/probes/oracle-question-0.json) |
| oracle-question-2000 | [Oracle question boundary 2000.](https://imd.fun/docs/#oracle-body) | PASS | HTTP 200; blockers=[{"code": "ambiguous_question", "detail": "Careful researchers could read this question more than one way. Name the period, the unit, the rounding or the term you mean, and check again."}]; outer input schema accepted; this does not assert admission. | [raw](results/probes/oracle-question-2000.json) |
| oracle-question-2001 | [Oracle question boundary 2001.](https://imd.fun/docs/#oracle-body) | PASS | HTTP 400; invalid_request: question: Too big: expected string to have <=2000 characters | [raw](results/probes/oracle-question-2001.json) |
| oracle-panelSize-4 | [Oracle panelSize boundary 4.](https://imd.fun/docs/#oracle-body) | PASS | HTTP 400; invalid_request: panelSize: Too small: expected number to be >=5 | [raw](results/probes/oracle-panelSize-4.json) |
| oracle-panelSize-5 | [Oracle panelSize boundary 5.](https://imd.fun/docs/#oracle-body) | PASS | HTTP 200; outer input schema accepted; this does not assert admission. | [raw](results/probes/oracle-panelSize-5.json) |
| oracle-panelSize-100 | [Oracle panelSize boundary 100.](https://imd.fun/docs/#oracle-body) | PASS | HTTP 200; outer input schema accepted; this does not assert admission. | [raw](results/probes/oracle-panelSize-100.json) |
| oracle-panelSize-101 | [Oracle panelSize boundary 101.](https://imd.fun/docs/#oracle-body) | PASS | HTTP 200; blockers=[{"code": "invalid_input", "detail": "the flat price covers a panel of up to 100; asked for 101"}] | [raw](results/probes/oracle-panelSize-101.json) |
| oracle-head-0 | [Oracle head boundary 0.](https://imd.fun/docs/#oracle-body) | PASS | HTTP 400; invalid_request: head: Too small: expected number to be >=1 | [raw](results/probes/oracle-head-0.json) |
| oracle-head-1 | [Oracle head boundary 1.](https://imd.fun/docs/#oracle-body) | PASS | HTTP 200; outer input schema accepted; this does not assert admission. | [raw](results/probes/oracle-head-1.json) |
| oracle-head-32 | [Oracle head boundary 32.](https://imd.fun/docs/#oracle-body) | PASS | HTTP 200; outer input schema accepted; this does not assert admission. | [raw](results/probes/oracle-head-32.json) |
| oracle-head-33 | [Oracle head boundary 33.](https://imd.fun/docs/#oracle-body) | PASS | HTTP 400; invalid_request: head: Too big: expected number to be <=32 | [raw](results/probes/oracle-head-33.json) |
| oracle-toleranceBps--1 | [Oracle toleranceBps boundary -1.](https://imd.fun/docs/#oracle-body) | PASS | HTTP 400; invalid_request: toleranceBps: Too small: expected number to be >=0 | [raw](results/probes/oracle-toleranceBps--1.json) |
| oracle-toleranceBps-0 | [Oracle toleranceBps boundary 0.](https://imd.fun/docs/#oracle-body) | PASS | HTTP 200; outer input schema accepted; this does not assert admission. | [raw](results/probes/oracle-toleranceBps-0.json) |
| oracle-toleranceBps-10000 | [Oracle toleranceBps boundary 10000.](https://imd.fun/docs/#oracle-body) | PASS | HTTP 200; outer input schema accepted; this does not assert admission. | [raw](results/probes/oracle-toleranceBps-10000.json) |
| oracle-toleranceBps-10001 | [Oracle toleranceBps boundary 10001.](https://imd.fun/docs/#oracle-body) | PASS | HTTP 400; invalid_request: toleranceBps: Too big: expected number to be <=10000 | [raw](results/probes/oracle-toleranceBps-10001.json) |
| schedule-baseline | [Job schedule check exposes unitAmount, runs, amount and terms.](https://imd.fun/docs/#paid) | PASS | HTTP 200 | [raw](results/probes/schedule-baseline.json) |
| schedule-runs-0 | [Schedule runs=0 follows documented bounds/refusals.](https://imd.fun/docs/#schedule-body) | PASS | HTTP 200; blockers=[{"code": "invalid_input", "detail": "runs: Too small: expected number to be >=1"}] | [raw](results/probes/schedule-runs-0.json) |
| schedule-runs-1 | [Schedule runs=1 follows documented bounds/refusals.](https://imd.fun/docs/#schedule-body) | PASS | HTTP 200; outer input schema accepted; this does not assert admission. | [raw](results/probes/schedule-runs-1.json) |
| schedule-runs-2 | [Schedule runs=1000000 follows documented bounds/refusals.](https://imd.fun/docs/#schedule-body) | PASS | HTTP 200; outer input schema accepted; this does not assert admission. | [raw](results/probes/schedule-runs-2.json) |
| schedule-runs-3 | [Schedule runs=1000001 follows documented bounds/refusals.](https://imd.fun/docs/#schedule-body) | PASS | HTTP 200; blockers=[{"code": "invalid_input", "detail": "runs: Too big: expected number to be <=1000000"}] | [raw](results/probes/schedule-runs-3.json) |
| schedule-label-0 | [Schedule label= follows documented bounds/refusals.](https://imd.fun/docs/#schedule-body) | PASS | HTTP 200; blockers=[{"code": "invalid_input", "detail": "label: Too small: expected string to have >=1 characters"}] | [raw](results/probes/schedule-label-0.json) |
| schedule-label-1 | [Schedule label=120 characters follows documented bounds/refusals.](https://imd.fun/docs/#schedule-body) | PASS | HTTP 200; outer input schema accepted; this does not assert admission. | [raw](results/probes/schedule-label-1.json) |
| schedule-label-2 | [Schedule label=121 characters follows documented bounds/refusals.](https://imd.fun/docs/#schedule-body) | PASS | HTTP 200; blockers=[{"code": "invalid_input", "detail": "label: Too big: expected string to have <=120 characters"}] | [raw](results/probes/schedule-label-2.json) |
| schedule-cadence-0 | [Schedule cadence={'every': 'PT29M'} follows documented bounds/refusals.](https://imd.fun/docs/#schedule-body) | PASS | HTTP 200; blockers=[{"code": "invalid_cadence", "detail": "every must be at least 30m for this action"}] | [raw](results/probes/schedule-cadence-0.json) |
| schedule-cadence-1 | [Schedule cadence={'every': 'PT30M'} follows documented bounds/refusals.](https://imd.fun/docs/#schedule-body) | PASS | HTTP 200; outer input schema accepted; this does not assert admission. | [raw](results/probes/schedule-cadence-1.json) |
| schedule-cadence-2 | [Schedule cadence={'cron': '* * * * *', 'tz': 'UTC'} follows documented bounds/refusals.](https://imd.fun/docs/#schedule-body) | PASS | HTTP 200; blockers=[{"code": "invalid_cadence", "detail": "cron fires 1m apart; this action needs at least 30m between runs"}] | [raw](results/probes/schedule-cadence-2.json) |
| schedule-submissionKey-0 | [Schedule submissionKey=11111111-1111-4111-8111-111111111111 follows documented bounds/refusals.](https://imd.fun/docs/#schedule-body) | PASS | HTTP 200; blockers=[{"code": "invalid_input", "detail": "input: Unrecognized key: \"submissionKey\""}] | [raw](results/probes/schedule-submissionKey-0.json) |
| schedule-expiresAt-0 | [Schedule expiresAt=2030-01-01T00:00:00Z follows documented bounds/refusals.](https://imd.fun/docs/#schedule-body) | PASS | HTTP 200; blockers=[{"code": "invalid_input", "detail": "input: Unrecognized key: \"expiresAt\""}] | [raw](results/probes/schedule-expiresAt-0.json) |
| jobs-docs-search | [Search jobs by objective for existing documentation-step runtime evidence.](https://imd.fun/docs/#jobs) | PASS | HTTP 200 | [raw](results/probes/jobs-docs-search.json) |
| jobs-path-search | [Search existing documentation jobs; no new execution.](https://imd.fun/docs/#jobs) | PASS | HTTP 200 | [raw](results/probes/jobs-path-search.json) |
| job-detail | [Documented GET response shape for /jobs/aca5f077-3da7-44bb-a66d-1680dcdb0525](https://imd.fun/docs/#jobs) | PASS | HTTP 200 | [raw](results/probes/job-detail.json) |
| job-result | [Documented GET response shape for /jobs/aca5f077-3da7-44bb-a66d-1680dcdb0525/result](https://imd.fun/docs/#jobs) | PASS | HTTP 200 | [raw](results/probes/job-result.json) |
| job-submissions | [Public GET is reachable and returns JSON for /jobs/aca5f077-3da7-44bb-a66d-1680dcdb0525/submissions; the docs do not specify a complete top-level schema.](https://imd.fun/docs/#jobs) | PASS | HTTP 200 | [raw](results/probes/job-submissions.json) |
| job-records | [Documented GET response shape for /jobs/aca5f077-3da7-44bb-a66d-1680dcdb0525/records](https://imd.fun/docs/#records) | PASS | HTTP 200 | [raw](results/probes/job-records.json) |
| job-assessments | [Documented GET response shape for /jobs/aca5f077-3da7-44bb-a66d-1680dcdb0525/assessments](https://imd.fun/docs/#records) | PASS | HTTP 200 | [raw](results/probes/job-assessments.json) |
| workflow-detail | [Documented GET response shape for /workflows/8827d667-b23f-404c-a52e-270e2a8f701b](https://imd.fun/docs/#workflows) | PASS | HTTP 200 | [raw](results/probes/workflow-detail.json) |
| oracle-detail | [Documented GET response shape for /oracle/requests/6c3d808e-c038-464c-9f1b-381718ea2937?members=0](https://imd.fun/docs/#oracle) | PASS | HTTP 200 | [raw](results/probes/oracle-detail.json) |
| oracle-attestation | [Documented GET response shape for /oracle/requests/6c3d808e-c038-464c-9f1b-381718ea2937/attestation](https://imd.fun/docs/#oracle) | FAIL | HTTP 200; unexpected Access-Control-Allow-Origin=None | [raw](results/probes/oracle-attestation.json) |
| oracle-pools | [Public GET is reachable and returns JSON for /oracle/requests/6c3d808e-c038-464c-9f1b-381718ea2937/pools; the docs do not specify a complete top-level schema.](https://imd.fun/docs/#oracle) | PASS | HTTP 200 | [raw](results/probes/oracle-pools.json) |
| site-detail | [Documented GET response shape for /sites/fbb9e6ca-8151-485c-aa22-744275954756](https://imd.fun/docs/#publications) | PASS | HTTP 200 | [raw](results/probes/site-detail.json) |
| launch-detail | [Documented GET response shape for /launches/87513a53-cb12-4e4e-9599-293a69a373ac?claims=1&work=1](https://imd.fun/docs/#launches) | PASS | HTTP 200 | [raw](results/probes/launch-detail.json) |
| launch-assurances | [Documented GET response shape for /launches/87513a53-cb12-4e4e-9599-293a69a373ac/assurances](https://imd.fun/docs/#launches) | PASS | HTTP 200 | [raw](results/probes/launch-assurances.json) |
| worker-standing | [Public GET is reachable and returns JSON for /workers/9fbeb473fba88fbdce3d33b03ec015711467f32ebff45f83c6166710f0021d7b/standing?queue=0; the docs do not specify a complete top-level schema.](https://imd.fun/docs/#fleet) | PASS | HTTP 200 | [raw](results/probes/worker-standing.json) |
| seat-detail | [Documented GET response shape for /seats/42?work=0&reviews=0](https://imd.fun/docs/#fleet) | PASS | HTTP 200 | [raw](results/probes/seat-detail.json) |
| seat-standing | [Public GET is reachable and returns JSON for /seats/42/standing; the docs do not specify a complete top-level schema.](https://imd.fun/docs/#fleet) | PASS | HTTP 200 | [raw](results/probes/seat-standing.json) |
| wallet-earnings | [Documented GET response shape for /wallets/0x0000000000000000000000000000000000000000/earnings?limit=1](https://imd.fun/docs/#fleet) | PASS | HTTP 200 | [raw](results/probes/wallet-earnings.json) |
| paid-by | [Documented GET response shape for /requests/paid-by/0x0000000000000000000000000000000000000000](https://imd.fun/docs/#paid) | PASS | HTTP 200 | [raw](results/probes/paid-by.json) |
| schedule-unknown | [Absent/nonmatching resource returns 404 unknown_schedule](https://imd.fun/docs/#schedules) | PASS | HTTP 404; unknown_schedule | [raw](results/probes/schedule-unknown.json) |
| site-unknown | [Absent/nonmatching resource returns 404 unknown_site](https://imd.fun/docs/#publications) | PASS | HTTP 404; unknown_site | [raw](results/probes/site-unknown.json) |
| read-unknown | [Absent/nonmatching resource returns 404 unknown_read](https://imd.fun/docs/#health) | PASS | HTTP 404; unknown_read: nothing resolves skill:imd-audit-nonexistent | [raw](results/probes/read-unknown.json) |
| review-unknown | [Absent/nonmatching resource returns 404 unknown_review](https://imd.fun/docs/#records) | PASS | HTTP 404; unknown_review: no review for that submission | [raw](results/probes/review-unknown.json) |
| record-unknown | [Absent/nonmatching resource returns 404 unknown_record](https://imd.fun/docs/#records) | PASS | HTTP 404; unknown_record | [raw](results/probes/record-unknown.json) |
| document-unknown | [Absent/nonmatching resource returns 404 unknown_document](https://imd.fun/docs/#records) | PASS | HTTP 404; unknown_document | [raw](results/probes/document-unknown.json) |
| job-non-audit | [Absent/nonmatching resource returns 404 unknown_audit](https://imd.fun/docs/#jobs) | PASS | HTTP 404; unknown_audit: no audit job with this id | [raw](results/probes/job-non-audit.json) |
| job-no-panel | [Absent/nonmatching resource returns 404 no_panel](https://imd.fun/docs/#research) | PASS | HTTP 404; no_panel: that job has no panel | [raw](results/probes/job-no-panel.json) |
| job-no-fuzz | [Absent/nonmatching resource returns 404 no_fuzz](https://imd.fun/docs/#research) | PASS | HTTP 404; no_fuzz: that job has no campaign | [raw](results/probes/job-no-fuzz.json) |
| schedule-owner-invalid | [Invalid owner returns 400 invalid_owner.](https://imd.fun/docs/#schedules) | PASS | HTTP 400; invalid_owner: owner must be a 0x wallet address | [raw](results/probes/schedule-owner-invalid.json) |
| cursor-invalid-jobs | [Invalid before cursor returns 400.](https://imd.fun/docs/#pagination) | PASS | HTTP 400; invalid_query: `before` must be a time, such as 2026-09-20T12:00:00Z | [raw](results/probes/cursor-invalid-jobs.json) |
| limit-jobs-0 | [limit=0 is clamped to 1.](https://imd.fun/docs/#pagination) | PASS | HTTP 200 | [raw](results/probes/limit-jobs-0.json) |
| limit-jobs-501 | [limit=501 is clamped to 500.](https://imd.fun/docs/#pagination) | PASS | HTTP 200 | [raw](results/probes/limit-jobs-501.json) |
| cursor-invalid-workflows | [Invalid before cursor returns 400.](https://imd.fun/docs/#pagination) | PASS | HTTP 400; invalid_query: `before` must be a time, such as 2026-09-20T12:00:00Z | [raw](results/probes/cursor-invalid-workflows.json) |
| limit-workflows-0 | [limit=0 is clamped to 1.](https://imd.fun/docs/#pagination) | PASS | HTTP 200 | [raw](results/probes/limit-workflows-0.json) |
| limit-workflows-501 | [limit=501 is clamped to 500.](https://imd.fun/docs/#pagination) | PASS | HTTP 200; sparse sample: clamp upper bound only, exact clamp not proven | [raw](results/probes/limit-workflows-501.json) |
| cursor-invalid-oracle-requests | [Invalid before cursor returns 400.](https://imd.fun/docs/#pagination) | PASS | HTTP 400; invalid_query: `before` must be a time, such as 2026-09-20T12:00:00Z | [raw](results/probes/cursor-invalid-oracle-requests.json) |
| limit-oracle-requests-0 | [limit=0 is clamped to 1.](https://imd.fun/docs/#pagination) | PASS | HTTP 200 | [raw](results/probes/limit-oracle-requests-0.json) |
| limit-oracle-requests-501 | [limit=501 is clamped to 500.](https://imd.fun/docs/#pagination) | PASS | HTTP 200 | [raw](results/probes/limit-oracle-requests-501.json) |
| cursor-invalid-schedules | [Invalid before cursor returns 400.](https://imd.fun/docs/#pagination) | PASS | HTTP 400; invalid_query: `before` must be a time, such as 2026-09-20T12:00:00Z | [raw](results/probes/cursor-invalid-schedules.json) |
| limit-schedules-0 | [limit=0 is clamped to 1.](https://imd.fun/docs/#pagination) | PASS | HTTP 200 | [raw](results/probes/limit-schedules-0.json) |
| limit-schedules-501 | [limit=501 is clamped to 500.](https://imd.fun/docs/#pagination) | PASS | HTTP 200; sparse sample: clamp upper bound only, exact clamp not proven | [raw](results/probes/limit-schedules-501.json) |
| cursor-invalid-feedback-batches | [Invalid before cursor returns 400.](https://imd.fun/docs/#pagination) | PASS | HTTP 400; invalid_query: `before` must be a time, such as 2026-09-20T12:00:00Z | [raw](results/probes/cursor-invalid-feedback-batches.json) |
| limit-feedback-batches-0 | [limit=0 is clamped to 1.](https://imd.fun/docs/#pagination) | PASS | HTTP 200 | [raw](results/probes/limit-feedback-batches-0.json) |
| limit-feedback-batches-501 | [limit=501 is clamped to 500.](https://imd.fun/docs/#pagination) | PASS | HTTP 200 | [raw](results/probes/limit-feedback-batches-501.json) |
| query-jobs-200 | [q length 200: documented maximum 200.](https://imd.fun/docs/#jobs) | PASS | HTTP 200 | [raw](results/probes/query-jobs-200.json) |
| query-jobs-201 | [q exceeds the stated 200-character maximum; docs do not specify whether to reject or truncate, so record behavior without inferring a refusal.](https://imd.fun/docs/#jobs) | OBSERVED | HTTP 200; documentation does not specify the exact outcome. | [raw](results/probes/query-jobs-201.json) |
| query-oracle-200 | [q length 200: documented maximum 200.](https://imd.fun/docs/#oracle) | PASS | HTTP 200 | [raw](results/probes/query-oracle-200.json) |
| query-oracle-201 | [q exceeds the stated 200-character maximum; docs do not specify whether to reject or truncate, so record behavior without inferring a refusal.](https://imd.fun/docs/#oracle) | OBSERVED | HTTP 200; documentation does not specify the exact outcome. | [raw](results/probes/query-oracle-201.json) |
| query-search-200 | [q length 200: documented maximum 200.](https://imd.fun/docs/#explorer) | PASS | HTTP 200 | [raw](results/probes/query-search-200.json) |
| query-search-201 | [q exceeds the stated 200-character maximum; docs do not specify whether to reject or truncate, so record behavior without inferring a refusal.](https://imd.fun/docs/#explorer) | OBSERVED | HTTP 200; documentation does not specify the exact outcome. | [raw](results/probes/query-search-201.json) |
| page-size-0 | [Out-of-range pageSize must be rejected or constrained to the documented 1–100 range; the docs do not prescribe which.](https://imd.fun/docs/#publications) | PASS | HTTP 400; invalid_query: {'formErrors': [], 'fieldErrors': {'pageSize': ['Too small: expected number to be >=1']}}; out-of-range query rejected. | [raw](results/probes/page-size-0.json) |
| page-size-1 | [pageSize=1; documented range 1–100 (out-of-range policy unspecified).](https://imd.fun/docs/#publications) | PASS | HTTP 200 | [raw](results/probes/page-size-1.json) |
| page-size-100 | [pageSize=100; documented range 1–100 (out-of-range policy unspecified).](https://imd.fun/docs/#publications) | PASS | HTTP 200 | [raw](results/probes/page-size-100.json) |
| page-size-101 | [Out-of-range pageSize must be rejected or constrained to the documented 1–100 range; the docs do not prescribe which.](https://imd.fun/docs/#publications) | PASS | HTTP 400; invalid_query: {'formErrors': [], 'fieldErrors': {'pageSize': ['Too big: expected number to be <=100']}}; out-of-range query rejected. | [raw](results/probes/page-size-101.json) |
| explorer-agent | [Explorer agent includes documented fields.](https://imd.fun/docs/#explorer) | FAIL | HTTP 200; missing jobs; missing lastAcceptedAt | [raw](results/probes/explorer-agent.json) |
| explorer-claim | [Wallet without allocation yields claim:null.](https://imd.fun/docs/#explorer) | PASS | HTTP 200 | [raw](results/probes/explorer-claim.json) |
| explorer-capabilities | [Explorer request capabilities passes through the control-plane shape.](https://imd.fun/docs/#explorer) | PASS | HTTP 200 | [raw](results/probes/explorer-capabilities.json) |
| docs-runtime | [An existing write-readme-and-docs job should be able to write its named documentation output under the documented path contract.](https://imd.fun/docs/#jobs) | FAIL | HTTP 200; historical runtime record contains the documented step and path_violation. | [raw](results/probes/docs-runtime.json) |
| docs-runtime-submissions | [Public attempts identify the exact paths rejected at runtime for the documentation step.](https://imd.fun/docs/#jobs) | PASS | HTTP 200 | [raw](results/probes/docs-runtime-submissions.json) |
| docs-runtime-result | [A blocked documentation job exposes complete:false and its result shape.](https://imd.fun/docs/#jobs) | PASS | HTTP 200 | [raw](results/probes/docs-runtime-result.json) |
| missing-paths-gas-and-size-report-after-rate-limit | [gas-and-size-report requires explicit step paths.](https://imd.fun/docs/#job-body) | FAIL | HTTP 200; documented invalid input was not refused. | [raw](results/probes/missing-paths-gas-and-size-report-after-rate-limit.json) |
| provided-paths-deploy-script | [A listed skill accepts explicit step paths under the documented path rule.](https://imd.fun/docs/#job-body) | FAIL | HTTP 200; blockers=[{"code": "unplannable_steps", "detail": "step 1 (deploy-script) declares its own budget, so the step may not also name paths"}]; unexpected unplannable_steps | [raw](results/probes/provided-paths-deploy-script.json) |
| provided-paths-gas-and-size-report | [A listed skill accepts explicit step paths under the documented path rule.](https://imd.fun/docs/#job-body) | FAIL | HTTP 200; blockers=[{"code": "unplannable_steps", "detail": "step 1 (gas-and-size-report) declares its own budget, so the step may not also name paths"}]; unexpected unplannable_steps | [raw](results/probes/provided-paths-gas-and-size-report.json) |
| body-bytes-16384 | [Whole check body of 16384 bytes follows the documented 16 KiB cap.](https://imd.fun/docs/#paid) | PASS | HTTP 200 | [raw](results/probes/body-bytes-16384.json) |
| body-bytes-16385 | [Whole check body of 16385 bytes follows the documented 16 KiB cap.](https://imd.fun/docs/#paid) | PASS | HTTP 413; request_too_large | [raw](results/probes/body-bytes-16385.json) |
| workflow-check | [Workflow check returns documented plan/facts/judged shape.](https://imd.fun/docs/#paid) | PASS | HTTP 200; blockers=[{"code": "recheck_failed", "detail": "The checker is not sure the request wants an independent security review of smart contracts, which the plan includes. Say whether it does."}] | [raw](results/probes/workflow-check.json) |
| workflow-required-request | [request is required on workflow.open.](https://imd.fun/docs/#workflow-body) | PASS | HTTP 400; invalid_request: request: Invalid input: expected string, received undefined | [raw](results/probes/workflow-required-request.json) |
| workflow-required-draft | [draft is required on workflow.open.](https://imd.fun/docs/#workflow-body) | PASS | HTTP 400; invalid_request: draft: Invalid input: expected object, received undefined | [raw](results/probes/workflow-required-draft.json) |
| workflow-refused-parentJobId | [Workflow draft refuses parentJobId.](https://imd.fun/docs/#workflow-body) | PASS | HTTP 200; blockers=[{"code": "invalid_input", "detail": "a paid workflow starts a project of its own; parentJobId and projectId are not accepted"}] | [raw](results/probes/workflow-refused-parentJobId.json) |
| workflow-refused-projectId | [Workflow draft refuses projectId.](https://imd.fun/docs/#workflow-body) | PASS | HTTP 200; blockers=[{"code": "invalid_input", "detail": "a paid workflow starts a project of its own; parentJobId and projectId are not accepted"}] | [raw](results/probes/workflow-refused-projectId.json) |
| workflow-refused-deploymentLaunchId | [Workflow draft refuses deploymentLaunchId.](https://imd.fun/docs/#workflow-body) | PASS | HTTP 200; blockers=[{"code": "invalid_input", "detail": "a paid workflow does not build against an existing launch"}] | [raw](results/probes/workflow-refused-deploymentLaunchId.json) |
| workflow-refused-submissionKey | [Workflow draft refuses submissionKey.](https://imd.fun/docs/#workflow-body) | PASS | HTTP 400; invalid_request: draft: Unrecognized key: "submissionKey" | [raw](results/probes/workflow-refused-submissionKey.json) |
| workflow-refused-unexpectedField | [Workflow draft refuses unexpectedField.](https://imd.fun/docs/#workflow-body) | PASS | HTTP 400; invalid_request: draft: Unrecognized key: "unexpectedField" | [raw](results/probes/workflow-refused-unexpectedField.json) |
| workflow-request-0 | [Workflow request has 1–16000 characters; aggregate 16 KiB cap also applies.](https://imd.fun/docs/#workflow-body) | PASS | HTTP 400; invalid_request: request: Too small: expected string to have >=1 characters | [raw](results/probes/workflow-request-0.json) |
| workflow-request-16001 | [Workflow request has 1–16000 characters; aggregate 16 KiB cap also applies.](https://imd.fun/docs/#workflow-body) | PASS | HTTP 400; invalid_request: request: Too big: expected string to have <=16000 characters | [raw](results/probes/workflow-request-16001.json) |
| oracle-required-question | [Short oracle check requires question.](https://imd.fun/docs/#oracle-body) | PASS | HTTP 400; invalid_request: question: Invalid input: expected string, received undefined | [raw](results/probes/oracle-required-question.json) |
| oracle-required-panelSize | [Short oracle check requires panelSize.](https://imd.fun/docs/#oracle-body) | PASS | HTTP 400; invalid_request: panelSize: Invalid input: expected number, received undefined | [raw](results/probes/oracle-required-panelSize.json) |
| paths-8-directory | [8 step paths (directory form) are within the documented maximum of 16.](https://imd.fun/docs/#job-body) | PASS | HTTP 200 | [raw](results/probes/paths-8-directory.json) |
| paths-9-directory | [9 step paths (directory form) are within the documented maximum of 16.](https://imd.fun/docs/#job-body) | FAIL | HTTP 200; blockers=[{"code": "bad_path_count", "detail": "expected between 1 and 16 allowed paths", "node": "implement_component"}]; unexpected bad_path_count | [raw](results/probes/paths-9-directory.json) |
| paths-16-file | [16 step paths (file form) are within the documented maximum of 16.](https://imd.fun/docs/#job-body) | PASS | HTTP 200 | [raw](results/probes/paths-16-file.json) |
| paths-16-glob | [Explore glob form for 16 paths; docs only specify repository-relative paths.](https://imd.fun/docs/#job-body) | OBSERVED | HTTP 200; documentation does not specify the exact outcome. | [raw](results/probes/paths-16-glob.json) |

## Exact requests for mismatches

### oracle-list

Documented claim: [GET /oracle/requests?limit=2 returns the documented response fields; record cross-origin headers.](https://imd.fun/docs/#oracle)

Observed: HTTP 200; requests rows missing panelSize: [0, 1]; requests rows missing quorum: [0, 1]

Exact request (from repository root; each curl is a live call and bypasses the runner budget, so wait at least 2 seconds and account for it):

```sh
curl --max-time 60 --request GET --header 'User-agent: IMD-public-docs-audit/1.0' --header 'Accept: application/json' --header 'Origin: https://example.org' 'https://api.imd.fun/oracle/requests?limit=2'
```

Full response, headers and timestamps: [oracle-list](results/probes/oracle-list.json).

### docs-no-paths

Documented claim: [write-readme-and-docs without step paths must be refused: paths are documented as required.](https://imd.fun/docs/#job-body)

Observed: HTTP 200; documented invalid input was not refused.

Exact request (from repository root; each curl is a live call and bypasses the runner budget, so wait at least 2 seconds and account for it):

```sh
curl --max-time 60 --request POST --header 'User-agent: IMD-public-docs-audit/1.0' --header 'Accept: application/json' --header 'Content-type: application/json' --data-binary @results/requests/docs-no-paths.json https://api.imd.fun/requests/check
```

Full response, headers and timestamps: [docs-no-paths](results/probes/docs-no-paths.json).

### docs-with-paths

Documented claim: [Documented step paths must not make write-readme-and-docs unplannable.](https://imd.fun/docs/#job-body)

Observed: HTTP 200; blockers=[{"code": "unplannable_steps", "detail": "step 1 (write-readme-and-docs) declares its own budget, so the step may not also name paths"}]; unexpected unplannable_steps

Exact request (from repository root; each curl is a live call and bypasses the runner budget, so wait at least 2 seconds and account for it):

```sh
curl --max-time 60 --request POST --header 'User-agent: IMD-public-docs-audit/1.0' --header 'Accept: application/json' --header 'Content-type: application/json' --data-binary @results/requests/docs-with-paths.json https://api.imd.fun/requests/check
```

Full response, headers and timestamps: [docs-with-paths](results/probes/docs-with-paths.json).

### paths-count-16

Documented claim: [The documented maximum of 16 repository-relative step paths should not exceed the internal allowed-path count.](https://imd.fun/docs/#job-body)

Observed: HTTP 200; blockers=[{"code": "bad_path_count", "detail": "expected between 1 and 16 allowed paths", "node": "implement_component"}]; unexpected bad_path_count

Exact request (from repository root; each curl is a live call and bypasses the runner budget, so wait at least 2 seconds and account for it):

```sh
curl --max-time 60 --request POST --header 'User-agent: IMD-public-docs-audit/1.0' --header 'Accept: application/json' --header 'Content-type: application/json' --data-binary @results/requests/paths-count-16.json https://api.imd.fun/requests/check
```

Full response, headers and timestamps: [paths-count-16](results/probes/paths-count-16.json).

### missing-paths-deploy-script

Documented claim: [deploy-script requires explicit step paths.](https://imd.fun/docs/#job-body)

Observed: HTTP 200; documented invalid input was not refused.

Exact request (from repository root; each curl is a live call and bypasses the runner budget, so wait at least 2 seconds and account for it):

```sh
curl --max-time 60 --request POST --header 'User-agent: IMD-public-docs-audit/1.0' --header 'Accept: application/json' --header 'Content-type: application/json' --data-binary @results/requests/missing-paths-deploy-script.json https://api.imd.fun/requests/check
```

Full response, headers and timestamps: [missing-paths-deploy-script](results/probes/missing-paths-deploy-script.json).

### oracle-attestation

Documented claim: [Documented GET response shape for /oracle/requests/6c3d808e-c038-464c-9f1b-381718ea2937/attestation](https://imd.fun/docs/#oracle)

Observed: HTTP 200; unexpected Access-Control-Allow-Origin=None

Exact request (from repository root; each curl is a live call and bypasses the runner budget, so wait at least 2 seconds and account for it):

```sh
curl --max-time 60 --request GET --header 'User-agent: IMD-public-docs-audit/1.0' --header 'Accept: application/json' --header 'Origin: https://example.org' https://api.imd.fun/oracle/requests/6c3d808e-c038-464c-9f1b-381718ea2937/attestation
```

Full response, headers and timestamps: [oracle-attestation](results/probes/oracle-attestation.json).

### explorer-agent

Documented claim: [Explorer agent includes documented fields.](https://imd.fun/docs/#explorer)

Observed: HTTP 200; missing jobs; missing lastAcceptedAt

Exact request (from repository root; each curl is a live call and bypasses the runner budget, so wait at least 2 seconds and account for it):

```sh
curl --max-time 60 --request GET --header 'User-agent: IMD-public-docs-audit/1.0' --header 'Accept: application/json' --header 'Origin: https://example.org' https://explorer.imd.fun/api/agents/42
```

Full response, headers and timestamps: [explorer-agent](results/probes/explorer-agent.json).

### docs-runtime

Documented claim: [An existing write-readme-and-docs job should be able to write its named documentation output under the documented path contract.](https://imd.fun/docs/#jobs)

Observed: HTTP 200; historical runtime record contains the documented step and path_violation.

Exact request (from repository root; each curl is a live call and bypasses the runner budget, so wait at least 2 seconds and account for it):

```sh
curl --max-time 60 --request GET --header 'User-agent: IMD-public-docs-audit/1.0' --header 'Accept: application/json' --header 'Origin: https://example.org' https://api.imd.fun/jobs/c2ba5413-a0fe-4e9a-9915-0e521c5bea2c
```

Full response, headers and timestamps: [docs-runtime](results/probes/docs-runtime.json).

### missing-paths-gas-and-size-report-after-rate-limit

Documented claim: [gas-and-size-report requires explicit step paths.](https://imd.fun/docs/#job-body)

Observed: HTTP 200; documented invalid input was not refused.

Exact request (from repository root; each curl is a live call and bypasses the runner budget, so wait at least 2 seconds and account for it):

```sh
curl --max-time 60 --request POST --header 'User-agent: IMD-public-docs-audit/1.0' --header 'Accept: application/json' --header 'Content-type: application/json' --data-binary @results/requests/missing-paths-gas-and-size-report-after-rate-limit.json https://api.imd.fun/requests/check
```

Full response, headers and timestamps: [missing-paths-gas-and-size-report-after-rate-limit](results/probes/missing-paths-gas-and-size-report-after-rate-limit.json).

### provided-paths-deploy-script

Documented claim: [A listed skill accepts explicit step paths under the documented path rule.](https://imd.fun/docs/#job-body)

Observed: HTTP 200; blockers=[{"code": "unplannable_steps", "detail": "step 1 (deploy-script) declares its own budget, so the step may not also name paths"}]; unexpected unplannable_steps

Exact request (from repository root; each curl is a live call and bypasses the runner budget, so wait at least 2 seconds and account for it):

```sh
curl --max-time 60 --request POST --header 'User-agent: IMD-public-docs-audit/1.0' --header 'Accept: application/json' --header 'Content-type: application/json' --data-binary @results/requests/provided-paths-deploy-script.json https://api.imd.fun/requests/check
```

Full response, headers and timestamps: [provided-paths-deploy-script](results/probes/provided-paths-deploy-script.json).

### provided-paths-gas-and-size-report

Documented claim: [A listed skill accepts explicit step paths under the documented path rule.](https://imd.fun/docs/#job-body)

Observed: HTTP 200; blockers=[{"code": "unplannable_steps", "detail": "step 1 (gas-and-size-report) declares its own budget, so the step may not also name paths"}]; unexpected unplannable_steps

Exact request (from repository root; each curl is a live call and bypasses the runner budget, so wait at least 2 seconds and account for it):

```sh
curl --max-time 60 --request POST --header 'User-agent: IMD-public-docs-audit/1.0' --header 'Accept: application/json' --header 'Content-type: application/json' --data-binary @results/requests/provided-paths-gas-and-size-report.json https://api.imd.fun/requests/check
```

Full response, headers and timestamps: [provided-paths-gas-and-size-report](results/probes/provided-paths-gas-and-size-report.json).

### paths-9-directory

Documented claim: [9 step paths (directory form) are within the documented maximum of 16.](https://imd.fun/docs/#job-body)

Observed: HTTP 200; blockers=[{"code": "bad_path_count", "detail": "expected between 1 and 16 allowed paths", "node": "implement_component"}]; unexpected bad_path_count

Exact request (from repository root; each curl is a live call and bypasses the runner budget, so wait at least 2 seconds and account for it):

```sh
curl --max-time 60 --request POST --header 'User-agent: IMD-public-docs-audit/1.0' --header 'Accept: application/json' --header 'Content-type: application/json' --data-binary @results/requests/paths-9-directory.json https://api.imd.fun/requests/check
```

Full response, headers and timestamps: [paths-9-directory](results/probes/paths-9-directory.json).

## CORS observations

All rows below sent `Origin: https://example.org`. An absent header does not make a server-to-server request fail. No OPTIONS/preflight calls were made; a GET header observation does not establish full browser POST support. Error responses are distinguished by status. Documentation says selected routes permit CORS ([Base URLs](https://imd.fun/docs/#base)).

| Probe | Request | Status | Access-Control-Allow-Origin |
|---|---|---|---|
| version | `GET https://api.imd.fun/version` | 200 | `absent` |
| health | `GET https://api.imd.fun/health` | 200 | `absent` |
| skills | `GET https://api.imd.fun/skills` | 200 | `absent` |
| services | `GET https://api.imd.fun/services` | 200 | `absent` |
| hourly | `GET https://api.imd.fun/steps/hourly` | 200 | `*` |
| jobs | `GET https://api.imd.fun/jobs?limit=5` | 200 | `absent` |
| workflows | `GET https://api.imd.fun/workflows?limit=2` | 200 | `absent` |
| oracle-list | `GET https://api.imd.fun/oracle/requests?limit=2` | 200 | `*` |
| oracle-counts | `GET https://api.imd.fun/oracle/counts` | 200 | `*` |
| schedules | `GET https://api.imd.fun/schedules?limit=2` | 200 | `*` |
| panels | `GET https://api.imd.fun/research/panels?limit=1` | 200 | `absent` |
| fuzz | `GET https://api.imd.fun/fuzz/results?limit=1` | 200 | `absent` |
| swarm | `GET https://api.imd.fun/swarm` | 200 | `*` |
| workers | `GET https://api.imd.fun/workers?fields=deviceKey` | 200 | `absent` |
| contributors | `GET https://api.imd.fun/contributors` | 200 | `absent` |
| seats | `GET https://api.imd.fun/seats/records` | 200 | `absent` |
| owners | `GET https://api.imd.fun/seats/owners` | 200 | `absent` |
| publications | `GET https://api.imd.fun/publications?pageSize=1` | 200 | `absent` |
| publication-counts | `GET https://api.imd.fun/publications/counts` | 200 | `absent` |
| sites | `GET https://api.imd.fun/sites` | 200 | `absent` |
| ens | `GET https://api.imd.fun/ens` | 404 | `*` |
| launches | `GET https://api.imd.fun/launches?limit=1` | 200 | `absent` |
| policies | `GET https://api.imd.fun/launch/policies` | 200 | `absent` |
| feedback | `GET https://api.imd.fun/feedback/batches?limit=1` | 200 | `absent` |
| explorer-version | `GET https://explorer.imd.fun/version` | 200 | `absent` |
| explorer-activity | `GET https://explorer.imd.fun/api/activity` | 200 | `absent` |
| explorer-search | `GET https://explorer.imd.fun/api/search?q=docs` | 200 | `absent` |
| capabilities-origin | `GET https://api.imd.fun/requests/capabilities` | 403 | `absent` |
| openapi-origin | `GET https://api.imd.fun/openapi.json` | 403 | `absent` |
| check-origin | `POST https://api.imd.fun/requests/check` | 403 | `absent` |
| jobs-docs-search | `GET https://api.imd.fun/jobs?q=README&limit=100` | 200 | `absent` |
| jobs-path-search | `GET https://api.imd.fun/jobs?q=documentation&limit=100` | 200 | `absent` |
| job-detail | `GET https://api.imd.fun/jobs/aca5f077-3da7-44bb-a66d-1680dcdb0525` | 200 | `absent` |
| job-result | `GET https://api.imd.fun/jobs/aca5f077-3da7-44bb-a66d-1680dcdb0525/result` | 200 | `absent` |
| job-submissions | `GET https://api.imd.fun/jobs/aca5f077-3da7-44bb-a66d-1680dcdb0525/submissions` | 200 | `absent` |
| job-records | `GET https://api.imd.fun/jobs/aca5f077-3da7-44bb-a66d-1680dcdb0525/records` | 200 | `absent` |
| job-assessments | `GET https://api.imd.fun/jobs/aca5f077-3da7-44bb-a66d-1680dcdb0525/assessments` | 200 | `absent` |
| workflow-detail | `GET https://api.imd.fun/workflows/8827d667-b23f-404c-a52e-270e2a8f701b` | 200 | `absent` |
| oracle-detail | `GET https://api.imd.fun/oracle/requests/6c3d808e-c038-464c-9f1b-381718ea2937?members=0` | 200 | `*` |
| oracle-attestation | `GET https://api.imd.fun/oracle/requests/6c3d808e-c038-464c-9f1b-381718ea2937/attestation` | 200 | `absent` |
| oracle-pools | `GET https://api.imd.fun/oracle/requests/6c3d808e-c038-464c-9f1b-381718ea2937/pools` | 200 | `*` |
| site-detail | `GET https://api.imd.fun/sites/fbb9e6ca-8151-485c-aa22-744275954756` | 200 | `absent` |
| launch-detail | `GET https://api.imd.fun/launches/87513a53-cb12-4e4e-9599-293a69a373ac?claims=1&work=1` | 200 | `absent` |
| launch-assurances | `GET https://api.imd.fun/launches/87513a53-cb12-4e4e-9599-293a69a373ac/assurances` | 200 | `absent` |
| worker-standing | `GET https://api.imd.fun/workers/9fbeb473fba88fbdce3d33b03ec015711467f32ebff45f83c6166710f0021d7b/standing?queue=0` | 200 | `absent` |
| seat-detail | `GET https://api.imd.fun/seats/42?work=0&reviews=0` | 200 | `absent` |
| seat-standing | `GET https://api.imd.fun/seats/42/standing` | 200 | `absent` |
| wallet-earnings | `GET https://api.imd.fun/wallets/0x0000000000000000000000000000000000000000/earnings?limit=1` | 200 | `absent` |
| schedule-unknown | `GET https://api.imd.fun/schedules/00000000-0000-4000-8000-000000000000` | 404 | `absent` |
| site-unknown | `GET https://api.imd.fun/sites/00000000-0000-4000-8000-000000000000` | 404 | `absent` |
| read-unknown | `GET https://api.imd.fun/reads/skill/imd-audit-nonexistent` | 404 | `absent` |
| review-unknown | `GET https://api.imd.fun/reviews/0000000000000000000000000000000000000000000000000000000000000000.json` | 404 | `absent` |
| record-unknown | `GET https://api.imd.fun/work-records/0000000000000000000000000000000000000000000000000000000000000000.json` | 404 | `absent` |
| document-unknown | `GET https://api.imd.fun/review-documents/0000000000000000000000000000000000000000000000000000000000000000.json` | 404 | `absent` |
| job-non-audit | `GET https://api.imd.fun/jobs/aca5f077-3da7-44bb-a66d-1680dcdb0525/report.md` | 404 | `absent` |
| job-no-panel | `GET https://api.imd.fun/jobs/aca5f077-3da7-44bb-a66d-1680dcdb0525/panel` | 404 | `absent` |
| job-no-fuzz | `GET https://api.imd.fun/jobs/aca5f077-3da7-44bb-a66d-1680dcdb0525/fuzz` | 404 | `absent` |
| schedule-owner-invalid | `GET https://api.imd.fun/schedules?owner=invalid` | 400 | `absent` |
| cursor-invalid-jobs | `GET https://api.imd.fun/jobs?before=not-a-time` | 400 | `absent` |
| limit-jobs-0 | `GET https://api.imd.fun/jobs?limit=0` | 200 | `absent` |
| limit-jobs-501 | `GET https://api.imd.fun/jobs?limit=501` | 200 | `absent` |
| cursor-invalid-workflows | `GET https://api.imd.fun/workflows?before=not-a-time` | 400 | `absent` |
| limit-workflows-0 | `GET https://api.imd.fun/workflows?limit=0` | 200 | `absent` |
| limit-workflows-501 | `GET https://api.imd.fun/workflows?limit=501` | 200 | `absent` |
| cursor-invalid-oracle-requests | `GET https://api.imd.fun/oracle/requests?before=not-a-time` | 400 | `absent` |
| limit-oracle-requests-0 | `GET https://api.imd.fun/oracle/requests?limit=0` | 200 | `*` |
| limit-oracle-requests-501 | `GET https://api.imd.fun/oracle/requests?limit=501` | 200 | `*` |
| cursor-invalid-schedules | `GET https://api.imd.fun/schedules?before=not-a-time` | 400 | `absent` |
| limit-schedules-0 | `GET https://api.imd.fun/schedules?limit=0` | 200 | `*` |
| limit-schedules-501 | `GET https://api.imd.fun/schedules?limit=501` | 200 | `*` |
| cursor-invalid-feedback-batches | `GET https://api.imd.fun/feedback/batches?before=not-a-time` | 400 | `absent` |
| limit-feedback-batches-0 | `GET https://api.imd.fun/feedback/batches?limit=0` | 200 | `absent` |
| limit-feedback-batches-501 | `GET https://api.imd.fun/feedback/batches?limit=501` | 200 | `absent` |
| query-jobs-200 | `GET https://api.imd.fun/jobs?q=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` | 200 | `absent` |
| query-jobs-201 | `GET https://api.imd.fun/jobs?q=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` | 200 | `absent` |
| query-oracle-200 | `GET https://api.imd.fun/oracle/requests?q=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` | 200 | `*` |
| query-oracle-201 | `GET https://api.imd.fun/oracle/requests?q=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` | 200 | `*` |
| query-search-200 | `GET https://explorer.imd.fun/api/search?q=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` | 200 | `absent` |
| query-search-201 | `GET https://explorer.imd.fun/api/search?q=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` | 200 | `absent` |
| page-size-0 | `GET https://api.imd.fun/publications?pageSize=0` | 400 | `absent` |
| page-size-1 | `GET https://api.imd.fun/publications?pageSize=1` | 200 | `absent` |
| page-size-100 | `GET https://api.imd.fun/publications?pageSize=100` | 200 | `absent` |
| page-size-101 | `GET https://api.imd.fun/publications?pageSize=101` | 400 | `absent` |
| explorer-agent | `GET https://explorer.imd.fun/api/agents/42` | 200 | `absent` |
| explorer-claim | `GET https://explorer.imd.fun/api/claim?launch=87513a53-cb12-4e4e-9599-293a69a373ac&wallet=0x0000000000000000000000000000000000000000` | 200 | `absent` |
| docs-runtime | `GET https://api.imd.fun/jobs/c2ba5413-a0fe-4e9a-9915-0e521c5bea2c` | 200 | `absent` |
| docs-runtime-submissions | `GET https://api.imd.fun/jobs/c2ba5413-a0fe-4e9a-9915-0e521c5bea2c/submissions` | 200 | `absent` |
| docs-runtime-result | `GET https://api.imd.fun/jobs/c2ba5413-a0fe-4e9a-9915-0e521c5bea2c/result` | 200 | `absent` |
