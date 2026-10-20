import { createRouter, createWebHistory } from 'vue-router'
const router = createRouter({ history: createWebHistory(), scrollBehavior: () => ({top:0}), routes: [
  {path:'/', component:() => import('../views/CollectionView.vue'), meta:{title:'学习工作台'}},
  {path:'/library', component:() => import('../views/CollectionView.vue'), meta:{title:'我的题库'}},
  {path:'/discover', component:() => import('../views/CollectionView.vue'), meta:{title:'发现题集'}},
  {path:'/sets/new', component:() => import('../views/EditorView.vue'), meta:{title:'创建题集'}},
  {path:'/sets/:id/edit', component:() => import('../views/EditorView.vue'), meta:{title:'编辑题集'}},
  {path:'/sets/:id', component:() => import('../views/DetailView.vue'), meta:{title:'题集详情'}},
  {path:'/practice/:id', component:() => import('../views/PracticeView.vue'), meta:{title:'专注练习'}},
  {path:'/history', component:() => import('../views/HistoryView.vue'), meta:{title:'学习记录'}},
  {path:'/documents',component:()=>import('../views/DocumentsView.vue'),meta:{title:'我的教材'}},
  {path:'/documents/:id',component:()=>import('../views/DocumentReaderView.vue'),meta:{title:'教材阅读'}},
  {path:'/evaluations',component:()=>import('../views/EvaluationsView.vue'),meta:{title:'评测台'}},
  {path:'/settings', component:() => import('../views/SettingsView.vue'), meta:{title:'模型设置'}},
  {path:'/index', redirect:'/'}, {path:'/index2',redirect:'/'},
  {path:'/:pathMatch(.*)*', component:() => import('../views/NotFoundView.vue'), meta:{title:'页面不存在'}},
] })
router.afterEach(to => document.title = `${to.meta.title} · ExamHub`)
export default router
