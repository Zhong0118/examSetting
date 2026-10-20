<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api, type Attempt } from '../lib/api'
import { date, message } from '../lib/state'
import Icon from '../components/Icon.vue'
import { automaticScore } from '../lib/scoring'
import AttemptResult from '../components/AttemptResult.vue'
const route=useRoute(), attempts=ref<Attempt[]>([]), selected=ref(''), loading=ref(true),error=ref(''),wrongOnly=ref(false)
const visible=computed(()=>attempts.value.filter(a=>!wrongOnly.value||a.results.some(r=>r.correct===false)))
const active=computed(()=>attempts.value.find(a=>a.id===selected.value))
async function load(){loading.value=true;error.value='';try{attempts.value=(await api.attempts()).attempts;selected.value=String(route.query.attempt||'')}catch(e){error.value=message(e)}finally{loading.value=false}}
onMounted(load)
</script>
<template><div class="page-container history-page"><header class="page-heading"><div><p class="heading-note">回顾，是理解的另一半</p><h1>学习记录</h1><p>每一次作答都值得回看，题目与答案保留提交时的版本</p></div></header><template v-if="active"><button class="back-link text-button" @click="selected='' "><Icon name="left"/>返回记录列表</button><AttemptResult :attempt="active"/><RouterLink :to="`/practice/${active.setId}`" class="button primary">再次练习<Icon name="right"/></RouterLink></template><template v-else><div class="section-head"><h2>练习足迹</h2><label class="check-label"><input v-model="wrongOnly" type="checkbox"/>只看有错题的练习</label></div><div v-if="loading" class="loading">正在读取学习记录…</div><div v-else-if="error" class="empty-state"><p>{{error}}</p><button class="button" @click="load">重试</button></div><div v-else-if="!visible.length" class="empty-state"><Icon name="history"/><h2>{{wrongOnly?'没有需要回顾的单选错题':'你的第一步，会被记住'}}</h2><p>{{wrongOnly?'取消筛选，查看全部学习记录':'完成一次练习，这里会保留你的答案与解析'}}</p><button v-if="wrongOnly" class="button" @click="wrongOnly=false">查看全部记录</button><RouterLink v-else to="/discover" class="button primary">去发现题集<Icon name="right"/></RouterLink></div><div v-else class="history-list"><button v-for="attempt in visible" :key="attempt.id" class="history-row" @click="selected=attempt.id"><span class="set-symbol"><Icon name="document"/></span><span class="history-title"><strong>{{attempt.setTitle}}</strong><span>{{date(attempt.createdAt)}} · 版本 {{attempt.version}} · {{attempt.results.length}} 道题</span></span><span class="history-score"><template v-if="automaticScore(attempt).total"><strong>{{automaticScore(attempt).correct}} / {{automaticScore(attempt).total}}</strong><span>单选题答对</span></template><span v-else>无单选题 · 简答待自评</span></span><Icon name="right"/></button></div></template></div></template>
