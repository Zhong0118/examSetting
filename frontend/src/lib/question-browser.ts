import type { Question } from './api'

export function filterQuestions(questions: Question[], query: string, type: string, topic: string) {
  const text = query.trim().toLowerCase()
  return questions.map((question, index) => ({question, index})).filter(({question}) =>
    (!type || question.type === type) && (!topic || question.topic === topic) &&
    `${question.prompt} ${question.topic} ${question.options.join(' ')}`.toLowerCase().includes(text))
}
