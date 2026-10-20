import { test, afterEach } from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import ts from 'typescript'
async function loadTypeScript(path) {
  const source = await readFile(new URL(path, import.meta.url), 'utf8')
  const { outputText } = ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ES2022 } })
  return import(`data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`)
}
const { api, ApiError } = await loadTypeScript('../src/lib/api.ts')
const { draftKey, readDraft, writeDraft } = await loadTypeScript('../src/lib/drafts.ts')
const originalFetch = globalThis.fetch
const originalStorage = globalThis.localStorage
afterEach(() => { globalThis.fetch = originalFetch; globalThis.localStorage = originalStorage })

test('writes use the same-origin session and the required request header', async () => {
  let captured
  globalThis.fetch = async (url, init) => { captured = { url, ...init }; return Response.json({ attempt: { id: 'attempt-1' } }) }
  await api.submit('set/1', 3, { q1: 'answer' })
  assert.equal(captured.url, '/api/sets/set%2F1/attempts')
  assert.equal(captured.credentials, 'same-origin')
  assert.equal(captured.headers['X-Requested-With'], 'ExamHub')
  assert.deepEqual(JSON.parse(captured.body), { version: 3, answers: { q1: 'answer' } })
})
test('practice uses the answer-free endpoint, never the author detail endpoint', async () => {
  let path
  globalThis.fetch = async url => { path = url; return Response.json({ set: {}, questions: [] }) }
  await api.practice('s1')
  assert.equal(path, '/api/sets/s1/practice')
})
test('conflict errors preserve server message and status for recovery UI', async () => {
  globalThis.fetch = async () => Response.json({ error: '题集版本已变更' }, { status: 409 })
  await assert.rejects(() => api.submit('s1', 1, {}), error => error instanceof ApiError && error.status === 409 && error.message === '题集版本已变更')
})
test('a non-JSON failure remains an actionable error', async () => {
  globalThis.fetch = async () => new Response('<html>Bad gateway</html>', { status: 502 })
  await assert.rejects(() => api.config(), error => error instanceof ApiError && error.status === 502)
})
test('drafts are isolated across user, set, and question version', () => {
  const storage = new Map()
  globalThis.localStorage = {getItem: key => storage.get(key) ?? null, setItem: (key,value) => storage.set(key,value)}
  writeDraft(draftKey('u1','s1',1), {q1:'A'})
  assert.deepEqual(readDraft(draftKey('u1','s1',1),['q1']), {q1:'A'})
  for (const args of [['u2','s1',1],['u1','s2',1],['u1','s1',2]]) assert.deepEqual(readDraft(draftKey(...args),['q1']), {})
})
test('draft recovery ignores corrupt data, unknown questions, and non-string answers', () => {
  globalThis.localStorage = {getItem: () => '{broken'}
  assert.deepEqual(readDraft('key',['q1']), {})
  globalThis.localStorage = {getItem: () => '{"q1":"A","q2":42,"unknown":"B"}'}
  assert.deepEqual(readDraft('key',['q1','q2']), {q1:'A'})
})
