<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api, type SetSummary, type Attempt } from '../lib/api'
import { date, message, user, authOpen } from '../lib/state'
import Icon from '../components/Icon.vue'
import SetList from '../components/SetList.vue'
import Pagination from '../components/Pagination.vue'
import { scoreLabel } from '../lib/scoring'
import { draftKey } from '../lib/drafts'
const route=useRoute(), sets=ref<SetSummary[]>([]), attempts=ref<Attempt[]>([]), loading=ref(true), error=ref(''), q=ref(''), topic=ref(''), scope=ref('mine')
const home=computed(()=>route.path==='/'), library=computed(()=>route.path==='/library')
const topics=ref<string[]>([]), total=ref(0), page=ref(1), pageSize=12, homeSets=ref<SetSummary[]|null>(null)
const resumed=computed(()=>homeSets.value?.find(s=>{try{return Object.values(JSON.parse(localStorage.getItem(draftKey(user.value!.id,s.id,s.version))||'{}')).some(a=>typeof a==='string'&&a.trim())}catch{return false}}))
const featured=computed(()=>resumed.value||homeSets.value?.find(s=>s.id===attempts.value[0]?.setId)||homeSets.value?.[0])
let generation=0, disposed=false, timer:ReturnType<typeof setTimeout>|undefined, historyRequest:Promise<{attempts:Attempt[]}>|undefined
function invalidate(){generation++;clearTimeout(timer);loading.value=true;error.value='';sets.value=[];total.value=0}
async function load(){
  if(disposed)return
  invalidate()
  const current=generation, initialHome=home.value&&homeSets.value===null&&page.value===1&&!q.value&&!topic.value
  try{
    if(home.value&&!historyRequest)historyRequest=api.attempts().catch(e=>{historyRequest=undefined;throw e})
    const [collection,history]=await Promise.all([api.setsPage(home.value?'workspace':library.value?scope.value:'discover',{page:page.value,pageSize,q:q.value,topic:topic.value}),home.value?historyRequest:Promise.resolve({attempts:[]})])
    if(disposed)return
    // The initial workspace page remains the recommendation source during later filtering.
    if(initialHome&&homeSets.value===null)homeSets.value=collection.sets
    if(current!==generation)return
    sets.value=collection.sets;total.value=collection.total;page.value=collection.page;topics.value=collection.topics;attempts.value=history!.attempts
  }catch(e){if(current===generation)error.value=message(e)}finally{if(current===generation)loading.value=false}
}
function changePage(next:number){if(loading.value||next===page.value||next<1||next>Math.ceil(total.value/pageSize))return;page.value=next;void load()}
watch(scope,()=>{topic.value='';topics.value=[]},{flush:'sync'})
watch([q,topic,scope],([query],[previous])=>{
  if(disposed)return
  page.value=1;invalidate()
  if(query!==previous)timer=setTimeout(load,250)
  else{const current=generation;void nextTick(()=>{if(current===generation)void load()})}
},{flush:'sync'})
onMounted(load)
onBeforeUnmount(()=>{disposed=true;generation++;clearTimeout(timer)})
</script>
<template>
<div class="page-container">
  <header class="page-heading">
    <div><h1>{{home?'学习工作台':library?'我的题库':'发现题集'}}</h1><p>{{home?'继续练习 或整理一份新的题集':library?'管理自己创建和收藏的题集':'浏览公开题集 保存或复制到自己的题库'}}</p></div>
    <RouterLink v-if="home" to="/documents" class="button"><Icon name="document"/>导入教材</RouterLink>
    <RouterLink v-else to="/sets/new" class="button primary"><Icon name="plus"/>创建题集</RouterLink>
  </header>
  <div class="workbench-grid" :class="{'collection-full':!home}">
    <div class="main-column">
      <section v-if="home" class="study-feature">
        <div class="feature-content"><span class="feature-label"><span class="status-dot"/>{{resumed?'上次未完成':'从这份题集开始'}}</span><h2>{{featured?.title||'还没有可练习的题集'}}</h2><p>{{featured?`${featured.topic||'综合学习'} · ${featured.questionCount} 道题`:'创建题集 或从公开题集开始'}}</p></div>
        <RouterLink :to="featured?`/practice/${featured.id}`:'/sets/new'" class="button primary">{{resumed?'继续练习':featured?'开始练习':'创建题集'}}<Icon name="right"/></RouterLink>
      </section>
      <div v-if="home" class="section-head collection-heading"><h2>按主题筛选</h2><RouterLink to="/discover" class="text-button">全部题集<Icon name="right"/></RouterLink></div>
      <div v-if="home&&topics.length" class="topic-collections"><button v-for="item in topics.slice(0,3)" :key="item" type="button" :class="{selected:topic===item}" :aria-pressed="topic===item" @click="topic=topic===item?'':item"><Icon name="library"/><strong>{{item}}</strong></button></div>
      <section class="library-section">
        <div class="section-head"><h2>{{home?'题集':library?'题集列表':'公开题集'}}</h2><span v-if="!loading&&!error" class="muted small">{{total}} 份题集</span></div>
        <div class="collection-toolbar">
          <div v-if="library" class="tabs" aria-label="题库范围" :style="{'--tab-index':scope==='saved'?1:0}"><button :class="{active:scope==='mine'}" :aria-pressed="scope==='mine'" @click="scope='mine'">我创建的</button><button :class="{active:scope==='saved'}" :aria-pressed="scope==='saved'" @click="scope='saved'">我收藏的</button></div>
          <label class="search-field"><Icon name="search"/><input v-model="q" aria-label="搜索题集" placeholder="搜索题集或知识点"/></label><select v-model="topic" aria-label="筛选主题"><option value="">全部主题</option><option v-for="item in topics" :key="item">{{item}}</option></select>
        </div>
        <Transition name="fade" mode="out-in">
        <div v-if="loading" class="loading" role="status">正在获取题集…</div>
        <div v-else-if="error" class="empty-state"><Icon name="warning"/><h3>题集加载失败</h3><p>{{error}}</p><button class="button" @click="load">重试</button></div>
        <SetList v-else-if="sets.length" :sets="sets"/>
        <div v-else class="empty-state"><Icon name="library"/><h3>{{q||topic?'没有匹配的题集':'还没有题集'}}</h3><p>{{q||topic?'试试其他关键词 或清除筛选':'创建题集 或从公开题集开始练习'}}</p><button v-if="q||topic" class="button" @click="q='';topic=''">清除筛选</button><RouterLink v-else :to="library&&scope==='saved'?'/discover':'/sets/new'" class="button primary">{{library&&scope==='saved'?'发现题集':'创建题集'}}</RouterLink></div>
        </Transition>
        <Pagination v-if="!loading&&!error" :page="page" :total="total" :page-size="pageSize" label="题集分页" @change="changePage"/>
      </section>
    </div>
    <aside v-if="home" class="context-rail">
      <section class="rail-recent"><div class="section-head"><h3>最近练习</h3><Icon name="history"/></div><template v-if="attempts.length"><RouterLink v-for="attempt in attempts.slice(0,3)" :key="attempt.id" :to="`/history?attempt=${attempt.id}`" class="recent-item"><strong>{{attempt.setTitle}}</strong><span>{{date(attempt.createdAt)}} · {{scoreLabel(attempt)}}</span></RouterLink></template><p v-else class="muted">暂无练习记录<br/>完成练习后会显示在这里</p><RouterLink to="/history" class="text-button">查看学习记录<Icon name="right"/></RouterLink></section>
      <section class="rail-shortcuts"><h3>学习工具</h3><RouterLink to="/documents"><Icon name="book"/>查看教材<Icon name="right"/></RouterLink><RouterLink to="/tutor"><Icon name="ai"/>开启教学会话<Icon name="right"/></RouterLink></section>
      <div class="rail-note"><Icon name="lock"/><p v-if="!user?.email">当前为访客空间<br/><button class="text-button" @click="authOpen=true">绑定账户保留学习记录</button></p><p v-else>内容与记录保存在当前账户</p></div>
    </aside>
  </div>
</div>
</template>
