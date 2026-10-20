import test from 'node:test'
import assert from 'node:assert/strict'
import { nextTick } from 'vue'
import { script } from './harness.mjs'

const questions = Array.from({length: 25}, (_, index) => ({
  id: `q${index}`, type: index % 2 ? 'short' : 'single',
  prompt: `Question ${index}`, topic: index % 3 ? '网络' : '事务',
  options: index % 2 ? [] : ['TCP', 'UDP'], answer: 'TCP', source: ''
}))

async function browser() {
  const {filterQuestions} = await script('lib/question-browser.ts', {}, ['filterQuestions'])
  return {filterQuestions, ...await script('views/DetailView.vue', {
    useRoute: () => ({params: {id: 'set'}}), useRouter: () => ({}),
    api: {}, filterQuestions
  }, ['set', 'search', 'typeFilter', 'topicFilter', 'page', 'filteredQuestions', 'visibleQuestions'])}
}

test('question directory combines text, type and topic filters without changing original numbers', async () => {
  const b = await browser()
  const rows = b.filterQuestions(questions, ' tcp ', 'single', '事务')
  assert.deepEqual(rows.map(row => row.index), [0, 6, 12, 18, 24])
  assert.equal(rows[2].question, questions[12])
  assert.deepEqual(b.filterQuestions(questions, '不存在', '', ''), [])
})

test('detail directory renders only ten rows per page and filters across every question', async () => {
  const b = await browser()
  b.set.value = {id: 'set', questions}
  assert.deepEqual(b.visibleQuestions.value.map(row => row.index), [0,1,2,3,4,5,6,7,8,9])
  b.page.value = 3
  assert.deepEqual(b.visibleQuestions.value.map(row => row.index), [20,21,22,23,24])
  b.search.value = 'Question 24'
  await nextTick()
  assert.equal(b.page.value, 1)
  assert.deepEqual(b.visibleQuestions.value.map(row => row.index), [24])
  assert.equal(b.set.value.questions.length, 25)
  b.typeFilter.value = 'short'
  await nextTick()
  assert.deepEqual(b.visibleQuestions.value, [])
})
