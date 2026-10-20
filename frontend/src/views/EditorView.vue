<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import { api, ApiError, type Question, type SetInput } from '../lib/api'
import { message, notify, user, registerIdentityGuard } from '../lib/state'
import Icon from '../components/Icon.vue'
import AIGenerator from '../components/AIGenerator.vue'
const route=useRoute(),router=useRouter(),editing=!!route.params.id,loading=ref(editing),busy=ref(false),error=ref(''),conflict=ref(false),baseline=ref(''),canEdit=ref(!editing)
const form=ref<SetInput>({title:'',description:'',topic:'',visibility:'private',questions:[]})
baseline.value=JSON.stringify(form.value)
const dirty=computed(()=>JSON.stringify(form.value)!==baseline.value)
const targetId=ref<string | undefined>(editing?String(route.params.id):undefined)
const recoveryKey=`examhub:editor:${user.value!.id}:${route.params.id || 'new'}`
function preserveEditor() {
  if(!dirty.value)return true
  try { localStorage.setItem(recoveryKey,JSON.stringify({form:form.value,targetId:targetId.value}));return true }
  catch { notify('无法保存编辑草稿，请先保留当前内容；账户暂未切换');return false }
}
const removeIdentityGuard=registerIdentityGuard(reason=>{
  if(reason==='preserve')return preserveEditor()
  if(busy.value){notify('题集正在保存，请等待完成后切换账户');return false}
  if(dirty.value && !window.confirm('切换账户前会保留当前编辑草稿。确定切换吗？'))return false
  return preserveEditor()
})
function restoreEditor() {
  try { const saved=JSON.parse(localStorage.getItem(recoveryKey)||'null');if(saved?.form?.title!==undefined && Array.isArray(saved.form.questions)){form.value=saved.form;targetId.value=saved.targetId || targetId.value;notify('已恢复当前账户的未保存编辑草稿')} } catch { /* Never delete unreadable recovery data. */ }
}
function blank(type:'single'|'short'='single'):Question{return {id:crypto.randomUUID(),type,prompt:'',options:type==='single'?['','']:[],answer:'',explanation:'',source:'',topic:''}}
function add(type:'single'|'short'){form.value.questions.push(blank(type))}
function changeType(q:Question){q.options=q.type==='single'?['','']:[];q.answer=''}
function importQuestions(questions:Question[]){form.value.questions.push(...questions);notify(`已导入 ${questions.length} 道题，请检查并保存`)}
function validate(){if(!form.value.questions.length)return '请至少添加一道题';for(const [i,q] of form.value.questions.entries()){if(!q.prompt.trim())return `第 ${i+1} 题缺少题干`;if(q.type==='single'){if(q.options.length<2||q.options.some(o=>!o.trim()))return `第 ${i+1} 题至少需要两个非空选项`;if(new Set(q.options.map(o=>o.trim())).size!==q.options.length)return `第 ${i+1} 题的选项不能重复`;if(!q.options.includes(q.answer||''))return `请为第 ${i+1} 题选择正确答案`}else if(!q.answer?.trim())return `请填写第 ${i+1} 题的参考答案`}return ''}
async function save(){
  if(!canEdit.value||busy.value)return
  error.value=validate();if(error.value)return
  busy.value=true
  const snapshot: SetInput=JSON.parse(JSON.stringify(form.value))
  try {
    const result=await api.save(snapshot,targetId.value)
    const unchanged=JSON.stringify(form.value)===JSON.stringify(snapshot)
    targetId.value=result.set.id
    form.value.version=result.set.version
    snapshot.version=result.set.version
    baseline.value=JSON.stringify(snapshot)
    if(!unchanged){preserveEditor();notify('已保存提交时的版本，后续修改仍在编辑器中，请再次保存');return}
    try{localStorage.removeItem(recoveryKey)}catch{}
    notify('题集已保存');await router.push(`/sets/${result.set.id}`)
  }catch(e){error.value=message(e);conflict.value=e instanceof ApiError&&e.status===409&&e.code!=='session_changed'}finally{busy.value=false}
}
async function load(restore=true){loading.value=true;error.value='';try{const {set}=await api.set(String(route.params.id));if(!set.isOwner){error.value='只有作者可以编辑题集';return}canEdit.value=true;form.value={title:set.title,description:set.description,topic:set.topic,visibility:set.visibility,version:set.version,questions:set.questions};baseline.value=JSON.stringify(form.value);conflict.value=false;if(restore)restoreEditor();else{try{localStorage.removeItem(recoveryKey)}catch{}}}catch(e){error.value=message(e)}finally{loading.value=false}}
function reload(){if(window.confirm('重新加载将丢弃当前未保存的修改，继续吗？'))return load(false)}
function beforeUnload(e:BeforeUnloadEvent){if(dirty.value){e.preventDefault();e.returnValue=''}}
onBeforeRouteLeave(()=>!dirty.value||window.confirm('当前题集有未保存的修改，确定离开吗？'))
onMounted(()=>{if(editing)load();else{form.value.questions=[blank()];baseline.value=JSON.stringify(form.value);restoreEditor()}window.addEventListener('beforeunload',beforeUnload)})
onBeforeUnmount(()=>{removeIdentityGuard();window.removeEventListener('beforeunload',beforeUnload)})
</script>
<template><div class="page-container editor-page"><RouterLink :to="editing?`/sets/${route.params.id}`:'/library'" class="back-link"><Icon name="left"/>{{editing?'返回题集':'返回题库'}}</RouterLink><header class="page-heading"><div><h1>{{editing?'编辑题集':'创建一份题集'}}</h1><p>把值得记住的内容，变成值得思考的问题</p></div><span class="muted small">{{form.questions.length}} 道题 · {{dirty?'有未保存的修改':'准备就绪'}}</span></header><div v-if="loading" class="loading">正在读取题集…</div><div v-else-if="canEdit" class="editor-grid"><form @submit.prevent="save"><section class="surface form-stack"><h2>题集信息</h2><label>题集名称<input v-model="form.title" required maxlength="200" placeholder="例如：计算机网络 · 传输层基础"/></label><label>题集简介<textarea v-model="form.description" rows="2" maxlength="2000" placeholder="这份题集适合谁，希望理解哪些内容"/></label><div class="form-columns"><label>主题<input v-model="form.topic" maxlength="80" placeholder="例如：计算机网络"/></label><label>可见范围<select v-model="form.visibility"><option value="private">仅自己可见</option><option value="unlisted">持有链接的人可见</option><option value="public">公开到发现页</option></select></label></div><p class="muted small">{{form.visibility==='private'?'私有题集只有自己可以打开':form.visibility==='unlisted'?'不会出现在发现页，可将链接分享给他人':'其他人可以发现、练习并复制改编此题集'}}</p></section><div class="section-head questions-heading"><h2>编辑题目</h2><span class="small muted">单选自动判分 · 简答自行对照</span></div><TransitionGroup name="list" tag="div" class="question-editor-list"><section v-for="(q,index) in form.questions" :key="q.id" class="surface question-editor"><div class="section-head"><div class="row"><span class="editor-number">{{String(index+1).padStart(2,'0')}}</span><select v-model="q.type" :aria-label="`第 ${index+1} 题题型`" @change="changeType(q)"><option value="single">单选题</option><option value="short">简答题</option></select></div><button type="button" class="icon-button danger" :aria-label="`删除第 ${index+1} 题`" @click="form.questions.splice(index,1)"><Icon name="delete"/></button></div><label>题干<textarea v-model="q.prompt" rows="3" required maxlength="10000" placeholder="写下一个清晰的问题"/></label><div v-if="q.type==='single'" class="editor-options"><p class="small muted">勾选左侧圆点，设为正确答案</p><div v-for="(_,i) in q.options" :key="i" class="editor-option"><input type="radio" :name="`answer-${q.id}`" :checked="q.answer===q.options[i] && !!q.options[i]" :aria-label="`选项 ${String.fromCharCode(65+i)} 为正确答案`" @change="q.answer=q.options[i]"/><span>{{String.fromCharCode(65+i)}}</span><input :value="q.options[i]" required :aria-label="`第 ${index+1} 题选项 ${String.fromCharCode(65+i)}`" placeholder="填写选项" @input="q.answer===q.options[i] && q.options[i] ? q.answer=($event.target as HTMLInputElement).value : null; q.options[i]=($event.target as HTMLInputElement).value"/><button type="button" class="icon-button" :disabled="q.options.length<=2" :aria-label="`删除选项 ${String.fromCharCode(65+i)}`" @click="q.answer===q.options[i] ? q.answer='' : null; q.options.splice(i,1)"><Icon name="close"/></button></div><button v-if="q.options.length<8" type="button" class="text-button" @click="q.options.push('')"><Icon name="plus"/>添加选项</button></div><label v-else>参考答案<textarea v-model="q.answer" required rows="3" placeholder="填写供学习者自评的参考答案"/></label><label>解析<textarea v-model="q.explanation" rows="2" placeholder="解释为什么，帮助建立理解"/></label><div class="form-columns"><label>知识点<input v-model="q.topic" placeholder="可选，如 TCP 拥塞控制"/></label><label>文本出处<input v-model="q.source" placeholder="可选，填写资料原文或出处"/></label></div></section></TransitionGroup><div class="add-question"><button type="button" class="button" @click="add('single')"><Icon name="plus"/>添加单选题</button><button type="button" class="button" @click="add('short')"><Icon name="plus"/>添加简答题</button></div><div v-if="error" class="error" role="alert">{{error}}<button v-if="conflict" type="button" class="text-button" @click="reload">加载最新版本</button></div><div class="save-bar"><span class="small muted">保存后才会更新题集</span><button class="button primary" :disabled="busy||loading">{{busy?'正在保存…':'保存题集'}}<Icon name="check"/></button></div></form><aside><AIGenerator :title="form.title" :topic="form.topic" @import="importQuestions"/><div class="editor-tip"><Icon name="book"/><h3>好问题，留一点思考空间</h3><p>一次只考查一个概念。解析可以说明推理过程，帮助学习者理解答案背后的原因。</p></div></aside></div><div v-else class="error" role="alert">{{error}}<button class="text-button" @click="load()">重试</button></div></div></template>
