<script setup lang="ts">
import type { QualityReport } from '../lib/api'
import { percent, qualityLabel } from '../lib/documents'
import Icon from './Icon.vue'
const props=defineProps<{report: QualityReport; stale?: boolean}>()
function ordinal(id:string){const index=props.report.items.findIndex(item=>item.questionId===id);return index<0?'未定位题目':`第 ${index+1} 题`}
function checkMessage(check:QualityReport['items'][number]['checks'][number]){
  if(check.code!=='duplicate')return check.message
  return props.report.items.reduce((text,item)=>text.split(item.questionId).join(ordinal(item.questionId)),check.message)
}
</script>
<template><section class="quality-panel"><div class="section-head"><h3><Icon name="check"/>题目质量检查</h3><span class="badge">{{report.ruleVersion}}</span></div><p v-if="stale" class="inline-note">题目已修改，以下报告对应上次检查，请重新检查。</p><div class="quality-summary"><span><strong>{{report.passed}} / {{report.total}}</strong> 题通过规则</span><span>规则通过率 {{percent(report.passRate)}}</span><span>引用覆盖 {{percent(report.citationCoverage)}}</span></div><details v-for="(item,index) in report.items" :key="item.questionId" :open="!item.passed"><summary>第 {{index+1}} 题 · {{item.passed?'规则通过':'需要检查'}}</summary><ul class="quality-checks"><li v-for="check in item.checks" :key="check.code" :class="check.status"><Icon :name="check.status==='pass'?'check':'warning'"/><span>{{checkMessage(check)}}<small>{{qualityLabel(check.code)}}</small></span></li></ul></details><p v-for="(pair,index) in report.duplicatePairs" :key="index" class="small muted">重复候选：{{ordinal(pair.left)}} 与 {{ordinal(pair.right)}}，词面相似度 {{percent(pair.similarity)}}</p><ul class="report-limits"><li v-for="limit in report.limits" :key="limit">{{limit}}</li><li v-if="!report.limits.length">规则通过不等于事实正确，也不代表学习效果。</li></ul></section></template>
