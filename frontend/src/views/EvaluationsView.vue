<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api, type BenchmarkReport, type Evaluation, type AIConfig } from '../lib/api'
import { createComparison, type ComparisonState } from '../lib/comparison'
import { percent, downloadJSON, qualityLabel } from '../lib/documents'
import { date, message, user, registerIdentityGuard, notify } from '../lib/state'
import DocumentRange, { type PdfSelection } from '../components/DocumentRange.vue'
import ComparisonReport from '../components/ComparisonReport.vue'
import Icon from '../components/Icon.vue'
const route=useRoute(),benchmark=ref<BenchmarkReport>(),benchmarkBusy=ref(false),benchmarkError=ref(''),error=ref(''),busy=ref(false),config=ref<AIConfig>(),history=ref<Evaluation[]>([]),selected=ref<Evaluation>(),state=ref<ComparisonState|null>(null)
const selection=ref<PdfSelection>({documentId:String(route.query.documentId||''),startPage:Number(route.query.startPage)||1,endPage:Number(route.query.endPage)||1}),rangeError=ref('请选择教材'),count=ref(5)
const key=`examhub:comparison:${user.value!.id}`
const flow=createComparison(api,localStorage,key,value=>state.value=value,beforeStart)
const unfinished=computed(()=>!!state.value&&!['done','ended'].includes(state.value.phase))
let timer:ReturnType<typeof setTimeout>,disposed=false
const labels={queued:'排队中',running:'运行中',completed:'已完成',failed:'失败',cancelled:'已取消'}
const archives=ref<ComparisonState[]>([])
async function beforeStart(saved:ComparisonState){
  config.value=await api.config()
  if(!config.value.configured)throw new Error('下一轮需要模型密钥，请在设置中配置后继续；已有任务和报告仍可读取')
  const previous=saved.baseline?.metadata
  if(previous?.model&&(previous.model!==config.value.model||previous.provider?.replace(/\/$/,'')!==config.value.baseUrl.replace(/\/$/,'')))throw Object.assign(new Error('模型配置与首轮不同，请恢复原配置或结束本次对比'),{status:400})
}
function loadArchives(){archives.value=Array.from({length:localStorage.length},(_,i)=>localStorage.key(i)).filter((item):item is string=>!!item&&item.startsWith(`${key}:archive:`)).flatMap(item=>{try{return [JSON.parse(localStorage.getItem(item)!)]}catch{return []}})}
function endComparison(){
  if(!window.confirm('结束本次对比并保留已有任务记录？已发送的后台任务不会取消，可以导出本地记录。'))return
  try{flow.end();clearTimeout(timer);error.value='';loadArchives()}catch(e){error.value=message(e)}
}
function schedule(){clearTimeout(timer);if(!disposed&&unfinished.value&&!state.value?.paused)timer=setTimeout(()=>run('tick'),1800)}
async function run(action:'start'|'resume'|'tick'){
  if(busy.value)return
  if(action==='start'&&(rangeError.value||!Number.isInteger(count.value)||count.value<1||count.value>10)){error.value=rangeError.value||'题数必须是 1–10 的整数';return}
  busy.value=true;error.value=''
  try{
    if(action==='start')await flow.start({...selection.value,count:count.value,title:'教材出题策略对比',topic:''})
    else if(action==='resume')await flow.resume()
    else await flow.tick()
    if(state.value?.evaluation){selected.value=state.value.evaluation;await loadHistory()}
    schedule()
  }catch(e){error.value=message(e)}finally{busy.value=false}
}
function pause(){clearTimeout(timer);try{flow.pause()}catch(e){error.value=message(e)}}
async function runBenchmark(){benchmarkBusy.value=true;benchmarkError.value='';try{benchmark.value=(await api.benchmark()).report}catch(e){benchmarkError.value=message(e)}finally{benchmarkBusy.value=false}}
async function loadHistory(){try{history.value=(await api.evaluations()).evaluations}catch(e){error.value=message(e)}}
async function openReport(id:string){try{selected.value=(await api.evaluation(id)).evaluation}catch(e){error.value=message(e)}}
const unregister=registerIdentityGuard(reason=>{if(reason==='confirm'&&busy.value){notify('对比请求正在处理中，请等待任务编号保存后切换账户');return false}pause();return true})
onMounted(async()=>{try{loadArchives();flow.restore();if(state.value?.evaluation)selected.value=state.value.evaluation;config.value=await api.config()}catch(e){error.value=message(e)}await loadHistory()})
onBeforeUnmount(()=>{disposed=true;clearTimeout(timer);flow.dispose();unregister()})
</script>
<template><div class="page-container evaluations-page"><header class="page-heading"><div><h1>评测台</h1><p>先验证检测规则，再用同一份教材比较真实生成策略</p></div></header><section class="benchmark-section surface"><div class="section-head"><div><span class="topic-label">固定标注测试集 · 不调用模型</span><h2>检测器回归基准</h2></div><button class="button" :disabled="benchmarkBusy" @click="runBenchmark"><Icon name="check"/>{{benchmarkBusy?'正在运行…':'运行固定集基准'}}</button></div><p class="muted">比较 structural-v1 与 grounded-v2 对原创缺陷样本的检测结果。Precision / Recall 是规则检测指标，不是模型正确率排行榜。</p><p v-if="benchmarkError" class="error" role="alert">{{benchmarkError}}</p><template v-if="benchmark"><div class="benchmark-meta"><span>{{benchmark.datasetId}} · {{benchmark.sampleCount}} 个样本 · {{benchmark.ruleVersion}}</span><button class="text-button" @click="downloadJSON(benchmark,`benchmark-${benchmark.datasetId}.json`)"><Icon name="download"/>导出实际结果</button></div><p class="hash-line">数据集 SHA256 {{benchmark.datasetHash}}</p><div class="benchmark-strategies"><article v-for="strategy in benchmark.strategies" :key="strategy.name"><h3>{{strategy.name}}</h3><div class="quality-summary"><span>Precision {{percent(strategy.precision)}}</span><span>Recall {{percent(strategy.recall)}}</span></div><p class="small muted">TP {{strategy.tp}} · FP {{strategy.fp}} · FN {{strategy.fn}} · TN {{strategy.tn}}</p><details v-for="(sample,sampleIndex) in strategy.samples" :key="sample.id"><summary>样本 {{sampleIndex+1}} · {{sample.label?'标注有缺陷':'标注无缺陷'}} · {{sample.predicted?'已检出':'未检出'}}</summary><p class="small muted">样本编号 {{sample.id}}</p><p v-if="sample.description">{{sample.description}}</p><article v-for="(question,i) in sample.questions" :key="question.id||i" class="benchmark-question"><strong>{{question.prompt}}</strong><p v-for="(option,j) in question.options" :key="j">{{String.fromCharCode(65+j)}}. {{option}}</p><p>参考答案：{{question.answer}}</p><p>{{question.explanation}}</p></article><ul><li v-for="issue in sample.issues" :key="issue">{{qualityLabel(issue)}}</li></ul><p v-if="!sample.issues.length" class="muted small">未报告问题</p></details></article></div><ul class="report-limits"><li v-for="limit in benchmark.limitations" :key="limit">{{limit}}</li></ul></template></section><section class="generation-section"><div class="section-head"><div><span class="topic-label">真实模型调用 · 需要主动启动</span><h2>同页资料，两个生成策略</h2></div></div><div class="evaluation-grid"><section class="surface form-stack"><p class="muted small">按顺序运行 baseline 与 grounded。使用相同教材、物理页、题量及已配置模型，grounded 可进行一次修复。失败仍会保存到报告。</p><DocumentRange v-model="selection" :disabled="unfinished||busy" @validation="rangeError=$event"/><label>每个策略的题数<input v-model.number="count" type="number" min="1" max="10" :disabled="unfinished||busy"/></label><p v-if="!config?.configured" class="inline-note">尚未配置模型密钥。<RouterLink to="/settings">前往设置</RouterLink></p><p v-else class="small muted">当前模型：{{config.model}}。两轮之间请勿修改模型配置。</p><button v-if="!unfinished" class="button primary" :disabled="busy||!config?.configured||!!rangeError" @click="run('start')">启动两轮真实生成<Icon name="right"/></button><template v-else><button v-if="state?.paused" class="button primary" :disabled="busy" @click="run('resume')">继续读取与恢复对比</button><button v-else class="button" @click="pause">暂停后续调用</button><button class="text-button" :disabled="busy" @click="endComparison">结束本次对比并保留记录</button><p class="small muted">暂停不会取消已发送的后台任务；再次继续时先读取已有任务，不重复创建。</p></template></section><section class="comparison-progress surface"><h3>对比进程</h3><p v-if="!state" class="muted">尚未启动模型任务<br/>点击左侧按钮后，才会发起真实调用</p><template v-else><p class="small muted">保存的页范围 {{state.input.startPage}}–{{state.input.endPage}} · 每轮 {{state.input.count}} 题{{state.paused&&!['done','ended'].includes(state.phase)?' · 已暂停':''}}</p><article v-for="strategy in (['baseline','grounded'] as const)" :key="strategy" class="run-stage"><span class="stage-marker"><Icon :name="state[strategy]?.status==='completed'?'check':'history'"/></span><div><h3>{{strategy==='baseline'?'Baseline · 结构校验':'Grounded · 引文验证与修复'}}</h3><p>{{state[strategy]?labels[state[strategy]!.status]:state.requestIds?.[strategy]?'等待恢复任务状态':'尚未启动'}}</p><p v-if="state[strategy]?.metadata?.metricsFinalized===false" class="small muted">等待后台完成调用与计时，暂不启动下一轮</p><p v-if="state[strategy]?.error" class="error">{{state[strategy]?.error}}</p><p v-if="state[strategy]?.metadata" class="small muted">{{state[strategy]?.metadata?.modelCalls}} 次调用 · {{state[strategy]?.metadata?.elapsedMs==null?'耗时未知':(state[strategy]!.metadata!.elapsedMs!/1000).toFixed(2)+' 秒'}}</p></div></article><p v-if="state.phase==='report'" class="inline-note">两轮均已结束，正在建立不可变对比快照</p><p v-if="state.phase==='ended'" class="inline-note">本次对比已结束，已有任务记录保留在本地，可导出后重新开始</p><p v-if="state.error" class="error">{{state.error}}{{state.permanentError?'；可结束本次对比后重新开始':''}}</p><p v-if="state.phase==='done'" class="inline-note">对比报告已保存，可在下方回看或导出</p></template><p v-if="error&&error!==state?.error" class="error" role="alert">{{error}}</p></section></div></section><ComparisonReport v-if="selected" :evaluation="selected"/><section v-if="archives.length" class="evaluation-history"><h2>已结束的本地对比记录</h2><p class="small muted">保留已发生的调用与错误，不代表成功评测。记录仅存于当前浏览器。</p><button v-for="(item,index) in archives" :key="item.operationId" class="button" @click="downloadJSON(item,`comparison-ended-${item.operationId}.json`)">导出记录 {{index+1}} · {{item.input.title}}</button></section><section class="evaluation-history"><div class="section-head"><h2>历史对比快照</h2><button class="text-button" @click="loadHistory">刷新列表</button></div><p v-if="!history.length" class="muted">还没有保存的对比。检测器固定集不产生模型对比记录。</p><button v-for="item in history" :key="item.id" class="history-row" @click="openReport(item.id)"><span class="set-symbol"><Icon name="document"/></span><span class="history-title"><strong>{{item.documentTitle}}</strong><span>{{date(item.createdAt)}} · {{item.model}} · 物理页 {{item.pages.join('、')}}</span></span><Icon name="right"/></button></section></div></template>
