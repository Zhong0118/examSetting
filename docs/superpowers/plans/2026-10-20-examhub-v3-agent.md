# ExamHub V3 Implementation Plan

> Use subagent-driven-development for disjoint engine/UI tasks; coordinator owns persistence, runtime and integration. User authorized direct implementation.

**Goal:** A bounded teaching Agent with real tool decisions, evidence, resumable sessions and behavioral evaluation.
**Architecture:** Pure validated tool engine + SQLite checkpoints + bounded existing HTTP model adapter, Vue workbench.
**Tech Stack:** Existing Flask/SQLite/Python stdlib, Vue/TypeScript. No new framework dependency.
**Spec:** docs/superpowers/specs/2026-10-20-examhub-v3-agent.md

## Constraints
- V2 published separately (004787a, PR #3); V3 publication authorized in the follow-up request.
- Original evidence and single-process limits apply. No paid model calls during acceptance.
- Bound each model turn to6 calls/session32, explicit user waiting, answer hiding, owner isolation, idempotent writes.

## Tasks
- [x] Engine worker: backend/tutor_engine.py + tests/test_tutor_engine.py. Test tool policies, turn-taking, citations, lexical retrieval and public redaction before implementation.
- [x] Frontend worker: frontend/**. Session setup/main workspace/history/trace/benchmark, identity isolation and retry-safe commands; tests + build.
- [x] Coordinator: backend/tutor.py + tests/test_tutor.py; expose read-only AI config accessor, app registration/guest migration, transaction/version/idempotency and bounded worker.
- [x] Evaluation worker after engine interface exists: backend/tutor_evaluation.py + fixture/test; execute actual tool engine across original behavior cases, truthful scope/version/hash.
- [x] Integration: API/engine/UI real HTTP fixture, independent review, desktop/mobile browser, failure recovery and all tests/build.
- [x] README, reproducible demo and job-interview evidence notes with measured outputs/limits; no invented model or teaching-effect claims.

## Decisions
- Choose a single tool loop over heavyweight orchestration: existing storage/runtime suffices for this bounded tutoring session; tools and checkpoint semantics are the assessed capability.
- Rule mode is visibly distinguished from model-driven Agent; no fake AI output without a configured model.

## Acceptance — 2026-10-20

- V2: commit `004787a55d676108f2303c5cb6b87e5b6434f935` pushed to `codex/examhub-v2`; [PR #3](https://github.com/Zhong0118/examSetting/pull/3) targets the unmerged V1 branch. Both push/PR CI passed for this SHA.
- V3 implemented on `codex/examhub-v3-agent`; publication authorized by the user after acceptance.
- Final backend: `cd backend && ../.venv/bin/python -m unittest discover -s tests -q` — 104 passed.
- Final frontend: `cd frontend && pnpm test && pnpm build` — 81 passed; Vue type checking and production build passed. `git diff --check` passed.
- Browser acceptance: real local HTTP provider fixture exercised all six tools, explicit user waiting, wrong-answer feedback, reason followup, pause/reload/resume, and answer draft preservation. Lost-ack retry produced only one answer. No paid model requests were made.
- PDF acceptance: teaching feedback opened physical page 2 and highlighted its original quote; returning to the session allowed followup completion. Desktop and 390px mobile layouts inspected; mobile benchmark has no horizontal overflow. Benchmark JSON downloaded through the actual UI.
- Offline benchmark: 12 original scenarios, 76 checks per strategy; rule 74/76 (10/12 scenarios), scripted-agent 76/76 (12/12), zero runtime errors. These are hand-authored strategy/guardrail checks, not real-model or learning-effect scores.
- Review fixes: accept/grade a pending answer issued on call 32 without call 33; quota reservation serializes with guest migration; only answered material enters retrieval/model evidence; full-public-JSON marker audit runs at every checkpoint and retains transient failures. Runtime/UI independent reviews and engine F1 followup were completed. The coordinator checked the final F2 implementation and its nine fault-injection combinations; a separate final F2 reviewer response was unavailable after session restoration.
- Reproducibility and interview boundaries: [teaching-agent architecture](../../architecture/teaching-agent.md). Browser artifacts are local ignored files under `.playwright-mcp/`; automated regression tests are versionable project files.
