<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Attempt } from '../lib/api'
import { date } from '../lib/state'
import Icon from './Icon.vue'
import { automaticScore } from '../lib/scoring'
const props=defineProps<{attempt:Attempt}>(), onlyWrong=ref(false)
const score=computed(()=>automaticScore(props.attempt))
const results=computed(()=>props.attempt.results.filter(r=>!onlyWrong.value||r.correct===false))
const shortCount=computed(()=>props.attempt.results.filter(r=>r.correct===null).length)
</script>
<template><section class="result-summary"><div><span class="topic-label">练习已完成</span><h2>{{attempt.setTitle}}</h2><p>{{date(attempt.createdAt)}} · 题集版本 {{attempt.version}}</p></div><div class="result-score"><template v-if="score.total"><strong>{{score.correct}}<span> / {{score.total}}</span></strong><span>单选题答对</span></template><span v-else>无单选题<br/>简答待自评</span></div></section><p v-if="shortCount" class="inline-note"><Icon name="edit"/>{{shortCount}} 道简答题请对照参考答案自行评价，不计入自动得分。</p><div class="section-head"><h2>回顾本次练习</h2><label class="check-label"><input v-model="onlyWrong" type="checkbox"/>只看错题</label></div><div v-if="!results.length" class="empty-state"><Icon name="check"/><h3>本次没有单选错题</h3><p>也可以查看全部题目，回顾简答与解析</p><button class="button" @click="onlyWrong=false">查看全部</button></div><article v-for="(result,i) in results" :key="result.questionId" class="question-preview result-question"><span class="result-indicator" :class="result.correct===null?'manual':result.correct?'correct':'incorrect'"><Icon :name="result.correct===null?'edit':result.correct?'check':'close'"/></span><div class="question-body"><span class="type-label">{{result.correct===null?'简答 · 待自评':result.correct?'单选 · 回答正确':'单选 · 需要回顾'}}</span><h3>{{i+1}}. {{result.prompt}}</h3><ul v-if="result.options?.length" class="preview-options"><li v-for="(option,j) in result.options" :key="j"><span>{{String.fromCharCode(65+j)}}</span>{{option}}</li></ul><div class="answer-comparison"><div><span>你的回答</span><p>{{result.userAnswer||'未作答'}}</p></div><div><span>参考答案</span><p>{{result.answer}}</p></div></div><p v-if="result.explanation" class="explanation">{{result.explanation}}</p><p v-if="result.source" class="source-text">出处：{{result.source}}</p></div></article></template>
