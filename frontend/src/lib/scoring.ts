import type { Attempt } from './api'
export function automaticScore(attempt: Attempt) {
  const single=attempt.results.filter(result=>result.type==='single')
  return {correct:single.filter(result=>result.correct===true).length,total:single.length}
}
export function scoreLabel(attempt: Attempt) {
  const score=automaticScore(attempt)
  return score.total ? `${score.correct} / ${score.total} 道单选正确` : '无单选题 · 简答待自评'
}
