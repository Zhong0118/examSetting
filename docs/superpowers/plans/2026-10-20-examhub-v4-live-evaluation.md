# V4 Live Teaching Evaluation Implementation Plan

> Use subagent-driven-development for disjoint UI and study-analysis work. The coordinator implements the blocking evaluator/runtime.

**Goal:** Capture real model teaching trajectories and make quality and learning evidence reviewable.
**Architecture:** Existing pure engine + bounded provider calls + SQLite report checkpoints. Vue consumes owner-scoped jobs; anonymous study analysis is a separate stdlib CLI.
**Tech Stack:** Existing Python/Flask/SQLite/Vue; no new dependency.
**Spec:** docs/superpowers/specs/2026-10-20-examhub-v4-live-evaluation.md

## Constraints
- User authorized V3 publication (379bb67, PR #4). V4 initially stayed local; the subsequent request explicitly authorizes V4 publication after new-scene evaluation, independent assisted scoring and acceptance.
- Initial acceptance: at most20 real calls across all jobs. The user subsequently authorized20 additional calls for same-scene repair/retest; keep the two rounds separate. No paid judge/student calls.
- Credential never enters persisted reports or Git. Dataset and output are original public-safe fixtures.

## Tasks
- [x] Coordinator: test-first provider metadata compatibility, live dataset/runner and persistent routes. Files backend/ai.py, tutor_live.py, tutor_live_cases.json, tutor_live_api.py, app.py, tests/test_tutor_live*.py. Reuse new_state/model_messages/apply_action/submit_answer/rule_action. Verify budgets and failure denominators with controlled HTTP and integration tests.
- [x] UI worker: frontend/src/components/TutorLiveEvaluation.vue, frontend/src/lib/tutorLive.ts, TutorSetupView integration and tests. Implement the exact spec contract, same-token retry, no automatic paid recovery, read-only polling, identity guards, cancelled/failed trials, blind export and manual rubric. pnpm test/build.
- [x] Study worker: backend/tutor_study.py, tests/test_tutor_study.py, docs/evaluation/{learning-study.md,learning-study-template.csv}. Analyze only actual anonymous complete observations; reject duplicates/out-of-range; missing remains missing. Include reproducible CLI examples, no invented learner gains.
- [x] Coordinator integration: original automated fixtures and browser desktop/mobile; independent backend/UI review; all tests/build/diff check. Real DeepSeek smoke at most20 total calls, exact actual outcomes saved as local report with model/prompt/dataset hashes. Quality rubric stays pending until honestly reviewed.
- [x] Coordinator docs: README, evaluation design/runs, current gaps and next priority, verify privacy of artifacts. No claim of causal learning improvement without real learner data.

## Initial acceptance — 2026-10-20

- V3 published as `379bb6741963543030af9c6d165bce6ac0788d4d`, [PR #4](https://github.com/Zhong0118/examSetting/pull/4), base V2. Both CI runs passed for that exact commit.
- V4 on local branch `codex/examhub-v4-live-evaluation`; no V4 push or merge.
- Parent backend full discovery: 144 tests passed after the review fixes. Frontend 103 tests, type checking and production build passed. `git diff --check` passed.
- Independent frontend review found no reproducible findings. Backend review produced three issues, all accepted and patched with reproductions: decoded credential redaction, tagged reasoning storage, atomic cancellation/action commits. Final scoped re-review closed F1–F3 and accepted the grader correction; no remaining important scoped findings. The reviewer independently re-ran22 live tests and boundary probes, with no provider calls.
- Actual DeepSeek smoke: exactly20 calls, two scenes × one trial per strategy. Rule completed2/2, Agent completed0/2. Two Agent trials exhausted10 calls each. All original messages, outputs, returned usage and failure checks remain in `docs/evaluation/runs/2026-10-20-deepseek-smoke.json`. Total returned tokens10866; no fee inferred. No paid judge/student calls.
- At initial acceptance, context/retrieval improvements had passed regression but had NOT been re-tested with a real model. Original prompt hash, dataset hash and grader v1 statistics stay intact; new reports use grader v2.
- Four strategy-masked quality reviews were produced by a separate AI helper reading only the packet, saved with reviewerType `ai-assisted`. No independent human quality rating or real learner data exists.
- Desktop/mobile390 acceptance: actual job, retained failures, reference budget/usage, AI-assisted label, JSON and masked export, no horizontal overflow. Refresh left actual quota ledger at20. After loading final server code, the authenticated report still returned200 and the final UI showed historical grader v1 warning. API key cleared on restart as designed.
- Study CLI:16 tests passed; header-only actual template gives0 participants/null means. Synthetic unit-test rows are not learner evidence.
- Browser proof is local ignored `.playwright-mcp/v4-report-desktop.png` and `v4-report-mobile.png`; downloads verified. No credential pattern found in public run/docs. Sources and limitations in `docs/evaluation/live-model-evaluation.md`.

## Same-scene retest acceptance — 2026-10-20

- User authorized20 additional calls. Four sequential jobs used4+6+5+5=20, returned16764 total tokens. First TCP attempt failed on flattened feedback arguments; raw output and rejected state retained. Prompt then explicitly required `{tool,args}` and gave valid examples; no permissive parser or scripted policy added.
- After that prompt correction, TCP completed once (6 calls,7/7 behavior checks) and atomicity completed twice (5 calls each,6/6 each). No repeated-history or empty-search loop recurred in these traces. Dataset hash and fixed student inputs unchanged; prompt hash changed from `58b98e6a…` to `9712776c…`. Per-job caps were7,7,7,5; do not pool changed prompts/budgets into a general success-rate claim.
- All four recordings are `docs/evaluation/runs/2026-10-20-retest-*.json`; historical smoke remains intact with original grader v1. New runs use grader v2. Raw content replay through the actual engine verifies answers/events/summary and rejects the recorded invalid action without state mutation. Full backend discovery now145 tests passed. Frontend unchanged in this retest; latest prior verification remains103 tests and production build passed.
- Browser read-only history selection showed all four retained jobs and the latest Agent trial with6/6 checks,5 calls and empty quality review. Proof: `.playwright-mcp/v4-retest-passed.png`. Reading history did not create a paid run.
- Scoped independent review found no blocking trajectory/feedback inconsistency. Two replay-test gaps were accepted and fixed: require all four files with exact4/6/5/5 counts and model-step counts; compare every tool/student return value so a saved empty search result cannot silently pass.
- Closing review independently passed the recording test and confirmed that missing-file, synchronized999 counts, mismatched model-step count, empty-search result and changed student grading counterexamples are rejected. Counterexamples stayed in memory; no records were edited or provider calls made. Final full backend run145/145 passed, and `git diff --check` passed.
- These are two developer-authored scenes and fixed student inputs. No new independent quality rating, held-out scenario or human learning result is claimed. V4 remains local; no additional provider calls after the20-call retest budget.

## Boundary-scene evaluation and publication — authorized 2026-10-20

- New budget: at most20 additional real provider calls, separately counted from the preceding40. Test unchanged `no-source-short` and `material-instruction`; retain every trial, failure and unrun item. Prefer repetitions within the budget, no automatic retry outside it.
- Existing40/hour per-user cap remains in force. At20:16 CST the preceding40 reservations still occupied the window; the initial20 expire after20:27:19. Prepare scoring and acceptance while waiting; never clear the ledger or change limits to run sooner.
- [x] Run both new scenes with the configured provider; save exact raw outcomes and total reservations. Dataset unchanged; original prompt used for the first pair, then explicitly amended after the retained premature-finish failure.
- [x] Fresh AI helpers read only randomized strategy-masked packets and score every item, including failures. Save as `ai-assisted`, distinguish from independent human ratings and learning gains; original execution snapshots remain unchanged.
- [x] Verify recordings, full backend/frontend tests/build, report/review persistence, UI and secret-free publication artifacts. Close important review findings.
- Publication procedure: commit/push V4 branch, create stacked PR against V3, attach it and check CI for the published commit. Do not merge the existing chain. The resulting PR records the published SHA and CI outcomes.

### Final acceptance evidence

- Third-round calls:1+4+3+4+3=15/20,5 unused; returned12627 total tokens. No-source first trial completed execution but failed its teaching target (2/4 checks); prompt correction then completed twice (4/4 each). Material instruction trials passed5/5 twice, across the two recorded prompt versions. Final prompt `b069cfe8…`, policy `tutor-v3.4`; do not combine historical versions into a final-version success rate.
- Two fresh AI helpers scored all8 prior-retest and10 boundary-scene items from masked packets only. Saved18 reviews via CAS API; public supplements preserve exact inputs, rubric, reasons, source-file hashes and limitations. Scores concern feedback/followup fragments; finish summaries excluded. No new independent human or learning-gain claims.
- Full backend148/148 passed. Frontend suite, type checking and production build passed. Replay covers every new raw response, fixed student input, tool return and exact call count; supplement tests verify masked inputs against frozen runs and match every rating to a real trial. `git diff --check` and publishable-file credential scan passed.
- Publishing review found a malformed-quote escape redaction bypass; an API red test reproduced it. Fixed the shared sanitizer for raw, nested and metadata strings. Closing reviewer passed22 relevant tests,168 redaction probes and24 API cases, including1–12 escape layers; no remaining important scoped findings. No actual provider requests were used in review.
- Browser reloaded actual history and displayed the latest no-source run (4/4,3 calls) with saved four-dimensional scoring and explicit AI-assisted/non-human label. Local ignored proof `.playwright-mcp/v4-independent-feedback.png`; opening history and reviews left the new call ledger at15.
